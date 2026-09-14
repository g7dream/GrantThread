# GrantThread — Many grants. One clear thread.

**Submission draft, updated 14 September 2026.** The current 280 local tests pass (190 backend, 52 scripts, 38 frontend API/auth), plus the production build. The public editable demo is deployed: 18 actual browser checks pass for OAuth, personal-copy creation, editing, selected sharing/download, both roles, a resolved conversation and Restore with login/history retained. Separate administrative cloud checks pass 55 isolation and restoration cases. Test accounts were confirmed administratively; real signup email delivery/code confirmation remain pending. The newest AI reviews stopped at a budget or failed under model throttling, without completing report preparation. Earlier grant-scoped Strands evidence and invited-account financial downloads remain separately verified. Public source and its MIT licence are available. Rehearsals, video, entrant details and final submission remain open.

## Tagline

Record shared grant work once, review the exceptions, and share a report with its evidence.

## Inspiration

A grant administrator may need to explain the same activity to several funders, with different report layouts, currencies and evidence requirements. The difficult part is keeping the underlying facts consistent while knowing which details can be shared. GrantThread connects incoming records, financial review and a targeted funder conversation.

The primary user is a professional grant administrator. The funder receives a deliberately shared package, while the grantee controls its internal records. The proposed track is Professional Agents.

## What it does

Each visitor can use one GrantThread email/password account to create an editable fictional Bright Path copy, switch between Grantee and its Northstar Funder view, and Restore the starting scenario for another take. No AWS account is needed; Gmail is usable as an email address, but Google single sign-on is not configured. Restore preserves login and agent history/allowances, affects only that visitor's copy and does not permanently delete S3 objects.

The fictional Bright Path Lab scenario spans three grants. Five expenses total EUR 5,200. A proposed venue split exceeds the original expense by EUR 200, and a printing expense lacks its configured payment proof. The reviewer inspects sources, corrects the split and can supply missing proof. The new browser walkthrough corrected the split but did not supply printing proof; it manually prepared the separate EUR 400 Youth Skills report. Two report layouts reuse confirmed facts. An explicit sharing manifest selects the report version and attachments a funder receives; a clarification thread retains the question, response and acknowledgement. One workshop can support two grants while remaining one unique activity.

Financials brings spreadsheet work into the web workflow. Administrators upload an XLSX ledger, inspect its sheet and column mappings, review editable drafts, and confirm the entries that belong in a grant report. Reports show category budgets and actuals and export an XLSX report, ledger and funding-receipt register. A funder's XLSX template can be populated through reviewed cell mappings. The server does not recalculate Excel formulas or provide a complete Excel editor.

A deterministic parser handles a narrowly supported text-based bank PDF layout. A bank debit can be reviewed as a payment match to an existing expense, recording paid status without counting the expense twice. Incoming credits need classification. Confirmed expenses remain immutable; a reasoned, linked adjustment preserves the original record. This is file parsing, not a bank connection. Genuine model-based bank extraction has not been demonstrated and is not claimed here.

For international grants, the administrator records the rate at which funding was received, including its entered direction. Drafts can use an eligible receipt automatically, a specific receipt, a weighted receipt rate or an explicitly entered rate. Deterministic calculations keep source and reporting amounts separate; confirmation freezes the rate, method and receipt references. This preserves conversion provenance. It does not fetch market rates, choose the funder's accounting policy, consume receipt balances or calculate spendable cash.

The separate Response estimates tool uses fixed simulated funder histories to illustrate the remaining wait after a chosen number of days. Its ranges are a scenario aid, not a live prediction or a promised response date. Recent activity history makes recorded confirmations, imports and other audited actions easier to review and export.

All published examples and demonstration figures are synthetic. They are not customer records, impact measurements or evidence of forecasting accuracy.

## How it is built

