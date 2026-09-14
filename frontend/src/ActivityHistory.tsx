import { useState } from 'react'
import { Clock3, History, RefreshCw, Search, ShieldCheck } from 'lucide-react'
import { Badge, DownloadButton, Empty, Loading, Notice, PageHeading, ResourceError, SectionHeading, useResource } from './components'
import './ActivityHistory.css'

type AuditEvent = { sequence: number; action: string; targetId: string; actorId: string; actorName?: string; at: string }
type ActivityHistoryData = { events: AuditEvent[]; total: number; limit: number; truncated: boolean }

const actionNames: Record<string, string> = {
  csv_import: 'Portfolio CSV imported',
  evidence_uploaded: 'Evidence uploaded',
  proposal_apply: 'Decision applied',
  proposal_reject: 'Decision rejected',
  proposal_recomputed: 'Decision recalculated',
  report_prepared: 'Report prepared',
  report_shared: 'Report shared',
  clarification_opened: 'Clarification opened',
  clarification_respond: 'Clarification answered',
  clarification_resolve: 'Clarification resolved',
  grant_created: 'Grant created',
  funds_receipt: 'Funding receipt recorded',
  financial_import_drafted: 'Financial import drafted',
  financial_source_reviewed: 'Financial source reviewed',
}
function actionName(action: string) {
  if (actionNames[action]) return actionNames[action]
  const words = action.replace(/_/g, ' ')
  return words ? words[0].toUpperCase() + words.slice(1) : 'Action not recorded'
}
function timestamp(value: string) {
  const parsed = new Date(value)
  return Number.isNaN(parsed.getTime()) ? 'Time not recorded' : new Intl.DateTimeFormat('en-GB', { year: 'numeric', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Europe/Bucharest' }).format(parsed)
}

export function ActivityHistoryPage({ revision }: { revision: number }) {
  const resource = useResource<ActivityHistoryData>('/activity', revision)
  const [action, setAction] = useState('all')
  const [search, setSearch] = useState('')
  if (resource.loading && !resource.data) return <Loading text="Opening recorded activity…" />
  if (resource.error && !resource.data) return <ResourceError error={resource.error} retry={resource.reload} />
  if (!resource.data) return null
  const { events, total, truncated } = resource.data
  const query = search.trim().toLowerCase()
  const filtered = events.filter(event => (action === 'all' || event.action === action) && `${actionName(event.action)} ${event.action} ${event.targetId} ${event.actorName || ''} ${event.actorId}`.toLowerCase().includes(query))
  const actions = [...new Set([...events.map(event => event.action), ...(action === 'all' ? [] : [action])])].sort((a, b) => actionName(a).localeCompare(actionName(b)))
  const hasFilters = action !== 'all' || !!query
  function clearFilters() { setAction('all'); setSearch('') }
  return <div className="activity-history-page">
    <PageHeading eyebrow="WORKSPACE HISTORY" title="Follow the changes." action={<><button className="button secondary" disabled={resource.loading} onClick={resource.reload}><RefreshCw size={16} className={resource.loading ? 'spin' : ''} />{resource.loading ? 'Refreshing…' : 'Refresh'}</button><DownloadButton path="/activity/csv" name="grantthread-activity-history.csv">Download entire history (.csv)</DownloadButton></>}>Review recorded actions in your organisation, with the actor, time and record reference kept together.</PageHeading>
    {resource.error && <Notice>Activity could not be refreshed. The last loaded records are shown below. {resource.error}</Notice>}
    <div className="activity-history-summary"><History size={22} /><div><strong>{total.toLocaleString()} recorded {total === 1 ? 'event' : 'events'}</strong><p>{truncated ? `Showing the latest ${events.length.toLocaleString()} events. Filters apply to these loaded records.` : 'Recorded events are shown newest first.'} The CSV includes the entire recorded history, oldest first, without these filters.</p></div><Badge><Clock3 size={12} />Europe/Bucharest</Badge></div>
    <section className="panel" aria-busy={resource.loading}>
      <SectionHeading title="Recorded actions" detail="Filter by action, or find a person or record reference." />
      <div className="activity-history-filters"><label>Action<select value={action} onChange={event => setAction(event.target.value)}><option value="all">All actions</option>{actions.map(value => <option key={value} value={value}>{actionName(value)}</option>)}</select></label><label className="activity-history-search">Find an event<span><Search size={17} /><input type="search" value={search} onChange={event => setSearch(event.target.value)} placeholder="Action, person or record reference" /></span></label>{hasFilters && <button className="text-button" onClick={clearFilters}>Clear filters</button>}</div>
      <p className="activity-history-count" role="status">{filtered.length.toLocaleString()} of {events.length.toLocaleString()} loaded events{hasFilters ? ' match these filters' : ''}</p>
      {filtered.length ? <div className="table-scroll activity-history-table" role="region" aria-label="Recorded workspace activity" tabIndex={0}><table><thead><tr><th scope="col">When · Bucharest</th><th scope="col">Action</th><th scope="col">Recorded actor</th><th scope="col">Record reference</th></tr></thead><tbody>{filtered.map(event => <tr key={event.sequence}><td><time dateTime={event.at || undefined}>{timestamp(event.at)}</time><small className="cell-detail">Event {event.sequence}</small></td><td><strong>{actionName(event.action)}</strong><small className="cell-detail activity-reference">{event.action}</small></td><td>{event.actorName ? <><strong>{event.actorName}</strong><small className="cell-detail activity-reference">{event.actorId || 'Actor ID not recorded'}</small></> : <><span className="activity-reference">{event.actorId || 'Actor not recorded'}</span><small className="cell-detail">Name not recorded for this event</small></>}</td><td><span className="activity-reference">{event.targetId || 'No record reference'}</span></td></tr>)}</tbody></table></div> : <Empty title={hasFilters ? 'No matching events' : 'No activity recorded yet'}>{hasFilters ? truncated ? 'Try a different filter, or download the entire history to search older records.' : 'Try another action, person or record reference, or clear your filters.' : 'Recorded imports, financial confirmations, decisions and report actions will appear here as you work.'}</Empty>}
    </section>
    <div className="activity-history-note"><ShieldCheck size={19} /><p>This is a read-only view of saved activity. It does not record every page view, sign-in or action, and it does not replace the source files or the history on individual records. Actor names appear only when they were saved with the event.</p></div>
  </div>
}
