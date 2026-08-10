import { useState } from 'react'
import type { ExamCoursePlanningState, SaveExamConfigurationRequest } from '../api/examScheduling'
import { EuropeanDateField } from './EuropeanDateField'
import { formatCalendarDateRange } from '../utils/datePresentation'
import { label } from '../config/terminology'
import { ActionableProblemList } from './ActionableProblemList'
import { fieldProblem, type UserProblem } from '../utils/userProblems'

type LecturerOption = { id: number; name: string; referenceCode?: string }
type FieldErrors = Partial<Record<'identifier' | 'duration' | 'capacity' | 'examType' | 'lecturer' | 'recommendationStart' | 'recommendationEnd', string>>

export function ExamRequirementEditor({ state, lecturers, busy, saving, onSave }: { state: ExamCoursePlanningState; lecturers: LecturerOption[]; busy: boolean; saving: boolean; onSave: (request: SaveExamConfigurationRequest) => Promise<void> | void }) {
  const current = state.configuration
  const [enabled, setEnabled] = useState(state.enabled)
  const [identifier, setIdentifier] = useState(current?.identifier ?? 'Prüfung')
  const [duration, setDuration] = useState(current?.durationMinutes ?? 90)
  const [capacity, setCapacity] = useState(current?.requiredCapacity ?? 1)
  const [examType, setExamType] = useState(current?.examType ?? 'Schriftlich')
  const [lecturerId, setLecturerId] = useState(current?.responsibleLecturerId ?? lecturers[0]?.id ?? 0)
  const [overrideEnabled, setOverrideEnabled] = useState(current?.recommendedStartOverride != null)
  const [startOverride, setStartOverride] = useState(current?.recommendedStartOverride ?? '')
  const [endOverride, setEndOverride] = useState(current?.recommendedEndOverride ?? '')
  const [errors, setErrors] = useState<FieldErrors>({})
  const readOnly = state.activeExam != null

  function reset() {
    setEnabled(state.enabled); setIdentifier(current?.identifier ?? 'Prüfung'); setDuration(current?.durationMinutes ?? 90); setCapacity(current?.requiredCapacity ?? 1); setExamType(current?.examType ?? 'Schriftlich'); setLecturerId(current?.responsibleLecturerId ?? lecturers[0]?.id ?? 0); setOverrideEnabled(current?.recommendedStartOverride != null); setStartOverride(current?.recommendedStartOverride ?? ''); setEndOverride(current?.recommendedEndOverride ?? ''); setErrors({})
  }

  const fieldIds: Record<keyof FieldErrors, string> = { identifier: 'exam-identifier', duration: 'exam-duration', capacity: 'exam-capacity', examType: 'exam-examType', lecturer: 'exam-lecturer', recommendationStart: 'exam-recommendation-start', recommendationEnd: 'exam-recommendation-end' }
  const problems: UserProblem[] = Object.entries(errors).map(([field, message]) => fieldProblem(fieldIds[field as keyof FieldErrors], message, field === 'recommendationStart' ? 'ein gültiges Startdatum im Format TT.MM.JJJJ' : field === 'recommendationEnd' ? 'ein gültiges Enddatum am oder nach dem Beginn im Format TT.MM.JJJJ' : 'eine gültige Eingabe'))

  function save() {
    const nextErrors: FieldErrors = {}
    if (enabled && !identifier.trim()) nextErrors.identifier = 'Prüfungsbezeichnung'
    if (enabled && (!Number.isInteger(duration) || duration <= 0)) nextErrors.duration = 'Dauer'
    if (enabled && (!Number.isInteger(capacity) || capacity <= 0)) nextErrors.capacity = 'Erforderliche Raumkapazität'
    if (enabled && !examType.trim()) nextErrors.examType = 'Prüfungsart'
    if (enabled && !lecturerId) nextErrors.lecturer = `Verantwortliche ${label('lecturer.singular')}`
    if (enabled && overrideEnabled && !startOverride) nextErrors.recommendationStart = 'Empfohlener Beginn'
    if (enabled && overrideEnabled && !endOverride) nextErrors.recommendationEnd = 'Empfohlenes Ende'
    else if (enabled && overrideEnabled && startOverride && endOverride < startOverride) nextErrors.recommendationEnd = 'Empfohlener Zeitraum'
    setErrors(nextErrors)
    const first = Object.keys(nextErrors)[0]
    if (first) {
      queueMicrotask(() => document.getElementById(fieldIds[first as keyof FieldErrors])?.focus())
      return
    }
    void onSave({ semesterId: state.semesterId, enabled, expectedRevision: current?.revision ?? null, configuration: enabled ? { identifier: identifier.trim(), durationMinutes: duration, recommendedStartOverride: overrideEnabled ? startOverride : null, recommendedEndOverride: overrideEnabled ? endOverride : null, requiredCapacity: capacity, examType: examType.trim(), responsibleLecturerId: lecturerId } : null })
  }

  const describedBy = (field: keyof FieldErrors) => errors[field] ? `exam-${field}-error` : undefined
  return (
    <section className="exam-card" aria-labelledby="exam-requirement-title">
      <div className="section-heading"><h3 id="exam-requirement-title">Prüfungsanforderung</h3></div>
      {readOnly && <p className="constraint-note" role="status">Eine aktive Prüfung ist vorhanden. Die dafür verwendete Konfiguration ist schreibgeschützt, bis die Prüfung vergangen oder gelöscht ist.</p>}
      {enabled && !state.finalTeachingAnchor && <p className="constraint-note">Noch kein letzter Lehrtermin gespeichert. Die Prüfung kann konfiguriert werden; automatische und manuelle Platzierung bleiben bis dahin blockiert.</p>}
      <label className="course-checkbox"><input type="checkbox" checked={enabled} disabled={busy || readOnly} onChange={(event) => setEnabled(event.target.checked)} /> Für diese {label('course.singular')} ist eine Prüfung erforderlich</label>
      {enabled && <div className="exam-form-grid">
        <label className="constraint-field" htmlFor="exam-identifier"><span>Prüfungsbezeichnung</span><input id="exam-identifier" name="exam-identifier" value={identifier} disabled={busy || readOnly} aria-invalid={errors.identifier ? 'true' : undefined} aria-describedby={describedBy('identifier')} onChange={(event) => setIdentifier(event.target.value)} />{errors.identifier && <small id="exam-identifier-error" className="field-error">Geben Sie eine Prüfungsbezeichnung ein.</small>}</label>
        <label className="constraint-field" htmlFor="exam-duration"><span>Dauer (Minuten)</span><input id="exam-duration" type="number" min="1" step="1" value={duration} disabled={busy || readOnly} aria-invalid={errors.duration ? 'true' : undefined} aria-describedby={describedBy('duration')} onChange={(event) => setDuration(Number(event.target.value))} />{errors.duration && <small id="exam-duration-error" className="field-error">Geben Sie eine positive ganze Minutenzahl ein.</small>}</label>
        <label className="constraint-field" htmlFor="exam-capacity"><span>Erforderliche Raumkapazität</span><input id="exam-capacity" type="number" min="1" step="1" value={capacity} disabled={busy || readOnly} aria-invalid={errors.capacity ? 'true' : undefined} aria-describedby={describedBy('capacity')} onChange={(event) => setCapacity(Number(event.target.value))} />{errors.capacity && <small id="exam-capacity-error" className="field-error">Geben Sie eine positive ganze Kapazität ein.</small>}</label>
        <label className="constraint-field" htmlFor="exam-examType"><span>Prüfungsart</span><input id="exam-examType" value={examType} disabled={busy || readOnly} aria-invalid={errors.examType ? 'true' : undefined} aria-describedby={describedBy('examType')} onChange={(event) => setExamType(event.target.value)} />{errors.examType && <small id="exam-examType-error" className="field-error">Geben Sie eine Prüfungsart ein.</small>}</label>
        <label className="constraint-field" htmlFor="exam-lecturer"><span>Verantwortliche {label('lecturer.singular')}</span><select id="exam-lecturer" value={lecturerId} disabled={busy || readOnly} aria-invalid={errors.lecturer ? 'true' : undefined} aria-describedby={describedBy('lecturer')} onChange={(event) => setLecturerId(Number(event.target.value))}>{lecturers.map((lecturer) => <option key={lecturer.id} value={lecturer.id}>{lecturer.name}{lecturer.referenceCode ? ` · ${lecturer.referenceCode}` : ''}</option>)}</select>{errors.lecturer && <small id="exam-lecturer-error" className="field-error">Wählen Sie eine verantwortliche Person aus.</small>}</label>
        <label className="course-checkbox"><input type="checkbox" checked={overrideEnabled} disabled={busy || readOnly} onChange={(event) => setOverrideEnabled(event.target.checked)} /> Empfohlenen Zeitraum von 1–2 Wochen anpassen</label>
        {overrideEnabled && <><EuropeanDateField id="exam-recommendation-start" label="Empfohlener Beginn" value={startOverride} disabled={busy || readOnly} onChange={(value) => setStartOverride(value ?? '')} required error={errors.recommendationStart ? 'Geben Sie einen gültigen Beginn im Format TT.MM.JJJJ ein.' : undefined} /><EuropeanDateField id="exam-recommendation-end" label="Empfohlenes Ende" value={endOverride} disabled={busy || readOnly} onChange={(value) => setEndOverride(value ?? '')} required error={errors.recommendationEnd ? (endOverride ? 'Das Ende muss am oder nach dem Beginn liegen.' : 'Geben Sie ein gültiges Ende im Format TT.MM.JJJJ ein.') : undefined} /></>}
        {current?.recommendedStartDate && <p className="constraint-note">Wirksamer Empfehlungszeitraum: {formatCalendarDateRange(current.recommendedStartDate, current.recommendedEndDate)}. Dies ist eine nicht blockierende Orientierung; eine manuelle Abweichung bleibt möglich.</p>}
      </div>}
      <ActionableProblemList problems={problems} />
      <div className="dialog-actions"><button type="button" className="secondary-button" onClick={reset} disabled={busy || readOnly}>Änderungen verwerfen</button><button type="button" onClick={save} disabled={busy || readOnly} aria-busy={saving || undefined}>{saving ? 'Speichern…' : 'Prüfungsanforderung speichern'}</button></div>
    </section>
  )
}
