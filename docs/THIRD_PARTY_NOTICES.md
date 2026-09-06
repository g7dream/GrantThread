# Third-party notices checklist

Original project code is intended for an MIT release. A root MIT licence does not relicense dependency code, fonts, images, SDKs or incorporated snippets. Preserve each dependency's applicable licence and notices in the source and distributed package where required.

Before public release:

1. Inspect the actual frontend lockfile and backend requirements, including transitive dependencies. Record exact versions and their upstream licence files.
2. Include required notices for bundled JavaScript, icons and fonts. Do not assume a font is covered by the application licence; preserve its own licence.
3. Check copied examples, templates and assets separately. Record origin and modifications for any prior project code.
4. Confirm original fixture text and synthetic assets contain no real organisation documents, signatures, account numbers, credentials or personal records.
5. Run a final secret and asset review before publishing repository history or the frontend ZIP. `.env` files and local data directories must remain excluded.

| Component | Exact version/source | Licence | Notice location | Checked |
| --- | --- | --- | --- | --- |
| Frontend runtime and build dependencies | Populate from lockfile | Pending review | Pending | No |
| Python and agent dependencies | Populate from requirements/installed distribution | Pending review | Pending | No |
| Bundled font/icon assets | Inspect final assets | Pending review | Pending | No |
| Incorporated prior work, if any | Contributor inventory required | Pending review | Pending | No |

This is release guidance, not a completed licence audit. Keep any generated dependency inventory with the release. See the competition [rules check](submission/RULES_CHECK.md) for the repository publication requirement.
