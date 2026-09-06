# GrantThread — Many grants. One clear thread.

**Submission draft, updated 6 September 2026.** The local workflow has been verified. AWS deployment, a genuine Bedrock agent run, the public repository and the final video remain unfinished. Fill the fields marked PENDING before submitting; user validation and administrator time-savings measurement remain pending.

## Tagline

Record shared grant work once, review the exceptions, and share a report with its evidence.

## Inspiration

A grant administrator may need to explain the same activity to several funders, with different report layouts and evidence requirements. The difficult part is keeping the underlying facts consistent while knowing which details can be shared. GrantThread explores one connected workflow from incoming records to a targeted funder conversation.

The primary user is a professional grant administrator. The funder receives a deliberately shared package, while the grantee keeps control of its internal records. The proposed track is Professional Agents.

## What it does

The synthetic scenario follows Bright Path Lab across three grants. Five expenses total EUR 5,200. A proposed venue split exceeds the original expense by EUR 200, and a printing expense lacks its configured payment proof. The reviewer sees these issues, inspects sources, corrects the split and adds the missing proof. Two report layouts reuse confirmed facts. An explicit manifest determines which report version and attachments the funder can review, then a clarification thread records the question and response.

Those figures are synthetic test inputs whose corrected results were verified locally, not real financial records or impact metrics. A single workshop supports two grants and remains one unique activity across the organisation.

## How it is built

The project uses a React/TypeScript interface and a Python domain layer. Local mode uses SQLite. The AWS deployment design uses Cognito, API Gateway, Lambda, DynamoDB, private S3, SQS, Strands and Bedrock; static frontend assets are packaged for Spaceship cPanel.

The Strands integration exposes scoped tools for reading evidence, exact calculations, proposed links and report preparation. Its installed SDK dispatch was exercised with controlled test inputs; a genuine Bedrock run is still pending. The model has no tool for applying canonical allocations or publishing a report. Separate authorised actions validate versions and confirm consequential changes. Factual report content comes from confirmed structured records and deterministic templates.

**PENDING before publication:** insert actual deployed services, region/model ID, completed job ID and visible tool-event evidence. Do not claim AWS deployment or a genuine agent run solely because the integration code exists.

## Design decisions and challenges

An invoice amount, a grant allocation and proof of payment are different facts. Treating them as interchangeable would hide the very questions the administrator needs to resolve. Likewise, a report snapshot and the grantee's internal workspace have different audiences. The design makes allocation review and attachment selection explicit.

A citation points to a source version and page. It does not guarantee that the source supports an interpretation. Missing values remain missing, and uploaded instructions do not grant the agent authority.

## What we can demonstrate

The local browser journey completed CSV preview/import, source inspection, the EUR 500 + EUR 500 venue correction, printing-proof upload and evidence approval. Digital Belonging's EUR 1,700 report moved from 5 of 6 configured requirements to a ready version at 6 of 6. The browser downloaded its PDF. Two selected original attachments were shared, the authenticated local Northstar identity saw one package, and a source-linked question went through grantee response and funder resolution.

The P0 workflow baseline passed 28 backend/worker tests, Python compilation and dependency checks, CloudFormation lint and the TypeScript/Vite build. The later response-calculator addition brings the current suite to 39 tests; see `docs/EVALUATION.md` for that separate scope. Both PDF layouts were rendered and visually inspected. Desktop and 390-pixel narrow-screen checks included a corrected overflow issue and mobile navigation focus behavior. No actual screen-reader session was run.

Three isolated service-layer journeys also reproduced the expected totals, both report formats and a resolved clarification. Their execution timings exclude browser use, network, model inference and human review; they establish no administrator time savings. No manual baseline or participant study exists. User validation is pending. The model correctly remained unavailable in these local runs, with no simulated success events.

The cPanel ZIP has been generated but needs actual AWS API/Cognito configuration and a rebuild before it can be a live release. These observations are local evidence; they do not pass the deployed agent gate. Full scope and limitations are recorded in `docs/EVALUATION.md`.

## What's next

Test with grant administrators and funder reviewers, examine permissioned real workflows, and measure repeated entry and review effort. Explore additional funding models only after confirming their actual requirements. OCR, banking, payments, external filing, cash forecasting and automatic eligibility decisions are outside this demonstration.

## Required fields to finish

| Field | Value |
| --- | --- |
| Repository | PENDING GitHub authentication and verified public URL under `g7dream`; public publication authorised but not performed |
| Live URL or functioning test build route | Local setup verified; PENDING hosted AWS/cPanel release and judge route |
| Video | PENDING public URL and measured duration |
| AWS Builder ID | PENDING enter privately in submission form |
| Architecture | `docs/ARCHITECTURE.md`; export a readable diagram for the submission |
| Testing instructions | PENDING hosted identity instructions; local setup in `docs/SETUP.md` |
| Licence and dependency notices | Verify root licence and final dependency notice inventory |
| Build dates and contributors | PENDING confirm final history and contributors |
| AI coding assistance | Codex used during implementation |
| Prior work and support disclosure | PENDING contributor review; do not infer absence |
| Builder post URLs | PENDING; drafts are not published posts |

Review [RULES_CHECK.md](RULES_CHECK.md) before submitting. Remove editorial notes and unresolved placeholders from public copy; disclose any remaining limitations plainly.
