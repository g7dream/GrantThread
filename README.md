# GrantThread

**Many grants. One clear thread.** A shared operations workspace for multi-grant administrators and the funders reviewing their deliberately shared reports.

GrantThread records expenses once, keeps proposed allocations separate from confirmed money, connects versioned evidence, prepares reports, and preserves a question-and-response history around immutable shared packages. Its Financials workspace adds XLSX ledger imports, text-based bank PDF review, funding receipts, exact currency conversion and mapped report-template exports. All bundled organisations, documents and outcomes are **synthetic demonstration data**.

Source is published at [g7dream/GrantThread](https://github.com/g7dream/GrantThread). Public access, default branch `master`, README and MIT licence were independently verified at source revision [`3b4ceba`](https://github.com/g7dream/GrantThread/commit/3b4ceba8b83e0924c7a7eda425768d865d964101).

## Current release status

The local P0 workflow is implemented and has been exercised from import through funder acknowledgement. It includes a React/TypeScript interface, persistent Python API, exact financial calculations, source review, PDF/manifest exports, server-issued local demo sessions and scoped funder views. The repository also includes a real Strands/Bedrock worker and AWS SAM infrastructure.

**14 September 2026: deployed backend, hosted grantee sign-in/reload and financial XLSX readback verified; final release checks remain.** The `grantthread-demo` stack is deployed in `eu-north-1`. A real Nova Lite reconciliation made four model calls and eight successful tool calls, then correctly reached `waiting_input` for missing printing proof and human allocation review. Forty-nine cloud backend checks passed through administrative Lambda invocation with trusted gateway claims; these do not verify API Gateway JWT validation or browser access. Real Cognito sign-in, normal reload, financial display and downloaded XLSX values pass. The final raw/gzip/Brotli checks match the built files, and the canonical browser loads the current bundle after the hosting cache repair. A fresh portfolio-wide browser job made nine model calls/eight tool calls (seven successes, one rejected evidence reference), exhausted its tool budget and saved no draft; this is distinct from the earlier grant-scoped run. Hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. See [the evaluation record](docs/EVALUATION.md) for exact evidence and remaining gates.

See [task progress](PROGRESS.md), [evaluation evidence](docs/EVALUATION.md) and [architecture](docs/ARCHITECTURE.md).

## Run locally

Requires Python 3.12 and Node.js with npm. From the repository root in PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
npm.cmd --prefix frontend ci
```

Start the API in one terminal:

```powershell
Set-Location backend
..\.venv\Scripts\python.exe -m grantthread.local_server
```

Start the interface in another terminal:

```powershell
npm.cmd --prefix frontend run dev
```

Open [the local application](http://127.0.0.1:5173/). Choose Bright Path Lab, Harbour Collective or Northstar Foundation. Anyone with access to this local demo can select any demo account; use fictional data only. Local identities establish opaque server sessions, and a client-side role flag is never permission. The API binds to loopback and rejects unrelated hosts/origins. Local demo login and reset are absent from the cloud API.

After dependencies are installed, `scripts/start-local.ps1` starts the local API and interface together. Use `-DataDirectory .\artifacts\my-test-workspace -Offline` for a separate fictional workspace with no Bedrock calls. [Local recovery](docs/LOCAL_RECOVERY.md) documents private backups and verified restore into a new directory. The `.env.example` file documents configuration keys; export backend variables in the terminal. Vite reads `frontend/.env.local`. Full instructions are in [local setup](docs/SETUP.md).

## Demonstration workflow

1. In **Evidence inbox**, import `fixtures/ledger-proposed.csv`. Preview its EUR 200 excess; invalid splits stay outside the confirmed ledger.
2. In **Decisions**, inspect the venue invoice and correct Digital Belonging to EUR 500, keeping Community Makers at EUR 500. Apply the corrected split.
3. Prepare Digital Belonging's report. Its printing payment proof is missing, so sharing remains blocked.
4. Upload `fixtures/payment-proof-printing.txt`, select Digital Belonging and the Printing expense, and approve its evidence connection after reviewing the source.
5. Prepare a new report and download its PDF/manifest. Community Makers uses a second, finance-first layout.
6. Review the recipient and explicitly select attachments. Confirm original-file disclosure before sharing. Internal readiness warnings and other funders' allocations are excluded from the funder projection.
7. Switch to Northstar Foundation, open the shared report and ask a question. Switch back to answer, then let the funder acknowledge resolution.

The resulting confirmed allocations are EUR **1,700 / 3,100 / 400**, totalling EUR **5,200** across five unique expenses. The shared workshop counts once in the organisation's unique activity total.

Grantees can also open **Response estimates** to try a grant and submission date. The tool estimates the remaining wait for a first funder reply from clearly labelled fictional past review durations. It shows the calendar-day window, time already waited and sample counts. Changing the scenario does not submit a report or change the ledger. See [the calculation and limits](docs/RESPONSE_ESTIMATES.md).

## Financials workflow

Choose a grant and its reporting currency, record funding receipts and import an XLSX ledger or text-based bank PDF. Review the source preview, create editable drafts, classify credits, correct categories and conversion details, then explicitly confirm entries. A matched bank debit marks an existing expense as paid without recording it twice. Later corrections are linked adjustments that retain the original confirmed amount and conversion history.

Supported currencies are EUR, RON, CAD, USD, GBP, CHF, AUD and NZD, all with two decimal places. Receipt mode can automatically choose the latest eligible receipt marked Automatic or use a specifically selected receipt. Receipt rates, weighted receipt rates and manually entered rates use decimal calculations and freeze on confirmation. Users choose the conversion method required by their funder; there is no market-rate feed, FIFO receipt consumption or financial spending-cap enforcement.

Choose the reporting period and category budgets, then export a financial workbook or populate explicitly mapped cells in a funder's XLSX template. Unrecognised bank layouts require an actual configured Bedrock model; no transactions are invented when it is unavailable. See [Financials: workflow, calculations and limits](docs/FINANCIALS.md).

**Activity history** shows the latest recorded organisation actions, their actors, times and record references. Filter the view or export the entire recorded history to CSV. It is private to the grantee and complements each record's source and version history; it does not claim to log every action.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
.\.venv\Scripts\python.exe -m unittest discover -s scripts/tests -v
npm.cmd --prefix frontend test
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts/benchmark_local.py
```

The latest completed local suites passed **244 tests: 169 backend, 50 release/build-script and 25 frontend API tests**, plus the production frontend build. The targeted checks cover money, currency, concurrent/stale actions, tenant scope, upload bounds, source versions, batch atomicity, shared projections, PDF text, clarification lifecycle, queue fencing, tool budgets and model timeout. The scripted benchmark runs three isolated **local service-layer** journeys; it excludes human review and does not establish time savings. It is separate from the still-required three deployed demonstration runs.

## AWS and cPanel

The configured destination is [timeillusion.com/grantthread/](https://timeillusion.com/grantthread/). The application stack, separate USD 25 budget alerts and genuine regional Nova Lite Strands reconciliation are verified. The CORS repairs are deployed and the hosted grantee login, reload and XLSX download pass. Hosted sharing and a source-linked question/answer also pass. Hosted receipt-PDF values, the selected original download and funder acknowledgement are verified. Repeated judge demonstrations remain open. The owner selected `CapacityMode=shared-demo` for the current concurrency quota of 10. Follow [the site setup record](docs/TIMEILLUSION_SETUP.md), [AWS first steps](docs/AWS_FIRST_STEPS.md), [infrastructure setup](infra/README.md) and [deployment instructions](docs/DEPLOYMENT.md). Keep uploads inside the dedicated lowercase `/grantthread/` folder.

AWS SAM defines Cognito code+PKCE login, JWT-authorised API Gateway, Python Lambda, private S3, DynamoDB and SQS. A configured **regional** Bedrock model is mandatory; no silent cross-region fallback exists. Server-managed membership determines authority. Only a user-authorised deterministic endpoint changes canonical allocations or publishes a snapshot. The seven model tools cannot publish, pay, email, execute SQL or access a shell.

The selected build route produces a Linux Python 3.12 x86_64 ZIP from pinned binary wheels and the private-data-excluding runtime stage. The first command downloads wheels from PyPI; subsequent builds can use its returned cache entirely offline. Run each command only after the preceding one succeeds:

```powershell
$download = .\.venv\Scripts\python.exe scripts/build_lambda.py --download | ConvertFrom-Json
$release = .\.venv\Scripts\python.exe scripts/build_lambda.py --wheelhouse $download.wheelhouse | ConvertFrom-Json
```

The output identifies the ZIP, SHA-256, build manifest and staged source template. This follows [AWS's Linux-wheel packaging approach](https://docs.aws.amazon.com/lambda/latest/dg/python-package.html#python-package-native-libraries); archive checks do not prove Linux runtime imports or a working application. The deployment guide covers the separate budget stack, immutable private S3 code object, both `CodeUri` substitutions and review of CloudFormation's server-side SAM change set. SAM CLI with Docker remains an optional standard build route.

After saving actual stack outputs, `scripts/configure_frontend.py --outputs FILE --site-url https://timeillusion.com/grantthread/` produces reviewed public environment settings. Install those settings as described in the deployment guide, then:

```powershell
$env:VITE_BASE_PATH = '/grantthread/'
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts/package_cpanel.py --site-url https://timeillusion.com/grantthread/
```

Cloud packaging refuses incomplete settings and assets that no longer match their build manifest. The cloud ZIP is written to `artifacts/GrantThread-cpanel.zip`; it contains compiled public assets, an `.htaccess` and deployment notes. To deliberately package the interface before AWS setup, use `--preview --site-url https://timeillusion.com/grantthread/`, producing `artifacts/GrantThread-preview.zip`. That preview shows setup is unfinished and does not provide cloud login. The parent-directory rewrite example handles mixed-case `/GrantThread` requests; verify it on the actual host. Packaging is not live deployment verification.

## Project layout

| Directory | Purpose |
| --- | --- |
| `frontend/` | Connected evidence, financial, reporting and funder surfaces, local font and authenticated API client |
| `backend/grantthread/` | Domain, service, persistence, local/Lambda transport, private storage, reports and bounded Strands worker |
| `backend/tests/` | Focused acceptance and worker checks |
| `infra/` | SAM template, operator seed/membership script and operation/teardown instructions |
| `fixtures/` | Fictional source documents, ordinary/ambiguous ledgers and expected figures |
| `docs/` | Architecture, permissions, evidence, deployment and submission drafts |
| `scripts/` | Local launch, cPanel packaging, benchmark and authorised GitHub repository helper |
| `artifacts/` | Generated local reports and release ZIP; excluded from source control |

## Limits and disclosure

This is a bounded demonstration, not production security or compliance certification. The organisation aggregate has a 340 KB application ceiling; a large ledger needs further partitioning. The original expense-allocation import accepts EUR CSVs up to 500 rows; evidence uploads accept UTF-8 TXT/text PDFs up to 5 MB and 20 pages (120,000 extracted characters). Financial XLSX/PDF uploads have a separate 2 MB limit, with up to 500 parsed transactions and 30 workbook sheets; bank AI output is capped at 60 rows per run. Full limits are in [Financials](docs/FINANCIALS.md). OCR and broad agreement extraction are deferred. Private original downloads use authorised, expiring S3 links in AWS to avoid Lambda's binary-response ceiling.

Use only fictional records in a public demonstration or local demo account. Do not upload sensitive financial files to a public demo deployment. Original uploads belong in private application storage, outside public fixtures, repository history and frontend packages.

Human review does not make all interpretations correct. AI proposals cannot directly change money, requirements, permissions or disclosures. Shared narrative is deterministic; source text and model prose are not automatically adopted as factual narrative. Read [model disclosure](docs/MODEL_DISCLOSURE.md) and [permission boundaries](docs/PERMISSIONS.md).

Original project code is [MIT licensed](LICENSE). See [third-party notices](docs/THIRD_PARTY_NOTICES.md). Submission materials are drafts under `docs/submission/`; publication and deployment evidence belongs in the release records.
