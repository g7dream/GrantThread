# GrantThread
## Four-day build plan for Codex GPT-6 Astra
**Agents for Humans Hackathon | Prepared 6 September 2026 | Owner: Lucian Cojocaru, Remnant Dream SRL**

### Product decision
**Many grants. One clear thread.** GrantThread is a shared operations workspace for organisations managing several grants and the grantmakers reviewing their reports. Start with the professional grant administrator; the funder receives a deliberately shared report and its evidence, not access to the grantee's whole organisation.

The product promise is practical: record an activity or expense once, allocate it explicitly, prepare the right report for each grant, and resolve the remaining questions in one place. The distinctive demonstration is a complete operational workflow, not a chatbot beside a dashboard.

### Build commitment
- **Core build:** 7-10 September, approximately 40-46 focused implementation hours with Codex, including deployment, verification and submission materials. This is an aggressive planning estimate, not a delivery guarantee.
- **Buffer:** 11-12 September for actual integration failures and evidence collection, not new features.
- **Freeze and submit:** aim for 13 September; 14 September is contingency. The official deadline is **15 September 2026 at 03:00 Europe/Bucharest**. [S1]
- **Delivery:** compiled web interface uploaded to an isolated Spaceship cPanel location; managed application and AI backend on AWS. This satisfies the hosting preference without forcing agents into shared-host processes.
- **User involvement:** one short configuration handoff and one final demonstration review. Routine design, library choices and implementation fixes should proceed autonomously.

### What success looks like
A grantee managing three grants imports a ledger and evidence, resolves one allocation issue and one missing document, prepares two distinct report formats, and shares one controlled package. A funder reviews that package, asks a targeted question and sees the response. The real Strands agent performs several scoped tool calls and leaves inspectable outputs.

The aim is a credible, polished entry aligned with the judging criteria. There is no defensible percentage chance of winning. Likewise, AI cannot be guaranteed never to be wrong: the architecture must constrain what a wrong output can change.

**Working name:** GrantThread. Preliminary exact-name web checks did not surface a clear competing grant product; domain and trademark availability remain unverified. Do not delay the hackathon for branding research.

<!-- PAGE -->
# 1. Research: problems worth solving
Research findings below support priorities, not claims that this product has already saved time. Sources are listed at the end.

| Observed problem | Evidence and limitation | Product decision |
| --- | --- | --- |
| Grant processes consume staff time | CEP's 2025 study reports median 55 hours across proposal, monitoring, reporting and evaluation for surveyed Europe-based funders, versus 25 for U.S. funders. This is not reporting alone and is not representative of all European funders. [S4] | Keep shared facts and evidence separate from each grant's report format. |
| Different reporting forms consume capacity | Yorkshire funders introduced a common reporting form in January 2026. Grantee feedback favoured some structured choices and found the first draft too short. Small-grant, qualitative case. [S5] | Use clear factual fields plus prepared narrative; do not equate fewer fields with less work. |
| Reports generate too little useful dialogue | CEP's practitioner commentary describes redundant reports and funder backlogs; roughly 60% of surveyed grantees discussed submitted reports with funders. Older observational evidence. [S6] | Give funders a concise changes-and-questions queue with evidence and closure. |
| Limited cash reserves raise the stakes | In NFF's 2025 U.S. nonprofit survey, 52% reported three months or less cash on hand. Self-selected survey; not a European prevalence estimate. [S7] | Separate awarded budget, allocated spending and confirmed receipts. Defer predictive cash planning. |
| Evidence requirements differ by funding model | EU guidance distinguishes actual-cost evidence from implementation evidence for lump-sum grants. This is operational guidance, not a survey of pain. [S8] | Store funding mode. Limit automatic checks to the supported actual-cost demo rules. |
| Another mandatory portal can add work | The Yorkshire initiative considered and rejected a shared portal, citing capacity, cost and relationships with individual funders. [S5] | Make report export valuable even when the funder never signs up. |

### Product hypotheses to test
1. One shared record can reduce re-entry across three reporting formats.
2. A targeted request with a source reference is easier to resolve than a broad request for more information.
3. A submitted snapshot gives funders useful context without exposing unrelated work.

If available, run 15-minute sessions with two multi-grant administrators and one funder. Ask about their last report, the last missing document, and information they would refuse to share. Use their answers to fix the demonstration, not expand the feature list. If none is available, state **user validation pending** and use reproducible synthetic benchmarks.

