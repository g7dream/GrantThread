# Evaluation record

Status on **6 September 2026: local workflow verified; deployed AWS/model gates pending**. The results below describe the current local working tree. A frozen public repository revision is not available in this record. Browser observations were recorded by the implementation session; automated benchmark details are in [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json).

## Executed checks

- **28 backend/worker unit tests passed** across `backend/tests/test_gates.py` and `backend/tests/test_worker.py`. They cover tenant boundaries, scoped downloads, exact allocations, stale/concurrent and atomic batch approvals, replacement lineage, malformed uploads, immutable snapshots, clarification roles, worker leases, duplicate delivery and model-failure containment.
- Python compilation, `pip check` and CloudFormation `cfn-lint` passed. These checks do not deploy AWS resources.
- The final TypeScript/Vite production build passed with the `/grantthread/` base path.
- Both report formats were rendered and visually inspected. Local sample PDFs, manifests and page images are in `artifacts/`.
- The cPanel ZIP was generated at `artifacts/GrantThread-cpanel.zip`: **147,423 bytes**, including the original MIT licence and required packaged notices, with checksum in `artifacts/GrantThread-cpanel.sha256`. It is an **unconfigured preview asset package** until actual AWS API/Cognito settings are supplied and the assets are rebuilt.

The worker tests exercise the installed Strands SDK with controlled model inputs and failure cases. They are not successful Bedrock inference runs. No live model, region, AWS account deployment or cloud expense has been verified.

## Browser journey observed locally

The browser previewed and imported the fixture CSV. The invalid venue allocation could not be applied, its page-one invoice source opened, and the authorised EUR 500 + EUR 500 correction was applied. Digital Belonging's report showed EUR 1,700 with readiness still **5 of 6** because printing payment proof was missing.

The printing proof fixture was uploaded, its source reviewed and one evidence proposal approved through the atomic batch action. A new report version became ready at **6 of 6**. The browser saved `digital-belonging-report-v2.pdf` in Downloads; page-one extraction confirmed EUR 1,700. Both report layouts were separately rendered and visually clean.

Sharing selected two original attachments. Switching through the server-validated local demo identity to Northstar showed one shared package, with its source excerpt restricted to the selected package. A source-linked funder question received a grantee response and funder acknowledgement; the final clarification status was resolved.

A desktop screenshot was inspected. At **390 × 844**, an initial horizontal overflow of 829 pixels was corrected; measured content width became 375 pixels within the 390-pixel viewport. The closed mobile navigation was hidden, and Escape restored focus to “Open navigation.” An actual screen-reader session was **not tested**.

## Release gates and their limits

| Gate | Observed result | Remaining release evidence |
| --- | --- | --- |
| G1: deployed slice | Not passed: AWS API/Cognito/Bedrock not configured | Actual hosted login, persisted records, queued genuine Strands result and refresh |
| G2: access and disclosure | Local automated boundaries passed; browser recipient package and selected sources checked | Repeat on deployed AWS, including signed upload/download paths and judge users |
| G3: money and versions | Local automated tests and browser correction passed | Repeat relevant checks on cloud persistence/concurrency |
| G4: containment | Local controlled tests for instructions, invented sources, financial claims, stale runs and timeout passed | Genuine configured model run with recorded source/tool results and failure behavior |
| G5: judge journey | Local browser journey and report exports passed; desktop/narrow navigation checked | Hosted fresh-session journey, actual screen-reader check where claimed, final public video |

Local passes do not establish production security, broad accessibility conformance, provider behavior or regulatory compliance. The public repository has not been published: GitHub authentication is not established. The owned hosting destination, AWS configuration and final genuine demonstration remain external gates.

## Exact money and source fixtures

The five unique expenses total EUR 5,200. The original proposed venue split exceeds EUR 1,000 by EUR 200. After the authorised correction, the observed allocations are **Digital Belonging EUR 1,700; Community Makers EUR 3,100; Youth Skills EUR 400**, totalling EUR 5,200. Initial confirmed non-venue allocations were EUR 4,200.

The standalone fixture parser check also produced one excess warning and no errors for the proposed CSV, no warnings/errors for the corrected CSV, and one conflicting-original-facts error for the ambiguous CSV. These checks used the actual seed descriptions, dates and amounts. One 24-participant workshop supports two grants while remaining one organisation activity.

## Scripted synthetic local benchmark

[scripts/benchmark_local.py](../scripts/benchmark_local.py) completed three isolated **service-layer** journeys using SQLite and local storage. Each performed seed, CSV preview/import, correction, evidence review, two reports/PDFs, a shared snapshot and a resolved clarification. Each observed EUR 5,200 of unique expenses and allocations, the exact EUR 1,700 / 3,100 / 400 split, two report formats and one resolved clarification. The agent status was `unavailable` in every run, with no fabricated tool events.

The latest measured duration for each run is stored in [BENCHMARK_RESULTS.json](BENCHMARK_RESULTS.json), which is regenerated by the benchmark script. Human review and manual-baseline durations are null because they were not measured.

These durations exclude browser interaction, network, model inference and human review. They are internal execution measurements, **not administrator task times or time savings**. No manual comparison, participant study, repeated-field count or productivity percentage has been measured. Use the label **scripted synthetic benchmark; user validation pending**.

Three local service runs do not satisfy the target of three consecutive complete live deployed demonstrations. A separate unit test varied a harmless fixture value to check that financial output was not hardcoded; the three benchmark rows use the same base fixture.

For a future human comparison, use equivalent synthetic tasks and include setup, checking, waiting and corrections in elapsed time. Record individual outcomes and task order. Keep failures and unresolved facts visible; do not extrapolate savings from the automated durations or external grant-administration research.
