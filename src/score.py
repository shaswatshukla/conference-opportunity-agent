"""Transparent conservative scores; missing evidence earns no positive points."""

import re

RULES = [
    ("business analysis", ("business analysis", "requirements analysis"), 100),
    ("data analytics", ("data analytics", "business intelligence", "power bi", "tableau"), 100),
    ("data governance", ("data governance", "data stewardship", "data management"), 100),
    ("supply chain", ("supply chain", "logistics"), 100),
    ("product management", ("product management",), 100),
    ("analytics engineering", ("analytics engineering",), 100),
    ("ai safety", ("ai safety", "ai governance", "frontier ai"), 80),
    ("ai", ("ai agents", "ai systems", "artificial intelligence"), 50),
]


def score(record, weights, interests, profile):
    required = {
        "relevance",
        "net_cost",
        "deadline_feasibility",
        "networking_hiring",
        "eligibility_certainty",
    }
    if (
        set(weights) != required
        or any(not isinstance(x, (float, int)) or not 0 <= x <= 1 for x in weights.values())
        or abs(sum(weights.values()) - 1) > 1e-8
    ):
        raise ValueError(
            "Scoring weights must contain exactly five nonnegative weights summing to 1"
        )
    text = " ".join(
        [record["fields"]["name"], record["fields"].get("topics", "unknown")]
        + [e["quote"] for e in record["evidence"].get("topics", [])]
    ).lower()
    interest_text = " ".join(interests).lower()
    matches = []
    for interest, phrases, points in RULES:
        if interest not in interest_text:
            continue
        hits = [phrase for phrase in phrases if re.search(r"\b" + re.escape(phrase) + r"\b", text)]
        if hits:
            matches.append({"interest": interest, "phrases": hits, "points": points})
    relevance = max((m["points"] for m in matches), default=0)
    components = {
        "relevance": {
            "points": relevance,
            "known": True,
            "reason": "Heuristic inference from sourced name/topics and configured interests; strongest match used.",
            "matches": matches,
        },
        "net_cost": {
            "points": 0,
            "known": False,
            "reason": "Personal net cost is unknown; conditional grants and illustrative travel estimates are not affordability evidence.",
        },
        "deadline_feasibility": {
            "points": 0,
            "known": False,
            "reason": "Application status, exact cutoff, visa timing or acceptance timing is unresolved.",
        },
        "networking_hiring": {
            "points": 0,
            "known": False,
            "reason": "No verified recruiter/hiring presence in Germany, Finland or India; sponsors and alumni affiliations do not prove hiring access.",
        },
        "eligibility_certainty": {
            "points": 0,
            "known": False,
            "reason": "Personal eligibility is not established; an MSc does not prove current student status and age is not supplied.",
        },
    }
    cost = record["feasibility"]["total_cost_after_grant_usd"]
    if cost != "unknown" and cost is not None:
        amount = float(cost)
        components["net_cost"].update(
            points=max(0, 100 - amount),
            known=True,
            reason="Published/established personal-cost scenario in USD; USD 0 earns 100, USD 100+ earns 0.",
        )
    remaining = record["feasibility"]["deadline"]["days_remaining"]
    if (
        record["feasibility"]["actionable"]
        and record["feasibility"]["visa"]["lead_days"] == 0
        and isinstance(remaining, int)
        and remaining > 1
    ):
        components["deadline_feasibility"].update(
            points=75 if remaining > 14 else 50 if remaining > 7 else 25,
            known=True,
            reason="Future date-only deadline with no international visa requirement in the attendance scenario; personal availability is still unconfirmed.",
        )
    age = profile.get("age", "unknown")
    if "no formal eligibility restrictions beyond being 18 or older" in record["fields"][
        "eligibility"
    ].lower() and isinstance(age, int):
        components["eligibility_certainty"].update(
            points=100 if age >= 18 else 0,
            known=True,
            reason="The published sole formal age rule was compared with an explicit profile age; selection and immigration eligibility remain separate.",
        )
    if record["fields"]["application_status"] == "closed":
        components["deadline_feasibility"].update(
            known=True, reason="Applications explicitly closed; zero deadline-feasibility points."
        )
    if record["confidence"] != "verified":
        for component in components.values():
            component["points"] = 0
        components["relevance"]["reason"] += " Unverified evidence: no positive points awarded."
    total = round(sum(weights[key] * value["points"] for key, value in components.items()), 2)
    known = round(100 * sum(weights[key] for key, value in components.items() if value["known"]), 2)
    bucket = (
        "closed"
        if record["fields"]["application_status"] == "closed"
        else "open"
        if record["feasibility"]["actionable"]
        else "needs_review"
    )
    return {
        "total": total,
        "scale": 100,
        "known_weight_percent": known,
        "unknowns_earn_zero": True,
        "components": components,
        "weights": weights,
        "bucket": bucket,
        "profile_review_status": profile.get("review_status", "unknown"),
    }


def rank(records):
    order = {"open": 0, "needs_review": 1, "closed": 2}
    return sorted(
        records,
        key=lambda r: (order[r["score"]["bucket"]], -r["score"]["total"], r["fields"]["name"]),
    )
