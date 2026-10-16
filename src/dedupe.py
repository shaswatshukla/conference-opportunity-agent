"""Conservative edition-aware fuzzy matching that preserves disagreements."""

import re
from copy import deepcopy
from difflib import SequenceMatcher


def normalize(value):
    return re.sub(r"[^a-z0-9]+", " ", value.lower()).strip()


def matches(a, b):
    left, right = a["fields"], b["fields"]
    # Unknown edition/city only merges on identical official URL, name and edition.
    # Distinct editions must never merge merely because they share a recurring URL.
    if left["edition"] != right["edition"]:
        return False
    for field in ("start_date", "city"):
        x, y = left[field], right[field]
        if x != "unknown" and y != "unknown" and normalize(x) != normalize(y):
            return False
    exact = a["official_url"] == b["official_url"] and normalize(left["name"]) == normalize(
        right["name"]
    )
    if exact:
        return True
    if any(left[x] == "unknown" or right[x] == "unknown" for x in ("edition", "city")):
        return False
    return (
        normalize(left["city"]) == normalize(right["city"])
        and SequenceMatcher(None, normalize(left["name"]), normalize(right["name"])).ratio() >= 0.94
    )


def dedupe(records):
    result = []
    for record in records:
        existing = next((entry for entry in result if matches(entry, record)), None)
        if existing is None:
            result.append(deepcopy(record))
            continue
        existing["sources"] = sorted(set(existing["sources"] + record["sources"]))
        for field, value in record["fields"].items():
            for item in record["evidence"][field]:
                if item not in existing["evidence"][field]:
                    existing["evidence"][field].append(item)
            previous = existing["fields"][field]
            if previous == "unknown":
                existing["fields"][field] = value
            elif value != "unknown" and value != previous:
                existing["conflicts"][field] = sorted(
                    set(existing["conflicts"].get(field, [previous]) + [value])
                )
        existing["warnings"] = sorted(set(existing["warnings"] + record["warnings"]))
        if existing["conflicts"] or record["confidence"] == "unverified":
            existing["confidence"] = "unverified"
            existing["last_verified"] = "unknown"
        elif record["last_verified"] < existing["last_verified"]:
            # All evidence must be fresh; merging cannot make an old fact newer.
            existing["last_verified"] = record["last_verified"]
    return result
