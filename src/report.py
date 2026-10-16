"""Evidence-first classified and ranked report with explicit unknowns."""

import csv
import io
from datetime import datetime, timedelta, timezone

from .common import atomic_json


def md(value):
    return str(value).replace("|", "\\|").replace("\n", " ")


def render(snapshot):
    records = snapshot["records"]
    urgent = [
        r
        for r in records
        if r["confidence"] == "verified"
        and r["fields"]["application_status"] != "closed"
        and isinstance(r.get("feasibility", {}).get("deadline", {}).get("days_remaining"), int)
        and 0 <= r["feasibility"]["deadline"]["days_remaining"] <= 14
    ]
    lines = [
        "# Opportunity discovery: stage 4",
        "",
        f"Run: {snapshot['created_at']} | Mode: {snapshot['mode']}",
        "",
        "Scope includes conferences, fellowships and AI safety programmes.",
        "This is the scoring review checkpoint. Estimates and heuristic scores are separate from verified source facts. Daily GitHub refresh is enabled; application drafts, ICS and alerts remain separate features.",
        "Verified means reviewed facts have grounded quotes on an allowlisted official page; it does not establish personal eligibility, affordability or a grant award.",
        "",
        "## Act this week",
        "",
        "\n".join(
            "- "
            + r["fields"]["name"]
            + ": "
            + r["feasibility"]["deadline"]["date"]
            + " (cutoff/timezone unknown; check official CFP)"
            for r in urgent
        )
        or "No verified deadline within 14 days in this run. Exact cutoff/timezone checks remain necessary before a calendar export.",
        "",
        "## Open applications",
        "",
    ]
    opened = [
        r
        for r in records
        if r["confidence"] == "verified" and r["fields"]["application_status"] == "open"
    ]
    lines.extend(
        [f"- {r['fields']['name']}: {r['official_url']}" for r in opened]
        or ["No verified open application records in this run."]
    )
    lines += [
        "",
        "## Upcoming events by region",
        "",
        "Records are ordered by actionability, then conservative score. Closed cycles stay below opportunities needing review.",
        "",
        "| Name | Kind | Dates | Location | Status | Confidence |",
        "|---|---|---|---|---|---|",
    ]
    for r in records:
        f = r["fields"]
        lines.append(
            "| "
            + " | ".join(
                md(x)
                for x in (
                    f["name"],
                    f["programme_kind"],
                    f["start_date"] + " – " + f["end_date"],
                    f["city"] + ", " + f["country"],
                    f["application_status"],
                    r["confidence"],
                )
            )
            + " |"
        )
    lines += [
        "",
        "## Ranked review",
        "",
        "Scores use relevance 40%, net cost 25%, deadline feasibility 15%, networking/hiring 10%, eligibility certainty 10%. Unknown components earn zero; low scores can reflect missing evidence. Closed records are reference cycles, not application recommendations.",
        "",
        "| Name | Primary type | Score /100 | Bucket | Estimated travel/stay INR | Personal net cost |",
        "|---|---|---|---|---|---|",
        *[
            "| "
            + " | ".join(
                md(x)
                for x in (
                    r["fields"]["name"],
                    r["classification"]["primary_type"],
                    r["score"]["total"],
                    r["score"]["bucket"],
                    r["feasibility"]["estimated_travel_stay_inr"],
                    r["feasibility"]["total_cost_after_grant_inr"],
                )
            )
            + " |"
            for r in records
            if "score" in r
        ],
        "",
        "## Watchlist updates",
        "",
        "LISA = The London Initiative for Safe AI; ERA = ERA:AI Fellowship. Organization pages without an edition-specific opportunity remain source checks rather than invented opportunity records.",
    ]
    lines += ["", "## Unverified leads", ""]
    leads = [r["official_url"] for r in records if r["confidence"] != "verified"] + snapshot[
        "leads"
    ]
    lines.extend(
        [f"- {url}" for url in sorted(set(leads))]
        or ["None emitted. This is not evidence of complete coverage."]
    )
    lines += ["", "## Expired/closed", ""]
    lines.extend(
        [
            f"- {r['fields']['name']} ({r['fields']['edition']}): {r['official_url']}"
            for r in records
            if r["fields"]["application_status"] == "closed"
        ]
        or ["No closed records extracted."]
    )
    lines += ["", "## Evidence and unknowns", ""]
    for r in records:
        lines += [
            f"### {r['fields']['name']}",
            "",
            f"Official URL: {r['official_url']}",
            f"Last verified: {r['last_verified']}",
            f"Extraction: {r['extraction_mode']}",
            "",
        ]
        for field, items in r["evidence"].items():
            for item in items:
                lines.append(
                    f"- {field}: **{md(item['value'])}**. Source quote: “{md(item['quote'])}” ({item['source_url']}; retrieved {item['retrieved_at']})."
                )
        lines += [
            "",
            "Unknown: " + ", ".join(k for k, v in r["fields"].items() if v == "unknown") + ".",
            "",
        ]
        if "score" in r:
            lines += [
                "",
                "Classification rationale: " + md(r["classification"]["rationale"]),
                "",
                "Score rationale:",
                "",
            ]
            for component, info in r["score"]["components"].items():
                lines.append(
                    f"- {component}: {info['points']}/100; {md(info['reason'])} Matches: {md(info.get('matches', []))}"
                )
            cost = r["feasibility"]
            lines += [
                "",
                "Cost/feasibility (estimates, not verified prices):",
                "",
                f"- Travel/stay scenario: INR {cost['estimated_travel_stay_inr']}; USD {cost['estimated_travel_stay_usd']}. FX date: {cost['fx_rate_date']}; source: {cost['fx_source']}.",
                f"- Published support: {md(cost['published_support_amount'])}; INR {cost['published_support_inr']}; USD {cost['published_support_usd']}. {cost['support_note']}",
                f"- Personal net cost: {cost['total_cost_after_grant_inr']}. Missing: {md(cost['unknown_costs'])}.",
                f"- Attendance assumption: {cost['travel_mode_assumption']}.",
                *["- Assumption: " + md(x) for x in cost["assumptions"]],
                f"- Deadline date: {cost['deadline']['date']}; cutoff time/timezone: unknown. Visa timing: {cost['visa']['timing']}.",
                f"- Visa requirement: {md(cost['visa']['requirement'])} Route: {md(cost['visa']['route'])}; lead days: {cost['visa']['lead_days']}.",
                f"- Visa note: {md(cost['visa'].get('note', 'unknown'))}",
            ]
            for source in cost["visa"].get("sources", []):
                lines.append(
                    "- Visa evidence: "
                    + source["url"]
                    + "; "
                    + md(source.get("quotes", source.get("note", "unknown")))
                )
        for warning in r["warnings"]:
            lines.append("- Warning: " + md(warning))
        if r["conflicts"]:
            lines.append("- Conflicting values preserved: " + md(r["conflicts"]))
    lines += [
        "",
        "## Coverage notes",
        "",
        "| Source | Pages checked | Records | Failures | Empty streak |",
        "|---|---|---|---|---|",
    ]
    for c in snapshot["coverage"]:
        lines.append(
            "| "
            + " | ".join(
                md(x)
                for x in (
                    c["source"],
                    len(c["pages"]),
                    c["records"],
                    len(c["failures"]),
                    c["empty_streak"],
                )
            )
            + " |"
        )
        for page in c["pages"]:
            lines.append(
                f"\n- {c['source']}: checked {page['url']} ({page['retrieved_at']}; {'fixture' if page['fixture'] else 'cached' if page['cached'] else 'live'})."
            )
        for failure in c["failures"]:
            lines.append(f"\n- Failed: {failure['url']}: {md(failure['reason'])}")
        if isinstance(c["empty_streak"], int) and c["empty_streak"] >= 2:
            lines.append(
                f"\n- BROKEN-SOURCE WARNING: {c['source']} produced zero extracted records for at least two consecutive successful runs. This may mean no current announcement or an extraction gap; it does not prove the website is broken."
            )
        for gap in c["gaps"]:
            lines.append(f"\n- {c['source']} gap: {md(gap)}")
    lines += ["", "Queued partner/sister URLs are leads only and have not been verified:", ""]
    lines.extend(["- " + url for url in snapshot["queued"]] or ["None."])
    lines += [
        "",
        "Coverage targets Europe (Germany and Finland prioritized), the US, Japan, South Korea, and virtual events worldwide. Likely missing: sources outside the twelve enabled adapters, unindexed local events, external application forms, pagination/links beyond the page budget, private/blocked or JavaScript-only pages, and unsupported fields. No completeness claim.",
        "No messages or applications were sent. GitHub refresh is scheduled daily at 09:17 Asia/Kolkata.",
        "",
    ]
    return "\n".join(lines)


