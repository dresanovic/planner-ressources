import { useCallback, useEffect, useState } from 'react'

import {
  HolidayCalendarApiError,
  createHoliday,
  deleteHoliday,
  listHolidays,
  updateHoliday,
  type HolidayRecord,
} from '../api/holidayCalendar'

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
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not load holidays.')
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
      .catch((reason) => {
        if (current) setError(reason instanceof Error ? reason.message : 'Could not load holidays.')
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
      setError('Enter a date and holiday name.')
      return
    }
    setBusy(true)
    setError('')
    try {
      if (selected) await updateHoliday(selected.id, { date, name, expectedRevision: selected.revision })
      else await createHoliday({ date, name })
      onChanged()
      await load()
      setMessage(selected ? 'Holiday updated.' : 'Holiday created.')
      resetForm()
    } catch (reason) {
      const apiError = reason instanceof HolidayCalendarApiError ? reason.errors[0]?.message : undefined
      setError(apiError ?? (reason instanceof Error ? reason.message : 'Could not save the holiday.'))
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
      setMessage('Holiday removed.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not remove the holiday.')
      setRemoving(null)
      if (reason instanceof HolidayCalendarApiError && reason.status === 409) await load(false)
    } finally {
      setBusy(false)
    }
  }

  return <>
    <section className="workbench">
      <header className="page-header"><div><p className="eyebrow">Planner administration</p><h1>Academic Data</h1></div></header>
      {message && <p role="status">{message}</p>}
      {error && <div><p role="alert">{error}</p><button type="button" className="secondary-button" disabled={busy || loading} onClick={() => void load()}>Retry holidays</button></div>}
      <div className="catalog-grid">
        <section className="planner-panel" aria-labelledby="holiday-list-title">
          <h2 id="holiday-list-title">Holidays</h2>
          {loading ? <p>Loading…</p> : holidays.length === 0 ? <p>No holidays yet</p> : (
            <ul className="catalog-list">
              {holidays.map((holiday) => <li key={holiday.id} className="catalog-list-item">
                <div><strong>{holiday.name}</strong><div>{holiday.date}</div></div>
                <div><button type="button" className="secondary-button" onClick={() => beginEdit(holiday)}>Edit</button><button type="button" className="destructive-button" onClick={() => setRemoving(holiday)}>Delete</button></div>
              </li>)}
            </ul>
          )}
        </section>
        <section className="planner-panel" aria-labelledby="holiday-editor-title">
          <h2 id="holiday-editor-title">{selected ? 'Edit holiday' : 'Create holiday'}</h2>
          <label className="catalog-field"><span>Date</span><input type="date" value={date} onChange={(event) => setDate(event.target.value)} /></label>
          <label className="catalog-field"><span>Name</span><input name="holiday-name" maxLength={200} value={name} onChange={(event) => setName(event.target.value)} /></label>
          <button type="button" className="generate-button" disabled={busy} onClick={() => void save()}>{selected ? 'Save changes' : 'Create holiday'}</button>
          {selected && <button type="button" className="secondary-button" disabled={busy} onClick={resetForm}>Cancel edit</button>}
        </section>
      </div>
    </section>
    {removing && <div className="dialog-backdrop"><section role="dialog" aria-modal="true" aria-labelledby="remove-holiday-title" className="confirmation-dialog">
      <h2 id="remove-holiday-title">Remove holiday?</h2>
      <p>{removing.name} on {removing.date} will stop constraining future generation. Saved sessions will not be changed.</p>
      <button type="button" className="destructive-button" disabled={busy} onClick={() => void confirmRemove()}>Remove holiday</button>
      <button type="button" className="secondary-button" disabled={busy} onClick={() => setRemoving(null)}>Cancel</button>
    </section></div>}
  </>
}
