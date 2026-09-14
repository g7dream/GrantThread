# Public editable demo

The application update with `PublicDemoSignup=true` completed on 14 September 2026. The current 280 local tests pass (190 backend, including 21 focused public-demo tests; 52 scripts; 38 frontend API/auth), plus the production build. The hosted `index-C8T0tDcQ.js` frontend and all 16 encoding/cache checks pass; native signup-page navigation and exact-origin role-header CORS are verified.

All 18 actual browser checks also pass: OAuth with an administratively confirmed fictional account, explicit copy creation, venue correction, report preparation and selected-source sharing/download, both roles, a resolved question and Restore from Funder. Restore preserves login and AI history, removes reports/conversations and returns the original venue decision with fresh IDs; normal reload retains that state. Evidence: ignored `artifacts/public-demo-browser-verification.json`. The automatic browser review stopped at its budget after six successful tools and two safely rejected proposals; it created no report or proposal. The report shared in the walkthrough was manually prepared from confirmed facts. Real signup email delivery and code confirmation remain unverified.

Another 55 cloud checks passed through administrative Lambda invocation: two independent demo copies, repeated start, role boundaries, selected sharing and a resolved question, refusal to restore an active job, fresh-generation restoration, stale record rejection and unchanged canonical/other-visitor aggregates. They used administrator-created fictional accounts with email delivery suppressed and no membership records. This proves the deployed backend path, not actual self-signup email delivery, OAuth or browser interactions. The automatically triggered reconciliation failed under model throttling after four successful tool calls; restoration retained that job history. These results are saved under ignored `artifacts/public-demo-cloud-smoke/`. See [EVALUATION.md](EVALUATION.md) for separately recorded browser verification; actual email-code delivery remains a distinct acceptance check.

## Create an account and start

1. Open `https://timeillusion.com/grantthread/` and choose **Create demo account**.
2. Register an email address and a GrantThread password on the secure Cognito page. An AWS account is not needed. A Gmail address can be used as an ordinary email address; Google federation is not configured.
3. Enter the verification code sent to that address. The configured password policy requires at least 14 characters, including uppercase, lowercase, a number and a symbol.
4. Return to GrantThread and choose **Create my editable demo**. This explicit action creates your fictional starting records; merely reading the session does not create or reset data.

Your copy contains Bright Path Lab's three grants, five expenses, nine fictional source documents, a workshop and a proposed venue allocation requiring review. The **Grantee** and **Funder** controls show both sides of your own demonstration. The funder view represents your copy's Northstar Foundation and sees only reports explicitly shared with it. It does not expose another visitor's data, the invited demonstration accounts or the Riverbend grant's private records. Harbour is not cloned into this flow.

Existing invited accounts retain their server-managed organisation and role. They do not receive public-demo switching or restoration controls. Signing up with an address that resembles an organisation name does not grant access to that organisation.

## A short recording sequence

1. Sign into your personal demo and show the portfolio's three grants.
2. Open **Decisions** and review the venue proposal. Correct the proposed split to EUR 500 for Digital Belonging and EUR 500 for Community Makers, then confirm it. The EUR 1,000 invoice cannot support the original EUR 1,200 proposal.
3. Prepare the **Youth Skills** report. Review its EUR 400 insurance allocation and select the insurance invoice as the attachment to share. Confirm the original-document disclosure and publish the report to Northstar.
4. Switch to **Funder**, open that shared report and download the selected original. Ask a short question, optionally citing its source.
5. Switch to **Grantee** and answer. Switch back to **Funder** and acknowledge the answer. The published snapshot remains distinct from private working records.
6. To show international financial reporting, use fictional values in **Financials**: record a receipt basis of 1 RON = 0.20 EUR, then review a RON 100 draft using that receipt. Its converted value should be EUR 20 before confirmation. Export the financial workbook after reviewing the entries.
7. If showing **Run review**, wait for its recorded result. Missing evidence or a tool-budget stop can correctly leave the run waiting for input. Do not describe a simulated estimate or deterministic report calculation as a model execution.

Use fictional uploads. Response-time estimates use labelled simulated histories; no response from a real funder is predicted or guaranteed.

## Restore for another take

Choose **Restore demo**, review the explanation and select **Restore starting demo**. The app reads the latest workspace version before submitting the confirmation. It replaces your current grants, expenses, imports, evidence references, reports and conversations with a fresh fictional scenario. Another visitor's copy and the invited accounts are unaffected. You remain signed in and can continue with either demo role.