The main counterargument is that cleaning every document before the app helps could add work. Demonstrate value from an ordinary ledger and a small imperfect evidence folder; correct exceptions progressively.

<!-- PAGE -->
# 2. Competition strategy and required outputs
**Recommended track: Professional Agents.** The primary user is a grant administrator doing professional work. Supporting nonprofits alone does not make Good Neighbor the best track; the FAQ says to choose by the primary user. [S2]

### Required submission checklist
- Build the new project during the permitted 10 August-14 September window; disclose incorporated prior work. Use Strands and an AWS account. [S1]
- Provide a public MIT or Apache repository with functioning code, assets, README and setup instructions; architecture diagram; AWS Builder ID; English materials; and a public YouTube/Vimeo demonstration of at most five minutes. [S1]
- Provide functioning judge access and retain it through **9 October, 03:00 Bucharest**. One project can win one prize. Romania is not listed as excluded; organisations and individuals may enter. [S1]
- Keep GrantThread independent of separately supported Reality Forge work. Rules restrict prior sponsor/administrator development support; clarify before transferring another competition's support. [S1]

### Build for the five equally weighted criteria
| Criterion | Evidence this build should provide |
| --- | --- |
| Technical implementation | Real Strands decisions and scoped tools, durable asynchronous jobs, exact calculations and a live deployed workflow. |
| Design | Coherent grantee and funder experiences; useful source panels, clear states and an exception queue. |
| Potential impact | A specific repeated-reporting task and measured work counts, including review time. |
| Creativity and originality | Shared evidence reused through explicit allocations and different report formats, with restricted funder sharing. |
| Presentation | One concise story from incoming evidence to corrected report and funder response. |

These priorities follow the published rubric. A live demo and AgentCore can strengthen technical scoring; AgentCore is optional. Do not replace a working Lambda deployment merely for a badge. [S3]

### Explicit bonus opportunity
Reserve time for **three distinct AWS Builder posts**: 0.2 additional points each, up to 0.6. Use **Agents for Humans** in each title and publish before the deadline. [S1]
1. The multi-grant reporting problem and product workflow.
2. Implementing scoped tools and event-driven work with Strands on AWS.
3. What the benchmark and failure cases revealed.

Keep the posts substantive, with screenshots, architecture and actual observations. Do not fabricate users or performance improvements.

Registered entrants can request $50 AWS promotional credits until **11 September, 22:00 Bucharest**, while supplies last. Request them early if entering; availability and cost coverage are not guaranteed. [S3]

<!-- PAGE -->
# 3. Scope and the demonstration dataset
### P0: ship these capabilities
- Grantee portfolio, grant detail and an evidence inbox.
- CSV expense import and text-based PDF/TXT evidence upload, with source/version metadata.
- Configured obligations, expense allocations and evidence links.
- A real Strands run triggered by imported or newly added evidence.
- A decisions queue with proposed changes, source links and exact calculations.
- Two grant-specific report formats, downloadable report PDF and evidence manifest.
- Explicit sharing of a report snapshot; funder review and clarification workflow.
- Seeded synthetic users, repeatable demo reset and visible agent-run activity.

### P1 / defer
Agreement extraction can propose fields; require review before making obligations authoritative. Add broad arbitrary-document import only after the P0 path works. Defer image OCR, bank/email integrations, automatic filings, funder payments or award decisions, eligibility scoring, cross-currency consolidation, cash-flow forecasting, payroll timesheets, custom workflow builders and mobile-native apps.

### Seed a realistic portfolio
All organisations, names, agreements, invoices and outcomes below are fictional and must be labelled synthetic.

| Grantee | Grant / funder | Award / mode |
| --- | --- | --- |
| Bright Path Lab | Digital Belonging / Northstar Foundation | EUR 20,000 / restricted actual-cost |
| Bright Path Lab | Community Makers / Riverbend Trust | EUR 15,000 / restricted actual-cost |
| Bright Path Lab | Youth Skills / Northstar Foundation | EUR 10,000 / restricted actual-cost |
| Harbour Collective | Volunteer Support / Northstar Foundation | EUR 12,000 / restricted actual-cost |

The fourth grant supplies a second grantee for the funder's portfolio and access-boundary test. It needs minimal seed data, not another feature set.

### Exact financial fixture
Five unique expenses total EUR 5,200: venue 1,000; printing 600; facilitator 1,200; kits 2,000; insurance 400. Initial **proposed** venue allocations of 700 + 500 exceed 1,000 by 200; the invalid split must never enter the canonical ledger.

