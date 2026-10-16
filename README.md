# Global Opportunity Discovery Agent

[![Tests](https://github.com/shaswatshukla/conference-opportunity-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/shaswatshukla/conference-opportunity-agent/actions/workflows/ci.yml)

A Python data pipeline that discovers conference and funded-programme opportunities, preserves source evidence, and produces a ranked report on a daily GitHub Actions schedule.

**Focus:** business analysis, data analytics, data governance, Python/data communities and AI safety programmes across **Europe, the United States, Japan and South Korea**, plus virtual events worldwide.

[Latest report](reports/latest.md) · [Daily refresh runs](https://github.com/shaswatshukla/conference-opportunity-agent/actions/workflows/schedule.yml) · [Architecture](ARCHITECTURE.md) · [Pipeline diagram](flow.md) · [Source registry](SOURCES.md)

## The problem

Conference fees are only one part of the attendance decision. Financial aid, volunteering, proposal deadlines, eligibility restrictions, travel costs and immigration requirements are scattered across different websites. Aggregator listings alone often omit the evidence needed to act confidently.

This project turns those pages into a repeatable discovery and review workflow. It keeps missing facts visible instead of filling them with guesses, and reports failures alongside findings.

## What is implemented

- **12 source adapters:** ERA, LISA, USENIX, EuroPython, PyCon DE, PyCon Finland, PyCon Japan, PyCon Korea, PyCon US, PyData, IIBA and DAMA.
- **Evidence-aware extraction:** exact source quotes, official URLs, retrieval timestamps and strict JSON validation.
- **Two extraction paths:** conservative literal rules that need no API key, and an optional local LLM bridge with a separate fact-review boundary.
- **Official-source verification:** per-adapter domain allowlists and field-level quote grounding.
- **Conservative deduplication:** edition-aware matching that retains evidence and conflicting values.
- **Opportunity classification:** free access, low-cost tiers, volunteering, grants, proposals and conference competitions; unsupported classifications remain unknown.
- **Transparent ranking:** configurable weights, component-level explanations and zero positive points for missing evidence.
- **Cost and feasibility scenarios:** clearly labelled planning assumptions, dated currency references and immigration-source notes.
- **Persistent reporting:** SQLite run snapshots/source health, Markdown reports and CSV/JSON exports.
- **Hosted operation:** daily refresh at **03:47 UTC / 09:17 India time**, manual workflow dispatch, cached public pages and downloadable run artifacts.

GitHub schedules may be delayed. Configured regions describe the search scope, not a promise of complete coverage or successful access to every source.

## Engineering decisions

| Decision | Purpose |
|---|---|
| Separate source adapters from extraction and verification | Extend discovery without treating every new link as an official source. |
| Preserve quotes and timestamps with each fact | Make a finding inspectable and distinguish cached evidence from a new check. |
| Validate structured output before use | Reject missing fields, unexpected properties and unsupported quotes. |
| Keep unknown values explicit | Avoid presenting an unspecified fee, eligibility rule or grant as confirmed. |
| Retain merge conflicts | Make disagreements reviewable rather than silently choosing a value. |
| Cache pages and persist rate-limit backoff | Reduce repeat requests and respect source limits. |
| Isolate offline fixtures from live verification | Reproduce failures and regressions without calling an archived page freshly verified. |
| Keep personal profiles out of GitHub | Make the project shareable while allowing local personalization. |

## Architecture

```text
Official sources
    → access policy + cached fetch
    → strict extraction + source quotes
    → official-page verification
    → deduplication + conflict preservation
    → classification + feasibility scenarios
    → explained scores
    → SQLite + Markdown + CSV/JSON
    → daily GitHub Actions report
```

Core modules:

| Area | Location |
|---|---|
| Pluggable sources and bounded crawling | `src/sources/` |
| Robots checks, public-only transport, caching and backoff | `src/http.py` |
| JSON schema and optional LLM bridge | `src/extract.py` |
| No-key literal extraction | `src/literal.py` |
| Verification and deduplication | `src/verify.py`, `src/dedupe.py` |
| Classification, costs and scoring | `src/classify.py`, `src/feasibility.py`, `src/score.py` |
| Run history and reports | `src/store.py`, `src/report.py` |
| Scheduled entry point | `src/cloud.py` |

## Run locally

Requires Python 3.11+. From a checkout with an activated virtual environment:

```bash
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m src.main discover --fixtures
python -m src.main discover
python -m src.main report
```

The fixture command works without an extraction API key and produces separate offline outputs. Fixture records remain unverified as live opportunities.

On Windows, `run.ps1` supports `test`, `fixtures`, `discover` and `report`; pass `-Python` to choose an executable. Make targets provide the same common commands where Make is installed.

For local personalization, copy `data/profile.example.yaml` to `data/profile.yaml` and edit it. The personal file is ignored by Git. Hosted runs use the generic example profile.

## Tests and validation

**45 automated tests** cover source contracts, saved pages and access failures, schema validation, fabricated evidence, official-domain checks, redirect aliases, edition-aware merges, conflicting eligibility, cached timestamps, Retry-After persistence, currency conversion/expiry, conditional grants, scoring weights, multilingual text and end-to-end fixture exports.

CI runs lint and tests. The daily workflow separately checks sources, commits the latest report and uploads CSV/JSON evidence artifacts.

## Configuration and outputs

Configuration lives in `config/`: interests, watchlist, regions, sources, recurring seeds, scoring weights and illustrative travel assumptions.

Default scoring weights are relevance **40%**, personal net cost **25%**, deadline feasibility **15%**, networking/hiring evidence **10%** and eligibility certainty **10%**. Relevance is a labelled heuristic. Closed cycles appear below records requiring review.

- `reports/latest.md`: stable link to the latest hosted report.
- `reports/YYYY-WW.md`: weekly digest file refreshed by daily runs.
- `data/opportunities.csv` and `data/opportunities.json`: current live exports.
- `data/opportunities.sqlite`: local/cached run history and source health.
- GitHub workflow artifacts: downloadable reports and exports.

## Boundaries and current limitations

A verified record confirms its known, quoted source facts. It does **not** confirm acceptance, personal eligibility, a grant award, affordability or visa approval.

The initial crawl attempts three pages per source. Some pages are blocked, unavailable, too large or rendered only through JavaScript; the report records those gaps. Native-language evidence is retained. Recurring historical editions do not establish a future edition.

Literal extraction intentionally leaves many dates, prices and conditions unknown. New LLM output stays unverified until reviewed. Ticket-tier normalization, exact deadline/timezone handling and deduplication of incomplete records still need improvement.

Travel budgets are illustrative assumptions, not market quotes. Conditional grants are not deducted as money already awarded. Saved FX references expire after seven days and visa references after thirty days; automatic reference refresh is not implemented.

Application drafts, ICS export and notification delivery are planned features. **The agent never submits applications.**

## Access and privacy

The transport checks robots.txt, paces requests, caches public pages and respects rate-limit backoff. It blocks private-network destinations, embedded credentials and unreviewed query endpoints. No login bypass or CAPTCHA evasion is used; source-specific terms still apply.

Credentials belong only in an ignored `.env`. Personal profiles, application answers, local credentials and drafts are excluded from the published project. See `.env.example` for the optional trusted local LLM-bridge contract.

## Next improvements

- Broader regional feeds and better selection of current-edition links.
- Stronger structured date/ticket extraction and incomplete-record deduplication.
- Automatic dated FX and immigration-reference refresh.
- Profile-grounded draft preparation and validated calendar exports.
