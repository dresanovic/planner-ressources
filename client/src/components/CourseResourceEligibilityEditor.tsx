import { useState } from 'react'
import type { CourseResourceCandidate, CourseResourceConfiguration } from '../api/resourceCatalog'
import { formatUnavailabilityPeriod } from '../utils/resourceAvailability'

function CandidateGroup({ title, candidates, selected, cohortSize, onToggle }: { title: string; candidates: CourseResourceCandidate[]; selected: number[]; cohortSize: number; onToggle: (id: number) => void }) {
  const [query, setQuery] = useState('')
  const visible = candidates.filter((candidate) => `${candidate.name} ${candidate.referenceCode}`.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()))
  return <fieldset className="eligibility-group"><legend>{title}</legend><label className="catalog-field">Search<input type="search" value={query} onChange={(event) => setQuery(event.target.value)} /></label><div className="eligibility-candidates">{visible.map((candidate) => {
    const isSelected = selected.includes(candidate.id)
    const disabled = !isSelected && !candidate.isUsable
    const usage = candidate.courseSessionUsage
    return <div key={candidate.id} className={!candidate.isUsable ? 'candidate-invalid' : ''}>
      <label><input type="checkbox" value={candidate.id} checked={isSelected} disabled={disabled} onChange={() => onToggle(candidate.id)} /><span><strong>{candidate.name} · {candidate.referenceCode}</strong>{candidate.kind === 'room' && <small>Capacity {candidate.capacity} · requires {cohortSize}</small>}{candidate.reasons.length > 0 && <small>{candidate.reasons.join(', ')}</small>}</span></label>
      <small>Assigned to {usage.draftSessionCount} saved session{usage.draftSessionCount === 1 ? '' : 's'} across {usage.draftScheduleCount} schedule{usage.draftScheduleCount === 1 ? '' : 's'} for this Course.</small>
      {candidate.unavailabilityPeriods.length > 0 && <details><summary>{candidate.unavailabilityPeriods.length} unavailable period{candidate.unavailabilityPeriods.length === 1 ? '' : 's'}</summary><ul>{candidate.unavailabilityPeriods.map((period) => <li key={period.id}>{formatUnavailabilityPeriod(period)}</li>)}</ul></details>}
    </div>
  })}</div></fieldset>
}

export function CourseResourceEligibilityEditor({ configuration, onSave, onCancel }: { configuration: CourseResourceConfiguration; onSave: (value: { expectedRevision: number; lecturerIds: number[]; roomIds: number[] }) => Promise<unknown> | unknown; onCancel: () => void }) {
  const [lecturerIds, setLecturerIds] = useState(configuration.eligibleLecturerIds)
  const [roomIds, setRoomIds] = useState(configuration.eligibleRoomIds)
  const [error, setError] = useState('')
  const toggle = (values: number[], id: number, set: (value: number[]) => void) => set(values.includes(id) ? values.filter((value) => value !== id) : [...values, id].sort((a, b) => a - b))
  async function save() {
    if (!lecturerIds.length || !roomIds.length) { setError('Keep at least one eligible lecturer and one eligible room.'); return }
    try { setError(''); await onSave({ expectedRevision: configuration.courseRevision, lecturerIds, roomIds }) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Could not save resource eligibility.') }
  }
  return <section className="course-resource-eligibility"><h3>Eligible lecturers and rooms</h3><p>Minimize lecturer changes and room changes within this Course whenever hard constraints allow. These fixed preferences have no rank, quota, or global scope.</p><CandidateGroup title="Lecturers" candidates={configuration.lecturerCandidates} selected={lecturerIds} cohortSize={configuration.cohortSize} onToggle={(id) => toggle(lecturerIds, id, setLecturerIds)} /><CandidateGroup title="Rooms" candidates={configuration.roomCandidates} selected={roomIds} cohortSize={configuration.cohortSize} onToggle={(id) => toggle(roomIds, id, setRoomIds)} />{error && <p role="alert">{error}</p>}<div className="dialog-actions"><button type="button" className="secondary-button" onClick={onCancel}>Cancel eligibility changes</button><button type="button" onClick={() => void save()}>Save eligibility</button></div></section>
}
