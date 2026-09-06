export type User = { id: string; name: string; role: 'grantee' | 'funder'; organisationId: string; organisationName: string }
export type Readiness = { evidenced: number; total: number; ready: boolean; missing: string[] }
export type Grant = { id: string; name: string; funderName: string; funderOrgId: string; granteeOrgId: string; currency: string; awardMinor: number; allocatedMinor: number; fundingMode: string; deadline: string | null; template: string; version: number; readiness: Readiness; synthetic?: boolean }
export type Requirement = { id: string; grantId: string; title?: string; description?: string; name?: string; status?: string; evidenced?: boolean; satisfied?: boolean; deadline?: string; dueDate?: string; kind?: string; expenseId?: string }
export type Allocation = { grantId: string; amountMinor: number; reportAmountMinor?: number }
export type Expense = { id: string; description: string; amountMinor: number; currency: string; date: string; allocations: Allocation[]; paid?: boolean; paymentEntryId?: string }
export type Activity = { id: string; title: string; participants: number; date: string; grantIds?: string[] }
export type SourceRef = { evidenceId: string; version: number; page: number; excerpt?: string }
export type Evidence = { id: string; name: string; kind: string; version: number; sha256: string; pageCount: number; grantIds: string[]; expenseId?: string; createdAt: string; status: string; excerpt: string; text?: string; pages?: (string | { page: number; text: string })[] }
export type Proposal = { id: string; kind: 'allocation' | 'evidence_link'; title: string; reason: string; status: string; version: number; inputVersion: number; expenseId?: string; evidenceId?: string; sourceRefs: SourceRef[]; before: unknown; after: unknown; applied?: { allocations: Allocation[] }; excessMinor?: number; createdAt: string }
export type Job = { id: string; status: string; engine: string; createdAt: string; finishedAt?: string; message: string; toolEvents: { name: string; at: string; result: unknown }[]; inputVersion: number; actorId: string; organisationId: string; kind?: string }
export type Attachment = { id: string; name: string; version: number; kind: string }
export type Report = { id: string; grantId: string; grantName: string; funderName: string; template: string; version: number; inputVersion: number; createdAt: string; status: string; readiness: Readiness; currency: string; awardMinor: number; allocatedMinor: number; expenses: { description: string; amountMinor: number }[]; activities: Activity[]; narrative: string; sourceRefs: SourceRef[]; availableAttachments: Attachment[]; sharedSnapshotId?: string; synthetic?: boolean }
export type Clarification = { id: string; snapshotId: string; grantName: string; question: string; status: 'open' | 'answered' | 'resolved'; createdAt: string; sourceRef?: SourceRef; messages: { actorName: string; role: string; message: string; at: string }[] }
export type Snapshot = { id: string; reportId: string; grantId: string; grantName: string; recipientOrgId: string; recipientName: string; granteeName: string; version: number; publishedAt: string; report: Report; attachments: Attachment[]; clarifications: Clarification[] }
export type Portfolio = { organisation: { id: string; name: string }; grants: Grant[]; decisions: Proposal[]; totals: { currency: string; awardMinor: number; allocatedMinor: number; expenseMinor: number; uniqueActivities: number; byCurrency?: { currency: string; awardMinor: number; allocatedMinor: number; expenseMinor: number }[] }; requirements: Requirement[]; jobs: Job[] }
export type GrantDetail = { grant: Grant; requirements: Requirement[]; expenses: Expense[]; activities: Activity[]; evidence: Evidence[]; reports: Report[] }
export type ResponseEstimate = {
  grantId: string; grantName: string; funderName: string; simulated: true
  asOfDate: string; submittedDate: string; elapsedDays: number
  sampleCount: number; comparableSampleCount: number; typicalTotalDays: number | null
  historicalRangeDays: { low: number; high: number } | null
  remainingDays: { low: number; typical: number; high: number } | null
  expectedDates: { earliest: string; typical: string; latest: string } | null
  status: 'estimated' | 'insufficient_history' | 'beyond_history'
  historyDays: number[]; method: 'conditional-empirical-quartiles'; unit: 'calendar_days'
}
