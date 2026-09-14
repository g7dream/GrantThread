# AWS first steps for GrantThread

The account owner handles signup, identity verification, payment details and terms in AWS directly. On 14 September, STS verified a temporary login to the intended account and read-only checks confirmed an active FREE plan. Subsequently, the regional application and separate budget stacks reached CREATE_COMPLETE, and both direct Converse and genuine Strands reconciliation passed. The latter correctly stopped at waiting_input for missing evidence and human allocation review. Hosted grantee sign-in/reload and financial XLSX readback now pass after CORS repairs. Hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, selected original download and resolved funder clarification pass; see [EVALUATION.md](EVALUATION.md). The steps below remain a setup reference for new environments; inspect existing stacks before an update. No AWS key belongs in chat, GitHub or the frontend ZIP.

## 1. Establish the account and a cost threshold

Sign in to the [AWS console](https://console.aws.amazon.com/) or use its account-creation path. Complete the account's checks and enable MFA for the root account. Use an ordinary operator identity for development; do not create root access keys. An AWS Builder ID is a separate submission identity, not a substitute for an AWS account.

The owner has supplied the budget alert email. It is saved only in ignored `artifacts/aws-deployment-private.parameters.json`, together with `MonthlyBudgetUsd=25` and the existing public site parameters. Deploy `infra/budget.yaml` as a separate `grantthread-demo-budget` stack in `us-east-1` before the regional application; AWS reports `AWS::Budgets::Budget` unavailable in Stockholm. Its parameters are `BudgetName` (default `grantthread-demo-monthly`), private `BudgetEmail` and `MonthlyBudgetUsd`. Filter the private values into the appropriate stack's parameter file. The budget alerts at 80% actual costs and 100% forecast costs, excluding credits and refunds so they cannot hide usage. The `grantthread-demo-budget` stack is now CREATE_COMPLETE in `us-east-1`; its USD 25 threshold, alert percentages, excluded credits/refunds and private recipient were verified. Budget alerts can arrive after usage has accrued and do not impose a hard cap. [AWS Budgets documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)

Keep a record of the selected account, region and operator profile locally. Do not put payment or recovery information in this repository.

The earlier account mismatch is resolved: profile `grantthread` now has a verified temporary root console login to the intended account. Prepare the ordinary development operator before ongoing deployment work; the budget recipient is already configured privately. The earlier checks and rejected quota request created no resources or support case; the later authorised deployment created the application and budget stacks. No plan upgrade occurred. No non-root operator has yet been configured; runtime services use Lambda IAM roles. A paid-plan requirement has not been established.

Free account plans expose only selected services/features and do not accept additional promotional credits. Their access ends when credits are depleted or the plan expires. Check that the selected plan permits the required Lambda, API Gateway, Cognito, S3, DynamoDB, SQS, CloudWatch, Budgets and Bedrock features; do not assume the signup credit display proves deployment eligibility. [AWS account plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)

## 2. Connect Windows with temporary credentials

Install the Windows AWS CLI v2 package and reopen PowerShell. Verify `aws --version`. The selected build uses the project Python environment and `scripts/build_lambda.py`: `--download` fetches pinned Linux wheels, then `--wheelhouse PATH` rebuilds offline. CloudFormation performs the server-side SAM transform after private S3 code packaging; Docker and SAM CLI are optional for this route. The standard alternative uses SAM CLI with Docker's `--use-container` build. See [DEPLOYMENT.md](DEPLOYMENT.md), [AWS CLI installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) and [SAM installation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html).

If the account already uses IAM Identity Center, configure its assigned operator role:

```powershell
aws configure sso --profile grantthread
aws sso login --profile grantthread
aws sts get-caller-identity --profile grantthread --region eu-north-1
```

The wizard needs the access portal/start URL, SSO region, account and assigned role. The SSO region is not necessarily the application's region. Confirm that the returned account is the intended one. [AWS CLI SSO setup](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)

For the temporary console-login profile used in this setup, specify `--region eu-north-1` on application and STS commands: region-sensitive login behavior was observed. Keep budget service calls explicitly in `us-east-1`. This is a note about this console-login setup, not a claim that ordinary SSO profiles require one particular application region.

For an account using console credentials rather than existing Identity Center, AWS CLI 2.32.0+ supports `aws login --profile grantthread` with temporary credentials. Use an authorised non-root console identity; the identity needs `SignInLocalDevelopmentAccess` in addition to permissions for the work. Follow the official instructions, including its credential-process compatibility route if an SDK cannot consume the login profile. [AWS CLI console sign-in](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)

If the local Python SDK reports a missing `awscrt` dependency when using this login profile, install the optional CRT extra in the activated local virtual environment, matching the repository's locked botocore version:

```powershell
python -m pip install "botocore[crt]==1.43.89"
```

The local fix installed `awscrt==0.36.0`; a subsequent boto3 STS check independently verified the intended account, and `pip check` passed. This is local login tooling, not a dependency to add to Lambda runtime requirements. Lambda uses its execution role rather than this console login profile.

Do not enable AWS Organizations just to make an SSO wizard succeed without reviewing the account consequence: AWS currently states that creating an organisation on a free-tier account upgrades it to a paid plan and expires its free-tier credits. An account-only Identity Center instance also does not provide the same AWS account permission assignments as an organisation instance. Use the existing login route or have the owner review that decision. [Identity Center setup](https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html)

Before the first stack deployment, inspect the chosen region's Lambda headroom:

```powershell
aws lambda get-account-settings --profile grantthread --region YOUR_REGION
```

The default `CapacityMode=reserved` reserves five concurrent API invocations and two worker invocations. AWS must also retain 100 unreserved units, so a fresh installation in that mode needs `AccountLimit.UnreservedConcurrentExecutions` of at least **107** before allocating these seven reservations. New accounts may have reduced quotas; do not assume the published default applies. [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)

The pre-deployment 14 September check in `eu-north-1` returned `ConcurrentExecutions=10`, `UnreservedConcurrentExecutions=10` and `FunctionCount=0`. The zero function count is historical; the application functions are now deployed. The owner selected the explicit `CapacityMode=shared-demo` route to use this current quota without an increase. It omits both Lambda reservation properties rather than setting them to zero, retains SQS mapping `MaximumConcurrency=2`, and lowers HTTP API throttle targets to rate five/burst five. The quota of 10 bounds total regional account concurrency, but grants no per-function capacity: API and worker traffic can starve each other or wait under load. API throttles are best-effort and do not impose an exact concurrency or spending cap. Use only for a small judging demo; recheck capacity and cost controls before changing account quotas or adding workloads. The stack exports `CapacityMode` for verification.

The earlier automated quota request for 107 was rejected because the API required a value greater than its default quota of 1000. No quota changed and no support case was opened; the private support draft remains unsent. A quota increase is not a prerequisite for shared-demo. The selected Linux-wheel runtime has since executed real S3/XLSX/PDF and Strands checks in Lambda; the browser path remains a separate gate.

The template currently leaves `UserPoolTier` unspecified, so a newly created Cognito pool uses AWS's **Essentials** default. Include that plan in the cost review; do not assume the older Lite defaults. [Cognito feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html)

## 3. Choose and verify one EU model region

Nova Lite (`amazon.nova-lite-v1:0`) lists `ON_DEMAND` in Stockholm (`eu-north-1`), and a genuine direct regional Converse roundtrip passed: the model requested the expected fictional tool, accepted its supplied test result and ended its turn. `artifacts/verify-regional-bedrock.json` records the evidence. This direct test verifies regional model access and tool use. A separate genuine GrantThread Strands job is now recorded in [EVALUATION.md](EVALUATION.md); it does not establish the still-pending full hosted browser workflow. The SAM template derives the matching foundation-model ARN from that exact ID and the deployment region/partition. It does not accept an inference-profile ARN or a geographic/global model prefix as a substitute.

Third-party model activation can require Marketplace permissions, a valid payment method and provider terms. Anthropic access has an additional first-use form for the standard Bedrock route. A one-time setup success may not settle every subscription prerequisite; repeat the verification after activation. [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

Cross-region inference can route model processing to other regions. GrantThread has no automatic fallback to it; if the desired model requires that route, stop and make the region/model decision explicitly. [Bedrock cross-region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)

With the intended profile and region selected, a read-only catalogue inspection is:

```powershell
aws bedrock list-foundation-models --profile grantthread --region eu-west-1 --query 'modelSummaries[].{Name:modelName,Id:modelId,Streaming:responseStreamingSupported}' --output table
```

Replace the candidate region with the one actually chosen. Catalogue listing does not prove inference permissions or tool use. Complete one small genuine tool-use request through the configured GrantThread agent, inspect its job events and record the result. Review account/provider terms before the first chargeable invocation.

A successful playground response through an EU/global inference profile does not satisfy the current regional-only worker contract. The direct regional tool roundtrip is now verified for the selected Nova Lite ID; the separate genuine GrantThread job is also verified, while hosted browser checks remain open. Keep account permissions, model selection and actual application execution evidence separate.

## 4. Hand off only non-secret configuration

The regional application takes only `FrontendOrigin`, `CallbackUrl`, `CognitoDomainPrefix`, `BedrockModelId` and `CapacityMode`. The model ARN is derived automatically. The operational budget email already stored in the ignored private parameters belongs only to the separate `us-east-1` budget stack. Keep that email out of public outputs and frontend configuration. Passwords and credentials stay in the AWS login flow or private account storage.

Use [DEPLOYMENT.md](DEPLOYMENT.md) for updates to the existing application/budget stacks. The deployed backend, genuine Strands job and administrative-invoke financial/scope checks are verified. CORS repairs and actual grantee sign-in/reload/XLSX download are verified. Hosted receipt-PDF values, selected original download and resolved clarification pass. Repeated judge journeys remain open. Non-root development-operator setup remains hardening work; interactive authentication, terms or billing changes still belong to the owner.

Local preparation can continue while deployment prerequisites are resolved. `scripts/build_lambda.py` invokes the source allowlist stage automatically; the optional Docker route also starts from `scripts/stage_sam.py`. The original template's absent `UNSTAGED` paths prevent accidental packaging of private `backend/.data`. After deployment, `scripts/configure_frontend.py` prepares a reviewable public environment file from saved stack outputs. Cloud cPanel packaging requires complete settings and verified build hashes; `--preview` deliberately produces a separate interface-only ZIP. The commands and required order are in [DEPLOYMENT.md](DEPLOYMENT.md).
