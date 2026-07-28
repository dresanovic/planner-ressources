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
      setAnnouncement('Selection updated because one or more courses are no longer eligible.')
    })
  }, [effectiveSelection, selected])

  async function prepare() {
    setBusy(true)
    setError('')
    try {
      setPreparation(await prepareExamGeneration(semesterId, scheduleRevisionId, effectiveSelection))
    } catch (reason) {
      setError((reason as ExamSchedulingApiError).errors?.map((item) => item.message).join(' ') || 'Could not prepare exams.')
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
      setError((reason as ExamSchedulingApiError).errors?.map((item) => item.message).join(' ') || 'Could not generate exams. Prepare again.')
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
        {!selectable && <small>{course.generationEligibility.message ?? course.generationEligibility.code ?? 'Exam generation is unavailable.'}</small>}
      </div>
    )
  }

  return (
    <section className="exam-card" aria-labelledby="exam-generation-title">
      <h3 id="exam-generation-title">Prepare exams</h3>
      <p className="constraint-note">Select 1–100 eligible courses. Unavailable courses remain visible with their current reason.</p>
      <div className="course-picker exam-generation-courses">
        <section aria-labelledby="eligible-exam-courses"><h4 id="eligible-exam-courses">Eligible courses</h4>{eligibleCourses.length ? eligibleCourses.map((course) => courseChoice(course, true)) : <p>No courses are currently eligible. Configure a requirement and save final teaching first.</p>}</section>
        <section aria-labelledby="unavailable-exam-courses"><h4 id="unavailable-exam-courses">Unavailable courses</h4>{unavailableCourses.length ? unavailableCourses.map((course) => courseChoice(course, false)) : <p>All configured courses are eligible.</p>}</section>
      </div>
      <div className="exam-generation-action-context">
        <p className="selection-count">{effectiveSelection.length} selected</p>
        {effectiveSelection.length === 0 && <p className="constraint-note">Select at least one eligible course to prepare exams.</p>}
        {error && <div role="alert" className="alert-item">{error}</div>}
        {preparation ? (
          <div className="replacement-warning">
            <p>Review {preparation.courses.length} prepared outcomes. Inputs are protected by snapshot tokens.</p>
            <ul>{preparation.courses.map((course) => <li key={course.courseId}><strong>{course.courseName}</strong>: {course.eligibility.eligible ? 'Ready to generate' : course.eligibility.message ?? course.eligibility.code}</li>)}</ul>
            <div className="dialog-actions">
              <button type="button" className="secondary-button" disabled={busy} onClick={() => setPreparation(null)}>Cancel</button>
              <button type="button" disabled={busy} onClick={() => void generate()}>{busy ? 'Generating…' : 'Generate confirmed exams'}</button>
            </div>
          </div>
        ) : <button type="button" disabled={disabled || busy || effectiveSelection.length < 1 || effectiveSelection.length > 100} onClick={() => void prepare()}>{busy ? 'Preparing…' : 'Prepare exams'}</button>}
        {result && <ExamGenerationResultSummary result={result} />}
      </div>
      <p className="sr-only" role="status" aria-live="polite">{announcement}</p>
    </section>
  )
}
