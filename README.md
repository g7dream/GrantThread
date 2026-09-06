# GrantThread

**Many grants. One clear thread.** A shared operations workspace for multi-grant administrators and the funders reviewing their deliberately shared reports.

GrantThread records expenses once, keeps proposed allocations separate from confirmed money, connects versioned evidence, prepares two report formats, and preserves a question-and-response history around immutable shared packages. All bundled organisations, documents and outcomes are **synthetic demonstration data**.

## Current release status

The local P0 workflow is implemented and has been exercised from import through funder acknowledgement. It includes a React/TypeScript interface, persistent Python API, exact financial calculations, source review, PDF/manifest exports, server-issued local demo sessions and scoped funder views. The repository also includes a real Strands/Bedrock worker and AWS SAM infrastructure.

**AWS/Cognito/SQS deployment and a genuine Bedrock run are not verified.** The interface reports the missing model connection as unavailable; it does not substitute simulated agent output. Eleven worker checks use explicitly labelled offline provider fixtures with the real Strands SDK. Public hosting, repository publication and the final demonstration video await account access and deployed verification.

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

Open [the local application](http://127.0.0.1:5173/). Choose Bright Path Lab, Harbour Collective or Northstar Foundation. Local identities establish opaque server sessions; a client-side role flag is never permission. The API binds to loopback and rejects unrelated hosts/origins. Local demo login and reset are absent from the cloud API.

After dependencies are installed, `scripts/start-local.ps1` starts the local API and interface together. The `.env.example` file documents configuration keys; export backend variables in the terminal. Vite reads `frontend/.env.local`. Full instructions are in [local setup](docs/SETUP.md).

## Demonstration workflow

1. In **Evidence inbox**, import `fixtures/ledger-proposed.csv`. Preview its EUR 200 excess; invalid splits stay outside the confirmed ledger.
2. In **Decisions**, inspect the venue invoice and correct Digital Belonging to EUR 500, keeping Community Makers at EUR 500. Apply the corrected split.
3. Prepare Digital Belonging's report. Its printing payment proof is missing, so sharing remains blocked.
4. Upload `fixtures/payment-proof-printing.txt`, select Digital Belonging and the Printing expense, and approve its evidence connection after reviewing the source.
5. Prepare a new report and download its PDF/manifest. Community Makers uses a second, finance-first layout.
6. Review the recipient and explicitly select attachments. Confirm original-file disclosure before sharing. Internal readiness warnings and other funders' allocations are excluded from the funder projection.
7. Switch to Northstar Foundation, open the shared report and ask a question. Switch back to answer, then let the funder acknowledge resolution.

The resulting confirmed allocations are EUR **1,700 / 3,100 / 400**, totalling EUR **5,200** across five unique expenses. The shared workshop counts once in the organisation's unique activity total.

## Verification

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend/tests -v
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts/benchmark_local.py
```

The targeted checks cover money, currency, concurrent/stale actions, tenant scope, upload bounds, source versions, batch atomicity, shared projections, PDF text, clarification lifecycle, queue fencing, tool budgets and model timeout. The scripted benchmark runs three isolated **local service-layer** journeys; it excludes human review and does not establish time savings. It is separate from the still-required three deployed demonstration runs.

## AWS and cPanel

Begin with [AWS first steps](docs/AWS_FIRST_STEPS.md), then [infrastructure setup](infra/README.md) and [deployment instructions](docs/DEPLOYMENT.md). The frontend is intended for a domain you control under lowercase `/grantthread/`; `spaceship.com` is the hosting provider's domain. No unrelated website should be overwritten.

AWS SAM defines Cognito code+PKCE login, JWT-authorised API Gateway, Python Lambda, private S3, DynamoDB and SQS. A configured **regional** Bedrock model is mandatory; no silent cross-region fallback exists. Server-managed membership determines authority. Only a user-authorised deterministic endpoint changes canonical allocations or publishes a snapshot. The seven model tools cannot publish, pay, email, execute SQL or access a shell.

After setting the public AWS/Cognito frontend values:

```powershell
$env:VITE_BASE_PATH = '/grantthread/'
npm.cmd --prefix frontend run build
.\.venv\Scripts\python.exe scripts/package_cpanel.py --base /grantthread/
```

The ZIP is written to `artifacts/GrantThread-cpanel.zip` and contains compiled public assets, an `.htaccess` and deployment notes. The included parent-directory rewrite example handles mixed-case `/GrantThread` requests. Its actual hosting behavior must be verified on your domain. A ZIP built without AWS public configuration is a preview package, not a functioning cloud deployment.

## Project layout

| Directory | Purpose |
| --- | --- |
| `frontend/` | Six connected surfaces, local font, authenticated API client and responsive styling |
| `backend/grantthread/` | Domain, service, persistence, local/Lambda transport, private storage, reports and bounded Strands worker |
| `backend/tests/` | Focused acceptance and worker checks |
| `infra/` | SAM template, operator seed/membership script and operation/teardown instructions |
| `fixtures/` | Fictional source documents, ordinary/ambiguous ledgers and expected figures |
| `docs/` | Architecture, permissions, evidence, deployment and submission drafts |
| `scripts/` | Local launch, cPanel packaging, benchmark and authorised GitHub repository helper |
| `artifacts/` | Generated local reports and release ZIP; excluded from source control |

## Limits and disclosure

This is a bounded synthetic demonstration, not production security or compliance certification. The organisation aggregate has a 340 KB application ceiling; a real large ledger needs further partitioning. Imports accept EUR CSVs up to 500 rows, and UTF-8 TXT/text PDFs up to 5 MB and 20 pages (120,000 extracted characters). OCR and broad agreement extraction are deferred. Private original downloads use authorised, expiring S3 links in AWS to avoid Lambda's binary-response ceiling.

Human review does not make all interpretations correct. AI proposals cannot directly change money, requirements, permissions or disclosures. Shared narrative is deterministic; source text and model prose are not automatically adopted as factual narrative. Read [model disclosure](docs/MODEL_DISCLOSURE.md) and [permission boundaries](docs/PERMISSIONS.md).

Original project code is [MIT licensed](LICENSE). See [third-party notices](docs/THIRD_PARTY_NOTICES.md). Submission materials are drafts under `docs/submission/`; no posts, video, entry or repository publication are claimed complete.
