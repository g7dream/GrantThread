# AWS deployment and operation

The application and separate budget stacks are deployed as of 14 September 2026. A genuine regional Strands/Nova Lite reconciliation and 49 administrative-invoke cloud application checks passed; these trusted-claim tests do not verify JWT/OAuth/CORS/browser behavior. Final raw/gzip/Brotli hashes match the configured build, and the canonical browser loads the current bundle. Both CORS repairs are deployed and actual grantee sign-in/reload and financial XLSX readback pass; hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. The app index/build-manifest validator and later Brotli-cache repairs are verified separately. See [EVALUATION.md](../docs/EVALUATION.md) for exact evidence. For the existing grantthread-demo stack, inspect current state and use reviewed UPDATE change sets; the instructions below also document fresh setup.

## First-time setup

1. The intended account is verified through temporary CLI and Python SDK login. Prepare a short-lived AWS CLI/SSO development operator profile locally. Do not paste access keys into source, browser configuration or chat. Recheck `aws sts get-caller-identity` before proceeding. The selected build uses `scripts/build_lambda.py` and Linux Python 3.12 x86_64 wheels; Docker/SAM CLI are optional. Complete the account-plan, selected capacity-mode and regional readiness checks in [AWS_FIRST_STEPS.md](../docs/AWS_FIRST_STEPS.md); successful login or visible credits alone do not satisfy them.
2. Pick one AWS region deliberately. Verify a **regional foundation model** supports Bedrock Converse tool use and is available to this account there. Run an actual small Converse tool-use request before selecting its ID. The template derives the exact permitted foundation-model ARN from the selected ID and stack region, rejects cross-region/inference-profile IDs, and provides no fallback. A model requiring an inference profile needs a separately reviewed region/IAM change.
3. Deploy `infra/budget.yaml` as the separate `grantthread-demo-budget` CloudFormation stack in `us-east-1` before the application. Its parameters are `BudgetName` (default `grantthread-demo-monthly`), private `BudgetEmail` and `MonthlyBudgetUsd` (25 selected). `AWS::Budgets::Budget` is unavailable in Stockholm. Wait for budget-stack completion; filter the private parameter file to this stack's keys only. Then use the confirmed application HTTPS origin `https://timeillusion.com` and exact callback `https://timeillusion.com/grantthread/`. `FrontendOrigin` has no trailing slash or path. `CallbackUrl` must match `VITE_COGNITO_REDIRECT_URI` byte for byte. These site values are public.
4. Build the allowlisted runtime with the wheel commands below. Upload the exact ZIP to an immutable hash-addressed object in a private regional deployment bucket. In a generated copy of the returned source template, replace both API and worker `CodeUri` properties with that verified private S3 URI. Create and review a CloudFormation change set, including its server-side processed SAM template, before execution. Its parameters are exactly `FrontendOrigin`, `CallbackUrl`, `CognitoDomainPrefix`, `BedrockModelId` and `CapacityMode`. The owner selected `shared-demo` for the current quota of 10; the default remains `reserved`. See [DEPLOYMENT.md](../docs/DEPLOYMENT.md) for the command sequence. Do not deploy into an unrelated stack or use a stale artifact after a failed build.
5. Read the stack's public outputs and use `scripts/configure_frontend.py --outputs artifacts/stack-outputs.json --site-url https://timeillusion.com/grantthread/` to prepare `artifacts/frontend.env.production`. Review it, copy it into `frontend/.env.production.local`, then rebuild. The helper makes no AWS calls and refuses an existing output unless `--overwrite` is explicit. No client secret exists. Cognito uses code + PKCE with scopes `openid email profile grantthread/access`. API Gateway requires the custom access-token scope; an ID token cannot satisfy it. Lambda additionally requires a server-managed subject membership and enforces all record scope. The complete output-export/build sequence is in [DEPLOYMENT.md](../docs/DEPLOYMENT.md).
6. Create the three synthetic judge accounts in the Cognito console. Complete their initial password challenge through managed login. Keep passwords in a private credential handoff. Account creation/invitations are deliberate operator actions; the script below sends no emails.
7. Use the installed project Python environment to seed and bind each **existing** Cognito account:

```powershell
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --seed
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email GRANTEE_EMAIL --identity brightpath
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email SECOND_GRANTEE_EMAIL --identity harbour
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email FUNDER_EMAIL --identity northstar
```

The script authenticates the operator with STS, resolves the user subject from the selected Cognito pool and conditionally writes `MEMBER#<subject>`. Users cannot assign their own role. Existing different memberships require the explicit `--replace-membership` flag. Operator permissions needed are `sts:GetCallerIdentity`, stack-specific `cloudformation:DescribeStacks`, pool-specific `cognito-idp:AdminGetUser`, table-specific `dynamodb:GetItem/PutItem` and bucket-specific `s3:PutObject` when seeding. Grant these separately from the application runtime roles.

