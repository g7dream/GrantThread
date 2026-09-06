# AWS deployment and operation

This template is a prepared deployment artifact. A successful local build does not establish a deployed API or Bedrock access. Deploy only after an AWS account, exact frontend URL and in-region tool-capable model are configured. The static interface belongs in an isolated Spaceship cPanel location; Lambda owns the API and worker.

## First-time setup

1. Sign in to an AWS account and configure a short-lived AWS CLI/SSO operator profile locally. Do not paste access keys into source, browser configuration or chat. Run `aws sts get-caller-identity` and confirm the account. Install AWS SAM CLI and Docker for a Linux-compatible build. Python 3.12 is the deployed runtime.
2. Pick one AWS region deliberately. Verify a **regional foundation model** supports Bedrock Converse tool use and is available to this account there. Run an actual small Converse tool-use request before selecting its ID. The template derives the exact permitted foundation-model ARN from the selected ID and stack region, rejects cross-region/inference-profile IDs, and provides no fallback. A model requiring an inference profile needs a separately reviewed region/IAM change.
3. Choose a dedicated HTTPS origin and the exact callback URL, including a subfolder if used. `FrontendOrigin` has no trailing slash or path. `CallbackUrl` must match the frontend `VITE_COGNITO_REDIRECT_URI` byte for byte. These are public values.
4. From the repository root, run `sam validate --lint --template-file infra/template.yaml`, `sam build --use-container --template-file infra/template.yaml`, then `sam deploy --guided`. Supply `FrontendOrigin`, `CallbackUrl`, `CognitoDomainPrefix`, `BedrockModelId`, `BudgetEmail` and `MonthlyBudgetUsd`. Review the CloudFormation change set before execution. Do not deploy into an existing unrelated application stack.
5. Read stack outputs. Set the frontend public API URL, region, Cognito domain/client ID, redirect URI and scopes `openid email profile grantthread/access`; rebuild the frontend before packaging. No client secret exists. Cognito uses code + PKCE. API Gateway requires the custom access-token scope; an ID token cannot satisfy it. Lambda additionally requires a server-managed subject membership and enforces all record scope.
6. Create the three synthetic judge accounts in the Cognito console. Complete their initial password challenge through managed login. Keep passwords in a private credential handoff. Account creation/invitations are deliberate operator actions; the script below sends no emails.
7. Use the installed project Python environment to seed and bind each **existing** Cognito account:

```powershell
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --seed
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email GRANTEE_EMAIL --identity brightpath
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email SECOND_GRANTEE_EMAIL --identity harbour
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email FUNDER_EMAIL --identity northstar
```

The script authenticates the operator with STS, resolves the user subject from the selected Cognito pool and conditionally writes `MEMBER#<subject>`. Users cannot assign their own role. Existing different memberships require the explicit `--replace-membership` flag. Operator permissions needed are `sts:GetCallerIdentity`, stack-specific `cloudformation:DescribeStacks`, pool-specific `cognito-idp:AdminGetUser`, table-specific `dynamodb:GetItem/PutItem` and bucket-specific `s3:PutObject` when seeding. Grant these separately from the application runtime roles.

## Release verification

From the deployed cPanel URL: managed login → read persisted seeded portfolio → add a permitted text document → inspect queued job → inspect genuine Strands tool events → refresh. Then test both grantees against altered private record IDs, and test the funder against unpublished drafts and unselected originals. A missing or failed model produces `unavailable`/`failed`; it never synthesizes tool events. Verify exact figures, stale approvals, export downloads and snapshot recipient boundaries before judge access.

Local compile/import and SDK schema checks do **not** prove this gate. Record a genuine deployed run ID, actual model ID, observed timestamps and screenshots in the evaluation evidence after it happens.

## Limits and cost controls

