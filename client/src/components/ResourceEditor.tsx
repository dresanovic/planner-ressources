import { useState, type FormEvent } from 'react'
import type { LecturerInput, ResourceRecord, ResourceType, RoomInput } from '../api/resourceCatalog'
import { label } from '../config/terminology'

export function ResourceEditor({ resourceType, initial, onSubmit, onCancel }: {
  resourceType: ResourceType
  initial?: ResourceRecord | null
  onSubmit: (input: LecturerInput | RoomInput) => Promise<unknown>
  onCancel: () => void
}) {
  const [name, setName] = useState(initial?.name ?? '')
  const [referenceCode, setReferenceCode] = useState(initial?.referenceCode ?? '')
  const [capacity, setCapacity] = useState('capacity' in (initial ?? {}) ? String((initial as { capacity: number }).capacity) : '')
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault(); setSaving(true); setError('')
    try {
      const base = { name, referenceCode }
      await onSubmit(resourceType === 'rooms' ? { ...base, capacity: Number(capacity) } : base)
      if (!initial) { setName(''); setReferenceCode(''); setCapacity('') }
    } catch {
      setError(`Die Ressource „${name || referenceCode}“ konnte nicht gespeichert werden. Ihre Eingaben bleiben erhalten; prüfen Sie die Felder und versuchen Sie es erneut.`)
    } finally { setSaving(false) }
  }

  const singular = label(resourceType === 'rooms' ? 'room.singular' : 'lecturer.singular')
  return <form className="catalog-editor" onSubmit={(event) => void submit(event)}>
    <label className="catalog-field">Name<input name="name" value={name} maxLength={200} onChange={(event) => setName(event.target.value)} /></label>
    <label className="catalog-field">Referenzcode<input name="referenceCode" value={referenceCode} maxLength={100} onChange={(event) => setReferenceCode(event.target.value)} /></label>
    {resourceType === 'rooms' && <label className="catalog-field">Kapazität<input name="capacity" type="number" min="1" step="1" value={capacity} onChange={(event) => setCapacity(event.target.value)} /></label>}
    {error && <p role="alert">{error}</p>}
    <div className="dialog-actions"><button type="button" className="secondary-button" onClick={onCancel}>Abbrechen</button><button type="submit" disabled={saving}>{initial ? `${singular} speichern` : `${singular} erstellen`}</button></div>
  </form>
}
