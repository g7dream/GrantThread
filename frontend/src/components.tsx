import { useEffect, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { AlertCircle, ArrowUpRight, Check, ChevronRight, Download, FileText, LoaderCircle, RefreshCw, X } from 'lucide-react'
import { api, download } from './api'
import type { Evidence, Job, SourceRef } from './types'

export const money = (amount = 0, currency = 'EUR') => new Intl.NumberFormat('en-IE', { style: 'currency', currency, minimumFractionDigits: amount % 100 ? 2 : 0, maximumFractionDigits: 2 }).format(amount / 100)
export const date = (value?: string) => value ? new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'Europe/Bucharest' }).format(new Date(value.length === 10 ? `${value}T12:00:00Z` : value)) : 'Not provided'
export const dateTime = (value: string) => new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Europe/Bucharest' }).format(new Date(value))
export const label = (value?: string) => value === 'northstar-outcomes' ? 'Outcomes report' : value === 'riverbend-financial' ? 'Financial report' : (value || 'pending').replace(/_/g, ' ')
export function Badge({ children, tone = '' }: { children: ReactNode; tone?: string }) { return <span className={`badge ${tone}`}>{children}</span> }
export function Status({ value }: { value: string }) { return <Badge tone={['approved', 'applied', 'evidenced', 'completed', 'ready', 'resolved', 'linked', 'confirmed', 'shared'].includes(value) ? 'positive' : ['rejected', 'failed', 'stale'].includes(value) ? 'negative' : 'warning'}>{label(value)}</Badge> }
export function Notice({ children, success = false }: { children: ReactNode; success?: boolean }) { return <div className={`notice ${success ? 'success' : ''}`} role={success ? 'status' : 'alert'}>{success ? <Check size={18} /> : <AlertCircle size={18} />}<span>{children}</span></div> }
export function Loading({ text = 'Loading your workspace…' }: { text?: string }) { return <div className="loading" role="status"><LoaderCircle className="spin" size={22} />{text}</div> }
export function Empty({ title, children }: { title: string; children: ReactNode }) { return <div className="empty"><span className="empty-icon"><FileText size={24} /></span><h3>{title}</h3><p>{children}</p></div> }
export function PageHeading({ eyebrow, title, children, action }: { eyebrow: string; title: string; children: ReactNode; action?: ReactNode }) { return <header className="page-heading"><div><div className="eyebrow">{eyebrow}</div><h1>{title}</h1><p>{children}</p></div>{action && <div className="heading-action">{action}</div>}</header> }
export function SectionHeading({ title, detail, action }: { title: string; detail?: string; action?: ReactNode }) { return <div className="section-heading"><div><h2>{title}</h2>{detail && <p>{detail}</p>}</div>{action}</div> }
export function useResource<T>(path: string, revision = 0) {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)
  const [retry, setRetry] = useState(0)
  useEffect(() => {
    if (!path) { setLoading(false); return }
    let active = true
    setLoading(true); setError('')
    api<T>(path).then(value => { if (active) setData(value) }).catch(e => { if (active) setError(e.message) }).finally(() => { if (active) setLoading(false) })
    return () => { active = false }
  }, [path, revision, retry])
  return { data, error, loading, reload: () => setRetry(n => n + 1) }
}
export function ResourceError({ error, retry }: { error: string; retry: () => void }) { return <div><Notice>{error}</Notice><button className="button secondary" onClick={retry}><RefreshCw size={16} />Try again</button></div> }
export function Modal({ title, children, close, className = '' }: { title: string; children: ReactNode; close: () => void; className?: string }) {
  const ref = useRef<HTMLDialogElement>(null)
  useEffect(() => { const dialog = ref.current; dialog?.showModal(); return () => dialog?.close() }, [])
  return <dialog ref={ref} className={`modal ${className}`} onCancel={close} onClick={e => { if (e.target === e.currentTarget) close() }}><div className="modal-header"><h2>{title}</h2><button className="icon-button" aria-label="Close dialog" onClick={close}><X size={20} /></button></div>{children}</dialog>
}
export function DownloadButton({ path, name, children, className = 'secondary' }: { path: string; name: string; children: ReactNode; className?: string }) {
  const [busy, setBusy] = useState(false); const [error, setError] = useState('')
  async function run() { setBusy(true); setError(''); try { await download(path, name) } catch (e) { setError((e as Error).message) } finally { setBusy(false) } }
  return <span className="download-wrap"><button className={`button ${className}`} disabled={busy} onClick={run}>{busy ? <LoaderCircle size={16} className="spin" /> : <Download size={16} />}{children}</button>{error && <span role="alert" className="inline-error">{error}</span>}</span>
}
export function SourceButton({ source, onOpen, children }: { source: SourceRef; onOpen: (source: SourceRef) => void; children?: ReactNode }) { return <button className="source-button" onClick={() => onOpen(source)}><FileText size={14} />{children || `Source · v${source.version} · p${source.page}`}<ArrowUpRight size={13} /></button> }
export function SourceDrawer({ source, close, snapshotId }: { source: SourceRef; close: () => void; snapshotId?: string }) {
  const { data, error, loading } = useResource<Evidence>(snapshotId ? '' : `/evidence/${source.evidenceId}`)
  const page = data?.pages?.[source.page - 1]
  const text = typeof page === 'string' ? page : page?.text || data?.text || data?.excerpt || source.excerpt
  return <Modal title="Source evidence" close={close} className="source-drawer"><div className="modal-body">
    {snapshotId ? <><Badge>Shared source · v{source.version} · page {source.page}</Badge><h3>Evidence in this shared package</h3>{source.excerpt && <blockquote>{source.excerpt}</blockquote>}<p className="muted">The package manifest records the source version. An original file is available only if the grantee explicitly included it.</p><DownloadButton path={`/shared-reports/${snapshotId}/attachments/${source.evidenceId}`} name={`source-${source.evidenceId}`}>Download included source</DownloadButton></> : loading ? <Loading text="Opening source…" /> : error ? <Notice>{error}</Notice> : data && <><Badge>Version {source.version} · page {source.page}</Badge><h3>{data.name}</h3>{data.version !== source.version && <Notice>This record is now version {data.version}. The cited version is {source.version}; verify the version before using this source.</Notice>}<div className="source-meta"><span>{label(data.kind)}</span><span>{date(data.createdAt)}</span><span>{data.pageCount} pages</span></div><div className="source-text">{text || 'No text is available for this source.'}</div><p className="muted tiny">Source text supports your review; a citation does not establish that a proposed interpretation is correct.</p><details><summary>Document fingerprint</summary><code className="fingerprint">{data.sha256}</code></details><DownloadButton path={`/evidence/${data.id}/download`} name={data.name}>Download evidence</DownloadButton></>}
  </div></Modal>
}
export function JobsPanel({ jobs, run, busy = false }: { jobs: Job[]; run?: () => void; busy?: boolean }) {
  const [currentJobs, setCurrentJobs] = useState(jobs)
  const [pollError, setPollError] = useState('')
  useEffect(() => { setCurrentJobs(jobs) }, [jobs])
  const running = currentJobs.some(job => ['queued', 'running'].includes(job.status))
  useEffect(() => {
    if (!running) return
    let active = true
    const timer = setInterval(() => { api<Job[]>('/jobs').then(value => { if (active) { setCurrentJobs(value); setPollError('') } }).catch(e => { if (active) setPollError(e.message) }) }, 3000)
    return () => { active = false; clearInterval(timer) }
  }, [running])
  return <section className="panel job-panel"><SectionHeading title="Agent activity" detail="Persisted runs and the tools they used." action={run && <button className="button secondary small" disabled={busy} onClick={run}><RefreshCw size={14} className={busy ? 'spin' : ''} />Run review</button>} />
    {pollError && <Notice>{pollError}</Notice>}{!currentJobs.length ? <p className="muted">No agent runs yet. Import evidence or start a review to create one.</p> : [...currentJobs].reverse().slice(0, 5).map(job => <details className="job" key={job.id}><summary><span className="job-title"><span className={`status-dot ${job.status}`} /><strong>{job.status === 'unavailable' ? 'Agent unavailable' : 'Portfolio reconciliation'}</strong></span><Status value={job.status} /><ChevronRight size={16} /></summary><div className="job-content"><p>{job.message || 'Waiting for the worker to process this job.'}</p><p className="tiny muted">{job.engine} · {dateTime(job.createdAt)} Bucharest{job.finishedAt ? ` · finished ${dateTime(job.finishedAt)}` : ""} · input version {job.inputVersion}</p>{job.toolEvents?.length ? <ol className="tool-events">{job.toolEvents.map((event, i) => <li key={i}><strong>{event.name}</strong><span className="tiny muted"> · {dateTime(event.at)}</span><pre>{typeof event.result === 'string' ? event.result : JSON.stringify(event.result, null, 2)}</pre></li>)}</ol> : <p className="muted tiny">No completed tool calls recorded.</p>}</div></details>)}
  </section>
}
