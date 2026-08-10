import { useState, type FormEvent } from 'react'
import type { UnavailabilityInput, UnavailabilityPeriod } from '../api/resourceCatalog'
import { formatUnavailabilityPeriod } from '../utils/resourceAvailability'
import { WEEKDAY_NAMES } from '../utils/weekdays'
import { EuropeanDateField } from './EuropeanDateField'

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
    } catch { setError('Der Abwesenheitszeitraum konnte nicht gespeichert werden. Ihre Eingaben bleiben erhalten; prüfen Sie die Werte und versuchen Sie es erneut.') }
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
    } catch {
      setError('Der Abwesenheitszeitraum konnte nicht gelöscht werden. Laden Sie den aktuellen Stand neu und prüfen Sie den Eintrag vor einem weiteren Versuch.')
    }
  }

  return <section className="resource-availability"><h3>Nichtverfügbarkeitszeiträume</h3>
    {periods.length === 0 ? <p>Keine Nichtverfügbarkeitszeiträume vorhanden.</p> : <ul className="availability-list">{ordered(periods).map((period) => <li key={period.id}><span>{formatUnavailabilityPeriod(period)}</span><span className="catalog-record-actions"><button type="button" className="secondary-button compact-button" onClick={() => edit(period)}>Bearbeiten</button><button type="button" className="secondary-button compact-button" onClick={() => { if (window.confirm('Diesen Nichtverfügbarkeitszeitraum löschen?')) void remove(period) }}>Löschen</button></span></li>)}</ul>}
    <form className="catalog-editor" onSubmit={(event) => void submit(event)}>
      <label className="catalog-field">Art<select value={kind} onChange={(event) => setKind(event.target.value as typeof kind)}><option value="recurring">Wöchentlich wiederkehrend</option><option value="dated">Datumsbezogen</option></select></label>
      {kind === 'recurring' ? <fieldset><legend>Wochentage</legend><div className="weekday-options">{WEEKDAY_NAMES.map((name, day) => <label key={name}><input type="checkbox" checked={weekdays.includes(day)} onChange={() => setWeekdays((current) => current.includes(day) ? current.filter((value) => value !== day) : [...current, day].sort())} />{name}</label>)}</div></fieldset> : <div className="availability-dates"><EuropeanDateField id="availability-start" className="catalog-field" label="Beginn" value={startDate} onChange={(value) => setStartDate(value ?? '')} required /><EuropeanDateField id="availability-end" className="catalog-field" label="Ende" value={endDate} onChange={(value) => setEndDate(value ?? '')} min={startDate || undefined} required /></div>}
      <div className="availability-times"><label className="catalog-field">Beginn<input type="time" value={startTime} onChange={(event) => setStartTime(event.target.value)} /></label><label className="catalog-field">Ende<input type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} /></label></div>
      {error && <p role="alert">{error}</p>}
      <button type="submit">{editing ? 'Nichtverfügbarkeitszeitraum speichern' : 'Nichtverfügbarkeitszeitraum hinzufügen'}</button>
    </form>
  </section>
}
