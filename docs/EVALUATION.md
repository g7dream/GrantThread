# Evaluation record

## 14 September — public editable demo update

The current local suites pass **280 tests: 190 backend, 52 scripts and 38 frontend API/auth**, plus the production frontend build. The backend adds 21 focused public-demo cases for subject-derived isolation, explicit idempotent creation, role scope, active-job/stale-version restore rejection, fresh-generation fencing and preserved history. Frontend checks cover server-enabled role-header gating, no token/role leakage to signed S3 requests, new-token/logout clearing, signup PKCE/state validation and a 20-second token-exchange deadline.

The new AWS update reached `UPDATE_COMPLETE`. Cognito `AllowAdminCreateUserOnly=false`, `health.publicDemoSignup=true` and CORS allowance for `x-grantthread-demo-role` were verified. The matching cPanel archive is extracted; all 16 identity/gzip/Brotli and canonical obsolete-validator checks pass. The actual browser loads `index-C8T0tDcQ.js` and opens the native Cognito signup page. Real signup email delivery and code confirmation have not been demonstrated: the fictional test accounts were created and confirmed administratively with email suppressed. Google federation is not configured; an ordinary Gmail email/password account is a separate flow.

**All 18 actual hosted-browser checks passed** for a new fictional visitor with no membership record, through native Cognito OAuth and API Gateway. The welcome and explicit start created three grants with EUR 4,200 confirmed allocations out of EUR 5,200 recorded. Correcting the venue split to EUR 500/500 raised confirmed allocations to EUR 5,200. The reviewer manually prepared the EUR 400 Youth Skills report, shared only the selected insurance original, switched to Funder in the same login, inspected the source and downloaded its actual 143 bytes. A source-linked question, Grantee reply and Funder acknowledgement reached resolved state. Restore from Funder preserved login, removed the shared report and all conversations, and returned Grantee to EUR 4,200, the original pending EUR 200 over-allocation and fresh `demo19` fixture IDs. Agent history remained, and normal reload preserved the restored state. Evidence: ignored `artifacts/public-demo-browser-verification.json`. This is one recorded browser journey, not three rehearsals or a load test.

**All 55 separate administrative cloud application checks passed** for two other fictional visitors. They cover separate namespaces, idempotent start, cross-visitor denials, own-only Northstar sharing, the resolved question lifecycle, active-job restore rejection (409), stale version rejection, fresh-generation IDs, stale URL denial, retained exact job history and unchanged other-visitor/canonical aggregate hashes. No membership records were created. These Lambda invocations bypass API Gateway, OAuth, JWT signature validation and CORS; they establish backend isolation separately from the one-account browser journey. Evidence: ignored `artifacts/public-demo-cloud-smoke/result.json`, collected 16:21 UTC on 14 September.

The two new automatic reviews did not complete report preparation:

| Run | Observed result | Boundary |
| --- | --- | --- |
| Browser-triggered `job-ce2123d9399042a3` after venue correction | `waiting_input` at the model/input budget; eight recorded tools, six successes and two safely rejected proposals for already-confirmed evidence; no new report or proposal; 14.083 seconds worker duration | Persisted `modelCalls: 11` counts before-model hook attempts. The eleventh was cancelled before provider invocation by the ten-call limit; this is **not evidence of eleven provider requests**. |
| Separate administrative-case `job-a06b980aa9f24aea` | Failed with `ModelThrottledException` after four successful recorded tools; no retry was performed | The 55 passing application checks include a terminal job state, not successful model completion. |

The job evidence is in ignored `artifacts/public-demo-cloud-smoke/alice-job-summary.json` and `worker-error-log.json`. The manually prepared Youth Skills report in the browser walkthrough is not output from either automatic review. These results do not establish guaranteed AI completion.

Restore affects only that visitor's scenario, preserves sign-in and agent history, and does not permanently delete S3 objects. Real email delivery/code confirmation remains an actual signup test. A second-account browser isolation run, concurrent-user load testing and repeated full rehearsals have not been performed; they are additional confidence checks, not prerequisites to using Restore or submitting. See [PUBLIC_DEMO.md](PUBLIC_DEMO.md). The earlier 244 local tests, 49 administrative cloud checks and invited-account browser results below are historical evidence for that earlier release, not proof of this new flow.

## Earlier 14 September — invited-account release