After an authorised correction to 500 + 500: Digital Belonging allocations are 500 venue + 600 printing + 600 facilitator = **1,700**. Community Makers has 500 venue + 600 facilitator + 2,000 kits = **3,100**. Youth Skills has insurance = **400**. Total allocated = **5,200**, exactly matching unique expense value.

Printing lacks payment evidence required by this fictional agreement. Its allocation remains recorded, while report readiness is incomplete. One workshop supports two grants but counts once in the organisation's unique activity total; grant-linked totals must not be summed as unique impact.

<!-- PAGE -->
# 4. Product experience and visual direction
### Visual identity
Create a calm, precise workspace that looks credible to both an NGO administrator and a programme officer. Use warm white **#F6F7F4**, ink **#172D35**, teal **#0A7C78**, muted slate **#637680**, amber **#B66C12** and error red **#B83E45**. Use a restrained thread/link motif joining an activity, its evidence and a report; no decorative stock photography.

Use a locally bundled sans-serif font, readable 14-16 px body text and tabular numerals for money. Desktop: 224 px sidebar, clear content grid, optional 360 px source drawer. On narrow screens stack panels, convert key tables to cards or labelled horizontal scroll, and preserve primary actions. Use 120-180 ms transitions and respect reduced motion.

### Six surfaces, one workflow
| Surface | What the first viewport answers | Primary action |
| --- | --- | --- |
| Portfolio | Which grants need attention, and what is actually missing? | Review decisions |
| Grant detail | What was promised, allocated and evidenced for this grant? | Prepare report |
| Evidence inbox | Which new documents have been linked or need clarification? | Add evidence |
| Decisions | What exact change needs my judgement, and why? | Review and apply |
| Reports | What is ready, what is unsupported, and what will be shared? | Preview / share |
| Funder workspace | What changed in my funded portfolio and which request is open? | Review report |

Avoid a wall of generic KPI cards. The portfolio should lead with **Needs a decision**, then the grant table and near-term obligations. Readiness is “6 of 8 configured requirements evidenced”, never “75% compliant”. Pending AI extraction must visibly keep configuration incomplete.

### Interaction details
Each proposed change shows the old value, suggested value, relevant source and resulting totals. Approve a meaningful batch, not every trivial document match. Users can reject, correct or defer. Unresolved evidence stays explicit. A source drawer opens the exact document version and page/excerpt; it must not imply that a citation proves the interpretation.

Report sharing opens a short manifest preview: recipient funder, grant, report version and selected attachments. Internal warnings, other funders' allocations and private discussion are excluded. Where an invoice contains unrelated sensitive detail, share a reviewed extract or redacted copy; the original requires an explicit selection.

For the public demo, show a persistent **Synthetic demonstration data** label. Role switching must authenticate or establish the corresponding server-validated demo identity; changing a client-side role flag is not authorisation.

<!-- PAGE -->
# 5. Useful AI with bounded consequences
### Replace an impossible guarantee with enforceable controls
No model, citation system or approval flow makes all errors impossible. The goal is to prevent model output from directly changing financial records, obligations, permissions or disclosures. Human review remains necessary for consequential judgements; it is concentrated into a few visible decisions.

| AI may do automatically | Requires an authorised user action | Not implemented |
| --- | --- | --- |
| Read already authorised evidence; propose links; run exact calculation tools; save draft reports; create internal review items; recheck affected drafts. | Confirm extracted grant rules; change canonical allocations or milestones; publish a report snapshot; select shared attachments; mark a clarification resolved. | Pay money; submit to external grant portals; email funders; approve awards; reject applicants; silently change access or declare legal eligibility. |

### Fact and proposal model
Store **source evidence**, **user-confirmed facts**, **calculated results**, and **AI proposals** separately. A citation must resolve to an authorised source version and page/record. Existence checking does not establish that the source entails the claim. Show proposed interpretations as such.

For the hackathon's final shareable report, use deterministic narrative templates populated from confirmed facts, counts and calculations. AI selects and organises supported material and drafts optional commentary, but unreviewed free prose does not automatically enter the shared report. Free prose stays labelled draft until explicitly accepted. Missing values are “not provided”, never filled from plausible guesses.

