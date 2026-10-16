"""Read-only discovery and scoring CLI. No application or messaging actions."""

import argparse
import hashlib
import importlib
import json
from dataclasses import asdict
from datetime import datetime, timedelta, timezone

import yaml

from .classify import classify
from .common import ROOT, config, load_dotenv, now
from .dedupe import dedupe
from .extract import extract
from .feasibility import FX, evaluate, reference
from .http import AccessError, Client, Page
from .report import write
from .score import rank, score
from .sources.base import collect
from .store import connect, latest, save
from .verify import verify


class FixtureClient:
    def __init__(self, directory):
        self.directory = directory
        self.audit = []
        self.entries = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))

    def fetch(self, url):
        entry = self.entries.get(url)
        if entry and "error" in entry:
            raise AccessError(entry["error"])
        if entry is None:
            raise AccessError("No saved fixture for this URL; no network fallback")
        return Page(
            entry.get("canonical_url", url),
            (self.directory / entry["file"]).read_text(encoding="utf-8"),
            entry["retrieved_at"],
            fixture=True,
        )


def discover(root=ROOT, fixture=False):
    settings = config("sources.yaml")
    watchlist = config("watchlist.yaml")
    if any(entry["selected_identity"] == "unknown" for entry in watchlist["entries"]):
        raise ValueError("Resolve every watchlist identity before discovery")
    client = (
        FixtureClient(root / "tests/fixtures")
        if fixture
        else Client(
            root / "data/cache",
            settings["cache_ttl_hours"],
            settings["min_request_interval_seconds"],
        )
    )
    snapshot = {
        "created_at": now(),
        "mode": "fixtures" if fixture else "live",
        "records": [],
        "coverage": [],
        "leads": [],
        "queued": [],
    }
    reviewed = root / ("tests/fixtures/extractions" if fixture else "data/extractions")
    for name in settings["enabled"]:
        if name not in (
            "era",
            "lisa",
            "usenix",
            "europython",
            "pyconde",
            "pyconfi",
            "pyconjp",
            "pyconkr",
            "pyconus",
            "pydata",
            "iiba",
            "dama",
        ):
            raise ValueError("Unknown source adapter")
        source = importlib.import_module("src.sources." + name)
        source.seeds = list(
            dict.fromkeys(
                source.seeds
                + [
                    item["official_url"]
                    for item in config("seeds.yaml")["seeds"]
                    if item["adapter"] == name
                ]
            )
        )
        batch = collect(source, client, settings["max_pages_per_source"])
        coverage = {
            "source": name,
            "pages": [],
            "records": 0,
            "failures": batch.failures,
            "gaps": [],
            "empty_streak": 0,
            "aliases": batch.aliases,
            "region": getattr(source, "region", "UK" if name in ("era", "lisa") else "US / Europe"),
        }
        for page in batch.pages:
            coverage["pages"].append({k: v for k, v in asdict(page).items() if k != "html"})
            try:
                events, mode = extract(page, reviewed, getattr(source, "rules", None))
                if mode == "no_extractor_configured":
                    coverage["gaps"].append("No extraction available for " + page.url)
                    snapshot["leads"].append(page.url)
                if not events and mode != "no_extractor_configured":
                    coverage["gaps"].append(
                        "No edition-specific opportunity extracted from " + page.url
                    )
                for event in events:
                    snapshot["records"].append(verify(event, source, client, page, mode))
                    coverage["records"] += 1
            except (ValueError, KeyError) as error:
                coverage["failures"].append(
                    {"url": page.url, "reason": type(error).__name__ + ": extraction rejected"}
                )
                snapshot["leads"].append(page.url)
            except Exception as error:
                # A schema failure must not abort all remaining sources or leak page/provider text.
                from jsonschema import ValidationError

                if not isinstance(error, ValidationError):
                    raise
                coverage["failures"].append(
                    {"url": page.url, "reason": "Strict schema validation failed"}
                )
        snapshot["coverage"].append(coverage)
        snapshot["queued"].extend(batch.queued)
        snapshot["leads"].extend(batch.leads)
    snapshot["records"] = dedupe(snapshot["records"])
    snapshot["stage"] = 4
    today = (
        datetime.fromisoformat(snapshot["created_at"])
        .astimezone(timezone(timedelta(hours=5, minutes=30)))
        .date()
    )
    fx = FX(reference(root, "fx.json"), today)
    visa_data = reference(root, "visa.json")
    profile_path = root / "data/profile.yaml"
    if not profile_path.exists():
        profile_path = root / "data/profile.example.yaml"
    profile = yaml.safe_load(profile_path.read_text(encoding="utf-8-sig"))
    assumptions = config("estimates.yaml")
    weights = config("scoring_weights.yaml")
    interests = config("interests.yaml")["interests"]
    for record in snapshot["records"]:
        record["classification"] = classify(
            record, config("settings.yaml")["low_cost_threshold_usd"], fx.convert
        )
        record["feasibility"] = evaluate(record, assumptions, fx, visa_data, today)
        record["score"] = score(record, weights, interests, profile)
    snapshot["records"] = rank(snapshot["records"])
    verified_urls = {
        r["official_url"] for r in snapshot["records"] if r["confidence"] == "verified"
    }
    verified_urls.update(
        e["source_url"]
        for r in snapshot["records"]
        if r["confidence"] == "verified"
        for items in r["evidence"].values()
        for e in items
        if e["officially_supported"]
    )
    verified_urls.update(
        alias
        for c in snapshot["coverage"]
        for alias, target in c.get("aliases", {}).items()
        if target in verified_urls
    )
    snapshot["leads"] = sorted(set(snapshot["leads"]) - verified_urls)
    snapshot["queued"] = sorted(set(snapshot["queued"]))
    db = connect(root / "data/opportunities.sqlite")
    try:
        save(db, snapshot)
    finally:
        db.close()
    return snapshot, write(snapshot, root)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("discover", "report", "snapshot"))
    parser.add_argument(
        "--fixtures", action="store_true", help="Offline replay; never updates live verification"
    )
    args = parser.parse_args()
    load_dotenv(ROOT / ".env")
    if args.action == "discover":
        snapshot, report = discover(fixture=args.fixtures)
        print(
            f"{len(snapshot['records'])} records; {sum(r['confidence'] == 'verified' for r in snapshot['records'])} verified; report: {report}"
        )
    elif args.action == "report":
        db = connect(ROOT / "data/opportunities.sqlite")
        try:
            print(write(latest(db, "fixtures" if args.fixtures else "live"), ROOT))
        finally:
            db.close()
    else:
        if not args.fixtures:
            parser.error(
                "snapshot requires --fixtures to explicitly save public regression fixtures"
            )
        manifest = {}
        for file in (ROOT / "data/cache").glob("*.json"):
            data = json.loads(file.read_text(encoding="utf-8"))
            if "url" not in data or data["url"].endswith("/robots.txt"):
                continue
            name = hashlib.sha256(data["url"].encode()).hexdigest()[:16] + ".html"
            (ROOT / "tests/fixtures" / name).write_text(data["html"], encoding="utf-8")
            manifest[data["url"]] = {"file": name, "retrieved_at": data["retrieved_at"]}
        from .common import atomic_json

        atomic_json(ROOT / "tests/fixtures/manifest.json", manifest)
        print(f"Saved {len(manifest)} public page fixtures")


if __name__ == "__main__":
    main()