- API Lambda: 28 seconds, five concurrent invocations. HTTP API: ten requests/second, burst twenty.
- Worker: two global concurrent invocations; SQS batch one; 180-second application lease/deadline with a 195-second Lambda termination ceiling.
- Each job: eight authorised tool executions, ten agent model turns, 1,200 maximum output tokens per response, and 48,000 UTF-8 input bytes per turn including prompt/tool schemas. The model transport uses a five-second connect timeout, ten-second socket read timeout and one total transport attempt. Strands throttling retries are disabled. The pinned Bedrock adapter can repeat one request after a specific tool-result formatting validation error; this compatibility correction is also bounded. A run-owned cancellation signal remains set while any transport thread winds down.
- Queued crashes: visibility timeout 1,200 seconds; at most two job claims; delivery max three before DLQ. Completed jobs are idempotently ignored. A timed-out/stale lease cannot persist further derived changes. New evidence creates a fresh scoped job referencing its waiting predecessor; hidden model reasoning is not replayed.
- Daily application job count and one active job per actor are enforced in the API. Documents, CSV and aggregate size limits are enforced there too. Bedrock failures cannot write confirmed money, grant rules, permissions or published snapshots.
- Private S3 with TLS, block-public-access, explicit upload CORS and server-side encryption. DynamoDB point-in-time recovery; 14-day Lambda logs. Runtime roles cannot manage Cognito accounts or memberships; worker IAM cannot invoke unlisted model resources or send mail.
- The monthly budget sends actual-spend alerts at 80% and forecast alerts at 100%. **This is an account-wide alert, not an automatic hard spend cap.** Email delivery and budget updates can lag. Promotional credits do not guarantee zero cost. Inspect the AWS bill and model usage during the demo period.

To stop new model spend immediately, set the worker's reserved concurrency to zero using the `WorkerName` stack output (`aws lambda put-function-concurrency --function-name NAME --reserved-concurrent-executions 0`), then disable its SQS event-source mapping. API/ledger reads remain usable, but requests may queue. Inspect and intentionally discard synthetic queued jobs before resuming; do not blindly replay DLQ messages. Do not erase the DLQ before diagnosing a failed delivery.

## Reset, rollback and teardown

A cloud reset is operator-only: `python infra/manage_demo.py --stack STACK --region REGION --reset-synthetic --confirm-stack STACK`. It replaces the synthetic organisation aggregates and preserves memberships. Old private S3 objects remain; they are not linked by the reset workspace and require a deliberate later retention cleanup. Never use a reset against real records.

Before a release, save the previous frontend ZIP and public configuration, and capture the CloudFormation change set. Upload to an isolated staging directory and preserve the prior destination before switching. Roll back by restoring that frontend artifact and previous Lambda/SAM release; do not reset data as a rollback technique.

Keep the verified judge release accessible for the required judging period. After the owner approves shutdown, stop workers, preserve needed evidence/export records and run `sam delete --stack-name STACK --region REGION`. The template deliberately retains DynamoDB and S3; inspect their exact names and export any needed content before separately deleting those resources. Retained storage and backups may continue to incur cost. Cognito accounts, queues, API and functions are deleted with the stack, so teardown ends judge access.

## Verified SDK contracts

The installed dependency versions are pinned in `backend/requirements.txt`. The implementation uses the public `Agent`, `BedrockModel`, `@tool`, sequential executor, `invoke_async` and lifecycle hook APIs inspected in Strands 1.54.0. Proposal validation is explicit Pydantic validation inside the two candidate-saving tools. It does not add a hidden structured-output tool beyond the seven-tool allowlist.

Run the offline control checks with `python -m unittest discover -s backend/tests -p test_worker.py -v`. These use an explicitly scripted test provider through the real Strands dispatcher and temporary data; they are never exposed as product agent runs. CloudFormation validation was performed with `cfn-lint==1.56.0`, a development tool separate from the runtime requirements.

Primary references: [Strands hooks](https://strandsagents.com/docs/user-guide/concepts/agents/hooks/), [Bedrock provider API](https://strandsagents.com/docs/api/python/strands.models.bedrock/), [JWT authorisers and scope requirements](https://docs.aws.amazon.com/apigateway/latest/developerguide/http-api-jwt-authorizer.html), [Lambda and SQS](https://docs.aws.amazon.com/lambda/latest/dg/with-sqs.html).
