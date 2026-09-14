# Financials: imports, conversion and review

Financials lets a grant administrator import a ledger or bank statement, review proposed entries, record funding receipts and prepare a report in the grant's reporting currency. A parsed row is a candidate, not confirmed spending. Only an authenticated grantee's explicit confirmation updates the financial ledger.

Use fictional records in the local demo and any public demonstration. Anyone accessing the local demo can select its demo accounts. Do not upload sensitive financial files to a public demo deployment. On 14 September 2026, 34 financial cloud checks passed through administrative Lambda invocation with trusted gateway claims and real S3/DynamoDB storage: XLSX and supported text-PDF imports, receipt conversion, payment matching, CAD 25→20 correction, report/template XLSX and PDF generation, and denied out-of-scope access. Those tests bypass browser/OAuth/JWT verification. Separate actual hosted browser checks confirmed sign-in/reload, entered rate direction, CAD 20 actuals and CAD 250 receipts. UI-downloaded XLSX and repaired-backend PDF version 2 independently read back with those values; the JSON manifest was valid. The PDF/manifest checks preceded the final frontend reload. With the final frontend loaded, the recipient downloaded the selected original invoice as actual verified text, and the source-linked question/answer/acknowledgement persisted as resolved. Genuine model-based bank extraction remains unverified. See [EVALUATION.md](EVALUATION.md) for exact evidence and timing.

## Import and review

1. Select or create the grant, including its reporting currency.
2. Record relevant funding receipts and the entered exchange-rate direction, if the report uses receipt-based conversion.
3. Import an XLSX ledger or text-based PDF bank statement into that grant. The original remains in private application storage.
4. Review the source preview. For an XLSX ledger, choose the sheet, header row, column mapping, date convention and default source currency as needed. Check excluded summary rows against the original.
5. Accept the preview to create editable drafts. Check dates, references, amounts, currency, category, cash movement type and conversion method. Confirm valid drafts or reject incorrect/duplicate drafts. A stale or invalid entry prevents its entire confirmation batch from applying.
6. For an incomplete or unbalanced bank extraction, resolve its drafts and record a source-review note after checking the missing or mismatched movements. Pending imports remain visible in reporting readiness; source warnings remain visible after review.

The same file, purpose and grant are recognised on repeated upload instead of creating another import. References retain the source import and sheet/row or PDF page. An imported source stays scoped to its selected grant. Draft edits retain history and expected versions; stale requests must refresh before applying.

### Ledger workbooks and formulas

The XLSX importer recognises common headers and supports explicit mappings for dates, descriptions, references, signed amounts, positive amounts with a debit/credit Direction column, separate debit/credit columns, currencies, categories and exchange rates. Credits become positive cash-movement drafts requiring classification; their original credit direction remains protected through edits and confirmation. Conflicting amount signs/directions or ambiguous debit/credit values block those rows. Choose the decimal separator for the source workbook. A workbook's entered rate becomes an explicit manual conversion rate, not a market quote.

The server never calculates spreadsheet formulas. A mapped transaction formula must already have a cached result. If it is missing, recalculate and save in Excel before importing again. Cached values can also be stale, so verify the saved source. Macros, external workbook links and embedded objects are unsupported. Exported user text is written as literal cell text rather than a spreadsheet formula.

### Bank statements and actual AI availability

The deterministic parser supports a narrow text layout identified by Banca Transilvania statement headers, explicit debit/credit columns and currency. This is file parsing, with no bank connection or endorsement. Unrecognised or unreliable layouts require a genuine configured Strands/Bedrock extraction job. Scanned pages and PDFs without extractable text are rejected; OCR is not implemented.

A bank job reads only the selected statement's extracted pages. It validates exact source excerpts, dates, monetary tokens, currency and debit/credit claims before saving candidate rows. Totals and opening/closing balances are separate checks when present; they never become transactions. Actual dated fees can be transactions. Missing checks, mismatches and incomplete extraction remain warnings. Passing these checks does not prove that every row was captured.

Without a model connection, the job is `unavailable` and retains the source without invented rows. A configured model can still fail or time out. Success saves a preview, not confirmed expenses. Bank AI output is capped at 60 rows per run, with incomplete extraction flagged. Review every page before treating a resulting total as complete.

