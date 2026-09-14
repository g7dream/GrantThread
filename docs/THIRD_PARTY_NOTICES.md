# Third-party notices checklist

Original project code is [MIT licensed](../LICENSE). A root MIT licence does not relicense dependency code, fonts, images, SDKs or incorporated snippets. Preserve each dependency's applicable licence and notices in the source and distributed package where required.

Before public release:

1. Inspect the actual frontend lockfile and backend requirements, including transitive dependencies. Record exact versions and their upstream licence files.
2. Include required notices for bundled JavaScript, icons and fonts. Do not assume a font is covered by the application licence; preserve its own licence.
3. Check copied examples, templates and assets separately. Record origin and modifications for any prior project code.
4. Confirm original fixture text and synthetic assets contain no real organisation documents, signatures, account numbers, credentials or personal records.
5. Run a final secret and asset review before publishing repository history or the frontend ZIP. `.env` files and local data directories must remain excluded.

The following inventory was checked against the installed distributions, their licence/notice files where present, and the frontend lockfile. It records the selected direct dependencies and financial-file libraries; it is not a full transitive licence audit.

| Component | Version | Reported licence / notice source |
| --- | --- | --- |
| React / React DOM | 19.2.8 | MIT; installed package `LICENSE` files. |
| Lucide React | 0.468.0 | ISC; its `LICENSE` also retains the Feather/MIT attribution. |
| Inter variable font | Fontsource package 5.3.0 | SIL Open Font License 1.1; [bundled font licence](../frontend/public/INTER-LICENSE.txt). |
| Vite / TypeScript | 6.4.3 / 5.9.3 | MIT / Apache-2.0, as recorded in `frontend/package-lock.json`; build dependencies. |
| openpyxl / et_xmlfile | 3.1.5 / 2.0.0 | MIT in installed distribution metadata; XLSX import/export and XML writing. |
| pypdf | 6.17.0 | BSD-3-Clause; installed distribution `licenses/LICENSE`. |
| ReportLab | 5.0.1 | BSD-style licence in installed `licenses/LICENSE`; included font directories have separate notices. |
| Strands Agents | 1.54.0 | Apache-2.0; installed `licenses/LICENSE` and `licenses/NOTICE`. |
| boto3 / botocore | 1.43.89 | Apache-2.0; installed distribution licence files. |
| Pydantic | 2.13.5 | MIT; installed distribution `licenses/LICENSE`. |

`scripts/package_cpanel.py` collects the installed React, React DOM and Lucide licence text into `THIRD_PARTY_NOTICES.txt`. The Inter notice is copied from `frontend/public/` with the static build. It packages compiled frontend assets, not backend dependencies, uploaded bank statements, ledgers, private templates or runtime records. Inspect the final ZIP, because files placed in the public asset directory are public by design.

The AWS/backend dependency installation includes openpyxl, et_xmlfile, pypdf, ReportLab and the agent stack pinned in `backend/requirements.txt`. Preserve distribution licence and notice files, including ReportLab's separate bundled-font notices, when preparing that artifact. The Linux runtime artifact has now executed on AWS, including XLSX/PDF and genuine Strands checks; that runtime proof does not complete the remaining transitive licence audit.

User financial sources and funder workbooks are private input, not project fixtures or reusable licensed templates. Do not copy them into public examples, source history, notices, screenshots or release ZIPs. Only fictional fixtures and temporary fictional test workbooks/statements belong in public verification material. A bank-layout recogniser names a format; it does not imply access to that bank or endorsement.

The remaining release check covers all transitive dependencies, incorporated prior work and final artifact contents. This inventory is not a completed licence audit. Keep the full dependency inventory with the release. See the competition [rules check](submission/RULES_CHECK.md) for the repository publication requirement.
