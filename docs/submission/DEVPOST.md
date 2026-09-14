# GrantThread — Many grants. One clear thread.

**Submission draft, updated 14 September 2026.** The local workflow and 244 automated tests have passed. The AWS backend stack is deployed, basic public API checks have passed, and a direct regional Nova Lite tool roundtrip is verified. A genuine GrantThread Strands reconciliation is verified: four model calls, eight successful tool calls and a correct waiting_input result for missing proof and human allocation review. Actual hosted Cognito sign-in, normal reload, financial display and XLSX download/readback now pass. A fresh portfolio-wide browser job reached its tool budget and saved no draft; hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. The public repository exists but is empty; source publication, the video and required entrant details remain pending. These are separate gates, not a completed submission.

## Tagline

Record shared grant work once, review the exceptions, and share a report with its evidence.

## Inspiration

A grant administrator may need to explain the same activity to several funders, with different report layouts, currencies and evidence requirements. The difficult part is keeping the underlying facts consistent while knowing which details can be shared. GrantThread connects incoming records, financial review and a targeted funder conversation.

The primary user is a professional grant administrator. The funder receives a deliberately shared package, while the grantee controls its internal records. The proposed track is Professional Agents.

## What it does

The fictional Bright Path Lab scenario spans three grants. Five expenses total EUR 5,200. A proposed venue split exceeds the original expense by EUR 200, and a printing expense lacks its configured payment proof. The reviewer inspects the sources, corrects the split and supplies the missing proof. Two report layouts reuse confirmed facts. An explicit sharing manifest selects the report version and attachments a funder receives; a clarification thread retains the question, response and acknowledgement. One workshop can support two grants while remaining one unique activity.

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

The current local suite passed **244 tests: 169 backend, 50 release/build-script and 25 frontend API tests**. The TypeScript/Vite production build also passed. These checks cover permissions, exact money and conversion, stale updates, financial import/export, worker boundaries, release packaging and request failures. They do not establish deployed behavior or model extraction quality.

Earlier local browser journeys completed source inspection, the EUR 500 + EUR 500 venue correction, printing-proof review, ready report/PDF download, selected-attachment sharing and funder clarification. Financial browser checks covered XLSX import, receipt-based conversion, a linked correction, template export and preservation of entered rate direction. Desktop and narrow-screen checks included mobile navigation focus and financial controls; no actual screen-reader session was run.

Cloud verification includes 49 application checks: nine scope, six agent and 34 financial checks using administrative Lambda invocation with trusted gateway claims. They exercised real storage, queue and model services, including XLSX/text-bank-PDF import, payment matching, receipt-based conversion and a correction from CAD 25 to CAD 20. They do not verify public API Gateway JWT signatures or browser behavior. Separate public requests returned health HTTP 200 and anonymous session HTTP 401. Final raw/gzip/Brotli hashes match the built files, and the canonical browser loads the current bundle. Separate actual browser checks passed Cognito sign-in, normal reload, financial figures and a downloaded XLSX independently read back as CAD 20 actuals and CAD 250 receipts. Hosted Youth Skills version 1 sharing with one selected source, Northstar login/package view and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. A USD 25 monthly budget alert is deployed; it is not a hard spending cap.

Three isolated local service journeys reproduced the fixture totals, both report formats and a resolved clarification. Their execution timings exclude browser use, network, model inference and human review. No administrator time savings, manual baseline or participant study has been measured. User validation remains pending. See [EVALUATION.md](../EVALUATION.md) for the evidence, transport boundary and remaining limitations.

## What's next

Complete the final download checks and hosted judge journey, record the genuine Strands execution and human review, then test the workflow with grant administrators and funder reviewers. Measure repeated entry and review effort using permissioned, comparable tasks. OCR, direct bank feeds, payments, external filing, spendable-cash forecasts and automatic eligibility or compliance decisions remain outside this demonstration.

## Required fields and gates to finish

| Field or gate | Current value |
| --- | --- |
| Repository | [g7dream/GrantThread](https://github.com/g7dream/GrantThread) exists and is public; empty repository verified. PENDING final source publication and public README/licence check. |
| Live URL or functioning test build route | Destination: `https://timeillusion.com/grantthread/`. Hosted grantee sign-in/reload and financial XLSX readback verified; selected sharing and a source-linked question/answer also verified. Financial PDF values, final-bundle selected original/shared-PDF/shared-manifest downloads and resolved clarification also verified. PENDING three consecutive full judge journeys and final handoff. Local setup is documented in [SETUP.md](../SETUP.md). |
| Genuine GrantThread agent evidence | Verified job `job-f2ce0cb489044197`, regional Nova Lite in `eu-north-1`, four model calls/eight tool successes, 8.59-second worker execution, final `waiting_input` with missing proof and human allocation review. The fresh portfolio-wide browser run separately hit its budget with no draft. PENDING final recording and completed judge journey. |
| Video | PENDING recording, public YouTube/Vimeo URL and measured duration of at most five minutes. |
| AWS Builder ID | PENDING entrant's Builder profile email, entered privately in the submission form; not the AWS account number. |
| Architecture | [ARCHITECTURE.md](../ARCHITECTURE.md); Deployed status recorded; PENDING export a readable diagram for the submission. |
| Testing instructions | PENDING verified hosted judge identities and access instructions, including availability through the judging period. |
| Licence and dependency notices | Root MIT licence exists; PENDING final dependency notices and published artifact checks. |
| Build dates and contributors | PENDING confirm final history and contributor details. |
| AI coding assistance | Codex used during implementation. |
| Prior work and support disclosure | PENDING contributor review; do not infer absence. |
| Builder post URLs | Optional; local drafts are not published posts. |

Review [RULES_CHECK.md](RULES_CHECK.md) before submitting. Replace completed gates with their actual evidence, remove editorial notes from submission copy, and state any remaining limitations plainly. No private financial sources, credentials or account details belong in public source, screenshots or the video.