Valid active jobs for the same import are reused. Changed inputs or expired leases allow a fresh run and fence the previous worker. Another active run for the same actor can prevent scheduling. A scheduling-limit warning after upload does not discard the saved source; it remains available for retry.

## Cash movements and immutable corrections

| Entry type | Confirmation behavior |
| --- | --- |
| Expense | Adds confirmed spending and its frozen conversion to the grant report; requires a reporting category. |
| Payment match | Associates a bank debit with an existing expense of the same amount, currency and grant; marks paid status without recording another expense. An existing conversion snapshot is preserved. |
| Refund, transfer or income | Records the classified movement; does not automatically create a reported expense or a funding receipt. |
| Unclassified | Cannot be confirmed until the administrator selects its meaning. Incoming bank credits start here. |
| Adjustment | Records a signed, reasoned correction linked to a confirmed expense, retaining its currency, category, grant and original exchange rate. |

A unique bank reference, amount, currency and grant match can suggest a payment-match draft. The administrator still reviews and confirms it. Duplicate checks guard repeated bank movements and already recorded expenses. An incoming bank credit cannot become a positive expense merely to include it in report spending.

Confirmed entries cannot be edited or rejected. Create a linked adjustment draft for a correction. The original and every confirmed adjustment remain in history. Corrections cannot reduce the original expense's cumulative source amount below zero.

Adjustments use cumulative rounding: convert the corrected total source amount at the original rate, then subtract the original reporting amount and previously confirmed adjustments. This prevents small corrections from accumulating independent rounding errors. A complete reversal returns the cumulative reporting amount to zero.

Confirm corrections to the same original expense one at a time. Confirming one changes the versions of other pending corrections to that expense, so refresh and review their recalculated differences before continuing. A batch containing two corrections to the same original is rejected atomically. The corrected cumulative source amount must remain within the supported money bounds.

## Receipts and exchange-rate direction

Supported source and reporting currencies are **EUR, RON, CAD, USD, GBP, CHF, AUD and NZD**, all with two decimal places in this application. Original and reporting amounts are stored separately as integer minor units; mixed portfolio currencies remain separate totals.

A receipt records the grant, receipt date, source currency and amount, entered rate, direction and reporting amount. Source currency is the currency of the money recorded locally; reporting currency belongs to the grant. The rate can express reporting units per source unit or source units per reporting unit. Internally it is normalised to reporting currency per source currency.

For example, CAD 1,000 of funding converts to RON 4,000 credited to a local bank account. On a CAD-reporting grant, enter **source currency RON, source amount 4,000, and rate 4 with direction `source_per_report`**: one CAD corresponds to four RON. The stored conversion is 0.25 CAD per RON, and the receipt reports CAD 1,000. Leave **Automatically use this rate for eligible drafts** checked. A later RON 100 expense in receipt mode, with automatic receipt selection, converts to CAD 25. This describes the software calculation; the administrator chooses the treatment required by the funder.

| Conversion method | Rate selected by the application |
| --- | --- |
| Same currency | Rate 1 when source and reporting currencies match. |
| Automatic receipt | In receipt mode with no explicit receipt selected, the latest receipt marked Automatic for the same grant and currency pair, received on or before the entry date. |
| Specific receipt | The selected receipt's normalised rate, for the same grant and currency pair, dated on or before the entry. |
| Weighted receipts | The source-amount-weighted rate of all matching receipts dated on or before the entry; future receipts are excluded. |
| Entered rate | A positive manually supplied rate in reporting units per source unit. |

The receipt form checks automatic use by default; users can clear it. An explicit receipt selection overrides automatic selection. Automatic eligibility requires `useAsDefault: true`; API callers omitting that field retain the previous opt-out behavior. The latest eligible receipt is ordered by received date, then creation time. If none is eligible, the draft needs a matching receipt or another explicit conversion method.

The weighted rate is `sum(source amount × normalised rate) / sum(source amount)`. RON 1,000 at 0.30 CAD/RON plus RON 3,000 at 0.40 CAD/RON gives 0.375 CAD/RON, not an unweighted average. The calculation uses decimal receipt values before rounding the resulting rate. Weighted mode includes all eligible matching receipts, whether or not they are marked Automatic.

