import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { ArrowRight, CalendarDays, Clock3, History, Info, LoaderCircle } from 'lucide-react'
import { api } from './api'
import { Badge, date, Empty, Loading, Notice, PageHeading, ResourceError, SectionHeading, useResource } from './components'
import type { Grant, ResponseEstimate } from './types'

function utcDate(daysAgo = 0) {
  const value = new Date()
  value.setUTCDate(value.getUTCDate() - daysAgo)
  return value.toISOString().slice(0, 10)
}
function daysRange(low: number, high: number) { return low === high ? String(low) : `${low}–${high}` }

export function ResponseEstimatesPage({ revision }: { revision: number }) {
  const grants = useResource<Grant[]>('/grants', revision)
  const [grantId, setGrantId] = useState('')
  const [submittedDate, setSubmittedDate] = useState(() => utcDate(7))
  const [result, setResult] = useState<ResponseEstimate | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const requestId = useRef(0)
  const selectedGrant = grants.data?.find(grant => grant.id === grantId) || grants.data?.[0]

  useEffect(() => {
    requestId.current++
    setResult(null); setBusy(false); setError('')
  }, [revision])
  useEffect(() => () => { requestId.current++ }, [])

  function invalidate() {
    // Advance synchronously during edits, before an older request can settle.
    requestId.current++
    setResult(null); setError(''); setBusy(false)
  }
  async function estimate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!selectedGrant || !submittedDate) return
    const currentRequest = ++requestId.current
    const scenario = { grantId: selectedGrant.id, submittedDate }
    setBusy(true); setError(''); setResult(null)
    try {
      const response = await api<ResponseEstimate>('/response-estimates', scenario)
      if (requestId.current !== currentRequest) return
      if (response.grantId !== scenario.grantId || response.submittedDate !== scenario.submittedDate || response.simulated !== true) {
        throw new Error('The estimate did not match this simulated scenario. Please try again.')
      }
      setResult(response)
    } catch (failure) {
      if (requestId.current === currentRequest) setError((failure as Error).message)
    } finally {
      if (requestId.current === currentRequest) setBusy(false)
    }
  }

  if (grants.loading && !grants.data) return <Loading text="Loading your grants…" />
  if (grants.error) return <ResourceError error={grants.error} retry={grants.reload} />

  return <>
    <PageHeading eyebrow="PLANNING A FOLLOW-UP" title="A little context for the wait." action={<Badge tone="warning">Simulated review history</Badge>}>
      Explore an unanswered submission scenario using fictional funder review durations.
    </PageHeading>
    <div className="estimate-layout">
      <section className="panel estimate-form-panel">
        <SectionHeading title="Your scenario" detail="This calculation does not submit a report or change your records." />
        {!grants.data?.length ? <Empty title="No grants available">A grant in your organisation is needed to choose the relevant simulated funder history.</Empty> :
          <form className="form-stack" onSubmit={estimate}>
            <label htmlFor="estimate-grant">Grant
              <select id="estimate-grant" required value={selectedGrant?.id || ''} onChange={event => { invalidate(); setGrantId(event.target.value) }}>
                {grants.data.map(grant => <option key={grant.id} value={grant.id}>{grant.name}</option>)}
              </select>
            </label>
            <p className="estimate-funder"><span>Funder</span><strong>{selectedGrant?.funderName}</strong></p>
            <label htmlFor="estimate-submitted">Date submitted
              <input id="estimate-submitted" type="date" required max={utcDate()} value={submittedDate} aria-describedby="estimate-date-help" onChange={event => { invalidate(); setSubmittedDate(event.target.value) }} />
            </label>
            <p className="tiny muted" id="estimate-date-help">Choose the date for this unanswered scenario. The calculation counts calendar days using the server’s UTC date.</p>
            {error && <Notice>{error}</Notice>}
            <button className="button primary full" disabled={busy || !selectedGrant || !submittedDate}>
              {busy ? <LoaderCircle size={17} className="spin" /> : <Clock3 size={17} />}
              {busy ? 'Calculating estimate…' : 'Estimate response'}
            </button>
          </form>}
        <div className="estimate-disclosure"><Info size={17} /><p>The history is simulated. These results describe an illustrative scenario, not this funder’s actual turnaround.</p></div>
      </section>
      <div className="estimate-result-region" aria-live="polite" aria-atomic="false" aria-busy={busy}>
        {busy ? <section className="panel"><Loading text="Comparing this wait with simulated reviews…" /></section> : result ? <EstimateResult result={result} /> :
          <section className="panel estimate-placeholder"><span className="estimate-placeholder-icon"><CalendarDays size={28} /></span><h2>Start with a grant and a date.</h2><p>See a remaining response range, the calendar dates it corresponds to and the fictional history behind it.</p><p className="tiny muted">Changing either input clears the previous estimate. Calculate again to review the new scenario.</p></section>}
      </div>
    </div>
    <div className="informational-strip"><History size={20} /><div><strong>How the comparison works</strong><p>The estimate uses completed simulated reviews that took longer than you have already waited. The range is illustrative, not a promised deadline.</p></div></div>
  </>
}

