import { useCallback, useEffect, useState } from 'react'

import {
  HolidayCalendarApiError,
  createHoliday,
  deleteHoliday,
  listHolidays,
  updateHoliday,
  type HolidayRecord,
} from '../api/holidayCalendar'
import { EuropeanDateField } from './EuropeanDateField'
import { label } from '../config/terminology'
import { formatCalendarDate } from '../utils/datePresentation'

export function HolidayAdministration({ onChanged }: { onChanged: () => void }) {
  const [holidays, setHolidays] = useState<HolidayRecord[]>([])
  const [selected, setSelected] = useState<HolidayRecord | null>(null)
  const [removing, setRemoving] = useState<HolidayRecord | null>(null)
  const [date, setDate] = useState('')
  const [name, setName] = useState('')
  const [loading, setLoading] = useState(true)
  const [busy, setBusy] = useState(false)
  const [message, setMessage] = useState('')
  const [error, setError] = useState('')

  const load = useCallback(async (clearError = true): Promise<HolidayRecord[] | null> => {
    setLoading(true)
    try {
      const items = await listHolidays()
      setHolidays(items)
      if (clearError) setError('')
      return items
    } catch {
      setError('Die Feiertage konnten nicht geladen werden. Prüfen Sie die Verbindung und versuchen Sie es erneut.')
      return null
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    let current = true
    void listHolidays()
      .then((items) => {
        if (!current) return
        setHolidays(items)
        setError('')
      })
      .catch(() => {
        if (current) setError('Die Feiertage konnten nicht geladen werden. Prüfen Sie die Verbindung und versuchen Sie es erneut.')
      })
      .finally(() => {
        if (current) setLoading(false)
      })
    return () => { current = false }
  }, [])

  function beginEdit(holiday: HolidayRecord) {
    setSelected(holiday)
    setDate(holiday.date)
    setName(holiday.name)
    setError('')
  }

  function resetForm() {
    setSelected(null)
    setDate('')
    setName('')
  }

  async function save() {
    if (!date || !name.trim()) {
      setError('Geben Sie ein Datum im Format TT.MM.JJJJ und einen Namen für den Feiertag ein.')
      return
    }
    setBusy(true)
    setError('')
    try {
      if (selected) await updateHoliday(selected.id, { date, name, expectedRevision: selected.revision })
      else await createHoliday({ date, name })
      onChanged()
      await load()
      setMessage(selected ? 'Feiertag aktualisiert.' : 'Feiertag erstellt.')
      resetForm()
    } catch (reason) {
      setError(reason instanceof HolidayCalendarApiError
        ? 'Der Feiertag konnte wegen ungültiger Angaben nicht gespeichert werden. Prüfen Sie Datum und Name; Ihre Eingaben bleiben erhalten.'
        : 'Der Feiertag konnte nicht gespeichert werden. Die genaue Ursache ist nicht verfügbar; Ihre Eingaben bleiben erhalten.')
      if (reason instanceof HolidayCalendarApiError && reason.status === 409 && selected) {
        const items = await load(false)
        const current = items?.find((holiday) => holiday.id === selected.id)
        if (current) setSelected(current)
        else if (items) setSelected(null)
      }
    } finally {
      setBusy(false)
    }
  }

  async function confirmRemove() {
    if (!removing) return
    setBusy(true)
    setError('')
    try {
      await deleteHoliday(removing.id, removing.revision, true)
      onChanged()
      await load()
      setRemoving(null)
      if (selected?.id === removing.id) resetForm()
      setMessage('Feiertag entfernt.')
    } catch (reason) {
      setError('Der Feiertag konnte nicht entfernt werden. Laden Sie den aktuellen Stand neu und prüfen Sie den Eintrag vor einem weiteren Versuch.')
      setRemoving(null)
      if (reason instanceof HolidayCalendarApiError && reason.status === 409) await load(false)
    } finally {
      setBusy(false)
    }
  }

  return <>
    <section className="workbench">
      <header className="page-header"><div><p className="eyebrow">Planungsverwaltung</p><h1>{label('academicData.heading')}</h1></div></header>
      {message && <p role="status">{message}</p>}
      {error && <div><p role="alert">{error}</p><button type="button" className="secondary-button" disabled={busy || loading} onClick={() => void load()}>Feiertage erneut laden</button></div>}
      <div className="catalog-grid">
        <section className="planner-panel" aria-labelledby="holiday-list-title">
          <h2 id="holiday-list-title">Feiertage</h2>
          {loading ? <p>Wird geladen…</p> : holidays.length === 0 ? <p>Noch keine Feiertage vorhanden.</p> : (
            <ul className="catalog-list">
              {holidays.map((holiday) => <li key={holiday.id} className="catalog-list-item">
                <div><strong>{holiday.name}</strong><div>{formatCalendarDate(holiday.date)}</div></div>
                <div><button type="button" className="secondary-button" onClick={() => beginEdit(holiday)}>Bearbeiten</button><button type="button" className="destructive-button" onClick={() => setRemoving(holiday)}>Löschen</button></div>
              </li>)}
            </ul>
          )}
        </section>
        <form className="planner-panel" aria-labelledby="holiday-editor-title" onSubmit={(event) => { event.preventDefault(); void save() }}>
          <h2 id="holiday-editor-title">{selected ? 'Feiertag bearbeiten' : 'Feiertag erstellen'}</h2>
          <EuropeanDateField id="holiday-date" className="catalog-field" label="Datum" value={date} onChange={(value) => setDate(value ?? '')} required />
          <label className="catalog-field"><span>Name</span><input name="holiday-name" maxLength={200} value={name} onChange={(event) => setName(event.target.value)} /></label>
          <button type="submit" className="generate-button" disabled={busy}>{selected ? 'Änderungen speichern' : 'Feiertag erstellen'}</button>
          {selected && <button type="button" className="secondary-button" disabled={busy} onClick={resetForm}>Bearbeitung abbrechen</button>}
        </form>
      </div>
    </section>
    {removing && <div className="dialog-backdrop"><section role="dialog" aria-modal="true" aria-labelledby="remove-holiday-title" className="confirmation-dialog">
      <h2 id="remove-holiday-title">Feiertag entfernen?</h2>
      <p>Der Feiertag „{removing.name}“ am {formatCalendarDate(removing.date)} wird bei zukünftigen Planungen nicht mehr berücksichtigt. Bereits gespeicherte Termine bleiben unverändert.</p>
      <button type="button" className="destructive-button" disabled={busy} onClick={() => void confirmRemove()}>Feiertag entfernen</button>
      <button type="button" className="secondary-button" disabled={busy} onClick={() => setRemoving(null)}>Abbrechen</button>
    </section></div>}
  </>
}
