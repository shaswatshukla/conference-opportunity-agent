import copy
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from jsonschema import ValidationError

from src.common import ROOT
from src.dedupe import dedupe
from src.extract import digest, extract, validate
from src.http import Page
from src.main import FixtureClient, discover
from src.report import render
from src.sources import era
from src.store import connect, latest, save
from src.verify import verify


class PipelineTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        (ROOT / "data/test-tmp").mkdir(parents=True, exist_ok=True)

    def setUp(self):
        self.client = FixtureClient(ROOT / "tests/fixtures")
        self.page = self.client.fetch("https://erafellowship.org/")
        self.events, self.mode = extract(self.page, ROOT / "tests/fixtures/extractions")
        self.event = copy.deepcopy(self.events[0])

    def test_schema_rejects_extra_fields(self):
        self.event["invented"] = "unsupported"
        with self.assertRaises(ValidationError):
            validate({"events": [self.event]}, self.page)

    def test_schema_rejects_missing_required_fields(self):
        del self.event["eligibility"]
        with self.assertRaises(ValidationError):
            validate({"events": [self.event]}, self.page)

    def test_rejects_fabricated_quote(self):
        self.event["ticket_prices"] = {"value": "Free", "quote": "All attendees get free flights."}
        with self.assertRaises(ValueError):
            validate({"events": [self.event]}, self.page)

    def test_rejects_fabricated_value_with_real_quote(self):
        self.event["ticket_prices"] = {"value": "Free", "quote": self.event["name"]["quote"]}
        with self.assertRaises(ValueError):
            validate({"events": [self.event]}, self.page)

    def test_unknown_is_explicit(self):
        self.assertEqual(self.event["ticket_prices"], {"value": "unknown", "quote": ""})
        self.event["ticket_prices"]["quote"] = "not evidence"
        with self.assertRaises(ValueError):
            validate({"events": [self.event]}, self.page)

    def test_changed_page_requires_new_extraction(self):
        changed = copy.copy(self.page)
        changed.html += "<p>Changed page.</p>"
        with patch.dict("os.environ", {}, clear=True):
            events, mode = extract(changed, ROOT / "tests/fixtures/extractions")
        self.assertEqual(events, [])
        self.assertEqual(mode, "no_extractor_configured")

    def test_wrong_page_identity_rejected(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            Path(directory, digest(self.page) + ".json").write_text(
                json.dumps(
                    {
                        "page_url": "https://imposter.example/",
                        "page_sha256": digest(self.page),
                        "payload": {"events": []},
                    }
                )
            )
            with self.assertRaises(ValueError):
                extract(self.page, Path(directory))

    def test_fixture_is_never_live_verified(self):
        record = verify(self.event, era, self.client, self.page, self.mode)
        self.assertEqual(record["confidence"], "unverified")
        self.assertEqual(record["last_verified"], "unknown")

    def test_foreign_host_not_promoted_to_official(self):
        self.event["official_url"] = "https://aggregator.example/event"
        record = verify(self.event, era, self.client, self.page, self.mode)
        self.assertEqual(record["confidence"], "unverified")

    def test_quote_occurrence_does_not_approve_unreviewed_model_output(self):
        page = Page(self.page.url, self.page.html, self.page.retrieved_at)
        client = type("Client", (), {"fetch": lambda self, url: page})()
        record = verify(self.event, era, client, page, "llm_bridge")
        self.assertEqual(record["confidence"], "unverified")

    def test_reviewed_live_page_can_be_verified(self):
        page = Page(self.page.url, self.page.html, self.page.retrieved_at)
        client = type("Client", (), {"fetch": lambda self, url: page})()
        record = verify(self.event, era, client, page, self.mode)
        self.assertEqual(record["confidence"], "verified")
        self.assertEqual(record["last_verified"], page.retrieved_at)

    def test_dedupe_preserves_quotes_and_different_editions(self):
        first = verify(self.event, era, self.client, self.page, self.mode)
        second = copy.deepcopy(first)
        second["sources"] = ["another-source"]
        second["evidence"]["name"][0]["source_url"] = "https://second.example/"
        merged = dedupe([first, second])
        self.assertEqual(len(merged), 1)
        self.assertEqual(len(merged[0]["evidence"]["name"]), 2)
        second["fields"]["edition"] = "2028"
        self.assertEqual(len(dedupe([first, second])), 2)

    def test_dedupe_preserves_conflicting_eligibility(self):
        first = verify(self.event, era, self.client, self.page, self.mode)
        second = copy.deepcopy(first)
        first["fields"]["eligibility"] = "Over 18"
        second["fields"]["eligibility"] = "Current students"
        merged = dedupe([first, second])[0]
        self.assertEqual(set(merged["conflicts"]["eligibility"]), {"Over 18", "Current students"})
        self.assertEqual(merged["confidence"], "unverified")

    def test_health_warns_after_two_successful_empty_live_runs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            db = connect(Path(directory) / "test.sqlite")
            snapshot = {
                "created_at": self.page.retrieved_at,
                "mode": "live",
                "records": [],
                "leads": [],
                "queued": [],
                "coverage": [
                    {
                        "source": "test",
                        "records": 0,
                        "failures": [],
                        "pages": [],
                        "gaps": [],
                        "empty_streak": 0,
                    }
                ],
            }
            save(db, snapshot)
            self.assertEqual(snapshot["coverage"][0]["empty_streak"], 1)
            save(db, snapshot)
            self.assertEqual(snapshot["coverage"][0]["empty_streak"], 2)
            self.assertIn("BROKEN-SOURCE WARNING", render(snapshot))
            snapshot["coverage"][0]["failures"] = [
                {"url": "https://failed.example/", "reason": "blocked"}
            ]
            save(db, snapshot)
            self.assertEqual(snapshot["coverage"][0]["empty_streak"], 2)
            self.assertEqual(latest(db, "live")["coverage"][0]["empty_streak"], 2)
            db.close()

    def test_end_to_end_fixture_run_preserves_unknown_costs(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data/test-tmp") as directory:
            import shutil

            target = Path(directory)
            shutil.copytree(ROOT / "tests/fixtures", target / "tests/fixtures")
            shutil.copytree(ROOT / "data/reference", target / "data/reference")
            profile_file = ROOT / "data/profile.yaml"
            if not profile_file.exists():
                profile_file = ROOT / "data/profile.example.yaml"
            shutil.copy(profile_file, target / "data/profile.yaml")
            snapshot, report = discover(target, fixture=True)
            self.assertGreaterEqual(len(snapshot["records"]), 3)
            self.assertTrue(report.exists())
            self.assertTrue(all(r["last_verified"] == "unknown" for r in snapshot["records"]))
            self.assertTrue(all(r["confidence"] == "unverified" for r in snapshot["records"]))
            self.assertTrue(
                all(
                    r["fields"]["name"] != "The London Initiative for Safe AI"
                    for r in snapshot["records"]
                )
            )
            self.assertTrue((target / "data/fixture-opportunities.csv").exists())
            self.assertFalse((target / "data/opportunities.csv").exists())


if __name__ == "__main__":
    unittest.main()
