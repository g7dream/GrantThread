# Deployment to Spaceship cPanel and AWS

The prepared route is an isolated **`/grantthread/`** folder on an owned HTTPS domain hosted through Spaceship, backed by the AWS SAM stack. `spaceship.com/GrantThread` names the provider's domain; it is not an established hosting destination owned by this project. Substitute the domain shown in the account's actual hosting configuration. Domain, SSL and account access remain to be verified.

Public GitHub publication under `g7dream` has been authorised. The proposed repository name is `GrantThread`; verify the resulting repository URL before including it in submission material. Repository authorisation does not establish authentication or mean that the repository has been created.

## AWS stack

Complete [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md). From the repository root, use the established operator profile:

```powershell
$env:AWS_PROFILE = 'grantthread'
sam validate --lint --template-file infra/template.yaml
sam build --use-container --template-file infra/template.yaml
sam deploy --guided
```

These are deployment instructions, not execution evidence. The build requires Docker and compatible tooling. The deploy action creates billed account resources and IAM roles; inspect the generated change set for the dedicated `grantthread-demo` stack and the selected region.

| SAM parameter | Supply |
| --- | --- |
| `FrontendOrigin` | Actual HTTPS origin without path/trailing slash, such as `https://owned-domain.example` |
| `CallbackUrl` | Exact app URL, such as `https://owned-domain.example/grantthread/` |
| `CognitoDomainPrefix` | Available lowercase login domain prefix |
| `BedrockModelId` | Tool-capable model actually verified in the chosen region |
| `BudgetEmail` | Operational email address, supplied privately |
| `MonthlyBudgetUsd` | Deliberately chosen amount; template default 25 |

The example domain is a placeholder, not a live site. The template derives the exact regional foundation-model ARN from `BedrockModelId` and the deployment region/partition; there is no separate `BedrockModelArn` parameter. The IAM runtime grants are separate from the operator's deployment permissions.

Read stack outputs. Create the synthetic Bright Path, Harbour and Northstar Cognito users through the authorised account workflow. Do not publish passwords or send invitation emails without authorisation. Bind each existing account using `infra/manage_demo.py`; the script resolves the selected Cognito pool's real subject and sends no emails:

```powershell
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --seed
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email GRANTEE_EMAIL --identity brightpath
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email SECOND_GRANTEE_EMAIL --identity harbour
.\.venv\Scripts\python.exe infra/manage_demo.py --stack grantthread-demo --region YOUR_REGION --email FUNDER_EMAIL --identity northstar
```

Replace uppercase placeholders. See [infra/README.md](../infra/README.md) for exact operator permissions, reset controls and model-job limits.

## Frontend public configuration

Build with the actual output values in `frontend/.env.production.local` (untracked):

```dotenv
VITE_BASE_PATH=/grantthread/
VITE_API_URL=ACTUAL_STACK_API_URL_INCLUDING_API_PATH
VITE_COGNITO_DOMAIN=ACTUAL_STACK_COGNITO_DOMAIN
VITE_COGNITO_CLIENT_ID=ACTUAL_STACK_CLIENT_ID
VITE_COGNITO_REDIRECT_URI=https://owned-domain.example/grantthread/
```

Use access-token scopes `openid email profile grantthread/access`; the API authoriser requires the custom access scope. Check the final frontend auth implementation/configuration when packaging. Public configuration is embedded at build time, so changing it requires another build. Never add an AWS access key, client secret, model credential or password to a Vite variable.

```powershell
npm.cmd --prefix frontend ci
npm.cmd --prefix frontend run build
```

Generate the ZIP from the compiled public assets:

```powershell
.\.venv\Scripts\python.exe scripts/package_cpanel.py --base /grantthread/
```

The script packages `frontend/dist` and generates the `.htaccess` SPA fallback **inside the ZIP**, together with deployment instructions, the original MIT licence and dependency notices. It does not require `.htaccess` to exist in `frontend/dist`. Output is `artifacts/GrantThread-cpanel.zip`; verify the current build against `artifacts/GrantThread-cpanel.sha256` rather than an old file-size value. Its AWS configuration is missing, so it is an **unconfigured preview asset package**, not a working hosted release. Rebuild and repackage after supplying the actual API/Cognito settings. Do not upload this repository, `node_modules`, `.venv` or local `.data`.

## cPanel upload and path casing

1. Open the owned domain's cPanel file manager and verify the exact document root. Preserve an existing site's files and back up any existing target folder before changing it.
2. Use a dedicated lowercase `grantthread` directory under that document root. Upload/extract the compiled ZIP there so `index.html` sits directly inside `grantthread`, not an extra nested folder.
3. Confirm HTTPS and request `/grantthread/`, a direct app link and its assets. A refresh must return the application while existing files remain directly served.
4. Handle `/GrantThread/` and other accepted capital variants with a redirect at the parent/domain configuration to lowercase `/grantthread/`. A rule inside the lowercase folder alone cannot reliably catch a differently cased folder path on a case-sensitive host. Inspect any existing parent `.htaccess` before adding redirects, and preserve its unrelated rules.
5. Test that canonicalisation preserves query strings needed for Cognito callbacks, avoids redirect loops and lands on the exact registered callback URL. Register the canonical lowercase URL with Cognito.

Do not upload while destination/domain ownership is unresolved. This is a concrete missing configuration value, not an invitation to replace another site.

## Verify, roll back and stop

From the actual hosted URL, complete login, read persisted data, upload evidence, observe a genuine queued Strands result and refresh. Run the role-boundary, exact-value, export and clarification scenarios. Record G1-G5 in [EVALUATION.md](EVALUATION.md). The presence of an upload ZIP does not pass those gates.

Keep the prior frontend ZIP and public settings. For a failed release restore that artifact and the last verified backend release; do not reset ledger data as a rollback. Stop new model work by setting the worker's reserved concurrency to zero and disabling its event-source mapping, following [infra/README.md](../infra/README.md). Budget alerts are not immediate shutdown controls.

After the judging obligation ends and shutdown is authorised, use the stack-specific teardown procedure in `infra/README.md`. The template retains the DynamoDB table and S3 bucket, so deleting the stack alone does not remove all stored data or storage charges. Inspect and export retained data before any separate deletion.
