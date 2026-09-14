# AWS first steps for GrantThread

The account owner handles signup, identity verification, payment details and terms in AWS directly. This guide prepares one account connection; it does not assert that an account, budget or model already works. No AWS key belongs in chat, GitHub or the frontend ZIP.

## 1. Establish the account and a cost threshold

Sign in to the [AWS console](https://console.aws.amazon.com/) or use its account-creation path. Complete the account's checks and enable MFA for the root account. Use an ordinary operator identity for development; do not create root access keys. An AWS Builder ID is a separate submission identity, not a substitute for an AWS account.

In Billing and Cost Management, create a monthly cost budget with an email address you check. The prepared SAM template defaults to USD 25 per month and alerts at 80% actual spend and 100% forecast spend; select an amount appropriate to your account before deployment. Budget alerts can arrive after usage has accrued and do not impose a hard cap. [AWS Budgets documentation](https://docs.aws.amazon.com/cost-management/latest/userguide/budgets-managing-costs.html)

Keep a record of the selected account, region and operator profile locally. Do not put payment or recovery information in this repository.

The current setup has an unresolved account choice: the CLI connection and the earlier GrantThread account were different. Select the intended account and check that account's credit balance before deploying. This guide does not choose an account or upgrade its plan.

Free account plans expose only selected services/features and do not accept additional promotional credits. Their access ends when credits are depleted or the plan expires. Check that the selected plan permits the required Lambda, API Gateway, Cognito, S3, DynamoDB, SQS, CloudWatch, Budgets and Bedrock features; do not assume the signup credit display proves deployment eligibility. [AWS account plans](https://docs.aws.amazon.com/awsaccountbilling/latest/aboutv2/free-tier-plans.html)

## 2. Connect Windows with temporary credentials

Install the Windows AWS CLI v2 package and reopen PowerShell. Verify `aws --version`. Install AWS SAM CLI for deploying this repository; Linux-compatible builds use Docker with the SAM `--use-container` option. [AWS CLI installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html), [SAM installation](https://docs.aws.amazon.com/serverless-application-model/latest/developerguide/install-sam-cli.html)

If the account already uses IAM Identity Center, configure its assigned operator role:

```powershell
aws configure sso --profile grantthread
aws sso login --profile grantthread
aws sts get-caller-identity --profile grantthread
```

The wizard needs the access portal/start URL, SSO region, account and assigned role. The SSO region is not necessarily the application's region. Confirm that the returned account is the intended one. [AWS CLI SSO setup](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sso.html)

For an account using console credentials rather than existing Identity Center, AWS CLI 2.32.0+ supports `aws login --profile grantthread` with temporary credentials. Use an authorised non-root console identity; the identity needs `SignInLocalDevelopmentAccess` in addition to permissions for the work. Follow the official instructions, including its credential-process compatibility route if an SDK cannot consume the login profile. [AWS CLI console sign-in](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-sign-in.html)

Do not enable AWS Organizations just to make an SSO wizard succeed without reviewing the account consequence: AWS currently states that creating an organisation on a free-tier account upgrades it to a paid plan and expires its free-tier credits. An account-only Identity Center instance also does not provide the same AWS account permission assignments as an organisation instance. Use the existing login route or have the owner review that decision. [Identity Center setup](https://docs.aws.amazon.com/singlesignon/latest/userguide/enable-identity-center.html)

Before the first stack deployment, inspect the chosen region's Lambda headroom:

```powershell
aws lambda get-account-settings --profile grantthread --region YOUR_REGION
```

The template reserves five concurrent API invocations and two worker invocations. AWS must also retain 100 unreserved units, so a new installation needs `AccountLimit.UnreservedConcurrentExecutions` of at least **107** before allocating these seven reservations. New accounts may have reduced quotas; do not assume the published default applies. If insufficient, resolve the quota with AWS before deploying rather than silently removing the application's concurrency caps. These commands are read-only but still require the intended account selection. [Lambda quotas](https://docs.aws.amazon.com/lambda/latest/dg/gettingstarted-limits.html), [reserved concurrency](https://docs.aws.amazon.com/lambda/latest/dg/configuration-concurrency.html)

The template currently leaves `UserPoolTier` unspecified, so a newly created Cognito pool uses AWS's **Essentials** default. Include that plan in the cost review; do not assume the older Lite defaults. [Cognito feature plans](https://docs.aws.amazon.com/cognito/latest/developerguide/cognito-sign-in-feature-plans.html)

## 3. Choose and verify one EU model region

Start by inspecting the account's Bedrock catalogue in one EU region, for example `eu-west-1` or `eu-central-1`. These are candidate regions, not a claim that any particular model is available there. Select a model only after confirming in-region availability, Converse tool-use support, account access and pricing. Record its exact regional model ID. The SAM template derives the matching foundation-model ARN from that ID and the deployment region/partition. It does not accept an inference-profile ARN or a geographic/global model prefix as a substitute.

Third-party model activation can require Marketplace permissions, a valid payment method and provider terms. Anthropic access has an additional first-use form for the standard Bedrock route. A one-time setup success may not settle every subscription prerequisite; repeat the verification after activation. [Bedrock model access](https://docs.aws.amazon.com/bedrock/latest/userguide/model-access.html)

Cross-region inference can route model processing to other regions. GrantThread has no automatic fallback to it; if the desired model requires that route, stop and make the region/model decision explicitly. [Bedrock cross-region inference](https://docs.aws.amazon.com/bedrock/latest/userguide/cross-region-inference.html)

With the intended profile and region selected, a read-only catalogue inspection is:

```powershell
aws bedrock list-foundation-models --profile grantthread --region eu-west-1 --query 'modelSummaries[].{Name:modelName,Id:modelId,Streaming:responseStreamingSupported}' --output table
```

Replace the candidate region with the one actually chosen. Catalogue listing does not prove inference permissions or tool use. Complete one small genuine tool-use request through the configured GrantThread agent, inspect its job events and record the result. Review account/provider terms before the first chargeable invocation.

A successful playground response through an EU/global inference profile does not satisfy the current regional-only worker contract. Validate the exact regional model ID intended for the template with a small Converse tool-use request first, then verify a real GrantThread job after deployment. Keep account permissions, model selection and actual execution evidence separate.

## 4. Hand off only non-secret configuration

The deployment needs the established operator profile name, selected region and verified model ID; the frontend's actual owned HTTPS domain and `/grantthread/` URL; and an operational budget email. The model ARN is derived automatically. Passwords and credentials stay in the AWS login flow or private account storage.

Next use [DEPLOYMENT.md](DEPLOYMENT.md). Once the chosen account is verified and its quota, access and model prerequisites are satisfied, routine stack configuration can proceed against the prepared files without asking the owner to make implementation choices. Account selection, terms, billing identity and initial login remain owner actions.

Local preparation can continue while the account decision is paused. Run `scripts/stage_sam.py` and build only the template path it returns; the original template's absent `UNSTAGED` paths prevent accidental packaging of private `backend/.data`. After deployment, `scripts/configure_frontend.py` prepares a reviewable public environment file from saved stack outputs. Cloud cPanel packaging requires complete settings and verified build hashes; `--preview` deliberately produces a separate interface-only ZIP. The commands and required order are in [DEPLOYMENT.md](DEPLOYMENT.md).
