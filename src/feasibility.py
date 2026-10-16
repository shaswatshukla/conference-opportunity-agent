"""Dated FX conversions, explicit budget assumptions and cautious visa timing."""

import json
import re
from datetime import date
from decimal import Decimal

from .classify import money

MONTHS = {
    name: index
    for index, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        1,
    )
}


class FX:
    def __init__(self, snapshot, today):
        self.snapshot = snapshot
        self.valid = 0 <= (today - date.fromisoformat(snapshot["rate_date"])).days <= 7

    def convert(self, amount, origin, target):
        if origin == target:
            return str(Decimal(str(amount)).quantize(Decimal("0.01")))
        rates = self.snapshot["rates"]
        if not self.valid or origin not in rates or target not in rates:
            return None
        converted = Decimal(str(amount)) / Decimal(str(rates[origin])) * Decimal(str(rates[target]))
        return str(converted.quantize(Decimal("0.01")))


def deadline_date(text):
    # Preserve precision: this parser never supplies a time, timezone or year.
    iso = re.search(r"\b20\d{2}-\d{2}-\d{2}\b", text)
    if iso:
        try:
            return date.fromisoformat(iso[0])
        except ValueError:
            return None
    match = re.search(
        r"\b(" + "|".join(MONTHS) + r")\s+(\d{1,2})(?:st|nd|rd|th)?[,]?\s+(\d{4})\b", text
    )
    if not match:
        return None
    try:
        return date(int(match[3]), MONTHS[match[1]], int(match[2]))
    except ValueError:
        return None


def evaluate(record, assumptions, fx, visa_data, today):
    f = record["fields"]
    country = {
        "United Kingdom": "UK",
        "United States": "USA",
        "United States of America": "USA",
    }.get(f["country"], f["country"])
    result = {
        "origin": assumptions["origin"],
        "travel_mode_assumption": "In-person planning scenario; attendance format is not confirmed"
        if f["format"] == "unknown"
        else f["format"],
        "entry_cost": money(f["ticket_prices"]) or "unknown",
        "estimated_travel_stay_inr": "unknown",
        "estimated_travel_stay_usd": "unknown",
        "total_cost_after_grant_inr": "unknown",
        "total_cost_after_grant_usd": "unknown",
        "fx_rate_date": fx.snapshot["rate_date"] if fx.valid else "unknown",
        "fx_source": fx.snapshot["source_url"],
        "assumptions": [],
        "unknown_costs": [
            "candidate ticket tier",
            "visa fees and appointment costs",
            "insurance",
            "grant award/payment timing and reimbursements",
        ],
        "visa": {
            "requirement": "unknown",
            "route": "unknown",
            "lead_days": "unknown",
            "timing": "unknown",
        },
        "deadline": {
            "date": "unknown",
            "time": "unknown",
            "timezone": "unknown",
            "days_remaining": "unknown",
        },
        "actionable": False,
    }
    budget = assumptions["countries"].get(country)
    if (
        budget
        and f["start_date"] != "unknown"
        and f["end_date"] != "unknown"
        and f["format"] != "virtual"
    ):
        duration = (
            date.fromisoformat(f["end_date"]) - date.fromisoformat(f["start_date"])
        ).days + 1
        if duration <= 0:
            raise ValueError("Event ends before it starts")
        nights = duration + assumptions["buffer_nights"]
        days = duration + assumptions["extra_travel_days"]
        total = (
            budget["return_flight_inr"]
            + nights * budget["accommodation_per_night_inr"]
            + days * budget["meals_and_local_transport_per_day_inr"]
        )
        result["estimated_travel_stay_inr"] = total
        result["estimated_travel_stay_usd"] = fx.convert(total, "INR", "USD") or "unknown"
        result["assumptions"] = [
            f"Illustrative budget only, set {assumptions['assumed_on']}; not a market quote.",
            f"Return flight INR {budget['return_flight_inr']} from {assumptions['origin']}.",
            f"{nights} nights at INR {budget['accommodation_per_night_inr']} per night.",
            f"{days} days of meals/local transport at INR {budget['meals_and_local_transport_per_day_inr']} per day.",
            "Support is conditional and is not deducted without a confirmed award, coverage limits and payment timing.",
        ]
    if f["format"] == "virtual":
        result["estimated_travel_stay_inr"] = 0
        result["estimated_travel_stay_usd"] = "0.00"
        result["visa"] = {
            "requirement": "No international travel in the remote-attendance scenario",
            "route": "not applicable",
            "lead_days": 0,
            "timing": "not applicable",
        }
        if record.get("classification", {}).get("primary_type") == "FREE":
            result["total_cost_after_grant_inr"] = 0
            result["total_cost_after_grant_usd"] = "0.00"
            result["unknown_costs"] = []
    grant = money(f["grant_coverage"])
    result["published_support_amount"] = grant or "unknown"
    result["published_support_inr"] = (
        (fx.convert(grant["amount"], grant["currency"], "INR") or "unknown") if grant else "unknown"
    )
    result["published_support_usd"] = (
        (fx.convert(grant["amount"], grant["currency"], "USD") or "unknown") if grant else "unknown"
    )
    result["support_note"] = (
        "Published support is not an award to this candidate. Accommodation and uncovered costs remain unknown."
    )
    age = (today - date.fromisoformat(visa_data["checked_date"])).days
    if f["format"] == "virtual":
        pass
    elif country == "India":
        result["visa"].update(
            requirement="No international travel in the India-based domestic scenario",
            route="not applicable",
            lead_days=0,
            timing="not applicable",
        )
    elif 0 <= age <= visa_data["max_age_days"] and country in visa_data["rules"]:
        result["visa"].update(visa_data["rules"][country])
        result["visa"]["checked_date"] = visa_data["checked_date"]
    else:
        result["visa"]["note"] = (
            "No fresh country/passport-specific reference; manual official-source check required."
        )
    deadline = deadline_date(f["deadlines"])
    if deadline:
        result["deadline"]["date"] = deadline.isoformat()
        result["deadline"]["days_remaining"] = (deadline - today).days
        if f["start_date"] != "unknown" and isinstance(result["visa"]["lead_days"], int):
            available = (date.fromisoformat(f["start_date"]) - deadline).days
            if available < result["visa"]["lead_days"]:
                result["visa"]["timing"] = "too_close_even_if_application_result_were_immediate"
            else:
                result["visa"]["timing"] = "unknown_acceptance_and_appointment_dates"
    result["actionable"] = (
        record["confidence"] == "verified"
        and f["application_status"] == "open"
        and bool(deadline)
        and (deadline - today).days > 0
    )
    return result


def reference(root, name):
    return json.loads((root / "data/reference" / name).read_text(encoding="utf-8"))
