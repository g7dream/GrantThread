# Evaluation record

Status on **14 September 2026: local improvements verified; deployed AWS/model gates pending**. AWS account selection is paused. No cloud API calls, deployment, credential changes or publication were performed during this local improvement pass. The known destination is `https://timeillusion.com/grantthread/`; its existing interface still lacks the configured backend.

## 14 September local reliability pass

- **158 backend tests passed**, including activity/CSV, transport limits, legacy credit recovery, correction fencing, Windows-safe recovery and repeat-seed source preservation. **8 frontend request-lifecycle tests passed**, covering stalled headers/JSON/error/download bodies, cleanup, HTML endpoints and no automatic financial-write retries. **26 release/staging tests passed**, including deterministic packages, source allowlists, changed assets, credential markers, competing destinations and failed-write cleanup.
- TypeScript/Vite production build, Python compilation and `pip check` passed. Source and staged SAM templates passed `cfn-lint`. SAM's Linux-container dependency build and actual deployment were not run.
- Three isolated service journeys passed again: EUR 5,200 total, the 1,700 / 3,100 / 400 split, two report formats and a resolved clarification. [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json) retains the unmeasured human-review/manual baseline fields.
- Current public assets are packaged separately as `artifacts/GrantThread-preview.zip` with a SHA-256 sidecar. Incomplete cloud settings and changed assets fail validation. SAM staging includes only 18 approved runtime modules, requirements and template metadata, excluding local data and uploads.
- The generated SAM stage was read and syntax-checked under the user's Windows account after fixing inherited directory permissions. This confirms local readability, not a Linux dependency build.

Browser tests used separate fictional workspaces under `artifacts/`; the normal `backend/.data` was not reset. A EUR 100 draft was selected, filtered out and restored to view unselected. Confirmation recorded the actor and target. Filtering history to one action still downloaded all three events in chronological order.

A RON 500 receipt entered as `1 EUR = 5 RON` showed EUR 100, the normalised rate and exact entered rate/direction. Currency/direction changes cleared the old receipt rate. Changing an imported draft from RON to USD cleared its manual rate. A comma separator required a fresh preview while numeric source cells retained their values. Downloading an original with unsaved description edits kept the editor open at version 1; cancel/reopen restored the unchanged saved description. Downloaded XLSX bytes matched the source SHA-256. A cleared optional template total cell stayed empty after save/reopen. A template missing the report's Uncategorised category was correctly rejected.

Recovery copied two fictional organisations and 20 referenced objects into a new directory. Previous sessions failed; fresh login retained the expense, receipt and four events. The restored server ran under the user's Windows account after fixing temporary-directory ACL inheritance. Deliberately invalid inherited cloud frontend settings still produced local identities/API. Ctrl+C released the launcher's ports. Relative data paths resolved correctly after PowerShell changed directories. Startup now leaves existing source files untouched; cloud recovery remains untested.

At 390 × 844, the financial page measured 375px wide. Mobile navigation excluded background controls; after fixing the `inert` timing, Escape restored the Open navigation button's focus. The activity and receipt layouts were visually inspected. Native screen-reader use remains untested.

An extracted preview served locally at `/grantthread/` without an API showed **Website preview / Setup is not finished**, unavailable uploads and optional owner diagnostics. This proves the static failure state, not Apache rewrites, cPanel upload, Cognito or Bedrock.

## 6 September baseline

The observations below describe the original local implementation and financial feature pass. Earlier counts/artifact names are historical; use the 14 September record and current artifact manifest for this candidate.

## Executed checks

