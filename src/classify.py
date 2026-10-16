"""One primary access/funding mechanism, distinct from programme kind."""

import re
from decimal import Decimal

PRIORITY = [
    "SCHOLARSHIP/GRANT",
    "VOLUNTEER",
    "SPEAKER/POSTER",
    "HACKATHON/COMPETITION",
    "FREE",
    "LOW_COST",
]


def money(text):
    """Never assume that an unqualified dollar sign means USD."""
    match = re.search(
        r"(?P<currency>USD|INR|GBP|EUR|US\$|£|€|₹)\s*(?P<amount>\d[\d,]*(?:\.\d{1,2})?)", text
    )
    if not match:
        return None
    currency = {"US$": "USD", "£": "GBP", "€": "EUR", "₹": "INR"}.get(
        match["currency"], match["currency"]
    )
    return {"currency": currency, "amount": str(Decimal(match["amount"].replace(",", "")))}


def classify(record, threshold_usd=100, convert=None):
    f = record["fields"]
    ticket, grant, deadline = (
        f[x].lower() for x in ("ticket_prices", "grant_coverage", "deadlines")
    )
    types = []
    reasons = []
    positive_grant = re.search(
        r"receive.{0,30}stipend|travel expense coverage|cover.{0,15}(?:transport|travel)|awarded.{0,20}(?:grant|scholarship)|Intercontinental Travel Grant:|Travel/Accommodation Grant:",
        grant,
    )
    if (
        positive_grant
        or re.search(r"intercontinental travel grant:|travel/accommodation grant:", grant)
    ) and not re.search(r"no (?:stipend|grant|scholarship)|not (?:covered|provided)", grant):
        types.append("SCHOLARSHIP/GRANT")
        reasons.append(
            "Explicit financial support in grant_coverage evidence; award to this candidate is not established."
        )
    positive_free = (
        bool(
            re.search(
                r"free (?:entry|registration|admission|virtual pass)|free[, ]+(?:fully )?(?:24.hour )?virtual|complimentary standard online ticket",
                ticket,
            )
        )
        and "not free" not in ticket
    )
    if "volunteer" in ticket and positive_free:
        types.append("VOLUNTEER")
        reasons.append("Volunteering explicitly linked to free access.")
    if re.search(
        r"(?:talk|paper|poster|workshop|lightning).{0,20}(?:proposal|submission)|call for (?:papers|proposals)",
        deadline,
    ):
        types.append("SPEAKER/POSTER")
        reasons.append(
            "An official CFP/proposal pathway is stated; speaker entry and travel support remain unknown unless explicitly sourced."
        )
    if re.search(r"hackathon|competition", ticket) and positive_free:
        types.append("HACKATHON/COMPETITION")
    if positive_free:
        types.append("FREE")
    price = money(f["ticket_prices"])
    usd = convert(price["amount"], price["currency"], "USD") if price and convert else None
    if usd is not None and Decimal(usd) < Decimal(str(threshold_usd)):
        types.append("LOW_COST")
        reasons.append(
            "A stated ticket tier is below the configured USD threshold; eligibility for that tier still needs verification."
        )
    types = [item for item in PRIORITY if item in types]
    return {
        "primary_type": types[0] if types else "unknown",
        "secondary_types": types[1:],
        "opportunity_confirmed": bool(types) and record["confidence"] == "verified",
        "rationale": reasons,
        "ticket_price": price or "unknown",
    }