### Financial and date rules
- Use integer minor units plus currency. Calculate through backend functions, never model arithmetic.
- Separate expense amount, allocation amount, paid status and report evidence status.
- Flag “allocations exceed recorded allocatable amount”; do not call it fraud or a universal funding-law violation.
- Preserve every original amount, currency, date and source. Block mixed-currency aggregation in the MVP.
- Do not guess payment dates, deadline times, grant rules or eligibility. Date-only obligations remain date-only; no fabricated hour.
- Corrections use conditional version updates. If evidence or rules changed after proposal creation, approval requires recomputation.

### Containment
Uploaded text is untrusted data. Scope documents before they reach the model. Do not provide shell, unrestricted HTTP, SQL, email or payment tools. User/organisation scope comes from verified server context, never a model argument. Cap document size, tool calls, model tokens, retries, runtime and daily job count. A model outage must leave the verified ledger intact.

Use one actual Strands agent with structured tool outputs and persisted pause/resume state; official guidance supports typed outputs and human intervention. Schema validity is not factual correctness. [S14]

<!-- PAGE -->
# 6. Hosting and architecture
### Decision: cPanel interface, AWS application
Spaceship supports cPanel, but its shared-host AUP restricts unattached daemons and frequent cron. Do not run a permanent agent or queue worker there. The exact hosting plan, domain, SSL and existing files are still unverified. [S9]

**Frontend:** React + TypeScript + Vite, a small component set and Tailwind styling. Build locally, upload the compiled assets. Use the existing project conventions if a relevant repository exists; this plan does not authorise replacing another website.

**Backend:** one Python domain layer used by the API and worker. Deploy through one AWS SAM template. No PHP backend, Redis, vector database, Kubernetes, VPC or second authentication system is needed for the first version.

### Request and data flow
1. cPanel serves the SPA over HTTPS. Cognito managed login uses authorization code + PKCE and a public app client with no client secret.
2. API Gateway validates the access token; Python Lambda enforces organisation, grant and report permissions on every operation.
3. DynamoDB stores scoped records and versioned proposals. Private S3 stores source documents and generated reports. The API authorises short-lived upload/download links.
4. An evidence event creates a job and sends its ID to SQS. A Strands Lambda worker fetches scoped data, invokes Bedrock and writes derived proposals/drafts.
5. The UI polls authorised job state. Approval uses a separate deterministic endpoint. No long synchronous model calls from the browser.

HTTP API requests have a 30-second maximum integration timeout, so acknowledge jobs promptly. Queue deliveries can repeat: use idempotency keys and conditional job transitions. [S10, S11]

### Initial guardrails, adjustable after measurement
PDF/TXT: 5 MB and 20 pages each; CSV: 500 rows. Text PDFs only for P0; scanned PDFs receive a clear unsupported message. One job per user at a time, queue batch size one, two worker invocations globally, at most eight tool calls and 180 seconds per run. These are initial application limits, not claims about platform defaults.

Pin the tested Strands/runtime versions and choose a Bedrock model with verified account access and tool-use support. Start in one EU region if the needed model is available; do not silently change region or enable cross-region processing for future real data. The public demo uses synthetic data only. [S12]

### cPanel package
Deliver a ZIP of public assets with correct Vite base path, `.htaccess` SPA fallback and deployment instructions for a dedicated subdomain or subfolder. API origin, region and Cognito client ID are public configuration; model credentials and AWS keys never enter the ZIP. Back up existing destination files before upload.

<!-- PAGE -->
# 7. Data, permissions and agent contracts
### Keep the data model explicit
| Record | Essential fields |
| --- | --- |
| Organisation / membership | organisationId, user subject, role; server-managed memberships |
| Grant | granteeOrgId, funderOrgId, currency, awardMinor, fundingMode, confirmed rule version |
| Requirement / activity | grant links, status, source reference, date or deadline with precision |
| Expense / allocation | expenseId, amountMinor, currency, grantId, allocationMinor, confirmed version |
| Evidence | organisationId, object key, document version, hash, page count, authorised links |
| Proposal / agent run | input versions, tool results, proposed operations, state, idempotency key |
| Report / shared snapshot | grantId, template version, included fact versions, attachment manifest, recipient, publication version |
| Clarification / audit event | snapshotId, question, scoped response, actor, action, timestamp |

Use a small number of DynamoDB tables with clear organisation/grant partitioning and documented indexes. Never infer permission from possession of a document ID. Record a report snapshot and sharing grant explicitly; the funder API projects shared data rather than serialising the grantee's internal grant record.

