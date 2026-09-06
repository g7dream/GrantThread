# Model, limits and claim disclosure

GrantThread integrates the Strands Agents SDK with an Amazon Bedrock model provider. Local SDK dispatch and containment tests passed using controlled model inputs. Bedrock is not configured for this release: there has been no genuine model inference run. The configured model and region must be recorded after actual verification.

| Evidence field | Current record |
| --- | --- |
| Model ID and region used | Not recorded; requires actual configured run |
| Strands/runtime versions tested | Strands 1.54.0; Python 3.12; installed dependencies locked in `backend/requirements.txt`; 28 local backend/worker tests passed |
| Genuine completed job ID and tool events | Pending evidence |
| Model runtime, token usage and cost | Unmeasured; local service timings in `BENCHMARK_RESULTS.json` exclude inference |
| User study | User validation pending |

The model proposes evidence links and report work through scoped tools. Canonical allocations and publication require explicit authorised API actions. Exact money uses integer minor units. Shared factual narratives use confirmed structured facts and deterministic templates; optional model prose remains a proposal until an appropriate review flow accepts it.

Source references identify document versions and pages. A valid reference does not establish that the document supports an interpretation. Uploaded documents are untrusted data, including text that looks like instructions to the agent.

Initial design limits are 5 MB per evidence file, 20 PDF pages, 500 CSV rows, eight tool calls and 180 seconds per job. Verify the actual enforced limits against the release code. Scanned PDFs/OCR, external filing, payments, grant award decisions and automatic legal/compliance judgements are out of scope. Missing facts stay missing.

Unavailability, timeout or retry must leave confirmed ledger data intact. Show the actual job status; do not substitute deterministic fixtures for a live Strands run or label cached results as live. If a video removes waiting, disclose the original elapsed time.

All supplied organisations, amounts, agreements, invoices, attendance and outcomes are synthetic. The release demonstrates a bounded workflow, not evidence of customer adoption, production security, universal accuracy or measured time savings.

Development used Codex as an AI coding assistant. Confirm the final contributor list and disclose any incorporated prior project work before submitting; do not assert that no prior work exists without checking repository history and assets.
