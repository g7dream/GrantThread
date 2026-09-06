# Local setup on Windows

Use this local route to inspect the synthetic workflow before connecting an AWS account. It does not require hosting access. The backend command below starts a local stdlib HTTP server; this is not the public authentication path.

## Prerequisites

Install Python 3.12 and a supported Node.js release with npm. Run these commands from the repository root in PowerShell. Use `py -3.12` where Windows' Python launcher is installed; if it is not, substitute your Python 3.12 executable.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend ci
```

Use the committed frontend lockfile with `npm ci`. Do not substitute unpinned dependency upgrades while reproducing a release. If PowerShell blocks `npm.ps1`, `npm.cmd` avoids that script policy issue.

## Start the application

In terminal one, from the repository root:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m grantthread.local_server
```

In terminal two, from the repository root:

```powershell
npm.cmd --prefix frontend run dev
```

Open `http://127.0.0.1:5173`. Choose the synthetic Bright Path, Harbour or Northstar identity. The backend listens at `http://127.0.0.1:8000`; Vite proxies `/api`. Local data defaults to `backend/.data` when started with the documented working directory. Keep that directory out of version control.

Use [MANUAL_SCENARIOS.md](MANUAL_SCENARIOS.md) for the principal workflow and `fixtures/README.md` for the source files. Missing model configuration must appear as an unavailable job; financial review, evidence storage and deterministic exports are separate capabilities.

## Optional genuine agent run

First complete [AWS_FIRST_STEPS.md](AWS_FIRST_STEPS.md), verify a tool-capable regional model in the account and set the current terminal's `AWS_PROFILE`, `AWS_DEFAULT_REGION` and `BEDROCK_MODEL_ID`. Keep `GRANTTHREAD_MODE` local; setting it to `aws` selects cloud storage and requires the deployed resources.

Restart the local backend with those values and trigger an evidence job. Record its actual outcome and tool events. A successful local Bedrock invocation still does not verify the deployed Cognito/API/SQS path.

## Reset and build

Use the local app's explicit demo reset action where present. The API reset contract is `POST /api/demo/reset` with `{"confirm":true}` and the current bearer session. It resets shared synthetic data, so coordinate with other local testers. Do not delete arbitrary directories to reset the app.

```powershell
npm.cmd --prefix frontend run build
```

Compiled frontend output is `frontend/dist`. For actual cPanel deployment follow [DEPLOYMENT.md](DEPLOYMENT.md); a local build with default API settings is not a configured cloud release.
