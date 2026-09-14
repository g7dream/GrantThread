import type { Expense, Grant, Job } from './types'

export type Receipt = {
  id: string; grantId: string; receivedDate: string; sourceCurrency: string; reportCurrency: string
  sourceAmountMinor: number; rate: string; rateDirection: 'report_per_source'; reportAmountMinor: number; note: string; useAsDefault?: boolean
  enteredRate?: string | number; enteredDirection?: 'report_per_source' | 'source_per_report'
}
export type FinanceKind = 'expense' | 'refund' | 'transfer' | 'income' | 'adjustment' | 'payment_match' | 'unclassified'
export type ConversionMode = 'receipt' | 'weighted_average' | 'manual' | 'same_currency'
export type FinanceEntry = {
  id: string; version: number; status: 'draft' | 'confirmed' | 'rejected'; kind: FinanceKind
  date: string; description: string; reference: string; sourceAmountMinor: number; currency: string
  grantId: string; category: string; conversionMode: ConversionMode; receiptId?: string; manualRate?: string
  reportAmountMinor?: number | null; reportCurrency?: string; fxRate?: string; matchExpenseId?: string; expenseId?: string; adjustsEntryId?: string
  reason?: string; warning?: string; source?: { importId: string; sheet?: string; row?: number; page?: number }
  history?: { at?: string; action?: string; actorId?: string; reason?: string; [key: string]: unknown }[]
}
export type FinanceImport = {
  id: string; version: number; name: string; kind: 'ledger' | 'bank' | 'template'; status: string; grantId: string
  sourceCurrency?: string; defaultCurrency?: string; defaultSheet?: string; dateFormat?: 'dmy' | 'mdy' | 'ymd'; suggestedDateFormat?: 'dmy' | 'mdy' | 'ymd'
  decimalSeparator?: '.' | ',' | null
  sheets: { name: string; rowCount: number; previewRows: unknown[][] }[]
  sheet?: string; headerRow?: number; mapping?: Record<string, string | number>; rows: Record<string, unknown>[]
  templateMapping?: { sheet: string; categoryColumn: string; actualColumn: string; startRow: number; endRow: number; totalCell?: string; rateCell?: string; periodStartCell?: string; periodEndCell?: string; rateDirection?: 'report_per_source' | 'source_per_report' }
  warnings: string[]; entryIds: string[]; message?: string; job?: Job; jobId?: string; engine?: string
  extractionComplete?: boolean; balanceChecks?: { currency: string; kind: string; matches: boolean }[]
  reviewedAt?: string; reviewNote?: string
}
export type FinancialsData = {
  grants: Grant[]; expenses: Expense[]; receipts: Receipt[]; entries: FinanceEntry[]; imports: FinanceImport[]; templates: FinanceImport[]
  currencies: string[]; categories: string[]
}
export type FinancialReport = {
  grant: Grant; periodStart: string; periodEnd: string
  rows: { category: string; budgetMinor: number; actualMinor: number; varianceMinor: number }[]
  entries: FinanceEntry[]; totalMinor: number; currency: string; unresolvedCount: number; unresolvedImportCount: number
  sourceWarnings: string[]; receiptsTotalMinor: number; version: number; rate?: string | null; synthetic?: boolean
}