function EstimateResult({ result }: { result: ResponseEstimate }) {
  const estimated = result.status === 'estimated' && result.remainingDays && result.expectedDates
  return <section className="panel estimate-result">
    <div className="estimate-result-heading"><div><div className="eyebrow">{result.funderName}</div><h2>{result.grantName}</h2></div><Badge tone="warning">Simulated estimate</Badge></div>
    <p className="estimate-asof">Scenario submitted {date(result.submittedDate)} · calculated as of {date(result.asOfDate)} (UTC)</p>
    {estimated ? <>
      <div className="estimate-range"><span>Illustrative remaining wait</span><strong>{daysRange(result.remainingDays!.low, result.remainingDays!.high)}<small>more calendar days</small></strong><p>Typical remaining wait in the matching samples: <b>{result.remainingDays!.typical} calendar days</b>.</p></div>
      <div className="estimate-dates"><CalendarDays size={20} /><div><span>Illustrative response dates</span><strong>{date(result.expectedDates!.earliest)}<span className="estimate-date-separator">to</span>{date(result.expectedDates!.latest)}</strong><small>Matching-sample median: {date(result.expectedDates!.typical)}</small></div></div>
    </> : <div className="estimate-unavailable"><Clock3 size={25} /><h3>{result.status === 'beyond_history' ? 'This wait has reached or passed the longest simulated review.' : 'There is too little matching history for a range.'}</h3><p>{result.status === 'beyond_history' ? 'None of the completed simulated reviews took longer than the time already elapsed. This history cannot support a remaining response date.' : 'At least three matching simulated reviews are needed to show a remaining response range. The available sample is too small.'}</p><p className="estimate-followup">{result.status === 'beyond_history' ? 'Check the funder’s published review schedule and consider a brief follow-up through your usual contact.' : 'Use the funder’s published review schedule or ask your usual contact about the expected timing.'}</p></div>}
    <dl className="estimate-facts">
      <div><dt>Already elapsed</dt><dd>{result.elapsedDays}<small>calendar days</small></dd></div>
      <div><dt>Historical median total</dt><dd>{result.typicalTotalDays === null ? 'Not available' : result.typicalTotalDays}<small>{result.typicalTotalDays === null ? 'No baseline recorded' : 'calendar days from submission'}</small></dd></div>
      <div><dt>Completed simulated reviews</dt><dd>{result.sampleCount}<small>samples in the full history</small></dd></div>
      <div><dt>Matching this unanswered wait</dt><dd>{result.comparableSampleCount}<small>reviews longer than {result.elapsedDays} days</small></dd></div>
    </dl>
    <p className="estimate-historical-range">{result.historicalRangeDays ? <>Historical middle range: <strong>{daysRange(result.historicalRangeDays.low, result.historicalRangeDays.high)} calendar days total</strong>.</> : 'No historical duration range is available.'} The historical baseline includes every completed simulated review.</p>
    <details className="estimate-history"><summary><History size={16} /><span>Inspect the simulated durations ({result.historyDays.length})</span><ArrowRight size={15} /></summary><div><p>Each number is the total duration of one fictional completed review, in calendar days. Highlighted samples took longer than the {result.elapsedDays} days already elapsed.</p>{result.historyDays.length ? <ul aria-label="Simulated review durations in calendar days">{result.historyDays.map((duration, index) => <li key={index} className={duration > result.elapsedDays ? 'matching' : ''}>{duration}<span className="sr-only"> calendar days{duration > result.elapsedDays ? ', matching this unanswered scenario' : ', shorter than or equal to the elapsed wait'}</span></li>)}</ul> : <p className="muted">No completed simulated reviews are available for this funder.</p>}<p className="tiny muted">The displayed ranges use the middle half of the corresponding simulated durations. All figures are calculated from this history; no live model or funder service is queried.</p></div></details>
  </section>
}
