# Model, limits and claim disclosure

GrantThread integrates the Strands Agents SDK with an Amazon Bedrock model provider. Offline tests exercise actual SDK dispatch with explicitly fictional, scripted provider responses. **No genuine Bedrock inference run or AWS/Cognito/SQS deployment is verified.** These tests do not establish model extraction quality, cloud operation or inference cost. The cPanel frontend package is a preview until an authenticated backend is configured and verified.

| Evidence field | Current record |
| --- | --- |
| Model ID and region used | Not recorded; requires actual configured run |
| Strands/runtime versions tested | Strands 1.54.0; Python 3.12; installed dependencies locked in `backend/requirements.txt` |
| Genuine completed job ID and tool events | Pending evidence |
| Model runtime, token usage and cost | Unmeasured; local service timings in `BENCHMARK_RESULTS.json` exclude inference |
| Local verification and test counts | See [EVALUATION.md](EVALUATION.md) and [PROGRESS.md](../PROGRESS.md) |
| User study | User validation pending |

Reconciliation proposes evidence links and report work through seven scoped Strands tools. It allows at most eight tool calls, ten model turns, 1,200 output tokens per model call and 180 seconds per job. Canonical allocations and publication require explicit authorised API actions. Shared factual narratives use confirmed structured facts and deterministic templates; source text and model prose are not automatically adopted as factual narrative.

Bank extraction is a separate `bank_statement` job, not an additional unrestricted reconciliation tool. A deterministic parser first handles a narrowly supported text-PDF layout. An unrecognised layout requires a real configured Bedrock provider. Without one, the source remains available and the job reports `unavailable`; no replacement transactions or invented AI results are generated.

The bank model receives only the selected statement's extracted pages. Its structured output describes up to 60 candidate transactions plus explicitly sourced totals and extraction flags. There are at most two model/provider requests, 4,000 output tokens per call and a 180-second job limit. Exact page excerpts, date and amount tokens, currency and debit/credit claims are checked before saving rows. Separately sourced totals/balances are checked when available; missing checks, mismatches and incomplete extraction produce visible warnings. A completed job means a preview was saved for review, not that every transaction was found or correctly interpreted. It never confirms ledger entries, funding receipts, exchange rates or payment instructions.

Both job types retain immutable actor scope and input versions. Claims and expiring leases prevent stale or duplicate workers from overwriting current review work. Confirmation remains a separate authorised user action.

Financials also supports deterministic XLSX ledgers, funding receipts, editable drafts, linked adjustments and mapped XLSX exports. Integer minor units and decimal rate arithmetic preserve original and reporting amounts separately. The user selects a receipt, weighted receipt rate or entered rate according to the funder's requirements. There is no live market-rate feed, automatic FX-policy choice, FIFO receipt consumption or financial spending-cap enforcement. Confirmation freezes conversion details. See [FINANCIALS.md](FINANCIALS.md).

The separate **Response estimates** calculator uses fixed simulated funder histories and deterministic calendar-day calculations. It is not an eighth agent tool, does not invoke a model and makes no database writes. Its estimated ranges describe a fictional scenario, not verified submission dates, forecasting accuracy, confidence intervals or funder commitments. See [RESPONSE_ESTIMATES.md](RESPONSE_ESTIMATES.md) for the calculation and limits.

Source references identify document versions and pages. A valid reference does not establish that the document supports an interpretation. Uploaded documents are untrusted data, including text that looks like instructions to the agent.

Evidence and financial imports have distinct limits. Evidence files support up to 5 MB and 20 PDF pages; financial XLSX/PDF uploads are limited to 2 MB. Financial parsing supports up to 500 transactions and 30 workbook sheets, while bank AI output supports up to 60 rows. The organisation aggregate has a 340 KB ceiling and may fill earlier than row limits. Full financial bounds and formula-cache behavior are documented in [FINANCIALS.md](FINANCIALS.md). OCR, direct bank feeds, external filing, payments, grant award decisions and automatic legal/compliance judgments are out of scope. Missing facts stay missing.

Unavailability, timeout or retry must leave confirmed ledger data intact. Show the actual job status; do not substitute deterministic fixtures for a live Strands run or label cached results as live. If a video removes waiting, disclose the original elapsed time.

All bundled organisations, source files, amounts and outcomes are fictional. Only fictional files belong in public demonstrations and published fixtures. Local demo accounts can be selected by anyone accessing that demo; do not upload sensitive financials to a public demo deployment. Private source files are excluded from public assets and repository release material. The release demonstrates a bounded workflow, not evidence of customer adoption, production security, universal accuracy or measured time savings.

Development used Codex as an AI coding assistant. Confirm the final contributor list and disclose any incorporated prior project work before submitting; do not assert that no prior work exists without checking repository history and assets.