### Permission contract
A grantee can manage its internal portfolio. A funder can read only shared snapshots and selected attachments for its grants, and participate in their clarification threads. A different grantee cannot read either. Background jobs carry immutable server-derived actor scope. A funder's AI run cannot query the grantee's private inbox or cross-grant ledger.

### Bounded Strands tools
- `list_requirements`: return confirmed obligations for authorised grants.
- `read_evidence`: retrieve allowed source text and stable references.
- `suggest_evidence_links`: persist candidates without changing confirmed links.
- `calculate_allocations`: exact per-expense and per-grant results.
- `check_report_readiness`: deterministic configured checks, including unconfirmed rules.
- `save_review_proposal`: typed proposed operations with source versions.
- `assemble_report_draft`: prepare supported content and a manifest; no publication.

A fresh document should cause the model to choose the relevant tools and affected report drafts. A fixed scripted animation is not an agent run. Display tool names, factual observations, timings and results; do not expose hidden reasoning.

### Minimum endpoint groups
`/portfolio`, `/grants`, `/expenses/import`, `/evidence/upload-intent`, `/evidence/complete`, `/jobs`, `/proposals`, `/proposals/{id}/apply`, `/reports`, `/reports/{id}/share`, `/shared-reports`, `/clarifications`.

Presigned uploads use server-generated object keys; validate size and type after upload before processing. All download and export paths recheck authorisation. Use conditional writes for approval; stale or repeated actions cannot duplicate allocations or mutate a published snapshot. [S13]

<!-- PAGE -->
# 8. Days 1-2: make the real workflow work
Times below are planning budgets. Prefer a complete working slice over partially implemented screens. Preserve existing architecture where one exists.

### Day 1 - foundation and deployed slice (10-12 hours)
| ID | Task | Completion evidence |
| --- | --- | --- |
| D1.1 | Inspect repo, hosting destination and available AWS credentials. Freeze defaults and create the SAM stack, repo structure and synthetic fixture. | Configuration list and clean seed; no real documents or credentials committed. |
| D1.2 | Implement Cognito login, API authorisation, scoped records, S3 access and queued job plumbing. | cPanel URL reaches an authenticated API; one record persists after refresh. |
| D1.3 | Implement exact allocation functions and CSV import preview. Store invalid allocations only as proposals. | Fixture produces a EUR 200 exception and rejects an invalid apply. |
| D1.4 | Build portfolio and evidence inbox with real seeded API data. Add a minimum genuine Strands tool call. | One queued Strands result appears in the live UI and remains after refresh. |

**M1:** deployed vertical slice. If model access or authentication still fails, resolve it before building additional pages. Spend at most 90 minutes on optional hosting mechanics; the frontend remains locally buildable while access is arranged.

### Day 2 - evidence and useful agent work (10-12 hours)
| ID | Task | Completion evidence |
| --- | --- | --- |
| D2.1 | Implement bounded text-PDF/TXT parsing, document versions, citations and metadata. Add ordinary CSV fixtures with one ambiguous row. | Upload creates a source record; unsupported inputs fail clearly. |
| D2.2 | Implement the Strands tools and event-triggered portfolio reconciliation. Save typed proposals and report drafts. | A new document changes which tools and records the agent uses. |
| D2.3 | Build decisions queue, before/after values, source drawer and batch approval. Implement stale-version and retry handling. | Correction changes canonical totals only after an authorised apply. |
| D2.4 | Prepare two report layouts and deterministic readiness checks. Add a pause for missing information and restart from updated evidence. | Missing proof is visible; adding it rechecks the affected draft. |

**M2:** the agent completes evidence-to-decision-to-draft work. A chatbot-only outcome fails this milestone. Unknown clauses or data remain unresolved rather than being guessed.

### Codex execution rhythm
Use focused implementation blocks, not repeated planning. Commit at milestones, keep a short `PROGRESS.md` with completed task IDs and the next concrete action, and record decisions in `DECISIONS.md`. Delegate independent UI, fixture and submission-document work when useful; one owner controls schema, permissions and integration. Do not run broad audits after every change.