- **116 tests passed**: 17 original workflow gates, 11 reconciliation worker tests, 11 response-estimate tests, 22 financial integration tests, 30 financial file tests, 13 bank-extraction tests and 12 bank-job lifecycle tests. They cover tenant boundaries, exact money/FX, atomic/stale changes, source parsing, duplicate payments, template preservation and bounded offline model dispatch.
- Python compilation, `pip check` and CloudFormation `cfn-lint` passed. These checks do not deploy AWS resources.
- The final TypeScript/Vite production build passed with the `/grantthread/` base path.
- Both report formats were rendered and visually inspected. Local sample PDFs, manifests and page images are in `artifacts/`.
- The cPanel ZIP is generated at `artifacts/GrantThread-cpanel.zip`, including the original MIT licence and required packaged notices. Use `artifacts/GrantThread-cpanel.sha256` to identify the current packaged build; file size changes when assets are rebuilt. It is an **unconfigured preview asset package** until actual AWS API/Cognito settings are supplied and the assets are rebuilt.

The worker tests exercise the installed Strands SDK with controlled model inputs and failure cases. They are not successful Bedrock inference runs. No live model, region, AWS account deployment or cloud expense has been verified.

## Browser journey observed locally

The browser previewed and imported the fixture CSV. The invalid venue allocation could not be applied, its page-one invoice source opened, and the authorised EUR 500 + EUR 500 correction was applied. Digital Belonging's report showed EUR 1,700 with readiness still **5 of 6** because printing payment proof was missing.

The printing proof fixture was uploaded, its source reviewed and one evidence proposal approved through the atomic batch action. A new report version became ready at **6 of 6**. The browser saved `digital-belonging-report-v2.pdf` in Downloads; page-one extraction confirmed EUR 1,700. Both report layouts were separately rendered and visually clean.

Sharing selected two original attachments. Switching through the server-validated local demo identity to Northstar showed one shared package, with its source excerpt restricted to the selected package. A source-linked funder question received a grantee response and funder acknowledgement; the final clarification status was resolved.

A desktop screenshot was inspected. At **390 × 844**, an initial horizontal overflow of 829 pixels was corrected; measured content width became 375 pixels within the 390-pixel viewport. The closed mobile navigation was hidden, and Escape restored focus to “Open navigation.” An actual screen-reader session was **not tested**.

## Response-estimate calculator

The added [Response estimates](RESPONSE_ESTIMATES.md) calculator uses fixed simulated funder-review durations. It is a deterministic, read-only scenario tool, separate from the seven Strands agent tools. It neither calls Bedrock nor establishes that a report was submitted. It changes no readiness, financial records or clarification state.

Its 11 tests passed within the 39-test suite. They cover numerical examples, conditioning on elapsed days, sparse/missing history, longest-history boundaries, malformed/future dates, leap-day arithmetic, authorised grant/funder scope and unchanged stored records. The frontend build passed after this addition.

Verified browser observations: Northstar's default scenario with seven days already waited shows **5–15 more days, median 11**; changing the grant or editing the date with native keyboard input clears the previous result; Riverbend's default scenario shows **11–23 more days, median 18**. At 25 days waited, two comparable samples produce no countdown. At 35 days, the tool explains that the longest simulated review has been reached and shows no remaining response date. Tab and Enter access/expand the sample history. Desktop and 390 × 844 viewport captures were inspected, with measured page width 375px within the 390px viewport. Native screen-reader operation remains untested. These simulated ranges are not confidence intervals, response guarantees or measured forecasting accuracy.

## Financial workspace verification

The browser imported a fictional XLSX ledger into drafts, recorded an automatic funding receipt, converted RON 100 to CAD 25 without entering a per-expense rate, and confirmed it. A linked correction of RON -20 retained the original rate and changed the report to CAD 20. A CAD 50 category budget produced CAD 30 variance. Receipt creation invalidated older affected draft versions; confirmed conversions remained frozen.

Both browser download actions produced files in Downloads. The in-app download event observer timed out once, but the downloaded file existed; independent workbook inspection and authenticated HTTP downloads verified the result. The populated template contained actual/total CAD 20, zeroed unused mapped categories, the chosen reciprocal rate of 4, and the selected period dates. Unmapped cells and a dependent formula remained unchanged. Generated report, ledger and receipt sheets were rendered for visual inspection; text wrapping and column widths were corrected. Exports retain the conversion basis and funding receipt IDs.

