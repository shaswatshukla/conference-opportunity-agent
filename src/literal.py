"""Conservative no-key refresh: copy literal public facts, never fill missing fields."""

import re

from .pages import parse


def extract_literals(page, rules, fields):
    text, _ = parse(page.html, page.url)
    lines = text.splitlines()
    events = []
    single = any(
        x in page.url.lower()
        for x in (
            "financial-aid",
            "finaid",
            "travel-grants",
            "global-business-analysis-day",
            "global2026",
            "/fellowship",
        )
    )
    for rule in rules:
        match = re.search(rule["name_pattern"], text, re.I)
        if not match:
            continue
        event = {field: {"value": "unknown", "quote": ""} for field in fields}
        event["official_url"] = page.url
        name = match[0]
        name_line = next(
            (line for line in lines if name in line and re.search(r"\b20\d{2}\b", line)),
            next(line for line in lines if name in line),
        )
        event["name"] = {"value": name, "quote": name_line}
        year = re.search(r"\b20\d{2}\b", name_line)
        if year:
            event["edition"] = {"value": year[0], "quote": name_line}

        def add(field, pattern):
            for line in lines:
                if re.search(pattern, line, re.I):
                    event[field] = {"value": line, "quote": line}
                    return

        named_free = next(
            (
                line
                for line in lines
                if name.lower() in line.lower()
                and re.search(r"free[, ]+(?:fully )?(?:24.hour )?virtual", line, re.I)
            ),
            None,
        )
        if named_free:
            event["ticket_prices"] = {"value": named_free, "quote": named_free}
            event["format"] = {"value": "virtual", "quote": named_free}
        if single:
            add(
                "grant_coverage",
                r"Intercontinental Travel Grant:|Travel/Accommodation Grant:|実費の70%|receive.{0,30}stipend|cover.{0,15}(transport|travel)",
            )
            add(
                "eligibility",
                r"open to anyone who needs financial|open to everyone in need|no formal eligibility restrictions",
            )
            add("deadlines", r"20\d{2}-\d{2}-\d{2}.*[Dd]eadline|[Dd]eadline.*20\d{2}-\d{2}-\d{2}")
            add(
                "ticket_prices",
                r"free[, ]+(?:fully )?(?:24.hour )?virtual|free registration|complimentary standard online ticket",
            )
            closed = next(
                (
                    line
                    for line in lines
                    if re.search(r"applications.*(?:closed|ended)|募集は終了", line, re.I)
                ),
                None,
            )
            if closed:
                event["application_status"] = {"value": "closed", "quote": closed}
            virtual = next(
                (
                    line
                    for line in lines
                    if re.search(r"fully virtual|virtual event|virtual conference", line, re.I)
                ),
                None,
            )
            if virtual:
                event["format"] = {"value": "virtual", "quote": virtual}
        topic = next((line for line in lines if name.lower() in line.lower()), name_line)
        event["topics"] = {"value": topic, "quote": topic}
        conference = next(
            (
                line
                for line in lines
                if re.search(r"\bconference\b|カンファレンス|컨퍼런스", line, re.I)
            ),
            None,
        )
        if conference:
            event["programme_kind"] = {"value": "conference", "quote": conference}
        events.append(event)
    return events