The interface uses React and TypeScript; a shared Python domain layer supports both local SQLite mode and the AWS backend. The `grantthread-demo` stack reached `CREATE_COMPLETE` in Stockholm (`eu-north-1`) in the intended AWS account. It provisions Cognito, API Gateway, Lambda, DynamoDB, private S3 and SQS. Static frontend assets are built for Spaceship cPanel at `https://timeillusion.com/grantthread/`; actual hosted login, financial/source downloads and resolved clarification are verified; repeated full demonstrations remain open.

Strands uses Amazon Bedrock and scoped tools to inspect authorised evidence, calculate exact allocations and propose review work. A direct regional Nova Lite (`amazon.nova-lite-v1:0`) Converse tool roundtrip succeeded. Separately, the real SQS/Strands job `job-f2ce0cb489044197` made four model calls and eight successful tool calls in 8.59 seconds of worker execution. It inspected authorised requirements/evidence, checked readiness and saved an incomplete report. Its correct final state was `waiting_input` for missing printing proof and human review of the venue allocation. It did not declare an unsupported ready report. A separate fresh portfolio-wide browser run, `job-c684f54d1e2c4114`, made nine model calls and eight tool calls (seven successes and one rejected missing-evidence reference), reached its tool budget and saved no draft or proposal. The earlier grant-scoped result is not the outcome of that later run. This limits any claim of reliable automatic report preparation.

The agent has no tool for applying canonical allocations, confirming financial entries or publishing a report. Separate authorised actions validate versions and confirm consequential changes. Factual report content comes from confirmed structured records and deterministic templates. Model suggestions do not become confirmed financial facts merely because a job finishes.

## Design decisions and challenges

An invoice amount, a grant allocation and proof of payment are different facts. Treating them as interchangeable would conceal issues the administrator needs to resolve. A report snapshot and the grantee's internal workspace also have different audiences, so allocation review and attachment selection are explicit.

Financial imports preserve original files and source row or page references. Conversion changes invalidate affected drafts before confirmation; later receipts do not silently revalue confirmed history. Credits, payment matches and adjustments retain their distinct meanings.

A citation identifies a source version and page. It does not guarantee that the source supports an interpretation. Missing values remain missing, and instructions inside uploaded documents do not grant the agent authority.

## What has been verified

The current local suite passed **280 tests: 190 backend, 52 release/build-script and 38 frontend API/auth tests**. The TypeScript/Vite production build also passed. These checks cover permissions, exact money and conversion, stale updates, financial import/export, worker boundaries, release packaging, request failures and personal-demo isolation/restoration. They do not establish deployed behavior or model extraction quality.

The new public-demo release separately passes all 16 hosted encoding/cache checks, 18 actual browser checks and 55 administrative Lambda application checks. The browser used native OAuth and API Gateway for one personal account, edited the venue split, manually prepared/shared Youth Skills with one selected original, downloaded that original, completed the two-role question lifecycle and restored from Funder. Login/history remained and restored records survived reload. Administrative checks establish two-visitor isolation, active-job/stale-version rejection and unchanged other copies; they bypass OAuth, JWT validation and CORS. Real email-code delivery remains unverified because accounts were confirmed administratively.

The new browser-triggered review recorded eight tools: six successes and two safely rejected already-confirmed evidence proposals. It stopped at its budget with no new report or proposal. Its persisted model counter of 11 includes the final before-model attempt cancelled before provider invocation by the ten-call limit; it is not eleven verified provider requests. A separate administrative-case review failed under model throttling after four successful tools. These outcomes and the earlier successful grant-scoped run are distinct; none establishes guaranteed automatic completion.

Earlier local browser journeys completed source inspection, the EUR 500 + EUR 500 venue correction, printing-proof review, ready report/PDF download, selected-attachment sharing and funder clarification. Financial browser checks covered XLSX import, receipt-based conversion, a linked correction, template export and preservation of entered rate direction. Desktop and narrow-screen checks included mobile navigation focus and financial controls; no actual screen-reader session was run.

