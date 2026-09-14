# Agents for Humans: Measuring the workflow and testing its failure cases

Draft for AWS Builder Center. Not published. Three local service-layer runs are measured below; human review, manual baseline and administrator savings remain unmeasured. A separate genuine Strands job has an 8.59-second worker execution measurement; it is not an administrator task time.

GrantThread's demonstration can look smooth while still hiding work. A useful measurement has to include preparation, source checking, corrections, model waiting and the final review. Counting only the time spent generating a report would miss much of the administrator's task.

The future human comparison will use equivalent synthetic data for a manual baseline and the application. The task is to prepare two report layouts from three grants, correct one excessive allocation, add a missing payment document and answer one funder question. It should record elapsed time, repeated fields, user decisions, incorrect or unresolved claims and checked export facts. If people participate, record task order and individual outcomes. That comparison has not been run.

The financial fixture has an independent answer: EUR 5,200 of unique expense value and, after correction, grant allocations of EUR 1,700, EUR 3,100 and EUR 400. The activity fixture also has an independent answer: one workshop with 24 fictional participants linked to two grants. Neither fixture is a claim about real-world savings.

Failure cases matter alongside speed. A repeated expense ID with conflicting original amounts should stop an import. An old proposal should conflict after its inputs change. A document that asks the agent to reveal another organisation's data should remain untrusted text. An invented citation should not become a source. A timed-out model run should leave the verified ledger intact.

The executed benchmark instead used three isolated SQLite service-layer journeys. It included seeding, CSV processing, the correction, evidence approval, both report/PDF formats, a shared snapshot and one resolved clarification. Every run produced EUR 5,200 in total allocations with the expected EUR 1,700 / 3,100 / 400 split. Agent status remained `unavailable`, with no fabricated tool events. Per-run service durations are recorded in the regenerated `docs/BENCHMARK_RESULTS.json`; they exclude browser use, network, inference and human review.

**Recorded results and gaps:**

| Observation | Result |
| --- | --- |
| Manual baseline elapsed/review time | Unmeasured |
| GrantThread administrator task/review time | Unmeasured; automated service timings are not substitutes |
| Repeated fields and decisions | Unmeasured |
| Exact expense and allocation totals | Matched the fixture in all three local service runs |
| Two report formats and resolved clarification | Produced in all three local service runs |
| Access/versions/containment cases | Covered by the current 244 local tests; 49 additional cloud application checks use administrative Lambda invocation with trusted claims |
| Three complete deployed journeys | Pending; the three recorded runs are local service execution only |

The label is “scripted synthetic benchmark; user validation pending.” Separately, the local browser completed the import-to-clarification journey and the report download. A 390-pixel viewport check exposed horizontal overflow, which was fixed and remeasured; keyboard Escape restored focus to the mobile navigation trigger. An actual screen-reader session was not performed.

These observations support the reproducibility of this local workflow, not broad productivity gains or production safety. The next measurement must include people doing the full task. The service-runtime numbers should never be presented as administrator completion times or a savings percentage.

**Before publication:** add the frozen release revision, screenshots or redacted test artifacts, actual AWS/model observations and the public release link. Local details and timing scope are recorded in `docs/EVALUATION.md` and `docs/BENCHMARK_RESULTS.json`. The backend deployment and genuine regional Strands reconciliation are verified. Actual hosted grantee sign-in/reload and XLSX readback pass. A second portfolio-wide browser run hit its budget after nine model calls/eight tools, rejected one missing-evidence reference and saved no draft; this distinct outcome belongs in the evaluation. Hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified, and no complete repeated judge workflow or productivity benefit is claimed.
