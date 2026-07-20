import { useState } from 'react'
import type { ExamCoursePlanningState, SaveExamConfigurationRequest } from '../api/examScheduling'

type LecturerOption = { id: number; name: string; referenceCode?: string }

export function ExamRequirementEditor({ state, lecturers, busy, onSave }: { state: ExamCoursePlanningState; lecturers: LecturerOption[]; busy: boolean; onSave: (request: SaveExamConfigurationRequest) => Promise<void> | void }) {
  const current = state.configuration
  const [enabled, setEnabled] = useState(state.enabled)
  const [identifier, setIdentifier] = useState(current?.identifier ?? 'Exam')
  const [duration, setDuration] = useState(current?.durationMinutes ?? 90)
  const [capacity, setCapacity] = useState(current?.requiredCapacity ?? 1)
  const [examType, setExamType] = useState(current?.examType ?? 'Written')
  const [lecturerId, setLecturerId] = useState(current?.responsibleLecturerId ?? lecturers[0]?.id ?? 0)
  const [overrideEnabled, setOverrideEnabled] = useState(current?.recommendedStartOverride != null)
  const [startOverride, setStartOverride] = useState(current?.recommendedStartOverride ?? '')
  const [endOverride, setEndOverride] = useState(current?.recommendedEndOverride ?? '')
  const [errors, setErrors] = useState<string[]>([])
  const readOnly = state.activeExam != null

  function reset() {
    setEnabled(state.enabled); setIdentifier(current?.identifier ?? 'Exam'); setDuration(current?.durationMinutes ?? 90); setCapacity(current?.requiredCapacity ?? 1); setExamType(current?.examType ?? 'Written'); setLecturerId(current?.responsibleLecturerId ?? lecturers[0]?.id ?? 0); setOverrideEnabled(current?.recommendedStartOverride != null); setStartOverride(current?.recommendedStartOverride ?? ''); setEndOverride(current?.recommendedEndOverride ?? ''); setErrors([])
  }

  function save() {
    const nextErrors: string[] = []
    if (enabled && !identifier.trim()) nextErrors.push('Enter an exam identifier.')
    if (enabled && (!Number.isInteger(duration) || duration <= 0)) nextErrors.push('Enter a positive whole duration.')
    if (enabled && (!Number.isInteger(capacity) || capacity <= 0)) nextErrors.push('Enter a positive required capacity.')
    if (enabled && !examType.trim()) nextErrors.push('Enter an exam type.')
    if (enabled && !lecturerId) nextErrors.push('Choose a responsible lecturer.')
    if (enabled && overrideEnabled && (!startOverride || !endOverride || endOverride < startOverride)) nextErrors.push('Enter a complete, ordered recommended range.')
    setErrors(nextErrors)
    if (nextErrors.length) return
    void onSave({ semesterId: state.semesterId, enabled, expectedRevision: current?.revision ?? null, configuration: enabled ? { identifier: identifier.trim(), durationMinutes: duration, recommendedStartOverride: overrideEnabled ? startOverride : null, recommendedEndOverride: overrideEnabled ? endOverride : null, requiredCapacity: capacity, examType: examType.trim(), responsibleLecturerId: lecturerId } : null })
  }

  return (
    <section className="exam-card" aria-labelledby="exam-requirement-title">
      <div className="section-heading"><h3 id="exam-requirement-title">Exam requirement</h3></div>
      {readOnly && <p className="constraint-note" role="status">An active exam exists. Its consumed configuration is read-only until the exam is past or deleted.</p>}
      {enabled && !state.finalTeachingAnchor && <p className="constraint-note">No final teaching session is saved yet. The exam may be configured now, but automatic and manual placement remain unavailable.</p>}
      <label className="course-checkbox"><input type="checkbox" checked={enabled} disabled={busy || readOnly} onChange={(event) => setEnabled(event.target.checked)} /> This course requires an exam</label>
      {enabled && <div className="exam-form-grid">
        <label className="constraint-field"><span>Identifier</span><input name="exam-identifier" value={identifier} disabled={busy || readOnly} onChange={(event) => setIdentifier(event.target.value)} /></label>
        <label className="constraint-field"><span>Duration (minutes)</span><input type="number" min="1" step="1" value={duration} disabled={busy || readOnly} onChange={(event) => setDuration(Number(event.target.value))} /></label>
        <label className="constraint-field"><span>Required room capacity</span><input type="number" min="1" step="1" value={capacity} disabled={busy || readOnly} onChange={(event) => setCapacity(Number(event.target.value))} /></label>
        <label className="constraint-field"><span>Exam type</span><input value={examType} disabled={busy || readOnly} onChange={(event) => setExamType(event.target.value)} /></label>
        <label className="constraint-field"><span>Responsible lecturer</span><select value={lecturerId} disabled={busy || readOnly} onChange={(event) => setLecturerId(Number(event.target.value))}>{lecturers.map((lecturer) => <option key={lecturer.id} value={lecturer.id}>{lecturer.name}{lecturer.referenceCode ? ` · ${lecturer.referenceCode}` : ''}</option>)}</select></label>
        <label className="course-checkbox"><input type="checkbox" checked={overrideEnabled} disabled={busy || readOnly} onChange={(event) => setOverrideEnabled(event.target.checked)} /> Override recommended 1–2 week range</label>
        {overrideEnabled && <><label className="constraint-field"><span>Recommended start</span><input type="date" value={startOverride} disabled={busy || readOnly} onChange={(event) => setStartOverride(event.target.value)} /></label><label className="constraint-field"><span>Recommended end</span><input type="date" value={endOverride} disabled={busy || readOnly} onChange={(event) => setEndOverride(event.target.value)} /></label></>}
        {current?.recommendedStartDate && <p className="constraint-note">Effective recommendation: {current.recommendedStartDate} to {current.recommendedEndDate}. This is a soft preference; manual placement may override it.</p>}
      </div>}
      {errors.length > 0 && <div role="alert" className="alert-item">{errors.join(' ')}</div>}
      <div className="dialog-actions"><button type="button" className="secondary-button" onClick={reset} disabled={busy || readOnly}>Cancel changes</button><button type="button" onClick={save} disabled={busy || readOnly}>{busy ? 'Saving…' : 'Save exam requirement'}</button></div>
    </section>
  )
}
