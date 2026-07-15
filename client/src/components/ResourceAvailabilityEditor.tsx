import { useState, type FormEvent } from 'react'
import type { UnavailabilityInput, UnavailabilityPeriod } from '../api/resourceCatalog'
import { formatUnavailabilityPeriod } from '../utils/resourceAvailability'
import { WEEKDAY_NAMES } from '../utils/weekdays'

function ordered(periods: UnavailabilityPeriod[]) {
  return [...periods].sort((left, right) => {
    const leftKey = left.kind === 'recurring' ? `0-${Math.min(...left.weekdays)}-${left.startTime}` : `1-${left.startDate}-${left.startTime}`
    const rightKey = right.kind === 'recurring' ? `0-${Math.min(...right.weekdays)}-${right.startTime}` : `1-${right.startDate}-${right.startTime}`
    return leftKey.localeCompare(rightKey) || left.id - right.id
  })
}

export function ResourceAvailabilityEditor({ periods, onCreate, onUpdate, onDelete }: {
  periods: UnavailabilityPeriod[]
  onCreate: (input: UnavailabilityInput) => Promise<unknown>
  onUpdate: (periodId: number, input: UnavailabilityInput & { expectedRevision: number }) => Promise<unknown>
  onDelete: (period: UnavailabilityPeriod) => Promise<unknown>
}) {
  const [kind, setKind] = useState<'recurring' | 'dated'>('recurring')
  const [weekdays, setWeekdays] = useState<number[]>([])
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [startTime, setStartTime] = useState('')
  const [endTime, setEndTime] = useState('')
  const [editing, setEditing] = useState<UnavailabilityPeriod | null>(null)
  const [error, setError] = useState('')

  function input(): UnavailabilityInput {
    return kind === 'recurring' ? { kind, weekdays, startTime, endTime } : { kind, startDate, startTime, endDate, endTime }
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setError('')
    try {
      if (editing) await onUpdate(editing.id, { ...input(), expectedRevision: editing.revision })
      else await onCreate(input())
      setEditing(null); setWeekdays([]); setStartDate(''); setEndDate(''); setStartTime(''); setEndTime('')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save unavailable period.') }
  }

  function edit(period: UnavailabilityPeriod) {
    setEditing(period); setKind(period.kind); setStartTime(period.startTime); setEndTime(period.endTime); setError('')
    if (period.kind === 'recurring') { setWeekdays(period.weekdays); setStartDate(''); setEndDate('') }
    else { setWeekdays([]); setStartDate(period.startDate); setEndDate(period.endDate) }
  }

  async function remove(period: UnavailabilityPeriod) {
    setError('')
    try {
      await onDelete(period)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not delete unavailable period.')
    }
  }

  return <section className="resource-availability"><h3>Unavailable periods</h3>
    {periods.length === 0 ? <p>No unavailable periods.</p> : <ul className="availability-list">{ordered(periods).map((period) => <li key={period.id}><span>{formatUnavailabilityPeriod(period)}</span><span className="catalog-record-actions"><button type="button" className="secondary-button compact-button" onClick={() => edit(period)}>Edit</button><button type="button" className="secondary-button compact-button" onClick={() => { if (window.confirm('Delete this unavailable period?')) void remove(period) }}>Delete</button></span></li>)}</ul>}
    <form className="catalog-editor" onSubmit={(event) => void submit(event)}>
      <label className="catalog-field">Type<select value={kind} onChange={(event) => setKind(event.target.value as typeof kind)}><option value="recurring">Recurring weekly</option><option value="dated">Dated</option></select></label>
      {kind === 'recurring' ? <fieldset><legend>Weekdays</legend><div className="weekday-options">{WEEKDAY_NAMES.map((name, day) => <label key={name}><input type="checkbox" checked={weekdays.includes(day)} onChange={() => setWeekdays((current) => current.includes(day) ? current.filter((value) => value !== day) : [...current, day].sort())} />{name}</label>)}</div></fieldset> : <div className="availability-dates"><label className="catalog-field">Start date<input type="date" value={startDate} onChange={(event) => setStartDate(event.target.value)} /></label><label className="catalog-field">End date<input type="date" value={endDate} onChange={(event) => setEndDate(event.target.value)} /></label></div>}
      <div className="availability-times"><label className="catalog-field">Start time<input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} /></label><label className="catalog-field">End time<input type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} /></label></div>
      {error && <p role="alert">{error}</p>}
      <button type="submit">{editing ? 'Save unavailable period' : 'Add unavailable period'}</button>
    </form>
  </section>
}
