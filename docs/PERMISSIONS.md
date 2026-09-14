# Permissions and disclosure contract

These are required invariants to verify, not a security certification. Test results belong in [EVALUATION.md](EVALUATION.md).

## Public personal-demo scope

When `PublicDemoSignup=true`, a gateway-validated account without an explicit membership can create its own fictional three-grant copy. The server derives its Bright Path and Northstar scopes from the authenticated subject. The only selectable values are `grantee` and `funder`; the caller cannot name an organisation, adopt an invited identity or access another visitor's copy. Existing invited memberships retain their assigned scope and reject the demo-role header. A signup email resembling an organisation name grants no membership.

Personal-demo start and restore are authenticated owner actions available through either of that subject's demo views. They operate on the same owned scenario; this does not give the funder view general permission to edit financial entries. Start is explicit and idempotent. Restore requires the current version and exact confirmation, rejects active jobs, advances the generation and replaces IDs so stale operations cannot alter the fresh scenario. It preserves sign-in and agent history; another visitor and the invited demonstration remain unchanged. Restore is not permanent object deletion, and an already issued signed source URL can last until its five-minute expiry.

The frontend sends the bounded role header only after the server confirms demo access and only to authenticated API requests. New tokens and sign-out clear the preference; signed S3 requests receive neither it nor the app token. The personal funder still sees only deliberately shared snapshots and selected originals. Use fictional records only. See [PUBLIC_DEMO.md](PUBLIC_DEMO.md).

The new 280-test local suites and AWS signup/health/CORS settings are verified. Eighteen actual hosted-browser checks pass for one personal account: OAuth, copy creation, both roles, selected sharing/download, the resolved conversation and Restore with login/history preserved. Fifty-five separate administrative Lambda checks pass for two-visitor isolation, stale-record denial, active-job rejection and unchanged other-visitor/canonical records. Those administrative checks bypass OAuth, API Gateway, JWT signature validation and CORS; the browser journey supplies separate evidence for its tested routes. Accounts were confirmed administratively, so real email delivery and code confirmation remain unverified. The earlier invited-account evidence below is a separate result; see [EVALUATION.md](EVALUATION.md).

## Grantee and recipient permissions

| Action or data | Owning grantee | Recipient funder | Other grantee |
| --- | --- | --- | --- |
| Internal grants, expenses, inbox, proposals and jobs | Allowed within organisation | Denied | Denied |
| Apply allocation or evidence proposal | Authorised grantee only | Denied | Denied |
| Financial imports, original bytes, receipts and conversion history | Allowed within organisation | Denied | Denied |
| Create/review drafts, confirm entries or create linked adjustments | Authorised grantee only | Denied | Denied |
| Run bank extraction for an owned import | Authorised grantee only | Denied | Denied |
| Financial XLSX report, template mapping and template export | Authorised grantee only | Denied | Denied |
| Prepare internal report draft | Authorised grantee only | Denied | Denied |
| Publish ready, current report | Explicit grantee action | Denied | Denied |
| Shared snapshot | Owning grantee | Named recipient only | Denied |
| Selected snapshot attachment | Owning grantee | Named recipient only | Denied |
| Original not selected for sharing | Owning grantee | Denied | Denied |
| Ask snapshot clarification | Denied | Named recipient | Denied |
| Answer snapshot clarification | Owning grantee | Denied | Denied |
| Resolve answered clarification | Denied | Named recipient | Denied |

Membership or automatic personal-demo scope comes from verified server identity. An organisation, role, grant ID or document ID supplied by the browser or model never grants access by itself. Repeat the same authorization checks for metadata, document bytes, PDFs, manifests, jobs and clarification routes. Presigned upload/download paths require the same authorised scope.

Bright Path Lab owns Digital Belonging, Community Makers and Youth Skills. Harbour Collective owns Volunteer Support. Northstar Foundation funds Digital Belonging, Youth Skills and Volunteer Support. Riverbend Trust funds Community Makers. A Northstar reviewer must not receive Community Makers' private allocations, sources or drafts through a shared Digital Belonging report.

Sharing uses an explicit attachment manifest. Original invoices may reveal unrelated data even when the surrounding report is scoped correctly; review each attachment. Use an approved extract or redacted copy where needed. This release does not claim automatic redaction.

Financial-source downloads and workbook exports are private grantee routes. Uploading a ledger, statement or report template does not attach that original to a shared report or grant a funder access to internal receipts, conversions or source files. A later explicit evidence-sharing action has its own disclosure review. Runtime uploads and private working documents must remain outside public fixtures, repository history and frontend release packages; all shipped examples are fictional.

The bank model receives only the selected import's extracted statement pages. It cannot browse other files or organisations, confirm drafts, select an FX policy or publish reports. The authenticated actor and source versions are fixed when a job is created. A stale version or lost lease prevents a late worker from replacing current review data. Bank output is a preview, even when every source check passes.

Confirmation freezes each financial entry's conversion snapshot. A correction creates a new linked adjustment instead of editing the confirmed record. Source review and confirmation record the actor and time. An exact payment match associates a bank debit with an existing expense; it does not authorise a payment or send a banking instruction.

Audit events should identify the actor, action, affected record and timestamp. Published report versions remain fixed when later evidence changes. The next revision is a new draft and sharing action.

## Targeted access checks

Use an authenticated second grantee and funder. Alter IDs for internal grants, evidence metadata and bytes, financial imports and originals, receipts, entries, template mappings/exports, jobs, proposals, report drafts, PDFs, manifests and clarification threads. Verify denials and inspect response bodies for leaked record details. Then test the allowed recipient snapshot and each selected attachment. Capture actor, endpoint, result and release revision without storing bearer tokens.

Local demo identity selection is unrestricted among the fictional demo accounts. Opaque session tokens do not make those accounts suitable for sensitive documents. Never expose that unrestricted local identity selector on a public deployment, and do not upload sensitive financials to a public demo. The new public demo has a separate subject-scoped role selector; it cannot select those invited identities. The earlier invited synthetic cloud users and server-managed memberships remain configured. Nine scope checks and further financial access denials passed through administrative Lambda invocation with trusted gateway claims. This verifies the deployed application boundary under those claims, not API Gateway JWT signatures or a complete browser login. Separate actual public-browser verification now passes Cognito sign-in, normal reload, grantee data access and financial XLSX download after the CORS repair. Actual hosted funder login, the selected Youth Skills package and a source-linked question/answer also pass. The final-bundle selected original download and resolved clarification also pass; these bounded route checks are not exhaustive cross-role verification; this is not a claim of complete JWT security coverage.
