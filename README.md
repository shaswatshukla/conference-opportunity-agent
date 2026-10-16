# Global conference and funded-programme discovery agent

Current stage: **regional discovery with daily GitHub hosting**. LISA means The London Initiative for Safe AI; ERA means ERA:AI Fellowship. The user approved funded fellowships and AI safety programmes alongside conferences.

Twelve source adapters are implemented; see the hosted global refresh section below. Discovery, grounded JSON extraction, official-page verification, deduplication, classification, budget scenarios, dated FX, visa flags, scoring, SQLite, Markdown and CSV exports work. Daily GitHub scheduling is authorized and configured. Drafts, ICS and notifications remain separate unfinished features. No applications or messages have been sent.

## Setup
Use Python 3.11+ and a short checkout path on Windows. From this repository directory:

~~~sh
python -m venv .venv
# Activate the environment using your shell's standard activation command.
python -m pip install -r requirements-dev.txt
python -m unittest discover -s tests -v
python -m src.main discover --fixtures
python -m src.main discover
~~~

On Windows, use .venv/Scripts/python.exe explicitly if needed. In this existing workspace the bundled runtime and local dependencies are already available:

~~~powershell
./run.ps1 test
./run.ps1 fixtures
./run.ps1 discover
./run.ps1 report
~~~

Pass -Python with a Python executable path to run.ps1 to select another installation. On systems with Make, use make discover, make report, make fixtures, make test and make lint. make calendar deliberately fails with a pending-stage message; it does not emit a misleading ICS file.

## Configuration and profile review
Review data/profile.yaml and data/answers.yaml. Current student status, age and application answers are unknown. A completed MSc never establishes current-student eligibility. Edit config/interests.yaml, regions.yaml, watchlist.yaml, sources.yaml, estimates.yaml and scoring_weights.yaml. Region priorities are recorded for the later expanded source layer; current discovery coverage is only the three adapters, not all configured regions. The threshold defaults to strictly under USD 100.

config/estimates.yaml contains illustrative assumptions from Lucknow: flight, nightly accommodation, daily meals/local travel, and buffer days. These are not market quotes. The report shows the arithmetic and assumption date. Entry fees, insurance, immigration costs and conditional grants can leave personal net cost unknown even when a travel subtotal is available. Published stipend amounts are never treated as an award to the candidate. The initial assumptions await your review.

## LLM extraction and evidence review
The initial public-page extractions were generated and checked by the assistant against saved official pages. They live in data/extractions keyed by page SHA256. A changed page must be extracted again; stale JSON is not silently reused.

For new pages, configure an optional trusted local LLM bridge through EXTRACTOR_COMMAND in .env. The value is a JSON array of executable and arguments, invoked without a shell. The bridge receives one JSON request on stdin containing schema, URL, SHA256, public visible page text and grounding instructions, and returns only the extraction JSON on stdout. Its provider credentials belong in .env only. No provider, paid account, network endpoint or model is assumed. See config/extraction.schema.json and src/extract.py for the protocol. Do not pass the profile or personal answers to this extraction bridge.

Every known fact needs an exact source quote. Sensitive values must occur in their quote; unknown values use the literal unknown and an empty quote. Strict schema rejects extra/missing fields. New bridge output remains unverified pending fact/value review: finding a quote on a page alone does not prove that it entails the model's value. Only mark a saved extraction envelope review_status: fact_checked after reviewing all values against its matching page. Until a bridge or reviewed response exists, the page becomes an extraction gap, not a fabricated event. No account is needed for fixture tests.

## Outputs
- reports/YYYY-WW.md: current ranked report, evidence, estimates and coverage.
- data/opportunities.csv and data/opportunities.json: current live snapshot.
- data/opportunities.sqlite: durable run snapshots and source health.
- reports/fixture-YYYY-WW.md and data/fixture-opportunities.*: isolated offline replay; fixtures never receive live verification.
- data/cache/: ignored public-page/robots cache, including rate-limit backoff.