Earlier status on **14 September 2026: deployed backend and hosted grantee/funder workflow verified, including financial downloads, selected original download and resolved clarification; repeated demonstrations and submission remain open**. The application stack `grantthread-demo` reached `CREATE_COMPLETE` in Stockholm (`eu-north-1`) in the intended account and has received subsequent updates. The separate `grantthread-demo-budget` stack reached `CREATE_COMPLETE` in `us-east-1`: USD 25 monthly threshold, alerts at 80% actual and 100% forecast, with credits/refunds excluded. Credentials, the budget recipient and private financial files remain private. The configured Cognito domain and other public frontend identifiers are visible in the browser build. Current setup uses the existing temporary root-console login; no non-root development operator has yet been established. Lambda runtime services use IAM execution roles.

The owner selected `CapacityMode=shared-demo` for the account concurrency quota of 10, without raising the quota or changing the plan. Both deployed functions are Active with successful updates and no reserved concurrency; `artifacts/live-capacity-verification.json` retains that check. The earlier local improvement pass made no AWS calls or deployments; the cloud evidence below was collected subsequently. Source revision [`3b4ceba`](https://github.com/g7dream/GrantThread/commit/3b4ceba8b83e0924c7a7eda425768d865d964101) is published at [g7dream/GrantThread](https://github.com/g7dream/GrantThread). Unauthenticated GitHub API checks independently verified public visibility, default branch `master`, README and MIT licence. Final video, Builder ID confirmation and submission remain pending.

## Earlier 14 September cloud verification

**Transport boundary:** the 49 application checks below use administrative Lambda invocation with trusted gateway claims and real deployed services. They test the application against actual cloud storage, queue and model behavior, but bypass API Gateway JWT signature validation, OAuth, CORS and browser rendering. Do not describe them as 49 hosted-browser tests.

| Evidence | Observed result | Scope |
| --- | --- | --- |
| Public API health/session | HTTP 200 with AWS mode and configured agent; anonymous session HTTP 401 | Actual public HTTP requests; `artifacts/cloud-health-check.json` |
| Scope checks | 9 passed | Server membership, other-organisation grant/source denial and funder financial denial; administrative invocation |
| Genuine reconciliation checks | 6 passed | Job scheduling, persisted status and another organisation's denied job read; administrative invocation plus real SQS/worker/Bedrock execution |
| Financial checks | 34 passed | Real S3 XLSX/text-bank-PDF imports, receipt rate, payment match, immutable correction, report/template XLSX and report PDF exports, activity and denied cross-scope reads |
| Hosted assets | All 16 final checks passed: five payloads matched their SHA-256 across identity/gzip/Brotli requests, plus the canonical page with obsolete validators | `artifacts/final-hosted-encoding-verification.json`, 15:40 UTC; the canonical browser DOM subsequently loaded `index-BSFSo7GJ.js` |
| Hosted caching | Canonical page with Brotli and obsolete validators returns 200/no-store and current HTML | A stale LiteSpeed compressed copy was cleared by resaving the exact index/manifest bytes with fresh modification times. Content-derived ZIP timestamps now prevent reuse of the former constant timestamp for changed content; future uploads still require verification |
| Hosted grantee session | Cognito email/password sign-in, normal browser reload and authenticated Bright Path Lab Portfolio passed | Actual public browser path after both CORS repairs; separate from administrative-invoke checks |
| Hosted financial download | UI displayed CAD 20 actuals, CAD 250 receipts and two included entries; actual downloaded XLSX independently read back with those values | `artifacts/hosted-browser-verification.json`; CUA download observer timed out, but the newly saved workbook established success |
| Hosted sharing and clarification | Youth Skills report version 1 shared with Northstar and exactly one selected attachment, `invoice-insurance`; recipient saw one package and EUR 400; question, grantee answer and funder acknowledgement persisted as resolved after fresh reload | Actual public browser path, including final-bundle original download with verified text bytes |

The genuine job **`job-f2ce0cb489044197`** used regional **`amazon.nova-lite-v1:0`** through Strands. It made **four model calls and eight successful tool calls** in **8.59 seconds from worker start to finish**. It listed requirements, read five authorised evidence sources, checked readiness and saved an incomplete report draft. Its final state was correctly **`waiting_input`**, with missing printing payment proof and the proposed venue allocation requiring human review. This is a successful bounded reconciliation execution, not a completed report or a bypass of the human decisions. Job token usage and attributable cost were not measured.

**A second, distinct run did not produce a draft.** The fresh portfolio-wide browser job `job-c684f54d1e2c4114`, created at 15:13 UTC, made **nine model calls and eight tool calls: seven successful and one rejected missing-evidence reference**. It reached the tool budget and ended at `waiting_input`, saving **no report drafts and no proposals**. Its worker duration was 11.95 seconds. The earlier grant-scoped job and its eight successful events remained visible after normal browser reload; they must not be presented as the fresh run's results. A real model run can consume its budget without completing useful report preparation. Evidence is in `artifacts/hosted-browser-agent/summary.json` and `job.json`.

The hosted browser showed the entered receipt basis (RON 1,000, CAD 1 = RON 4, reporting CAD 250), separate currency totals and the existing CAD 20 financial report. A real UI XLSX download was independently read back. The receipt-aware report PDF version 2 downloaded as 2,983 bytes; PDF text confirmed CAD 250 receipts and CAD 20 expense. The 408-byte JSON manifest parsed with the correct grant. These financial PDF/JSON checks used the repaired backend before the final frontend bundle was loaded; they were not repeated with the final JS. Separate recipient shared-report downloads did pass with the final JS: the 2,872-byte PDF contained Youth Skills, Insurance and EUR 400, and the 922-byte shared manifest parsed with the correct keys. After the Brotli repair, the canonical browser loaded `index-BSFSo7GJ.js`, recovered the authenticated Northstar session and downloaded the selected original as 143 bytes of actual fictional insurance-invoice text (EUR 400), not a JSON descriptor. Its SHA-256 was `63fb8adc2fee09c768417f7cd401b08bd0de7a5576b22ae5e21469194fba8d74`. The source-linked question, grantee response and Northstar acknowledgement persisted as resolved after fresh reload. Evidence is retained in `artifacts/hosted-browser-verification.json`.

Private local evidence records are retained under:

- `artifacts/cloud-smoke-scope-20260914-175645-b69658/result.json`
- `artifacts/cloud-smoke-agent-20260914-175708-c48dda/result.json` and `genuine-job.json`
- `artifacts/cloud-smoke-financial-20260914-175740-0049e9/result.json`

The financial case converted RON 100 to CAD 25 using the recorded receipt rate, matched a bank debit without adding spending, and confirmed a linked RON -20 correction to leave CAD 20. It rejected stale reconfirmation and out-of-scope financial/report reads. This exercised the deterministic supported text-bank parser; **no genuine AI bank extraction was performed**.

A separate direct Nova Lite Converse tool roundtrip passed earlier, recorded in `artifacts/verify-regional-bedrock.json`: 168 output tokens and 1.39 seconds. Those measurements belong to the direct smoke test, not the application job. Local capacity/budget tests and `cfn-lint` checks preceded deployment; real Lambda execution now additionally establishes runtime imports on the deployed Linux build. The tested hosted handoff is verified; three consecutive full demonstrations and the final judge handoff remain open.

## Earlier 14 September local reliability pass

- **169 backend tests passed**, including activity/CSV, transport limits, legacy credit recovery, correction fencing, source-download descriptors, Windows-safe recovery and repeat-seed source preservation. **25 frontend request-lifecycle tests passed**, covering stalled headers/JSON/error/download bodies, credentialless signed downloads, global/regional S3 URL validation, preserved inline JSON/PDF/XLSX bytes, cleanup, HTML endpoints and no automatic financial-write retries. **50 release/build-script tests passed**, including deterministic packages, source allowlists, changed assets, credential markers, competing destinations and failed-write cleanup.
- Those completed local suites total **244 tests**. TypeScript/Vite production build, Python compilation and `pip check` passed. Source and staged SAM templates passed `cfn-lint`. The 50 script tests include cache, API preflight and source-download CORS regressions. Equal-length HTML/manifest changes receive changed content-derived ZIP timestamps; unchanged assets and repeated identical ZIPs remain stable. Both API preflight repairs and the receipt-PDF/source-download fixes are deployed. Actual hosted login, financial PDF values and the final-bundle source download pass, with their distinct frontend timing recorded above. The deployment used a pinned Linux-wheel build, not a local SAM container build.
- Three isolated service journeys passed again: EUR 5,200 total, the 1,700 / 3,100 / 400 split, two report formats and a resolved clarification. [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json) retains the unmeasured human-review/manual baseline fields.
- The earlier interface-only artifact was `artifacts/GrantThread-preview.zip`; the current hosted assets are the cloud-configured release described above. Incomplete cloud settings and changed assets fail validation. SAM staging includes only 18 approved runtime modules, requirements and template metadata, excluding local data and uploads.
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

At this 6 September baseline, worker tests exercised the installed Strands SDK with controlled provider inputs and failure cases. Live model and deployment proof had not yet been collected; the later 14 September record above supersedes that historical status.

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

## Earlier invited-account release gates and their limits

| Gate | Observed result | Remaining release evidence |
| --- | --- | --- |
| G1: deployed slice | Public grantee login/reload, persisted data, real financial download and browser-triggered Strands execution observed | Fresh portfolio-wide job reached its tool budget with no draft; finish a complete reviewed report journey on the frozen runtime |
| G2: access and disclosure | Local boundaries, cloud administrative-invoke denials, actual public grantee/funder sessions, a selected shared package and its final-bundle original download passed | A selected successful route is not universal JWT/security coverage; repeat relevant denials after consequential changes |
| G3: money and versions | Local tests, cloud receipt/payment-match/CAD 25→20 correction, browser financial display and independent XLSX/PDF value readback passed | PDF readback used the fixed backend before final JS; no load/concurrency claim |
| G4: containment | Controlled local failures, grant-scoped incomplete draft and portfolio-wide budget stop with rejected evidence/no draft observed | These distinct runs do not establish reliable automatic completion; AI bank extraction remains unverified |
| G5: judge journey | Hosted grantee/funder sessions, data, agent events, financial XLSX/PDF/manifest downloads, selected original download and resolved clarification passed | Three consecutive full demonstrations, final video and judge handoff remain open; the fresh portfolio-wide model run produced no draft |

Local and bounded cloud checks do not establish production security, broad accessibility conformance, universal model behavior or regulatory compliance. The source repository, README and MIT licence are publicly published and independently verified. The tested hosted handoff and financial/source downloads are verified; complete repeated demonstrations, video and judge handoff remain open. Both useful and budget-limited genuine model executions are recorded.

## Exact money and source fixtures

The five unique expenses total EUR 5,200. The original proposed venue split exceeds EUR 1,000 by EUR 200. After the authorised correction, the observed allocations are **Digital Belonging EUR 1,700; Community Makers EUR 3,100; Youth Skills EUR 400**, totalling EUR 5,200. Initial confirmed non-venue allocations were EUR 4,200.

The standalone fixture parser check also produced one excess warning and no errors for the proposed CSV, no warnings/errors for the corrected CSV, and one conflicting-original-facts error for the ambiguous CSV. These checks used the actual seed descriptions, dates and amounts. One 24-participant workshop supports two grants while remaining one organisation activity.

## Scripted synthetic local benchmark

[scripts/benchmark_local.py](../scripts/benchmark_local.py) completed three isolated **service-layer** journeys using SQLite and local storage. Each performed seed, CSV preview/import, correction, evidence review, two reports/PDFs, a shared snapshot and a resolved clarification. Each observed EUR 5,200 of unique expenses and allocations, the exact EUR 1,700 / 3,100 / 400 split, two report formats and one resolved clarification. The agent status was `unavailable` in every run, with no fabricated tool events.

The latest measured duration for each run is stored in [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json), which is regenerated by the benchmark script. Human review and manual-baseline durations are null because they were not measured.

These durations exclude browser interaction, network, model inference and human review. They are internal execution measurements, **not administrator task times or time savings**. No manual comparison, participant study, repeated-field count or productivity percentage has been measured. Use the label **scripted synthetic benchmark; user validation pending**.

Three local service runs do not satisfy the target of three consecutive complete live deployed demonstrations. A separate unit test varied a harmless fixture value to check that financial output was not hardcoded; the three benchmark rows use the same base fixture.

For a future human comparison, use equivalent synthetic tasks and include setup, checking, waiting and corrections in elapsed time. Record individual outcomes and task order. Keep failures and unresolved facts visible; do not extrapolate savings from the automated durations or external grant-administration research.
