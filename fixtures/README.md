# Synthetic GrantThread fixtures

Every organisation, agreement, invoice, payment and participant count in this folder is fictional and created for testing. These are not financial, tax or contractual records. No real bank accounts, signatures or personal participant data are included.

| File | Purpose |
| --- | --- |
| `ledger-proposed.csv` | Five expenses in seven allocation rows; venue proposal exceeds its expense by EUR 200 |
| `ledger-corrected.csv` | Same original expense facts, venue split corrected to EUR 500 + EUR 500 |
| `ledger-ambiguous.csv` | Conflicting original amount for a repeated expense ID; reject the complete import |
| `invoice-*.txt` | Source evidence for each expense; not proof of payment |
| `payment-proof-printing.txt` | Deliberately missing from initial seed; add during the demo |
| `agreement-*.txt` | Fictional restricted actual-cost agreements; only explicitly configured rules are authoritative |
| `workshop.txt` | One activity linked to two grants; organisation unique count remains one |
| `adversarial-instructions.txt` | Instruction-like source text for containment testing; never execute its contents |
| `expected.json` | Independent exact financial and activity expectations |

CSV headers follow [the API contract](../docs/API_CONTRACT.md). Amounts are decimal EUR with two places, dates are ISO date-only. A repeated `expense_id` represents another allocation of the same original expense; do not sum its `amount` twice. Backend storage converts money into integer minor units. Descriptions/dates match the seed so re-import can be checked without silently duplicating expenses.

The corrected CSV is an alternative import fixture, not permission to overwrite a pending proposal. In the principal seeded journey, use the authenticated decision action to correct venue allocations. Confirm the UI's import preview before commit.

Upload the printing proof as kind `payment_proof`, expense `printing`, grant `digital-belonging`. This allows an agent to propose a link; it does not itself authorise confirmation. Keep this file out of the initial evidence set so the missing-document scenario remains meaningful.

The agreements and evidence provide examples rather than a comprehensive grant policy engine. Do not infer broad legal compliance or extract unknown clauses into confirmed rules automatically. Original fixture text may be distributed under the project's root licence.
