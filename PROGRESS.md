# GrantThread task ledger

Local P0 candidate implemented on **6 September 2026** from [the supplied plan](docs/BUILD_PLAN.md). Integrated in dependency order, with independent frontend, infrastructure and documentation work in parallel. Cloud gates remain separate from local completion.

| ID | Task | Status | Evidence / remaining gate |
| --- | --- | --- | --- |
| D1.1 | Workspace, architecture and synthetic fixture | Local complete | Empty repository inspected; structure, licence, fixture and decisions recorded. AWS account/domain still need configuration. |
| D1.2 | Authentication, scoped persistence, files and queue | Implemented; cloud gate open | Local sessions/SQLite work; Cognito, DynamoDB, S3 and SQS SAM definitions validated. No live AWS connection. |
| D1.3 | Exact allocations and CSV preview | Complete locally | EUR 200 invalid split rejected; verified totals EUR 1,700 / 3,100 / 400; browser preview distinguishes original and proposed amounts. |
| D1.4 | Portfolio, evidence inbox and Strands integration | Implemented; genuine run open | API-backed UI verified; real SDK dispatch tested with labelled offline providers. Missing Bedrock is shown honestly. |
| D2.1 | Bounded text evidence, versions and citations | Complete locally | Parser limits, immutable originals, replacement lineage and failed-upload recovery checked. Browser proof upload/source drawer passed. |
| D2.2 | Scoped agent tools and event reconciliation | Implemented; live gate open | Seven tools, typed proposals, traces, input/lease fencing, limits and resume tested. Real Bedrock decisions need access. |
| D2.3 | Decisions and versioned batch approval | Complete locally | Exact correction, atomic evidence batches, stale refresh, review scope, history and concurrent approval passed. |
| D2.4 | Two layouts, readiness and updated inputs | Complete locally; live resume open | Missing proof blocks sharing; approval changes 5/6 to 6/6; stale drafts require regeneration. Evidence/approval schedules configured rechecks. |
| D3.1 | Report composition, PDF and manifest | Complete locally | Both layouts rendered and inspected; browser PDF saved to disk with EUR 1,700. |
| D3.2 | Explicit sharing, snapshots and funder projection | Complete locally; cloud gate open | Only two selected originals shared. Other tenant/grant/private-source attempts denied in tests. |
| D3.3 | Funder and clarification lifecycle | Complete locally | Browser question linked to source, grantee response and funder acknowledgement preserved in history. |
| D3.4 | Demo identities, reset and failure states | Complete locally; judge accounts open | Server-authenticated local switching/reset available. Model outage leaves ledger usable. Cognito judge accounts need setup. |
| D4.1 | Targeted gates and synthetic benchmark | Local complete; release gates open | 28 checks and 3 isolated service journeys passed. G1 and three deployed journeys remain unverified. Human timing not measured. |
| D4.2 | Desktop/narrow-screen and keyboard usability | Complete locally | Desktop and 390x844 inspected; overflow fixed (page 375px <= viewport 390px), hidden nav excluded, Escape restores focus. Native screen reader not run. |
| D4.3 | Setup, licence, architecture and submission drafts | Complete as drafts | README, diagram, permissions, AWS/cPanel guides, Devpost, three Builder posts and 4:30 video script prepared. No publications claimed. |
| D4.4 | Release package and final demonstration | Package prepared; release open | cPanel ZIP and source candidate prepared. Real video, judge access and public GitHub push await external setup. |

## Verified artifacts

- artifacts/GrantThread-cpanel.zip: public compiled assets for lowercase /grantthread/, licences, .htaccess, parent case-redirect example and deployment notes. **Supply AWS public configuration and rebuild before live use.**
- artifacts/GrantThread-source.zip: committed source candidate for the authorised public repository, without local data, credentials or installed dependencies.
- artifacts/digital-belonging-sample.pdf, artifacts/community-makers-sample.pdf and matching manifests.
- docs/BENCHMARK_RESULTS.json: three local synthetic service journeys; no human baseline, timing or product-saving claims.
- docs/EVALUATION.md: exact verification scope and open gates.

## Next concrete tasks: external setup

1. **AWS:** identify/sign in to the intended account, configure a short-lived operator profile, choose one EU region and verify a regional tool-capable model. Follow [AWS first steps](docs/AWS_FIRST_STEPS.md). No AWS CLI/profile/model access is currently available here.
2. **Domain:** identify the actual domain managed in Spaceship. The provider's spaceship.com address is not the deployment domain. Use a dedicated /grantthread/ folder, back up the destination and install the parent redirect for mixed-case paths.
3. **GitHub:** sign in under g7dream. Public publication is authorised, but Git Credential Manager has no usable sign-in. scripts/github_repository.py inspects access; --create creates the authorised public repository after sign-in. Do not paste tokens into chat or source.
4. Deploy SAM, bind synthetic Cognito users, inject public frontend configuration, rebuild/upload the ZIP, then run G1 and deployed scope/journey checks.
5. Record the genuine demonstration, verify judge access, review the concrete submission package, and publish only specifically authorised outputs. Video/posts/competition entry are not yet published.

No input is needed for routine code/packaging choices. Account sign-in and the actual domain are the current external dependencies.
