import { useState } from 'react'
import type { CourseResourceCandidate, CourseResourceConfiguration } from '../api/resourceCatalog'
import { formatUnavailabilityPeriod } from '../utils/resourceAvailability'
import { label } from '../config/terminology'
import { safeReasonText } from '../utils/userProblems'

function CandidateGroup({ title, candidates, selected, cohortSize, onToggle }: { title: string; candidates: CourseResourceCandidate[]; selected: number[]; cohortSize: number; onToggle: (id: number) => void }) {
  const [query, setQuery] = useState('')
  const visible = candidates.filter((candidate) => `${candidate.name} ${candidate.referenceCode}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()))
  return <fieldset className="eligibility-group"><legend>{title}</legend><label className="catalog-field">Suchen<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div className="eligibility-candidates">{visible.map((candidate) => {
    const isSelected = selected.includes(candidate.id)
    const disabled = !isSelected && !candidate.isUsable
    const usage = candidate.courseSessionUsage
    return <div key={candidate.id} className={!candidate.isUsable ? 'candidate-invalid' : ''}>
      <label><input type="checkbox" value={candidate.id} checked={isSelected} disabled={disabled} onChange={() => onToggle(candidate.id)} /><span><strong>{candidate.name} · {candidate.referenceCode}</strong>{candidate.kind === 'room' && <small>Kapazität {candidate.capacity} · benötigt {cohortSize}</small>}{candidate.reasons.length > 0 && <ul>{candidate.reasons.map((reason, index) => <li key={`${candidate.id}-reason-${index}`}>{safeReasonText(reason, candidate.name)}</li>)}</ul>}</span></label>
      <small>{usage.draftSessionCount} gespeicherte Termine in {usage.draftScheduleCount} Planungen für diese {label('course.singular')}.</small>
      {candidate.unavailabilityPeriods.length > 0 && <details><summary>{candidate.unavailabilityPeriods.length} Nichtverfügbarkeitszeiträume</summary><ul>{candidate.unavailabilityPeriods.map((period) => <li key={period.id}>{formatUnavailabilityPeriod(period)}</li>)}</ul></details>}
    </div>
  })}</div></fieldset>
}

export function CourseResourceEligibilityEditor({ configuration, onSave, onCancel }: { configuration: CourseResourceConfiguration; onSave: (value: { expectedRevision: number; lecturerIds: number[]; roomIds: number[] }) => Promise<unknown> | unknown; onCancel: () => void }) {
  const [lecturerIds, setLecturerIds] = useState(configuration.eligibleLecturerIds)
  const [roomIds, setRoomIds] = useState(configuration.eligibleRoomIds)
  const [error, setError] = useState('')
  const toggle = (values: number[], id: number, set: (value: number[]) => void) => set(values.includes(id) ? values.filter((value) => value !== id) : [...values, id].sort((a, b) => a - b))
  async function save() {
    if (!lecturerIds.length || !roomIds.length) { setError(`Wählen Sie mindestens eine geeignete ${label('lecturer.singular')} und einen geeigneten ${label('room.singular')} aus.`); return }
    try { setError(''); await onSave({ expectedRevision: configuration.courseRevision, lecturerIds, roomIds }) } catch { setError('Die Ressourcenzuordnung konnte nicht gespeichert werden. Ihre Auswahl bleibt erhalten; laden Sie den aktuellen Stand neu und prüfen Sie die Zuordnung.') }
  }
  return <section className="course-resource-eligibility"><h3>Geeignete {label('lecturer.plural')} und {label('room.plural')}</h3><p>Wechsel von Lehrpersonen und Räumen innerhalb dieser {label('course.singular')} werden minimiert, soweit harte Einschränkungen dies erlauben. Diese festen Präferenzen haben weder Rang noch Quote oder globale Wirkung.</p><CandidateGroup title={label('lecturer.heading')} candidates={configuration.lecturerCandidates} selected={lecturerIds} cohortSize={configuration.cohortSize} onToggle={(id) => toggle(lecturerIds, id, setLecturerIds)} /><CandidateGroup title={label('room.heading')} candidates={configuration.roomCandidates} selected={roomIds} cohortSize={configuration.cohortSize} onToggle={(id) => toggle(roomIds, id, setRoomIds)} />{error && <p role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="secondary-button" onClick={onCancel}>Änderungen verwerfen</button><button type="button" onClick={() => void save()}>Eignung speichern</button></div></section>
}
