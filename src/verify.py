"""Field-level official-source checks; fixtures never receive live verification."""

from urllib.parse import urlsplit

from .common import now
from .extract import FIELDS
from .http import AccessError
from .pages import normalize, parse


def verify(event, source, client, discovery_page, extraction_mode):
    official = event["official_url"]
    evidence = {field: [] for field in FIELDS}
    warnings = []
    if urlsplit(official).hostname not in source.hosts:
        official_page = None
        warnings.append("Official identity not established: host outside source allowlist")
    else:
        try:
            official_page = client.fetch(official)
        except AccessError as error:
            official_page = None
            warnings.append("Official verification failed: " + str(error))
    text = normalize(parse(official_page.html, official)[0]) if official_page else ""
    supported = True
    for field in FIELDS:
        fact = event[field]
        if fact["value"] == "unknown":
            continue
        grounded = normalize(fact["quote"]) in text and bool(text)
        evidence[field].append(
            {
                "value": fact["value"],
                "quote": fact["quote"],
                "source_url": discovery_page.url,
                "retrieved_at": discovery_page.retrieved_at,
                "officially_supported": grounded,
                "official_url": official if grounded else "unknown",
            }
        )
        if not grounded:
            supported = False
    fresh = official_page and not official_page.fixture
    verified = bool(
        supported and fresh and extraction_mode in ("reviewed_llm_json", "literal_rules")
    )
    if extraction_mode not in ("reviewed_llm_json", "literal_rules"):
        warnings.append(
            "LLM output requires fact/value review; quote occurrence alone does not establish entailment"
        )
    if official_page and official_page.fixture:
        warnings.append("Fixture replay: not a fresh official verification")
    return {
        "official_url": official,
        "fields": {field: event[field]["value"] for field in FIELDS},
        "evidence": evidence,
        "confidence": "verified" if verified else "unverified",
        "last_verified": official_page.retrieved_at if verified else "unknown",
        "checked_at": now(),
        "sources": [source.name],
        "extraction_mode": extraction_mode,
        "warnings": warnings,
        "conflicts": {},
    }