Official URLs are allowlisted per adapter, independently from extracted links. Verified refers to the known reviewed event facts, not affordability, selection, personal eligibility or visa approval. Merge conflicting facts without dropping evidence and demote the conflicting record. Cache use retains original retrieval times. Reports list visited, failed, skipped and queued URLs. Two successful empty source runs produce a health warning; an organization with no current announcement can legitimately be empty.

## Scoring review
Weights are relevance 40%, personal net cost 25%, deadline feasibility 15%, networking/hiring 10%, eligibility certainty 10%. Weights must sum to 1. Relevance is an explicitly labelled keyword heuristic using sourced topics and your interests; its strongest matching rule is used. The AI safety rule receives 80/100 and broader AI 50/100. Missing components earn zero and the known evidence weight is stored. Alumni affiliations and sponsor names never prove recruiter presence in Germany/Finland/India. Closed cycles are ordered below open/review-needed records regardless of topical score. Correct the weights before stage 5.

## Access and privacy
Prefer official APIs, RSS, iCal or sitemaps when provided. The initial adapters use a small public HTML crawl, checking robots.txt, pacing requests, obeying Retry-After via persistent backoff and caching responses for 24 hours. Redirects are rechecked. Failed/denied robots checks stop access. Private destinations, credential URLs, unreviewed query endpoints and nonstandard ports are blocked. No login bypass or CAPTCHA evasion. Source-specific terms still require review before broadening access; robots permission is not a terms-of-service guarantee. See SOURCES.md.

Keep secrets only in ignored .env; never log them. Keep personal outputs in a private repository or private artifacts. No alerts or schedules are enabled and no submission code exists. Application submission always belongs to the user.

## Extending and limits
Each source needs its own module, access metadata, public sanitized fixtures, contract tests and coverage notes. config/seeds.yaml records recurring official pages. Partner/sister URLs are queued and persisted, but do not gain official trust until evaluated. The historical ERA fixture is a sanitized official mentor-page excerpt demonstrating the 2025 cohort remains discoverable; it does not invent historical dates or grant terms.

Twelve source adapters are implemented. Search API discovery, broader regional/body coverage and automatic reference refresh are not yet implemented. FX snapshots expire after seven days; visa references expire after thirty days. Stale or unavailable reference data yields unknown, not stale advice. Exact deadline timezones/CFP conditions still require official detail checks before ICS. Scalar evidence fields preserve source text; deeper ticket-tier and deadline normalization will accompany the calendar/application stage. Coverage is never complete. See reports/watchlist-resolution.md for identity research and the current digest for gaps.

## Delivery stages
1. Scaffold and documentation: complete.
2. Resolve watchlist and expanded scope: complete.
3. Three sources plus read-only evidence pipeline and tests: complete for initial bounded coverage.
4. Classification, costs/visa uncertainty and scored list: ready for user review.
5. Profile-grounded drafts, ICS with official-page spot-checks, approved alerts and GitHub Actions: pending scoring review.

## Hosted global daily refresh

The private GitHub repository is shaswatshukla/conference-opportunity-agent. Daily global refresh runs at 03:47 UTC (09:17 Asia/Kolkata), subject to GitHub scheduling delays. It can also run manually from Actions. The latest committed report is [reports/latest.md](reports/latest.md); CSV/JSON evidence are downloadable from each workflow run artifact.

Twelve adapters now cover ERA, LISA, USENIX, EuroPython, PyCon DE, PyCon Finland, PyCon Japan, PyCon Korea, PyCon US, PyData, IIBA and DAMA. Each is bounded to three attempted pages per run. Native-language text is retained. Blocked, unavailable or JavaScript-only sources remain gaps rather than being bypassed. A past annual edition is historical, not a promise about the next one. The configured regional scope is broader than any finite crawl can fully cover.

No paid LLM API key is necessary for daily refresh: conservative literal rules can refresh quoted names, announced grant terms and explicit statuses on supported official pages. Every other field stays unknown. A configured LLM bridge can improve coverage, with the existing fact-review boundary. Cloud runs use a generic example profile: your local profile, answers, credentials and drafts are not uploaded. FX/visa reference expiry remains enforced. No notification delivery or application submission is enabled.