Entered rates support up to 18 decimal places. Inversion and weighted rates round to 18 decimal places using decimal half-up rounding. Converted money rounds half-up to a minor unit. Adding a receipt increments affected automatic/weighted draft versions so an older screen cannot confirm a newly changed conversion without refreshing. Confirmation saves the rate, method, reporting amount and relevant receipt identifiers; later receipts or edits do not silently recalculate confirmed history. Exported ledger rates are text, preserving their stored decimal representation.

The application does not choose the funder's FX policy, fetch market rates, consume receipt balances in FIFO order or enforce a funding-receipt/grant spending cap. Receipt selection supplies conversion provenance, not an assertion that the funds have not already been spent. The user must select and review the required policy.

## Financial reports and XLSX templates

Choose inclusive start/end dates and category budgets in the grant's reporting currency. Actuals include confirmed expenses and linked adjustments within that period. Refunds, transfers, income and payment matches are not additional report expenses. Variance is budget minus actual; budgets are comparison figures, not spending-cap enforcement. The report includes unresolved draft/import counts and source warnings.

The standard export includes **Financial Report**, **Ledger** and **Funding Receipts** sheets with original/reporting amounts, rate details and source/history references. It is a private download, not an automatic funder submission.

For a funder template, upload its XLSX and review the mapping. Map category actuals, optionally a total, period start/end and a rate cell. The mapping must cover every report category, use distinct valid output cells and avoid merged-cell interiors and every cell covered by an array formula. Exports change only mapped values; other cells and formulas are retained through the workbook library. This does not guarantee support for every Excel feature or arbitrary layout.

A mapped rate cell requires exactly one foreign currency pair and one conversion rate in the report. Identical numeric rates for different currencies do not represent one shared conversion basis. If there are several pairs/rates or no foreign rate, leave it unmapped and use the ledger's conversion detail. Preserved formulas are not calculated by the server: open the exported workbook in Excel, recalculate and verify it before use. Explicitly mapping a cell can replace its previous ordinary formula.

Period start/end cells can also be mapped. Match the template rate direction explicitly: reporting currency per source unit is the default; the reciprocal is used only when selected. Only mapped cells change; other headings, balances and carry-forward figures still need review. The generated ledger identifies each selected funding receipt so its conversion can be traced to the receipt sheet.

## Enforced scope and bounds

| Area | Bound |
| --- | --- |
| Financial upload | Nonempty XLSX/PDF, up to 2 MB each. |
| Workbook | Up to 30 sheets, 50 data columns and 500 parsed transactions; expanded ZIP content up to 20 MB, with additional compression and structure checks. Formatting does not imply unlimited data capacity. |
| Bank PDF | Up to 20 text-bearing pages and 100,000 extracted characters; no encrypted or scanned-only PDFs. |
| Bank AI | Up to 60 output rows, 120,000 UTF-8 bytes of statement text, two model/provider requests, 4,000 output tokens per call and 180 seconds per job. |
| Workspace | Up to 40 financial imports, 500 financial entries, 150 funding receipts and 30 grants; the 340 KB organisation aggregate ceiling can be reached earlier. |
| Review batch | One to fifty distinct drafts, with current versions. |
| Rates | Positive values from 0.000001 to 100000 before and after normalisation; up to 18 entered decimal places. |
| Agent scheduling | Up to 30 created runs per actor per UTC day; active runs are reused or blocked as described above. |

Original bytes and extracted PDF pages belong in private storage, not aggregate response bodies. Financial originals, receipts, entries and XLSX exports are restricted to the owning grantee; receiving a report snapshot does not grant funders access. Public fixtures contain fictional data only. Local runtime data and generated artifacts remain excluded from repository releases and frontend packages.

The cloud transport returns a clear `export_too_large` error for generated binary downloads larger than 4 MiB, before base64 encoding exceeds the Lambda response ceiling. Reduce the workbook size or reporting period when possible. Original-source downloads use separate authorised S3 links in cloud mode. Local backup and restore instructions are in [LOCAL_RECOVERY.md](LOCAL_RECOVERY.md).

Implementation is in `finance_io.py`, `finance_math.py`, `finance_service.py` and `bank_agent.py` under `backend/grantthread/`. Current test counts belong in [EVALUATION.md](EVALUATION.md), not claims of live AWS/model validation. See also [permissions](PERMISSIONS.md), [architecture](ARCHITECTURE.md) and [model disclosure](MODEL_DISCLOSURE.md).