From the repository root, run each preparation command only after the preceding one succeeds. The first build downloads pinned binary wheels; the second verifies a network-free rebuild from the returned cache:

```powershell
$download = .\.venv\Scripts\python.exe scripts/build_lambda.py --download | ConvertFrom-Json
$release = .\.venv\Scripts\python.exe scripts/build_lambda.py --wheelhouse $download.wheelhouse | ConvertFrom-Json
if ($release.sha256 -ne $download.sha256) { throw 'Cached rebuild did not reproduce the downloaded build' }
```

This uses [AWS's Linux-wheel package approach](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-native-libraries), targeting the deployed CPython version and x86_64 architecture. `--download` fetches wheels from PyPI; `--wheelhouse PATH` is entirely offline. Both call the source staging allowlist automatically and return `zip`, `sha256`, `manifest`, `wheelhouse` and `sourceTemplate`. Review wheel/file hashes, target metadata and package size; native runtime imports and application execution remain separate checks.

Staging is offline and copies only explicitly approved runtime modules plus locked requirements into `artifacts/sam-source/<content-hash>/`. Local records, uploads, test fixtures and credentials are excluded. The original template deliberately has absent `UNSTAGED` source paths: **never change `CodeUri` back to the working `backend` directory**, where `.data` may contain real records. Rebuild after code or template changes. Existing stages are reused only when their contents match their manifest; tampered or incomplete stages fail validation.

CloudFormation performs the SAM transform after both code URIs have been replaced with the verified private S3 object. The wheel builder does not produce or verify a locally transformed SAM template. Inspect the change set and processed template before executing it; stack completion still requires a real Lambda import and hosted workflow test.

The optional standard SAM/Docker route is:

```powershell
$stage = .\.venv\Scripts\python.exe scripts/stage_sam.py | ConvertFrom-Json
sam validate --lint --template-file $stage.template
sam build --use-container --template-file $stage.template
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

This alternative requires SAM CLI and a working Linux container runtime. Review its change set before execution; never deploy an old `.aws-sam/build/template.yaml` after a failed build.

After the frontend build, the cloud package command is:

```powershell
.\.venv\Scripts\python.exe scripts/package_cpanel.py --base /grantthread/ --site-url https://timeillusion.com/grantthread/
```

It requires complete public cloud settings, the exact callback/base, production metadata and matching asset hashes before creating `artifacts/GrantThread-cpanel.zip`. Use `--preview` explicitly to create the separate `GrantThread-preview.zip` without claiming a connected backend. Both packages contain compiled public assets and licence/deployment notices only. A configured package still needs live verification.

## Release verification

From the deployed cPanel URL: managed login → read persisted seeded portfolio → add a permitted text document → inspect queued job → inspect genuine Strands tool events → refresh. Then test both grantees against altered private record IDs, and test the funder against unpublished drafts and unselected originals. A missing or failed model produces `unavailable`/`failed`; it never synthesizes tool events. Verify exact figures, stale approvals, export downloads and snapshot recipient boundaries before judge access.

Local compile/import and SDK schema checks do **not** prove this gate. Record a genuine deployed run ID, actual model ID, observed timestamps and screenshots in the evaluation evidence after it happens.

## Limits and cost controls

- `CapacityMode=reserved` (default): API reserved concurrency five, worker reserved concurrency two. A fresh deployment needs at least 107 unreserved account units before allocation. HTTP API throttle targets: ten requests/second, burst twenty.
- `CapacityMode=shared-demo`: both reservation properties are omitted, not set to zero. The current account-wide quota of 10 bounds regional concurrent execution without requiring a quota increase. API, workers and unrelated functions share this pool with no per-function guarantee; under load the API can starve and jobs can wait. HTTP API throttle targets drop to five requests/second, burst five; these are best-effort request controls, not exact concurrency or cost caps. Use only for a small judging demo. Recheck this mode before increasing account quotas or adding workloads; the account quota supplies its aggregate bound.
- Both modes: SQS mapping maximum concurrency two and batch one; 180-second application lease/deadline with a 195-second Lambda termination ceiling. The stack's `CapacityMode` output identifies the selected policy. Authentication, IAM, budget and daily job controls do not vary by mode.
- Each job: eight authorised tool executions, ten agent model turns, 1,200 maximum output tokens per response, and 48,000 UTF-8 input bytes per turn including prompt/tool schemas. The model transport uses a five-second connect timeout, ten-second socket read timeout and one total transport attempt. Strands throttling retries are disabled. The pinned Bedrock adapter can repeat one request after a specific tool-result formatting validation error; this compatibility correction is also bounded. A run-owned cancellation signal remains set while any transport thread winds down.
- Queued crashes: visibility timeout 1,200 seconds; at most two job claims; delivery max three before DLQ. Completed jobs are idempotently ignored. A timed-out/stale lease cannot persist further derived changes. New evidence creates a fresh scoped job referencing its waiting predecessor; hidden model reasoning is not replayed.
- Daily application job count and one active job per actor are enforced in the API. Documents, CSV and aggregate size limits are enforced there too. Bedrock failures cannot write confirmed money, grant rules, permissions or published snapshots.
- Private S3 with TLS, block-public-access, explicit upload/download CORS for the configured frontend origin and server-side encryption. DynamoDB point-in-time recovery; 14-day Lambda logs. Runtime roles cannot manage Cognito accounts or memberships; worker IAM cannot invoke unlisted model resources or send mail.
- The separate `grantthread-demo-budget` stack in `us-east-1` sends actual-cost alerts at 80% and forecast alerts at 100%. Its `IncludeCredit=false` and `IncludeRefund=false` measure account-wide costs before credits/refunds offset them. **This is an alert, not an automatic hard spend cap.** Email delivery and budget updates can lag. Promotional credits do not guarantee zero cost. Inspect the AWS bill and model usage during the demo period.

To stop new queue invocations in either mode, disable the worker's SQS event-source mapping. Already running model work can continue until its deadline. In reserved mode, additionally set the worker's reserved concurrency to zero using the `WorkerName` stack output (`aws lambda put-function-concurrency --function-name NAME --reserved-concurrent-executions 0`). Shared-demo does not depend on being able to create a reservation in the small account. API/ledger operations may still run, subject to shared capacity, while new jobs wait. Inspect and intentionally discard synthetic queued jobs before resuming; do not blindly replay DLQ messages. Do not erase the DLQ before diagnosing a failed delivery.

## Known operator and IAM hardening

Setup currently uses the existing temporary root-console login; no access keys or non-root development operator were created. Runtime uses Lambda execution roles. The SAM-generated worker role includes `AWSLambdaSQSQueueExecutionRole`, whose SQS receive/delete/read-attribute permissions use `Resource: *`. Before broader use or unrelated queues, replace it through reviewed infrastructure changes with explicit queue-scoped permissions and verify logging and queue processing. Application scope tests do not establish complete infrastructure least privilege. See [deployment notes](../docs/DEPLOYMENT.md#current-operation-and-hardening).

## Reset, rollback and teardown

A cloud reset is operator-only: `python infra/manage_demo.py --stack STACK --region REGION --reset-synthetic --confirm-stack STACK`. It replaces the synthetic organisation aggregates and preserves memberships. Old private S3 objects remain; they are not linked by the reset workspace and require a deliberate later retention cleanup. Never use a reset against real records.

Before a release, save the previous frontend ZIP and public configuration, and capture the CloudFormation change set. Upload to an isolated staging directory and preserve the prior destination before switching. Roll back by restoring that frontend artifact and previous Lambda/SAM release; do not reset data as a rollback technique.

Keep the verified judge release accessible for the required judging period. After the owner approves shutdown, stop workers, preserve needed evidence/export records and run `sam delete --stack-name STACK --region REGION`. The template deliberately retains DynamoDB and S3; inspect their exact names and export any needed content before separately deleting those resources. Retained storage and backups may continue to incur cost. Cognito accounts, queues, API and functions are deleted with the stack, so teardown ends judge access.

The separate budget stack in `us-east-1` remains after application deletion. Keep its alerts until retained resources and charges have been reviewed, then include that exact stack in the authorised final cleanup.

## Verified SDK contracts

The installed dependency versions are pinned in `backend/requirements.txt`. The implementation uses the public `Agent`, `BedrockModel`, `@tool`, sequential executor, `invoke_async` and lifecycle hook APIs inspected in Strands 1.54.0. Proposal validation is explicit Pydantic validation inside the two candidate-saving tools. It does not add a hidden structured-output tool beyond the seven-tool allowlist.

Run the offline control checks with `python -m unittest discover -s backend/tests -p test_worker.py -v`. These use an explicitly scripted test provider through the real Strands dispatcher and temporary data; they are never exposed as product agent runs. CloudFormation validation was performed with `cfn-lint==1.56.0`, a development tool separate from the runtime requirements.

Primary references: [Strands hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/), [Bedrock provider API](https://strandsagents.com/docs/api/python/strands.models.bedrock/), [JWT authorisers and scope requirements](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), [Lambda and SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html).
