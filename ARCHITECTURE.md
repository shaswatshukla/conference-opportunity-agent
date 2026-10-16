# Planned architecture

Python source adapters share a robots-aware, rate-limited cached HTTP client. Adapters emit leads. Strict-schema LLM extraction must reject invalid payloads and ungrounded quotes. Treat page instructions as untrusted data. Establish official identity independently from an aggregator claim.

SQLite will retain events, editions, opportunity pathways, field evidence, source health, runs, conflicts, FX snapshots, visa citations and notification keys. Keep fetch time distinct from verification time. Use migrations and atomic exports. Fuzzy dedupe by name, year and city must preserve evidence and avoid merging editions.

Every opportunity has exactly one primary type; secondary pathways remain explicit. Unclassifiable leads stay unverified. Eligibility and costs are never inferred. Date-only deadlines retain their precision without invented cutoff times or timezones. Estimates are separate from sourced prices, with assumptions and rate dates.

Scoring uses relevance 40%, net cost 25%, feasibility 15%, employer/recruiter evidence 10%, eligibility certainty 10%. Store component rationale and explicit treatment of missing data. Unknowns cannot create positive evidence. Grants are conditional until eligibility and award status are known.

Draft claims reference profile/answer field paths; missing information becomes a question. No submission code. Notifications use a disabled-by-default idempotent outbox. Planned Actions use public sources, least privilege, concurrency control and private artifacts. No schedules are active at this stage.

## Implemented checkpoint
Stages 3 and 4 are implemented for three bounded adapters. SQLite stores transactional JSON run snapshots and durable empty-result streaks. There is no normalized field-evidence relational schema yet; evidence and conflicts are retained within each snapshot. LLM bridge output requires semantic fact review before promotion. FX/visa reference snapshots have explicit expiry. Drafts, calendars, alerts and scheduled workflows remain unimplemented pending score review.