def write(snapshot, root):
    date = datetime.fromisoformat(snapshot["created_at"]).astimezone(
        timezone(timedelta(hours=5, minutes=30))
    )
    week = date.strftime("%G-%V")
    prefix = "fixture-" if snapshot["mode"] == "fixtures" else ""
    reports = root / "reports"
    reports.mkdir(exist_ok=True)
    report = reports / (prefix + week + ".md")
    report.write_text(render(snapshot), encoding="utf-8")
    atomic_json(root / "data" / (prefix + "opportunities.json"), snapshot)
    output = io.StringIO(newline="")
    fields = [
        "name",
        "edition",
        "programme_kind",
        "start_date",
        "end_date",
        "city",
        "country",
        "application_status",
        "official_url",
        "confidence",
        "last_verified",
        "evidence_json",
        "primary_type",
        "score",
        "estimated_travel_stay_inr",
        "estimated_travel_stay_usd",
        "total_cost_after_grant_inr",
    ]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    import json

    for r in snapshot["records"]:
        row = {key: r["fields"].get(key, r.get(key, "unknown")) for key in fields}
        row["evidence_json"] = json.dumps(r["evidence"], ensure_ascii=False)
        row["primary_type"] = r.get("classification", {}).get("primary_type", "unknown")
        row["score"] = r.get("score", {}).get("total", "unknown")
        for key in (
            "estimated_travel_stay_inr",
            "estimated_travel_stay_usd",
            "total_cost_after_grant_inr",
        ):
            row[key] = r.get("feasibility", {}).get(key, "unknown")
        # Neutralize spreadsheet formulas in exported user-controlled strings.
        writer.writerow(
            {
                key: "'" + str(value) if str(value).startswith(("=", "+", "-", "@")) else value
                for key, value in row.items()
            }
        )
    csv_path = root / "data" / (prefix + "opportunities.csv")
    temp = csv_path.with_suffix(".csv.tmp")
    temp.write_text(output.getvalue(), encoding="utf-8-sig")
    temp.replace(csv_path)
    return report