<!-- PAGE -->
# 9. Days 3-4: close the loop and submit well
### Day 3 - two-sided workflow and deliverables (10-11 hours)
| ID | Task | Completion evidence |
| --- | --- | --- |
| D3.1 | Finish exact report composition, source manifest and downloadable PDF. Keep optional AI prose out of shared output until reviewed. | Two report formats contain consistent confirmed figures and working source references. |
| D3.2 | Implement publication manifest, immutable report snapshots, explicit attachments and funder read projection. | Northstar sees its shared package; other grants and private evidence remain inaccessible. |
| D3.3 | Build funder portfolio and clarification lifecycle: question, response, acknowledged resolution and new report version if needed. | One request is answered without losing its source or history. |
| D3.4 | Add seeded demo identities, reset, useful empty/error/loading states and public synthetic-data labelling. | Fresh-session judge flow completes; verified ledger survives AI unavailability. |

**M3:** one grantee-to-funder story runs end to end, with a downloadable artifact. Freeze P0 scope here. Cut broad agreement extraction and dashboard extras before cutting real agent work, access isolation or export.

### Day 4 - evidence, polish and competition package (10-11 hours)
| ID | Task | Completion evidence |
| --- | --- | --- |
| D4.1 | Run the five targeted gates on the final candidate and perform the small benchmark. | Measured results file with failures and review time included. |
| D4.2 | Fix usability and presentation blockers; check one desktop and one narrow-screen flow. | Clear source evidence, readable figures and no broken main actions. |
| D4.3 | Finalise README, reproducible setup, MIT/Apache licence, architecture, Devpost description and three AWS Builder posts. | Concrete drafts ready to publish; claims match the working release. |
| D4.4 | Record and edit the public video, prepare judge credentials and freeze a release. | Video under five minutes; clean-install instructions and live URL work. |

**M4:** user can approve one concrete demonstration and submission package. Codex should prepare all publishable assets before asking for any still-required external-publication approval. Do not claim posts or submissions are published until confirmed.

### If the schedule slips
- First cut: charts, animations, cash forecasts, OCR, extra report templates and bulk agreement ingestion.
- Next cut: broad self-service onboarding; retain the real authenticated synthetic workflow and seed script.
- Do not cut: genuine Strands tools, financial invariants, tenant boundaries, source references, usable export, demo honesty or required submission materials.
- Use 11-12 September only for gates that failed, access problems and final measurement. Do not restart the stack or add AgentCore late.

<!-- PAGE -->
# 10. Five checks, not an exhaustive test programme
The user wants speed and limited review. Run a build plus the narrow checks below at their relevant milestone, then once on the release candidate. Re-run only affected checks after a fix. No coverage target, lint marathon or speculative penetration-test programme.

| Gate | Small, meaningful verification | Failure action |
| --- | --- | --- |
| G1: real deployed slice | cPanel URL -> login -> API -> persisted record -> queued genuine Strands result, then refresh. | Fix integration before expanding UI. |
| G2: access and disclosure | Two grantees and a funder try altered IDs for records, files, jobs, drafts and exports; inspect shared snapshot manifest. | Block sharing until isolation works. |
| G3: exact money and versions | Hand-calculated EUR fixture, partial allocation, rounding, mixed-currency refusal, repeated queue message and stale approval. | Block ledger changes until exact and idempotent. |
| G4: AI containment | Uploaded instruction to disclose other data; invented citation; unsupported numeric claim; model timeout. | Reject unsafe/unsupported proposal and preserve confirmed facts. |
| G5: judge journey | Fresh session completes import, correction, report, share and clarification; download opens; desktop and mobile are readable. | Fix only failures on the main journey. |

### Lightweight measurement
Compare a manual baseline and GrantThread on equivalent synthetic tasks: create two report formats from three grants, resolve an over-allocation and a missing document, then answer one funder question. Include setup, checking and corrections in elapsed time. Record repeated fields entered, unresolved issues, exported facts and number of user decisions.

If participants are available, alternate task order and report individual results for the small sample. Otherwise say **scripted synthetic benchmark; user validation pending**. Do not translate CEP's 55 hours into claimed product savings, invent testimonials or report statistical significance from two people.

### Acceptance targets, not achieved metrics
- Final seeded figures exactly match EUR 1,700 / 3,100 / 400 and total EUR 5,200.
- Every displayed source reference resolves within the viewer's scope.
- Every prescribed cross-organisation access attempt is denied.
- Unsupported AI claims cannot silently enter the generated factual report.
- A failed or retried model run does not corrupt verified records.
- The complete live demonstration works three consecutive times on the release candidate; vary one harmless fixture value to confirm it is not hardcoded.

Passing these checks increases confidence in this bounded demo. It does not certify production security, regulatory compliance or universal factual accuracy.

