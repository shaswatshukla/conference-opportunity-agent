# Source registry (planned)

Implemented initial adapters: ERA, LISA and USENIX. Other rows are a planned registry, not implemented coverage. Public availability is not permission for unrestricted scraping. Review current terms before broadening access.

| Source | Proposed access | Reliability | Terms/access notes |
|---|---|---|---|
| Confs.tech | Public dataset/API if permitted | Discovery only | Confirm license and current endpoint |
| Dev Events | Public calendar/feed if available | Discovery only | Terms unknown |
| Eventbrite | Official API with configured credentials | Discovery only | API permissions and quotas apply |
| Meetup | Official API where authorized | Discovery only | No personal logins; otherwise skip |
| Luma | Public event pages or authorized API | Discovery only | Check robots and terms |
| Lanyrd-style archives | Public archives | Historical leads only | Never infer current edition |
| WikiCFP | Permitted public pages/feed | Discovery only | Check robots and terms |
| ConferenceIndex | Permitted public pages | Unverified leads | Official corroboration required |
| AllConferenceAlert | Permitted public pages | Unverified leads | Official corroboration required |
| 10times | Permitted public pages | Unverified leads | Official corroboration required |
| ACM; IEEE; USENIX | Official program pages/feeds/sitemaps | Primary for own events | Each body gets separate adapter and fixtures; check policies |
| GHC/AnitaB | Official event and grant pages | Primary for own programs | Eligibility must be explicit |
| NumFOCUS; PyData; PyCon | Official chapter/event pages | Primary for own programs | Separate adapters; grants vary by edition |
| Microsoft; Google; AWS; Databricks; Snowflake | Official community/event pages | Primary for own programs | Separate adapters; no login bypass |
| Women Who Code | Official current or archive pages | Primary only if attributable | Current activity unknown; do not assume recurrence |
| DAMA chapters; IIBA chapters | Official local chapter feeds/pages | Primary for own programs | Separate adapters; membership conditions explicit |
| Gartner; TDWI; Big Data LDN; Data Council; Data + AI summits | Official event pages | Primary for own events | Separate adapters; no assumed waivers |
| Power BI; Tableau; Qlik communities | Official event pages/feeds | Primary for own programs | Separate adapters; some content may require login and must be skipped |
| CSCMP; Gartner supply chain; ISM | Official event pages | Primary for own events | Separate adapters; verify ticket and grant terms |
| EuroPython | Official event and financial aid pages | Primary for own programs | Edition-specific eligibility |
| Configured web search | Official search API | Discovery only | Provider, budget and quotas unresolved |
| Annual seed list | Stored official URLs, rechecked | Historical until verified | No invented next edition |
| Partner/sister links | Bounded queue through access checks | Discovery only | Limit depth and hosts; prevent private-network fetches |
| FX provider | Authorized dated API | Supporting cost evidence | Provider unresolved; no fabricated conversions |
| Government visa sources | Official consular/immigration pages | Primary rule evidence | Dated advice; unknown lead time stays unknown |

Initial adapter choices are ERA, LISA and USENIX; the rest remain planned. Every adapter requires fixtures and failure/zero-result tests. Two consecutive zero-result runs must appear as a health warning. Coverage reports list checked sources, failures, skipped sources, query/region bounds and likely omissions. No complete worldwide coverage is claimed.

## Implemented access checks — 16 October 2026

ERA (erafellowship.org), LISA (www.safeai.org.uk), USENIX (www.usenix.org): official public HTML checked with robots.txt through the cached HTTP client. Three-page source budget, 24-hour cache and minimum three-second pacing, increased when robots requires it. Initial run reused six unique official pages; ERA fellowship-1 redirects to fellowship and is deduplicated. Partners/CFPs beyond the budget are queued. No login or submission endpoints were used. These sites are primary for their own statements, not evidence of personal acceptance or funding. No complete source-specific legal audit is claimed.

Supporting references: ECB exchange-rate table dated 16 October 2026; UK Home Office visa-national list, visitor limitations and processing guidance; US Department of State visitor and visa-waiver pages. Saved citations are in data/reference. FX expires after seven days, immigration references after thirty days; automatic refresh is not implemented yet.

## Expanded regional adapters — 17 October 2026
EuroPython (Europe), PyCon DE (Germany), PyCon FI (Finland), PyCon JP (Japan), PyCon Korea (South Korea), PyCon US (US), PyData (Europe/global), IIBA (business analysis/global) and DAMA (data management/global) are now implemented in individual source modules. Three attempted pages per source, official-domain allowlists and robots checks apply. Native-language source text is retained. Daily refresh is no-key using conservative literal fields, with optional LLM enrichment. The latest report gives actual checked pages and failures: configured coverage does not imply successful access or completeness.