Earlier invited-account cloud verification includes 49 application checks: nine scope, six agent and 34 financial checks using administrative Lambda invocation with trusted gateway claims. They exercised real storage, queue and model services, including XLSX/text-bank-PDF import, payment matching, receipt-based conversion and a correction from CAD 25 to CAD 20. They do not verify public API Gateway JWT signatures or browser behavior. Separate public requests returned health HTTP 200 and anonymous session HTTP 401. Actual invited-account browser checks passed Cognito sign-in, normal reload, financial figures and a downloaded XLSX independently read back as CAD 20 actuals and CAD 250 receipts. Hosted receipt-PDF values, selected original downloads and resolved clarification also passed. These are historical results from the earlier 244-test release, distinct from the new personal-demo checks. Repeated judge demonstrations remain open. A USD 25 monthly budget alert is deployed; it is not a hard spending cap.

Three isolated local service journeys reproduced the fixture totals, both report formats and a resolved clarification. Their execution timings exclude browser use, network, model inference and human review. No administrator time savings, manual baseline or participant study has been measured. User validation remains pending. See [EVALUATION.md](../EVALUATION.md) for the evidence, transport boundary and remaining limitations.

## What's next

Verify signup email delivery with an actual inbox and record the supported workflow with the actual Strands outcome and human review. Additional rehearsals are recommended for confidence, not a submission requirement. Then test with grant administrators and funder reviewers and measure repeated entry/review effort using permissioned, comparable tasks. OCR, direct bank feeds, payments, external filing, spendable-cash forecasts and automatic eligibility or compliance decisions remain outside this demonstration.

## Required fields and gates to finish

| Field or gate | Current value |
| --- | --- |
| Repository | [g7dream/GrantThread](https://github.com/g7dream/GrantThread), public, MIT licensed. Public visibility, default branch `master`, README and licence independently verified; confirm the release revision when recording. |
| Live URL or functioning test build route | [GrantThread](https://timeillusion.com/grantthread/): 18 personal-demo browser checks pass, including OAuth, both roles, selected original download, resolved clarification and Restore/reload. Earlier invited-account financial XLSX/PDF and shared-manifest downloads are separately verified. PENDING real signup email verification and judge handoff; repeated rehearsals are optional confidence checks. |
| Genuine GrantThread agent evidence | Earlier regional Nova Lite job `job-f2ce0cb489044197`: four model calls/eight tool successes, 8.59 seconds, incomplete draft and `waiting_input` for missing proof/human review. New personal-demo reviews separately stopped at a budget with no report/proposal or failed under throttling. PENDING final recording of the actual outcome. |
| Video | PENDING recording, public YouTube/Vimeo URL and measured duration of at most five minutes. |
| AWS Builder ID | PENDING entrant's Builder profile email, entered privately in the submission form; not the AWS account number. |
| Architecture | [ARCHITECTURE.md](../ARCHITECTURE.md); local rendered and verified SVG/PNG/PDF exports are ready in `artifacts/GrantThread-architecture.*`. Select the readable diagram for submission. |
| Testing instructions | [PUBLIC_DEMO.md](../PUBLIC_DEMO.md) documents email/password signup, personal-copy creation, both roles and Restore. Eighteen browser checks pass; real email verification and availability through judging remain to confirm. Repeated rehearsals are recommended. |
| Licence and dependency notices | Public root MIT licence verified; dependency and fixture notices are included in the published source. Recheck notices against any later packaged release. |
| Build dates and contributors | PENDING confirm final history and contributor details. |
| AI coding assistance | Codex used during implementation. |
| Prior work and support disclosure | PENDING contributor review; do not infer absence. |
| Builder post URLs | Optional; local drafts are not published posts. |

Review [RULES_CHECK.md](RULES_CHECK.md) before submitting. Replace completed gates with their actual evidence, remove editorial notes from submission copy, and state any remaining limitations plainly. No private financial sources, credentials or account details belong in public source, screenshots or the video.