<!-- PAGE -->
# 11. Demonstration and handoff package
### Five-minute video plan: target 4 minutes 30 seconds
| Time | On-screen event and evidence |
| --- | --- |
| 0:00-0:25 | Introduce one organisation, three grants and repeated reporting. Say who benefits and why. |
| 0:25-1:05 | Import the ledger and evidence. Show real Strands tool activity and saved results. |
| 1:05-1:50 | Inspect the EUR 200 over-allocation and missing payment proof; open source references. |
| 1:50-2:30 | Apply an authorised correction and add the missing proof. Both report drafts update. |
| 2:30-3:15 | Preview the exact sharing manifest. Switch to the funder identity and review only its report. |
| 3:15-3:50 | Ask and answer one clarification; show the version trail and excluded unrelated grant. |
| 3:50-4:15 | Show one rejected unsupported claim and measured benchmark results, including limitations. |
| 4:15-4:30 | Show architecture and name Strands/AWS's actual role. End with the working product. |

Use a genuine run in the video. If waiting is edited, label the elapsed time. A cached demonstration can be available as a fallback only if clearly identified; never portray it as a live model run.

### Repository deliverables
- `frontend/`: SPA source, styles, auth and API client.
- `backend/`: domain calculations, API routes, scoped agent tools and report generation.
- `infra/`: AWS SAM template, setup and teardown instructions; region/model parameters.
- `fixtures/`: clearly synthetic agreements, evidence, CSVs, expected figures and demo seed/reset.
- `docs/`: architecture, permissions, short evaluation results, model/limits disclosure and deployment instructions.
- `README.md`, licence, `.env.example`, lockfiles, `PROGRESS.md`, `DECISIONS.md` and release notes.
- A cPanel upload ZIP containing public frontend files only; credentials supplied separately.

### Final user review: 10-15 minutes
Show the complete workflow once. Ask for corrections to product positioning and any external publication not already authorised. Provide ready-to-use Devpost text, video link or file, three post drafts, live site and public-code publication state. Do not ask Lucian to approve routine refactors or inspect every source file.

### What still needs real-world validation after the hackathon
Interview grant administrators across at least two funding models, test with permissioned documents, harden access and retention, assess actual contractual requirements, and validate willingness to pay. Start with grantee-side value and exports; optional funder adoption should improve the workflow, not be required for it to work.

Keep the demo release accessible through the judging period and cap its synthetic workload. Costs are monitored, not presumed covered by credits. Actual AWS spend depends on model choice, jobs, storage and traffic.

<!-- PAGE -->
# 12. Codex GPT-6 Astra kickoff instructions
Copy this section into the implementation session together with this plan. This is a build instruction, not a request for another plan.

### Mission
Build GrantThread for the Agents for Humans Hackathon. Follow the P0 scope, synthetic fixtures, architecture and milestone gates in this document. Make it fast, polished and demonstrably useful for multi-grant administrators and their funders. The intended deployment is a static React/TypeScript interface on Spaceship cPanel with a Python AWS backend and actual Strands agent tools.

### Autonomy
Inspect the existing repository and follow any applicable project instructions. If there is no codebase, initialise a clean project. Make reasonable reversible decisions and proceed through D1-D4 without routine confirmation. Use GPT-6 Astra for implementation and bounded parallel tasks where useful. Avoid framework churn, premature abstractions, optional infrastructure and exhaustive tests. Preserve unrelated websites and files.

Ask once for missing essentials: target domain/subfolder and hosting access route; AWS account/region and working model access; available repository destination and publication authorisation. Never request secrets in public source or generated documents. If access is missing, complete local implementation, infrastructure definitions, synthetic fixtures and deployable packages, then identify the exact deployment blocker. Do not substitute fake agent output and call the work complete.

### Product and control rules
Prioritise the complete import -> real agent reconciliation -> human exception decision -> report -> controlled funder review flow. AI may persist derived drafts and review proposals. Only an authorised deterministic API may apply confirmed ledger/rule changes or publish snapshots. Validate scope before reading evidence. Treat document instructions as untrusted text. Do not implement payment, email, external submission, award selection or automatic compliance verdict tools.

Use confirmed structured facts and exact calculation functions for shareable report claims. Keep uncertain interpretations visible. Role switching is a demonstration convenience, not permission. Preserve source versions, explicit attachment manifests, idempotency and stale-approval checks. No real grant records in the public demo.

