import { useEffect, useMemo, useState } from 'react'
import {
  generateExams,
  prepareExamGeneration,
  type ExamCoursePlanningState,
  type ExamGenerationPreparation,
  type ExamGenerationResult,
  type ExamSchedulingApiError,
} from '../api/examScheduling'
import { ExamGenerationResultSummary } from './ExamGenerationResultSummary'
import { label } from '../config/terminology'

export function ExamGenerationPanel({
  semesterId,
  scheduleRevisionId = 0,
  courses,
  disabled,
  onChanged,
}: {
  semesterId: number
  scheduleRevisionId?: number
  courses: ExamCoursePlanningState[]
  disabled: boolean
  onChanged: (result: ExamGenerationResult) => Promise<void> | void
}) {
  const [selected, setSelected] = useState<number[]>([])
  const [preparation, setPreparation] = useState<ExamGenerationPreparation | null>(null)
  const [result, setResult] = useState<ExamGenerationResult | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [announcement, setAnnouncement] = useState('')
  const eligibleCourses = useMemo(
    () => courses.filter((course) => course.generationEligibility.eligible),
    [courses],
  )
  const unavailableCourses = useMemo(
    () => courses.filter((course) => !course.generationEligibility.eligible),
    [courses],
  )
  const selectableCourseIds = useMemo(
    () => new Set(eligibleCourses.map((course) => course.courseId)),
    [eligibleCourses],
  )
  const effectiveSelection = selected.filter((courseId) => selectableCourseIds.has(courseId))

  useEffect(() => {
    if (effectiveSelection.length === selected.length) return
    queueMicrotask(() => {
      setSelected(effectiveSelection)
      setAnnouncement(`Die Auswahl wurde aktualisiert, weil mindestens eine ${label('course.singular')} nicht mehr geeignet ist.`)
    })
  }, [effectiveSelection, selected])

  async function prepare() {
    setBusy(true)
    setError('')
    try {
      setPreparation(await prepareExamGeneration(semesterId, scheduleRevisionId, effectiveSelection))
    } catch (reason) {
      const failure = reason as ExamSchedulingApiError
      setError(failure.status === 409 ? 'Die Prüfungsdaten wurden zwischenzeitlich geändert. Laden Sie den aktuellen Stand und bereiten Sie die Prüfungen erneut vor.' : 'Die Prüfungen konnten nicht vorbereitet werden. Ihre Auswahl bleibt erhalten; prüfen Sie die verfügbaren Lehrveranstaltungen und versuchen Sie es erneut.')
    } finally {
      setBusy(false)
    }
  }

  async function generate() {
    if (!preparation) return
    setBusy(true)
    setError('')
    try {
      const value = await generateExams({
        semesterId: preparation.semesterId,
        scheduleRevisionId: preparation.scheduleRevisionId,
        institutionToday: preparation.institutionToday,
        sharedSnapshotToken: preparation.sharedSnapshotToken,
        courses: preparation.courses.map(({ courseId, configurationId, configurationRevision, inputSnapshotToken }) => ({
          courseId,
          configurationId,
          configurationRevision,
          inputSnapshotToken,
        })),
      })
      setResult(value)
      setPreparation(null)
      setSelected([])
      await onChanged(value)
    } catch (reason) {
      const failure = reason as ExamSchedulingApiError
      setError(failure.status === 409 ? 'Die vorbereiteten Prüfungsdaten sind nicht mehr aktuell. Laden Sie den aktuellen Stand und bereiten Sie die Prüfungen erneut vor.' : 'Die Prüfungen konnten nicht erzeugt werden. Die genaue Ursache ist nicht verfügbar; prüfen Sie den aktuellen Stand, bevor Sie die Vorbereitung wiederholen.')
      setPreparation(null)
    } finally {
      setBusy(false)
    }
  }

  function courseChoice(course: ExamCoursePlanningState, selectable: boolean) {
    return (
      <div key={course.courseId} className="exam-course-choice">
        <label className="course-checkbox">
          <input
            type="checkbox"
            checked={effectiveSelection.includes(course.courseId)}
            disabled={disabled || busy || !selectable}
            onChange={(event) => setSelected(event.target.checked
              ? [...effectiveSelection, course.courseId]
              : effectiveSelection.filter((id) => id !== course.courseId))}
          />
          <span>{course.courseName}</span>
        </label>
        {!selectable && <small>Für diese Lehrveranstaltung ist die Prüfungserzeugung derzeit nicht verfügbar. Prüfen und speichern Sie zuerst die Prüfungsanforderung und den letzten Lehrtermin.</small>}
      </div>
    )
  }

  return (
    <section className="exam-card" aria-labelledby="exam-generation-title">
      <h3 id="exam-generation-title">Prüfungen vorbereiten</h3>
      <p className="constraint-note">Wählen Sie 1–100 geeignete {label('course.plural')}. Nicht verfügbare {label('course.plural')} bleiben mit dem aktuellen Grund sichtbar.</p>
      <div className="course-picker exam-generation-courses">
        <section aria-labelledby="eligible-exam-courses"><h4 id="eligible-exam-courses">Geeignete {label('course.plural')}</h4>{eligibleCourses.length ? eligibleCourses.map((course) => courseChoice(course, true)) : <p>Derzeit ist keine {label('course.singular')} geeignet. Konfigurieren Sie zuerst eine Prüfungsanforderung und speichern Sie den letzten Lehrtermin.</p>}</section>
        <section aria-labelledby="unavailable-exam-courses"><h4 id="unavailable-exam-courses">Nicht verfügbare {label('course.plural')}</h4>{unavailableCourses.length ? unavailableCourses.map((course) => courseChoice(course, false)) : <p>Alle konfigurierten {label('course.plural')} sind geeignet.</p>}</section>
      </div>
      <div className="exam-generation-action-context">
        <p className="selection-count">{effectiveSelection.length} ausgewählt</p>
        {effectiveSelection.length === 0 && <p className="constraint-note">Wählen Sie mindestens eine geeignete {label('course.singular')}, um Prüfungen vorzubereiten.</p>}
        {error && <div role="alert" className="alert-item">{error}</div>}
        {preparation ? (
          <div className="replacement-warning">
            <p>Prüfen Sie {preparation.courses.length} vorbereitete Ergebnisse. Die Eingaben sind gegen zwischenzeitliche Änderungen geschützt.</p>
            <ul>{preparation.courses.map((course) => <li key={course.courseId}><strong>{course.courseName}</strong>: {course.eligibility.eligible ? 'Bereit zur Erzeugung' : 'Derzeit nicht zur Erzeugung geeignet; prüfen Sie die Prüfungsanforderung und den letzten Lehrtermin.'}</li>)}</ul>
            <div className="dialog-actions">
              <button type="button" className="secondary-button" disabled={busy} onClick={() => setPreparation(null)}>Abbrechen</button>
              <button type="button" disabled={busy} onClick={() => void generate()}>{busy ? 'Wird erzeugt…' : 'Bestätigte Prüfungen erzeugen'}</button>
            </div>
          </div>
        ) : <button type="button" disabled={disabled || busy || effectiveSelection.length < 1 || effectiveSelection.length > 100} onClick={() => void prepare()}>{busy ? 'Wird vorbereitet…' : 'Prüfungen vorbereiten'}</button>}
        {result && <ExamGenerationResultSummary result={result} />}
      </div>
      <p className="sr-only" role="status" aria-live="polite">{announcement}</p>
    </section>
  )
}