The supplied private ledger and report were checked in memory only. The parser found 66 expense rows with RON amounts and preserved high-precision rates, excluded balance/summary/audit comparison rows, and explicitly flagged the separate income table. The report template retained all 16 sheets, 10 array formulas, unmapped values and styles. The sample bank PDF parsed as one credit with balanced totals. No private source files or extracted financial records were added to the repository or public fixtures.

At 1280px, the financial page measured 1265px wide; at 390px, it measured 375px. Keyboard Home selected the first financial tab. Import, receipt, confirmation, correction, budget and mapping controls were exercised through the browser. Native screen-reader use remains untested. Parser/service tests cover bank statement upload, overlapping statements, payment matching and unavailable AI; no genuine Bedrock bank extraction was performed.

All backend tests, Python compilation, dependency consistency and the production frontend build passed. See [FINANCIALS.md](FINANCIALS.md) for supported formats, receipt selection and remaining limits.

## Release gates and their limits

| Gate | Observed result | Remaining release evidence |
| --- | --- | --- |
| G1: deployed slice | Not passed: AWS API/Cognito/Bedrock not configured | Actual hosted login, persisted records, queued genuine Strands result and refresh |
| G2: access and disclosure | Local automated boundaries passed; browser recipient package and selected sources checked | Repeat on deployed AWS, including signed upload/download paths and judge users |
| G3: money and versions | Local automated tests and browser correction passed | Repeat relevant checks on cloud persistence/concurrency |
| G4: containment | Local controlled tests for instructions, invented sources, financial claims, stale runs and timeout passed | Genuine configured model run with recorded source/tool results and failure behavior |
| G5: judge journey | Local browser journey and report exports passed; desktop/narrow navigation checked | Hosted fresh-session journey, actual screen-reader check where claimed, final public video |

Local passes do not establish production security, broad accessibility conformance, provider behavior or regulatory compliance. The public repository has not been published in this pass. AWS account/configuration, hosted authenticated behavior and a genuine model demonstration remain external gates; the owned hosting destination is now known.

## Exact money and source fixtures

The five unique expenses total EUR 5,200. The original proposed venue split exceeds EUR 1,000 by EUR 200. After the authorised correction, the observed allocations are **Digital Belonging EUR 1,700; Community Makers EUR 3,100; Youth Skills EUR 400**, totalling EUR 5,200. Initial confirmed non-venue allocations were EUR 4,200.

The standalone fixture parser check also produced one excess warning and no errors for the proposed CSV, no warnings/errors for the corrected CSV, and one conflicting-original-facts error for the ambiguous CSV. These checks used the actual seed descriptions, dates and amounts. One 24-participant workshop supports two grants while remaining one organisation activity.

## Scripted synthetic local benchmark

[scripts/benchmark_local.py](../scripts/benchmark_local.py) completed three isolated **service-layer** journeys using SQLite and local storage. Each performed seed, CSV preview/import, correction, evidence review, two reports/PDFs, a shared snapshot and a resolved clarification. Each observed EUR 5,200 of unique expenses and allocations, the exact EUR 1,700 / 3,100 / 400 split, two report formats and one resolved clarification. The agent status was `unavailable` in every run, with no fabricated tool events.

The latest measured duration for each run is stored in [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json), which is regenerated by the benchmark script. Human review and manual-baseline durations are null because they were not measured.

These durations exclude browser interaction, network, model inference and human review. They are internal execution measurements, **not administrator task times or time savings**. No manual comparison, participant study, repeated-field count or productivity percentage has been measured. Use the label **scripted synthetic benchmark; user validation pending**.

Three local service runs do not satisfy the target of three consecutive complete live deployed demonstrations. A separate unit test varied a harmless fixture value to check that financial output was not hardcoded; the three benchmark rows use the same base fixture.

For a future human comparison, use equivalent synthetic tasks and include setup, checking, waiting and corrections in elapsed time. Record individual outcomes and task order. Keep failures and unresolved facts visible; do not extrapolate savings from the automated durations or external grant-administration research.
