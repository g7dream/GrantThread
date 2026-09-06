# Decisions

- 2026-09-06: Preserve the supplied P0 stack: React/TypeScript/Vite frontend; Python domain layer shared by local API, Lambda and worker; SAM-managed Cognito, DynamoDB, S3 and SQS. cPanel serves compiled public assets only. Sites hosting is not used because the requested deployment is cPanel/AWS.
- 2026-09-06: Empty workspace means no pre-existing application to preserve. Use MIT for original code and keep third-party licence notices.
- 2026-09-06: Provide a loopback-only local development server with server-issued demo sessions and SQLite persistence. Cloud authentication remains Cognito access tokens validated by API Gateway, with server-owned membership records. Local demo login is disabled in Lambda.
- 2026-09-06: Missing model access yields an explicit unavailable job, never a fake Strands trace. Deterministic financial and reporting functions remain available during outages.
- 2026-09-06: Store each small synthetic organisation aggregate with an optimistic version. This simplifies atomic financial updates in both SQLite and DynamoDB; impose a bounded aggregate size for the demonstration and document production partitioning limits.
- 2026-09-06: User selected Spaceship cPanel and authorised a public GitHub repository under g7dream. Use lowercase `/grantthread/`; the actual owned domain remains unknown. No repository or hosting publication has occurred because authenticated access is unavailable.
- 2026-09-06: Evidence batches validate all selected versions and commit once. Uploads and approvals invalidate stale input versions; model work resumes as a fresh, traceable job after authorised corrections. Published snapshots and source-object keys remain immutable.
- 2026-09-06: Cloud source downloads redirect to authorised S3 GET links valid for five minutes. This supports the documented 5 MB source limit without exceeding Lambda's base64 response ceiling.
