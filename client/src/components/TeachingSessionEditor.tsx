import type { SessionEditFailure } from '../api/draftSchedule'
import {
  derivedLengthLabel,
  resourceLabel,
  type EditableDraftSessionRequest,
  type TeachingSessionEditModel,
} from './sessionEditModel'
import { label } from '../config/terminology'
import { EuropeanDateField } from './EuropeanDateField'

type Props = {
  session: TeachingSessionEditModel
  draft: EditableDraftSessionRequest
  isSaving: boolean
  isDisabled: boolean
  errors: SessionEditFailure[]
  onChange: (draft: EditableDraftSessionRequest) => void
  onCancel: () => void
  onSave: () => void
}

export function TeachingSessionEditor({
  session,
  draft,
  isSaving,
  isDisabled,
  errors,
  onChange,
  onCancel,
  onSave,
}: Props) {
  const availableLecturers = session.eligibleLecturers.length > 0
    ? session.eligibleLecturers
    : [session.lecturer]
  const availableRooms = session.eligibleRooms.length > 0
    ? session.eligibleRooms
    : [{ ...session.room, capacity: session.context.cohortSize }]

  return (
    <form className="session-edit-fields" onSubmit={(event) => { event.preventDefault(); onSave() }}>
      <EuropeanDateField id={`teaching-date-${session.id}`} className="inline-edit-field" label="Datum" autoFocus value={draft.date} disabled={isDisabled} onChange={(value) => onChange({ ...draft, date: value ?? '' })} required />
      <label className="inline-edit-field">
        <span>Beginn</span>
        <input type="time" value={draft.startTime} disabled={isDisabled} onChange={(event) => onChange({ ...draft, startTime: event.target.value })} />
      </label>
      <label className="inline-edit-field">
        <span>Ende</span>
        <input type="time" value={draft.endTime} disabled={isDisabled} onChange={(event) => onChange({ ...draft, endTime: event.target.value })} />
      </label>
      <span>{derivedLengthLabel(draft.startTime, draft.endTime)}</span>
      <span>{session.context.course.name}</span>
      <span>{session.context.cohort.name}</span>
      <label className="lecturer-edit-field">
        <span>{label('lecturer.fieldLabel')}</span>
        <select value={draft.lecturerId} disabled={isDisabled} onChange={(event) => onChange({ ...draft, lecturerId: Number(event.target.value) })}>
          {availableLecturers.map((lecturer) => <option value={lecturer.id} key={lecturer.id}>{resourceLabel(lecturer)}</option>)}
        </select>
      </label>
      <label className="inline-edit-field">
        <span>{label('room.fieldLabel')}</span>
        <select value={draft.roomId} disabled={isDisabled} onChange={(event) => onChange({ ...draft, roomId: Number(event.target.value) })}>
          {availableRooms.map((room) => (
            <option value={room.id} key={room.id}>
              {resourceLabel(room)}{room.capacity ? ` (${room.capacity} Plätze)` : ''}
            </option>
          ))}
        </select>
      </label>
      <div className="edit-actions">
        <button type="submit" disabled={isSaving || isDisabled}>Speichern</button>
        <button type="button" className="secondary-button" onClick={onCancel} disabled={isSaving}>Abbrechen</button>
        {errors.length > 0 && (
          <div className="inline-error" role="alert">
            {errors.map((error) => <span key={error.code}>Der Termin konnte nicht gespeichert werden. Prüfen Sie die markierten Angaben; Ihre Eingaben bleiben erhalten.</span>)}
          </div>
        )}
      </div>
    </form>
  )
}
