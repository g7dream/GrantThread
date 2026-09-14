# Deployment to Spaceship cPanel and AWS

The confirmed frontend destination is **`https://timeillusion.com/grantthread/`**, an isolated folder hosted through Spaceship cPanel. Its interface has loaded publicly, but the AWS backend and secure sign-in are not connected. Preserve the existing Time Illusion website and use only its dedicated `grantthread` folder.

AWS deployment is paused until the owner selects the intended account. A successful CLI login does not settle that decision or establish that its credits belong to this project. Follow the account, quota and regional-model checks in [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md) before any cloud deployment.

Public GitHub publication under `g7dream` has been authorised. The proposed repository name is `GrantThread`; verify the resulting repository URL before including it in submission material. Repository authorisation does not establish authentication or mean that the repository has been created.

## AWS stack

Complete [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md). From the repository root, stage the runtime source locally first. Run each command only after the previous one succeeds:

```powershell
$stage = .\.venv\Scripts\python.exe scripts/stage_sam.py | ConvertFrom-Json
sam validate --lint --template-file $stage.template
sam build --use-container --template-file $stage.template
```

The staging command makes no AWS requests. It copies only approved runtime modules and locked requirements into a content-addressed directory under `artifacts/sam-source/`. It excludes local `.data`, uploaded files, tests, credential files and Python caches. Restage after every source change. The original template deliberately points to an absent `UNSTAGED` location: do not replace that guard with `../backend`, because the normal SAM Python builder can collect local records from that working directory.

These are preparation instructions, not deployment evidence. The Linux-compatible build requires AWS SAM CLI and Docker. Once the account and configuration are settled, use the established operator profile and the **built** template:

```powershell
$env:AWS_PROFILE = 'grantthread'
aws sts get-caller-identity
sam deploy --guided --template-file .aws-sam/build/template.yaml
```

Confirm that the returned account is the chosen one. The deploy action creates billed account resources and IAM roles; review the generated change set for the dedicated `grantthread-demo` stack and selected region before execution. Do not deploy an old `.aws-sam/build/template.yaml` after a failed build.

| SAM parameter | Supply |
| --- | --- |
| `FrontendOrigin` | `https://timeillusion.com` |
| `CallbackUrl` | `https://timeillusion.com/grantthread/` |
| `CognitoDomainPrefix` | Available lowercase login domain prefix |
| `BedrockModelId` | Tool-capable model actually verified in the chosen region |
| `BudgetEmail` | Operational email address, supplied privately |
| `MonthlyBudgetUsd` | Deliberately chosen amount; template default 25 |

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

Cloud packaging fails if public settings are incomplete, the callback/base do not match, production metadata is missing, or HTML/JavaScript/CSS hashes disagree with the build. `grantthread-build.json` is build evidence, not runtime configuration; editing it alone does not connect the app. Private files, hidden paths, source maps and unexpected assets are rejected. Validation occurs before replacing the previous ZIP; identical inputs produce the same ZIP hash.

The script generates `.htaccess`, deployment instructions and licence notices inside `artifacts/GrantThread-cpanel.zip`, with a matching `.sha256` sidecar. Passing these offline checks does not establish working authentication, permissions or AI; complete the hosted verification below.

If only an interface preview is intended, explicitly request the separate artifact:

```powershell
.\.venv\Scripts\python.exe scripts/package_cpanel.py --preview --base /grantthread/ --site-url https://timeillusion.com/grantthread/
```

This writes `artifacts/GrantThread-preview.zip` and its checksum, clearly marked as a preview. With the present missing AWS settings, it supports interface inspection only. The older `GrantThread-cpanel.zip` created before these guards remains a legacy unconfigured artifact; its filename does not make it a working release. Do not upload this repository, `node_modules`, `.venv`, source staging directories or local `.data`.

## cPanel upload and path casing

1. Open the owned domain's cPanel file manager and verify the exact document root. Preserve an existing site's files and back up any existing target folder before changing it.
2. Use a dedicated lowercase `grantthread` directory under that document root. Upload/extract the compiled ZIP there so `index.html` sits directly inside `grantthread`, not an extra nested folder.
3. Confirm HTTPS and request `/grantthread/`, a direct app link and its assets. A refresh must return the application while existing files remain directly served.
4. Handle `/GrantThread/` and other accepted capital variants with a redirect at the parent/domain configuration to lowercase `/grantthread/`. A rule inside the lowercase folder alone cannot reliably catch a differently cased folder path on a case-sensitive host. Inspect any existing parent `.htaccess` before adding redirects, and preserve its unrelated rules.
5. Test that canonicalisation preserves query strings needed for Cognito callbacks, avoids redirect loops and lands on the exact registered callback URL. Register the canonical lowercase URL with Cognito.

Use only the confirmed dedicated destination. Changes to another domain or the parent website require a separately verified destination and matching Cognito/CORS configuration.

## Verify, roll back and stop

From the actual hosted URL, complete login, read persisted data, upload evidence, observe a genuine queued Strands result and refresh. Run the role-boundary, exact-value, export and clarification scenarios. Record G1-G5 in [EVALUATION.md](EVALUATION.md). The presence of an upload ZIP does not pass those gates.

Keep the prior frontend ZIP and public settings. For a failed release restore that artifact and the last verified backend release; do not reset ledger data as a rollback. Stop new model work by setting the worker's reserved concurrency to zero and disabling its event-source mapping, following [infra/README.md](../infra/README.md). Budget alerts are not immediate shutdown controls.

After the judging obligation ends and shutdown is authorised, use the stack-specific teardown procedure in `infra/README.md`. The template retains the DynamoDB table and S3 bucket, so deleting the stack alone does not remove all stored data or storage charges. Inspect and export retained data before any separate deletion.
