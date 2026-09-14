# Deployment to Spaceship cPanel and AWS

The confirmed frontend destination is **`https://timeillusion.com/grantthread/`**, an isolated folder hosted through Spaceship cPanel. Actual Cognito sign-in, normal reload, grantee financial display and XLSX download/readback pass. Final raw/gzip/Brotli hashes match the built files, and the canonical browser loads the current bundle after the cache repair. Hosted sharing with one selected attachment, funder sign-in and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. Preserve the existing Time Illusion website and use only its dedicated `grantthread` folder.

The application `grantthread-demo` in `eu-north-1` and budget `grantthread-demo-budget` in `us-east-1` reached CREATE_COMPLETE. A genuine regional Nova Lite Strands reconciliation and 49 cloud backend checks passed through administrative Lambda invocation with trusted gateway claims; public-browser proof is recorded separately and now includes the grantee sign-in/reload and XLSX download. Selected sharing, verified original-download bytes and the resolved hosted clarification pass. These bounded checks do not establish universal cross-role or JWT security coverage. The owner selected `CapacityMode=shared-demo` under the current quota of 10. Use UPDATE change sets for these existing stacks, after inspecting their state. [EVALUATION.md](EVALUATION.md) records exact proof and current blockers.

Source revision `3b4ceba8b83e0924c7a7eda425768d865d964101` is published at [g7dream/GrantThread](https://github.com/g7dream/GrantThread). Unauthenticated GitHub API checks independently verified public visibility, default branch `master`, README and MIT licence. Video, entrant details and submission are separate unfinished steps.

## Current operation and hardening

The USD 25 budget alerts at 80% actual and 100% forecast, excluding credits/refunds; its verified recipient remains private. The existing temporary root-console login was used for setup, without creating access keys. A non-root development operator is not yet established. Runtime uses Lambda execution roles.

The deployed SAM-generated worker role includes `AWSLambdaSQSQueueExecutionRole`. Its SQS receive/delete/read-attributes permissions use `Resource: *`, broader than the dedicated application queue. Before adding unrelated queues or broader workloads, replace that managed policy through reviewed infrastructure changes with explicit queue-scoped permissions and recheck logging/worker operation. This is a known hardening limit, not a claim of production least privilege. [AWS managed policy reference](https://docs.aws.amazon.com/aws-managed-policy/latest/reference/AWSLambdaSQSQueueExecutionRole.html)

App index and build-manifest requests passed 200/no-store checks without ETag/Last-Modified when older validators were supplied. That check did not cover every content encoding: a later `Accept-Encoding: br` request returned stale HTML referencing the previous JS bundle even though raw/gzip responses matched the new upload. Constant ZIP timestamps and an unchanged index byte size left LiteSpeed's compressed copy stale. The content-derived timestamp repair passes its regression test. Resaving the exact live index/manifest bytes with fresh modification times cleared the compressed cache: all 16 final encoding/cache checks pass, and the canonical browser loads the current JS. Inspect raw, gzip, Brotli and actual browser assets again after future releases. The API Gateway OPTIONS route with authorisation NONE and the Lambda pre-authentication 204 response repair are deployed. Actual grantee login/reload and XLSX readback now pass. The receipt-PDF and source-download fixes are deployed; PDF values, final-bundle original download and resolved funder acknowledgement are verified. Financial PDF/manifest checks preceded the final JS reload; shared PDF/manifest and original downloads were also verified afterwards.

## AWS stack

Complete [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md). Deploy the separate cost-alert stack **`grantthread-demo-budget` in `us-east-1` first**, using `infra/budget.yaml`. AWS reports `AWS::Budgets::Budget` unavailable in Stockholm, so it is not part of the regional application stack. Supply `BudgetName` (default `grantthread-demo-monthly`), the privately stored `BudgetEmail`, and `MonthlyBudgetUsd` (25 selected). Keep the email in an ignored local parameter file; do not pass the mixed application/budget parameter file unchanged to either stack.

For a new budget stack, with a private JSON list containing only its `ParameterKey`/`ParameterValue` entries:

```powershell
aws cloudformation create-change-set --stack-name grantthread-demo-budget --change-set-name BUDGET_REVIEW_NAME --change-set-type CREATE --template-body file://infra/budget.yaml --parameters file://PRIVATE_BUDGET_PARAMETERS_JSON --region us-east-1 --profile grantthread
aws cloudformation wait change-set-create-complete --stack-name grantthread-demo-budget --change-set-name BUDGET_REVIEW_NAME --region us-east-1 --profile grantthread
aws cloudformation describe-change-set --stack-name grantthread-demo-budget --change-set-name BUDGET_REVIEW_NAME --region us-east-1 --profile grantthread
```

Replace the private file and review-name placeholders. Review the budget change set and its private parameters before executing it:

```powershell
aws cloudformation execute-change-set --stack-name grantthread-demo-budget --change-set-name BUDGET_REVIEW_NAME --region us-east-1 --profile grantthread
aws cloudformation wait stack-create-complete --stack-name grantthread-demo-budget --region us-east-1 --profile grantthread
```

Verify completion before creating the application. If that stack already exists, inspect it and use an `UPDATE` change set and `stack-update-complete` waiter. The budget measures account-wide costs with credits and refunds excluded, alerts at 80% actual and 100% forecast, and is not a spend cap. Keep it active throughout the demo and any retained-resource cleanup.

The selected application build route works from Windows without requiring Docker or SAM CLI. It uses Linux CPython 3.12 x86_64 binary wheels, following [AWS's Python Lambda cross-platform package guidance](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-native-libraries). Run each command only after the previous one succeeds:

```powershell
$download = .\.venv\Scripts\python.exe scripts/build_lambda.py --download | ConvertFrom-Json
$release = .\.venv\Scripts\python.exe scripts/build_lambda.py --wheelhouse $download.wheelhouse | ConvertFrom-Json
if ($release.sha256 -ne $download.sha256) { throw 'Cached rebuild did not reproduce the downloaded build' }
```

`--download` fetches exactly pinned binary wheels from PyPI and builds the ZIP. Its JSON result includes `wheelhouse`; `--wheelhouse PATH` rebuilds from that cache with no network. Both modes automatically call the source allowlist staging helper and make no AWS requests. The result also identifies `zip`, `sha256`, `manifest` and `sourceTemplate`. Keep the returned build manifest and ZIP together. Inspect the target platform, wheel/file hashes and package size. The 14 September runtime passed real Lambda XLSX/PDF and Strands checks; rerun relevant smoke tests for a changed runtime artifact.

Staging copies only approved runtime modules and locked requirements into a content-addressed directory under `artifacts/sam-source/`. It excludes local `.data`, uploaded files, tests, credential files and Python caches. Rebuild after source or template changes. The original template deliberately points to an absent `UNSTAGED` location: do not replace that guard with `../backend`, because the normal SAM Python builder can collect local records from that working directory.

To prepare the selected CloudFormation deployment:

1. Upload the exact `$release.zip` into an authorised **private deployment bucket in `eu-north-1`**, with public access blocked and encryption enabled. Use an immutable content-addressed object key such as `lambda/<full ZIP SHA-256>/function.zip`. Verify the uploaded checksum; if that key already exists, verify identical content and reuse it without overwriting.
2. Make an ignored generated copy of `$release.sourceTemplate`, such as `artifacts/application-cloud.yaml`. Replace **both** `ApiFunction.Properties.CodeUri` and `WorkerFunction.Properties.CodeUri` with that exact `s3://BUCKET/KEY`. Assert that both point to the same verified ZIP and that no local `./backend` or `UNSTAGED` code URI remains. Preserve every other template property and the `Transform: AWS::Serverless-2016-10-31` declaration.
3. Check the generated template with `cfn-lint --template artifacts/application-cloud.yaml --regions eu-north-1`. Store only the five application parameters listed below in a separate ignored JSON parameter file; the budget recipient does not belong in this file.
4. Create a change set against the dedicated `grantthread-demo` stack. CloudFormation performs the [server-side SAM transform](https://docs.aws.amazon.com/AWSCloudFormation/latest/TemplateReference/transform-aws-serverless.html); no local SAM-translated template is claimed by the wheel builder.

For a new application stack, replace the file/name placeholders and use the established operator profile:

```powershell
$env:AWS_PROFILE = 'grantthread'
aws sts get-caller-identity --region eu-north-1
aws cloudformation create-change-set --stack-name grantthread-demo --change-set-name REVIEW_NAME --change-set-type CREATE --template-body file://artifacts/application-cloud.yaml --parameters file://PRIVATE_APPLICATION_PARAMETERS_JSON --capabilities CAPABILITY_IAM --region eu-north-1
aws cloudformation wait change-set-create-complete --stack-name grantthread-demo --change-set-name REVIEW_NAME --region eu-north-1
aws cloudformation describe-change-set --stack-name grantthread-demo --change-set-name REVIEW_NAME --region eu-north-1
aws cloudformation get-template --stack-name grantthread-demo --change-set-name REVIEW_NAME --template-stage Processed --region eu-north-1
```

Confirm the account, review resource changes and the processed template before execution, including scoped IAM, the exact private ZIP location, Cognito/CORS settings, SQS concurrency two and the absence of both function reservations in shared-demo. Creating the change set is not execution or runtime proof. Use `UPDATE` for an existing inspected application stack; do not target an unrelated stack or reuse a stale generated template after a failed build.

Only after that concrete change set has been reviewed, execute it and wait for stack completion:

```powershell
aws cloudformation execute-change-set --stack-name grantthread-demo --change-set-name REVIEW_NAME --region eu-north-1
aws cloudformation wait stack-create-complete --stack-name grantthread-demo --region eu-north-1
```

For an update use the corresponding `stack-update-complete` waiter. Then verify Lambda imports and the hosted workflow; neither the offline ZIP checks nor a successful stack transform establishes them.

SAM CLI with Docker remains an optional standard route. It still starts from the allowlisted stage and must not be mixed with a stale wheel-build artifact:

```powershell
$stage = .\.venv\Scripts\python.exe scripts/stage_sam.py | ConvertFrom-Json
sam validate --lint --template-file $stage.template
sam build --use-container --template-file $stage.template
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Review its change set before execution as well. This alternative requires SAM CLI and a working Linux container runtime; the selected wheel/CloudFormation route does not.

| SAM parameter | Supply |
| --- | --- |
| `FrontendOrigin` | `https://timeillusion.com` |
| `CallbackUrl` | `https://timeillusion.com/grantthread/` |
| `CognitoDomainPrefix` | Available lowercase login domain prefix |
| `BedrockModelId` | Tool-capable model actually verified in the chosen region |
| `CapacityMode` | `shared-demo` for the current small judging demo; default `reserved` otherwise |

`shared-demo` omits both Lambda reservations; it never sets them to zero. API Gateway uses best-effort throttle targets of five requests/second and burst five, and the SQS mapping retains `MaximumConcurrency=2`. The current account-wide concurrency quota of 10 bounds all concurrent functions in that region. It supplies no per-function guarantee: API traffic, workers and other functions share the pool, so API starvation or queued work is possible under load. Use this only for a small judging demo, and recheck capacity, cost exposure and isolation before changing the account quota or adding other workloads.

The default `reserved` mode preserves API concurrency five, worker concurrency two, and API throttle targets of ten requests/second and burst twenty. It requires at least 107 unreserved units before a fresh deployment allocates those reservations. The stack's `CapacityMode` output records the selected policy. The separate budget stack, authentication, scoped IAM, daily job limits and worker deadlines apply in both modes.

The template derives the exact regional foundation-model ARN from `BedrockModelId` and the deployment region/partition; there is no separate `BedrockModelArn` parameter. A playground response through geographic/global inference is insufficient: the worker requires verified direct regional Converse tool use. The IAM runtime grants are separate from the operator's deployment permissions.

Read stack outputs. Create the synthetic Bright Path, Harbour and Northstar Cognito users through the authorised account workflow. Do not publish passwords or send invitation emails without authorisation. Bind each existing account using `infra/manage_demo.py`; the script resolves the selected Cognito pool's real subject and sends no emails:

```powershell
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --seed
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email GRANTEE_EMAIL --identity brightpath
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email SECOND_GRANTEE_EMAIL --identity harbour
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email FUNDER_EMAIL --identity northstar
```

Replace uppercase placeholders. See [infra/README.md](../infra/README.md) for exact operator permissions, reset controls and model-job limits.

## Frontend public configuration

After the stack exists in the chosen account, save only its public outputs and prepare the frontend configuration offline:

```powershell
aws cloudformation describe-stacks --stack-name grantthread-demo --profile grantthread --region YOUR_REGION --query 'Stacks[0].Outputs' --output json | Set-Content -Encoding utf8 artifacts/stack-outputs.json
.\.venv\Scripts\python.exe scripts/configure_frontend.py --outputs artifacts/stack-outputs.json --site-url https://timeillusion.com/grantthread/
```

Replace `YOUR_REGION` with the verified application region. `configure_frontend.py` makes no network requests and writes `artifacts/frontend.env.production`; it refuses to overwrite an existing candidate unless `--overwrite` is explicit. Review that file, the account/stack selected above, and the callback/CORS values. The helper copies only supported public settings and checks `CallbackUrl` and `FrontendOrigin` when exported by the stack. Then copy the reviewed file into the untracked build configuration:

```powershell
Copy-Item -LiteralPath artifacts/frontend.env.production -Destination frontend/.env.production.local
```

The resulting public settings have this shape:

```dotenv
VITE_BASE_PATH=/grantthread/
VITE_API_URL=ACTUAL_STACK_API_URL_INCLUDING_API_PATH
VITE_COGNITO_DOMAIN=ACTUAL_STACK_COGNITO_DOMAIN
VITE_COGNITO_CLIENT_ID=ACTUAL_STACK_CLIENT_ID
VITE_COGNITO_REDIRECT_URI=https://timeillusion.com/grantthread/
```

Use access-token scopes `openid email profile grantthread/access`; the API authoriser requires the custom access scope. Check the final frontend auth implementation/configuration when packaging. Public configuration is embedded at build time, so changing it requires another build. Never add an AWS access key, client secret, model credential or password to a Vite variable.

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
```

Generate the ZIP from the compiled public assets:

```powershell
.\.venv\Scripts\python.exe scripts/package_cpanel.py --base /grantthread/ --site-url https://timeillusion.com/grantthread/
```

Cloud packaging fails if public settings are incomplete, the callback/base do not match, production metadata is missing, or HTML/JavaScript/CSS hashes disagree with the build. `grantthread-build.json` is build evidence, not runtime configuration; editing it alone does not connect the app. Private files, hidden paths, source maps and unexpected assets are rejected. Validation occurs before replacing the previous ZIP; identical inputs produce the same ZIP hash. Each file receives a deterministic SHA-256-derived DOS timestamp in the fixed past range 1980–2019. Equal-length changed HTML and manifests therefore change their archive modification time, while unchanged assets retain theirs; this avoids reusing one constant timestamp that left LiteSpeed compressed content stale. After extraction, independently verify raw, gzip and Brotli responses and the script loaded by the browser. Reproducible packaging alone does not establish cache freshness.

The script generates `.htaccess`, deployment instructions and licence notices inside `artifacts/GrantThread-cpanel.zip`, with a matching `.sha256` sidecar. Passing these offline checks does not establish working authentication, permissions or AI; complete the hosted verification below.

If only an interface preview is intended, explicitly request the separate artifact:

```powershell
.\.venv\Scripts\python.exe scripts/package_cpanel.py --preview --base /grantthread/ --site-url https://timeillusion.com/grantthread/
```

This writes `artifacts/GrantThread-preview.zip` and its checksum, clearly marked as interface-only. The current hosted release is cloud-configured, with verified grantee sign-in/reload and XLSX readback. Identify any package by its actual manifest/hash; do not infer configuration from an old filename. Do not upload this repository, `node_modules`, `.venv`, source staging directories or local `.data`.

## cPanel upload and path casing

1. Open the owned domain's cPanel file manager and verify the exact document root. Preserve an existing site's files and back up any existing target folder before changing it.
2. Use a dedicated lowercase `grantthread` directory under that document root. Upload/extract the compiled ZIP there so `index.html` sits directly inside `grantthread`, not an extra nested folder.
3. Confirm HTTPS and request `/grantthread/`, a direct app link and its assets. A refresh must return the application while existing files remain directly served.
4. Handle `/GrantThread/` and other accepted capital variants with a redirect at the parent/domain configuration to lowercase `/grantthread/`. A rule inside the lowercase folder alone cannot reliably catch a differently cased folder path on a case-sensitive host. Inspect any existing parent `.htaccess` before adding redirects, and preserve its unrelated rules.
5. Test that canonicalisation preserves query strings needed for Cognito callbacks, avoids redirect loops and lands on the exact registered callback URL. Register the canonical lowercase URL with Cognito.

Use only the confirmed dedicated destination. Changes to another domain or the parent website require a separately verified destination and matching Cognito/CORS configuration.

## Verify, roll back and stop

From the actual hosted URL, complete login, read persisted data, upload evidence, observe a genuine queued Strands result and refresh. Run the role-boundary, exact-value, export and clarification scenarios. Record G1-G5 in [EVALUATION.md](EVALUATION.md). The presence of an upload ZIP does not pass those gates.

Keep the prior frontend ZIP and public settings. For a failed release restore that artifact and the last verified backend release; do not reset ledger data as a rollback. Disable the worker's SQS event-source mapping to stop new queue invocations, following [infra/README.md](../infra/README.md); already running work remains subject to its deadline. In reserved mode, setting worker reserved concurrency to zero is an additional operator stop control. Budget alerts are not immediate shutdown controls.

After the judging obligation ends and shutdown is authorised, use the stack-specific teardown procedure in `infra/README.md`. The template retains the DynamoDB table and S3 bucket, so deleting the stack alone does not remove all stored data or storage charges. Inspect and export retained data before any separate deletion.

The `grantthread-demo-budget` stack is separate in `us-east-1`; application teardown does not delete it. Retain its alerts until remaining storage and charges have been reviewed, then remove it only as part of the authorised final cleanup.