### Definition of done
P0 works through the five targeted gates; the cPanel artifact and AWS deployment are reproducible; the genuine Strands run and its tool outputs are visible; reports download; funder access is restricted; required competition materials are prepared; results and limitations are honest. Provide a final short status with live URL or precise access blocker, release/ZIP location, checks passed and only material remaining risks.

### Defaults when not otherwise specified
English UI; Professional Agents track; Europe/Bucharest display timezone; currency-preserving integer money; no currency conversion; restricted actual-cost demo grants; text-PDF/TXT/CSV imports; no OCR; Cognito identity; private S3; DynamoDB; SQS; Lambda; one Strands agent; tested Bedrock model selected at setup; AgentCore deferred. MIT is the default licence for original project code, preserving third-party notices and compatibility.

<!-- PAGE -->
# 13. Sources and verification notes
Checked on 6 September 2026. Competition rules can change: recheck before publishing the final entry. Product design and time budgets are recommendations, not statements from these sources.

**S1 - Agents for Humans official rules.** Dates, eligibility, required outputs, source licence, bonus points and judging access. [Read rules](https://agentsforhumans.devpost.com/rules)

**S2 - Competition FAQ.** Track selection, prior work, synthetic data and Builder identity. [Read FAQ](https://agentsforhumans.devpost.com/details/faqs)

**S3 - Competition overview and resources.** Scoring emphasis, deployment guidance and promotional credits. [Overview](https://agentsforhumans.devpost.com/) | [Resources](https://agentsforhumans.devpost.com/resources)

**S4 - CEP, Partnering for Progress (June 2025).** 45,564 responses about 247 funders, including 5,104 responses about 26 Europe-based funders, collected 2020-24. Nonrepresentative of all funders; 55 hours spans several grant processes. [Report](https://cep.org/wp-content/uploads/2025/06/CEP_Partnering_for_Progress_FNL.pdf)

**S5 - Yorkshire Funders common report form (February 2026).** First-person implementation case, particularly small grants; qualitative rather than measured product impact. [Case study](https://www.funderscollaborativehub.org.uk/blogs/creating-solutions-yorkshire-funders-launch-a-common-report-form)

**S6 - CEP, Why Do We Bother? (2021).** Practitioner commentary on reporting burden and weak feedback loops. [Article](https://cep.org/blog/why-do-we-bother-the-tragedy-of-foundation-reporting-requirements/)

**S7 - NFF 2025 State of the Nonprofit Sector Survey.** 2,206 U.S. respondents; self-selected, unweighted sample. [Results](https://nff.org/state-of-the-nonprofit-sector-survey/2025-state-of-the-survey-nonprofit-sector-survey/) | [Methodology](https://nff.org/state-of-the-nonprofit-sector-survey/2025-state-of-the-survey-nonprofit-sector-survey/2025-survey-methodology/)

**S8 - European Commission Online Manual (May 2026).** Instrument-specific evidence and reporting guidance; not a universal rule for foundation grants. [Manual](https://ec.europa.eu/info/funding-tenders/opportunities/docs/2021-2027/common/guidance/om_en.pdf)

**S9 - Spaceship official hosting information.** cPanel offering and shared-host operating limits. [Hosting](https://www.spaceship.com/web-hosting/) | [Acceptable Use Policy](https://www.spaceship.com/legal/hosting-aup/)

**S10 - AWS HTTP API quotas and JWT authorisers.** Async-job and identity architecture. [Timeout limits](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-quotas.html) | [JWT authorisation](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html)

**S11 - AWS Lambda with SQS.** Retry and duplicate-processing behaviour. [Documentation](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html)

**S12 - Strands deployment and operation.** Pin tested versions and limit agent capabilities. [Lambda deployment](https://strandsagents.com/docs/user-guide/deploy/deploy_to_aws_lambda/) | [Production guidance](https://strandsagents.com/docs/user-guide/deploy/operating-agents-in-production/)

**S13 - AWS S3 signed URLs.** Private object access pattern. [Documentation](https://docs.aws.amazon.com/AmazonS3/latest/userguide/using-presigned-url.html)

**S14 - Strands structured outputs and human intervention.** Schema and pause/resume capabilities; neither proves factual correctness. [Structured output](https://strandsagents.com/docs/user-guide/concepts/agents/structured-output/) | [Human in the loop](https://strandsagents.com/docs/user-guide/concepts/agents/interventions/human-in-the-loop/)
