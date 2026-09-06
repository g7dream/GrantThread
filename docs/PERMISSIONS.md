# Permissions and disclosure contract

These are required invariants to verify, not a security certification. Test results belong in [EVALUATION.md](EVALUATION.md).

| Action or data | Owning grantee | Recipient funder | Other grantee |
| --- | --- | --- | --- |
| Internal grants, expenses, inbox, proposals and jobs | Allowed within organisation | Denied | Denied |
| Apply allocation or evidence proposal | Authorised grantee only | Denied | Denied |
| Prepare internal report draft | Authorised grantee only | Denied | Denied |
| Publish ready, current report | Explicit grantee action | Denied | Denied |
| Shared snapshot | Owning grantee | Named recipient only | Denied |
| Selected snapshot attachment | Owning grantee | Named recipient only | Denied |
| Original not selected for sharing | Owning grantee | Denied | Denied |
| Ask snapshot clarification | Denied | Named recipient | Denied |
| Answer snapshot clarification | Owning grantee | Denied | Denied |
| Resolve answered clarification | Denied | Named recipient | Denied |

Membership comes from verified server identity. An organisation, role, grant ID or document ID supplied by the browser or model never grants access by itself. Repeat the same authorization checks for metadata, document bytes, PDFs, manifests, jobs and clarification routes. Presigned upload/download paths require the same authorised scope.

Bright Path Lab owns Digital Belonging, Community Makers and Youth Skills. Harbour Collective owns Volunteer Support. Northstar Foundation funds Digital Belonging, Youth Skills and Volunteer Support. Riverbend Trust funds Community Makers. A Northstar reviewer must not receive Community Makers' private allocations, sources or drafts through a shared Digital Belonging report.

Sharing uses an explicit attachment manifest. Original invoices may reveal unrelated data even when the surrounding report is scoped correctly; review each attachment. Use an approved extract or redacted copy where needed. This release does not claim automatic redaction.

Audit events should identify the actor, action, affected record and timestamp. Published report versions remain fixed when later evidence changes. The next revision is a new draft and sharing action.

## Targeted access checks

Use an authenticated second grantee and funder. Alter IDs for internal grants, evidence metadata and bytes, jobs, proposals, report drafts, PDFs, manifests and clarification threads. Verify denials and inspect response bodies for leaked record details. Then test the allowed recipient snapshot and each selected attachment. Capture actor, endpoint, result and release revision without storing bearer tokens.

Never expose local demo identity selection on a public deployment. Cloud judge identities need actual Cognito users and server-managed memberships.