Download anything you want to keep first. A queued or running agent job blocks restoration until it finishes. If another tab changes the workspace during confirmation, refresh the restore dialog and review again. Restoration advances the workspace generation and creates new fixture IDs and source keys, so stale confirmations and requests already in progress cannot write into the new scenario.

Agent run history remains to preserve the daily per-actor limit. Restoration cannot reset that allowance. Private S3 objects are not permanently deleted by this action; replaced uploads lose their workspace references, while an already issued source-download link can remain valid until its five-minute expiry. Permanent deletion is an operator lifecycle task, not the Restore button.

## Operator configuration

`infra/template.yaml` defines `PublicDemoSignup` as a string parameter with allowed values `true` and `false`, default `false`. It jointly configures Cognito self-signup and the API's `GRANTTHREAD_PUBLIC_DEMO` flag. Native Cognito signup verifies email before confirmation. The custom `grantthread/access` access-token scope, JWT authoriser and existing membership validation remain required. No browser endpoint writes membership records, and no new IAM permissions are required for public-demo provisioning.

Deploy the updated runtime and template together using the build, immutable private ZIP and change-set process in [DEPLOYMENT.md](DEPLOYMENT.md). Include a sixth application parameter in addition to the existing five:

```json
{"ParameterKey":"PublicDemoSignup","ParameterValue":"true"}
```

For the existing application stack, this is the exact CloudFormation parameter syntax. Replace `REVIEWED_PACKAGED_TEMPLATE.yaml` with the generated template whose two CodeUri values reference the reviewed immutable Lambda ZIP. The command prepares an UPDATE change set; it does not execute it:

```powershell
aws cloudformation create-change-set --stack-name grantthread-demo --change-set-name public-demo-review --change-set-type UPDATE --template-body file://REVIEWED_PACKAGED_TEMPLATE.yaml --parameters ParameterKey=FrontendOrigin,UsePreviousValue=true ParameterKey=CallbackUrl,UsePreviousValue=true ParameterKey=CognitoDomainPrefix,UsePreviousValue=true ParameterKey=BedrockModelId,UsePreviousValue=true ParameterKey=CapacityMode,UsePreviousValue=true ParameterKey=PublicDemoSignup,ParameterValue=true --capabilities CAPABILITY_IAM --region eu-north-1 --profile grantthread
```

Inspect the account, change set and processed template before execution. Keep the selected `shared-demo` capacity, exact-origin CORS and the separate budget stack. Deploy the matching compiled frontend to the dedicated cPanel directory, then verify the actual served assets across content encodings. No AWS secret belongs in frontend configuration.

The app advertises the flag through public `GET /api/health` as `publicDemoSignup`. Setting the parameter back to `false` disables self-signup and automatic demo access for accounts without an explicit membership; it preserves their stored records. Existing invited memberships continue to work. This is an operational switch, not a data-deletion action.

Public signup increases the number of actors who can use the application. The existing 30-run daily limit is per actor. Lambda account concurrency and the USD 25 alert budget are not a global spending cap. Review admission, retention and account-wide cost controls before treating this small judging demo as a production service.

## API and acceptance checks

| Request | Contract |
| --- | --- |
| `GET /api/session` | Returns `user`, `mode` and, for an automatic demo account, `demo: {available, initialized, version, roles}`. Read-only. |
| `POST /api/demo/start` | Empty JSON object. Creates only missing personal fixture data, then returns the session shape. Repeating it preserves edits. |
| `POST /api/demo/reset` | `{"version": CURRENT_INTEGER, "confirm": "RESTORE DEMO"}`. Returns the session shape after conditional restoration. |
| `x-grantthread-demo-role` | Optional `grantee` or `funder` for automatic demo accounts only. The server derives both scopes from the validated subject. Existing members reject this header. |

The one-account OAuth/start/edit/share/question/Restore/reload browser sequence passed on 14 September. Separate administrative cloud checks verify two-account isolation, unchanged other copies, old-record denial and active-job restore rejection. Complete the remaining real email-code signup check with an actual inbox; test accounts so far were confirmed administratively with email suppressed. For additional confidence, optionally repeat isolation using a second browser account, recheck existing invited access and rehearse the recording. These extra checks are not prerequisites to using Restore or submitting.

Record this new hosted evidence separately from administrative Lambda invocation and from the earlier invited-user walkthrough. Do not collect or publish users' passwords, verification codes, access tokens or signed source URLs in test artifacts.
