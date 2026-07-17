import { useEffect, useMemo, useRef, useState } from 'react'
import {
  clearGenerationConstraints,
  clearCourseDraft,
  createManualDraftSession,
  deleteDraftSession,
  generateDraftSchedule,
  getDraftSchedules,
  getGenerationConstraints,
  type DraftSchedule,
  type CreateManualDraftSessionRequest,
  type GenerationConstraints,
  type GenerationFailure,
  type UpdateDraftSessionRequest,
  updateDraftSession,
} from '../api/draftSchedule'
import {
  generateConflictAwareSchedules,
  prepareConflictAwareGeneration,
  type OptimizationError,
  type OptimizationGenerationResult,
  type OptimizationPreparation,
} from '../api/conflictAwareGeneration'
import {
  getPlanningOptions,
  type CourseOption,
  type PlanningOptions,
  type SemesterOption,
} from '../api/planningOptions'
import { BatchResultSummary } from '../components/BatchResultSummary'
import { DraftSchedulePanel, GenerationConstraintEditor } from '../components/DraftSchedulePanel'
import { MultiCourseGenerationPanel } from '../components/MultiCourseGenerationPanel'
import { ReplacementConfirmationDialog } from '../components/ReplacementConfirmationDialog'
import { calculateDefaultEndTime, deriveCourseProgress, isValidSessionTimeRange } from '../components/manualSessionUtils'
import { ScheduleDeletionDialog, type ScheduleDeletionScope } from '../components/ScheduleDeletionDialog'

type GenerationMode = 'single' | 'batch'
type SessionDeletionConfirmation = {
  sessionId: number
  draftScheduleId: number
  draftRevision: number
  scope: Extract<ScheduleDeletionScope, { kind: 'session' }>
}
type CourseDeletionConfirmation = {
  courseId: number
  semesterId: number
  draftScheduleId: number
  draftRevision: number
  scope: Extract<ScheduleDeletionScope, { kind: 'courseDraft' }>
}

export function CourseSchedulePage({ catalogRevision = 0 }: { catalogRevision?: number }) {
  const [planningOptions, setPlanningOptions] = useState<PlanningOptions | null>(null)
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [selectedSemesterId, setSelectedSemesterId] = useState<number | null>(null)
  const [generationConstraints, setGenerationConstraints] = useState<GenerationConstraints | null>(null)
  const [schedules, setSchedules] = useState<DraftSchedule[]>([])
  const [mode, setMode] = useState<GenerationMode>('single')
  const [selectedBatchCourseIds, setSelectedBatchCourseIds] = useState<number[]>([])
  const [errors, setErrors] = useState<GenerationFailure[]>([])
  const [batchErrors, setBatchErrors] = useState<OptimizationError[]>([])
  const [batchPreparation, setBatchPreparation] = useState<OptimizationPreparation | null>(null)
  const [batchResult, setBatchResult] = useState<OptimizationGenerationResult | null>(null)
  const [unavailableDatesInput, setUnavailableDatesInput] = useState('')
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [constraintsLoading, setConstraintsLoading] = useState(false)
  const [overviewLoading, setOverviewLoading] = useState(false)
  const [loadedOverviewSemesterId, setLoadedOverviewSemesterId] = useState<number | null>(null)
  const [singleGenerating, setSingleGenerating] = useState(false)
  const [batchPreparing, setBatchPreparing] = useState(false)
  const [batchExecuting, setBatchExecuting] = useState(false)
  const [overviewRefreshError, setOverviewRefreshError] = useState(false)
  const [overviewResetKey, setOverviewResetKey] = useState(0)
  const [semesterSelectionMissing, setSemesterSelectionMissing] = useState(false)
  const [manualSaving, setManualSaving] = useState(false)
  const [sessionUpdating, setSessionUpdating] = useState(false)
  const [manualErrors, setManualErrors] = useState<GenerationFailure[]>([])
  const [progressAnnouncement, setProgressAnnouncement] = useState('')
  const [sessionDeletion, setSessionDeletion] = useState<SessionDeletionConfirmation | null>(null)
  const [courseDeletion, setCourseDeletion] = useState<CourseDeletionConfirmation | null>(null)
  const [deletionBusy, setDeletionBusy] = useState(false)
  const [deletionErrors, setDeletionErrors] = useState<GenerationFailure[]>([])
  const [deletionNotice, setDeletionNotice] = useState('')
  const selectedCourseIdRef = useRef<number | null>(null)
  const selectedSemesterIdRef = useRef<number | null>(null)

  useEffect(() => { selectedCourseIdRef.current = selectedCourseId }, [selectedCourseId])
  useEffect(() => { selectedSemesterIdRef.current = selectedSemesterId }, [selectedSemesterId])

  const selectedCourse = useMemo(
    () => planningOptions?.courses.find((course) => course.id === selectedCourseId) ?? null,
    [planningOptions, selectedCourseId],
  )
  const selectedSemester = useMemo(
    () => planningOptions?.semesters.find((semester) => semester.id === selectedSemesterId) ?? null,
    [planningOptions, selectedSemesterId],
  )
  const semesterCourses = useMemo(
    () => planningOptions?.courses.filter((course) => course.semesterId == null || course.semesterId === selectedSemesterId) ?? [],
    [planningOptions, selectedSemesterId],
  )
  const courseSelectionInvalid = selectedCourse != null && selectedCourse.semesterId != null && selectedCourse.semesterId !== selectedSemesterId
  const courseUnavailable = selectedCourse?.availability?.available === false
  const planningSelectionInvalid = semesterSelectionMissing || courseSelectionInvalid || courseUnavailable
  const selectableCourses = useMemo(() => selectedCourse && courseSelectionInvalid ? [selectedCourse, ...semesterCourses.filter((course) => course.id !== selectedCourse.id)] : semesterCourses, [selectedCourse, courseSelectionInvalid, semesterCourses])
  const selectedProgress = useMemo(
    () => selectedCourse && selectedSemesterId && loadedOverviewSemesterId === selectedSemesterId && !overviewLoading && !overviewRefreshError
      ? deriveCourseProgress(selectedCourse.totalUnits, schedules, selectedCourse.id, selectedSemesterId)
      : null,
    [selectedCourse, selectedSemesterId, loadedOverviewSemesterId, overviewLoading, overviewRefreshError, schedules],
  )
  const unavailableDates = useMemo(
    () => [...new Set(unavailableDatesInput.split(',').map((value) => value.trim()).filter(Boolean))].sort(),
    [unavailableDatesInput],
  )
  const selectedDraft = useMemo(
    () => schedules.find((schedule) => schedule.courseId === selectedCourseId && schedule.semesterId === selectedSemesterId) ?? null,
    [schedules, selectedCourseId, selectedSemesterId],
  )
  const capacityValidRooms = useMemo(
    () => planningOptions?.rooms.filter((room) => selectedCourse != null && room.capacity >= selectedCourse.cohortSize) ?? [],
    [planningOptions, selectedCourse],
  )
  const mutationBusy = singleGenerating || batchPreparing || batchExecuting || manualSaving || sessionUpdating || deletionBusy
  const contextBusy = mutationBusy || overviewLoading
  const writeBusy = contextBusy || overviewRefreshError

  useEffect(() => {
    let current = true
    void getPlanningOptions()
      .then((options) => {
        if (!current) return
        const currentCourseId = selectedCourseIdRef.current
        const currentSemesterId = selectedSemesterIdRef.current
        const courseMissing = currentCourseId != null && !options.courses.some((course) => course.id === currentCourseId)
        const semesterMissing = currentSemesterId != null && !options.semesters.some((semester) => semester.id === currentSemesterId)
        setSemesterSelectionMissing(semesterMissing)
        setPlanningOptions((previous) => {
          const previousCourse = previous?.courses.find((course) => course.id === currentCourseId)
          const previousSemester = previous?.semesters.find((semester) => semester.id === currentSemesterId)
          return {
            ...options,
            courses: courseMissing && previousCourse
              ? [{ ...previousCourse, availability: { available: false, reasons: ['OPTION_NO_LONGER_AVAILABLE'] } }, ...options.courses]
              : options.courses,
            semesters: semesterMissing && previousSemester ? [previousSemester, ...options.semesters] : options.semesters,
          }
        })
        const initialSemesterId = options.semesters[0]?.id ?? null
        setSelectedSemesterId((value) => value ?? initialSemesterId)
        setSelectedCourseId((value) => value ?? options.courses.find((course) => course.semesterId == null || course.semesterId === initialSemesterId)?.id ?? null)
      })
      .catch(() => current && setErrors([{ code: 'REQUEST_FAILED', message: 'Could not load planning options.' }]))
      .finally(() => current && setOptionsLoading(false))
    return () => { current = false }
  }, [catalogRevision])

  useEffect(() => {
    if (!selectedCourseId || !selectedSemesterId || planningSelectionInvalid) {
      return
    }
    let current = true
    async function loadConstraints() {
      setConstraintsLoading(true)
      try {
        const value = await getGenerationConstraints(selectedCourseId as number, selectedSemesterId as number)
        if (current) setGenerationConstraints(value)
      } catch (error) {
        if (!current) return
        setGenerationConstraints(null)
        setErrors(toFailures(error, 'Could not load generation constraints.'))
      } finally {
        if (current) setConstraintsLoading(false)
      }
    }
    void loadConstraints()
    return () => { current = false }
  }, [selectedCourseId, selectedSemesterId, planningSelectionInvalid])

  useEffect(() => {
    if (!selectedSemesterId) return
    let current = true
    async function loadOverview() {
      setOverviewLoading(true)
      setOverviewRefreshError(false)
      try {
        const value = await getDraftSchedules(selectedSemesterId as number)
        if (current) {
          setSchedules(value)
          setLoadedOverviewSemesterId(selectedSemesterId as number)
        }
      } catch {
        if (current) setOverviewRefreshError(true)
      } finally {
        if (current) setOverviewLoading(false)
      }
    }
    void loadOverview()
    return () => { current = false }
  }, [selectedSemesterId])

  async function refreshOverview(semesterId: number, resetInteractions = true) {
    setOverviewLoading(true)
    setOverviewRefreshError(false)
    try {
      const current = await getDraftSchedules(semesterId)
      setSchedules(current)
      setLoadedOverviewSemesterId(semesterId)
      setDeletionNotice('')
      if (resetInteractions) setOverviewResetKey((key) => key + 1)
      return true
    } catch {
      setOverviewRefreshError(true)
      return false
    } finally {
      setOverviewLoading(false)
    }
  }

  async function handleGenerateSingle() {
    if (planningSelectionInvalid) {
      const code = semesterSelectionMissing ? 'SEMESTER_NO_LONGER_AVAILABLE' : courseSelectionInvalid ? 'COURSE_SEMESTER_MISMATCH' : (selectedCourse?.availability?.reasons[0] ?? 'COURSE_UNAVAILABLE')
      setErrors([{ code, message: 'Choose an available Course and Semester before generating.' }])
      return
    }
    if (!selectedCourseId || !selectedSemesterId || !generationConstraints) {
      setErrors([{ code: 'MISSING_SELECTION', message: 'Select a course and semester.' }])
      return
    }
    setSingleGenerating(true)
    setErrors([])
    try {
      await generateDraftSchedule(
        selectedCourseId,
        selectedSemesterId,
        generationConstraints.planningPeriod,
        generationConstraints.allowedTeachingWindows,
      )
      const saved = await getGenerationConstraints(selectedCourseId, selectedSemesterId)
      setGenerationConstraints(saved)
      await refreshOverview(selectedSemesterId, false)
    } catch (error) {
      setErrors(toFailures(error, 'Generation failed.'))
    } finally {
      setSingleGenerating(false)
    }
  }

  async function startBatch(courseIds = selectedBatchCourseIds) {
    if (!selectedSemesterId) return
    setBatchPreparing(true)
    setBatchErrors([])
    try {
      const prepared = await prepareConflictAwareGeneration(selectedSemesterId, courseIds, unavailableDates)
      if (prepared.replacementCourseIds.length > 0) {
        setBatchPreparation(prepared)
      } else {
        await executeBatch(prepared, false)
      }
    } catch (error) {
      setBatchErrors(toBatchErrors(error))
    } finally {
      setBatchPreparing(false)
    }
  }

  async function executeBatch(preparation: OptimizationPreparation, confirmed: boolean) {
    setBatchExecuting(true)
    setBatchErrors([])
    try {
      const result = await generateConflictAwareSchedules(preparation, confirmed)
      setBatchResult(result)
      setBatchPreparation(null)
      if (selectedSemesterId !== result.semesterId) setSelectedSemesterId(result.semesterId)
      await refreshOverview(result.semesterId, false)
    } catch (error) {
      setBatchErrors(toBatchErrors(error))
    } finally {
      setBatchExecuting(false)
    }
  }

  async function retryFailedCourses() {
    if (!batchResult) return
    const failedIds = batchResult.outcomes.filter((outcome) => outcome.status === 'failed' || outcome.status === 'stale').map((outcome) => outcome.courseId)
    setSelectedSemesterId(batchResult.semesterId)
    setSelectedBatchCourseIds(failedIds)
    await startBatchForSemester(batchResult.semesterId, failedIds)
  }

  async function startBatchForSemester(semesterId: number, courseIds: number[]) {
    setBatchPreparing(true)
    setBatchErrors([])
    try {
      const prepared = await prepareConflictAwareGeneration(semesterId, courseIds, unavailableDates)
      if (prepared.replacementCourseIds.length > 0) setBatchPreparation(prepared)
      else await executeBatch(prepared, false)
    } catch (error) {
      setBatchErrors(toBatchErrors(error))
    } finally {
      setBatchPreparing(false)
    }
  }

  async function handleClearGenerationConstraints() {
    if (!selectedCourseId || !selectedSemesterId) return
    setConstraintsLoading(true)
    setErrors([])
    try {
      await clearGenerationConstraints(selectedCourseId, selectedSemesterId)
      setGenerationConstraints(await getGenerationConstraints(selectedCourseId, selectedSemesterId))
    } catch (error) {
      setErrors(toFailures(error, 'Could not clear constraints.'))
    } finally {
      setConstraintsLoading(false)
    }
  }

  async function handleUpdateSession(sessionId: number, payload: UpdateDraftSessionRequest) {
    setSessionUpdating(true)
    try {
      await updateDraftSession(sessionId, payload)
      if (selectedSemesterId) await refreshOverview(selectedSemesterId, false)
    } finally {
      setSessionUpdating(false)
    }
  }

  async function handleCreateManualSession(payload: CreateManualDraftSessionRequest) {
    if (!selectedCourseId || !selectedSemesterId) return
    setManualSaving(true)
    setManualErrors([])
    try {
      const result = await createManualDraftSession(selectedCourseId, payload)
      const refreshed = await refreshOverview(selectedSemesterId, false)
      setProgressAnnouncement(refreshed
        ? `Draft Session added. ${result.remainingUnits} units remaining.`
        : `Draft Session saved, but the overview could not be refreshed. ${result.remainingUnits} units remain in the saved state.`)
    } catch (error) {
      setManualErrors(toFailures(error, 'Could not add the Draft Session.'))
    } finally {
      setManualSaving(false)
    }
  }

  function beginSessionDeletion(session: DraftSchedule['sessions'][number], schedule: DraftSchedule) {
    const course = planningOptions?.courses.find((item) => item.id === schedule.courseId)
    const semester = planningOptions?.semesters.find((item) => item.id === schedule.semesterId)
    if (!course || !semester) return
    const scheduledAfter = Math.max(schedule.sessions.reduce((sum, item) => sum + item.units, 0) - session.units, 0)
    setDeletionNotice('')
    setDeletionErrors([])
    setSessionDeletion({
      sessionId: session.id,
      draftScheduleId: schedule.draftScheduleId,
      draftRevision: schedule.revision,
      scope: {
        kind: 'session',
        courseName: schedule.context.course.name,
        semesterName: semester.name,
        date: session.date,
        startTime: session.startTime,
        endTime: session.endTime,
        unitsRemoved: session.units,
        resultingRemainingUnits: Math.max(course.totalUnits - scheduledAfter, 0),
        lastSession: schedule.sessions.length === 1,
      },
    })
  }

  async function confirmSessionDeletion() {
    if (!sessionDeletion) return
    setDeletionBusy(true)
    setDeletionErrors([])
    try {
      const result = await deleteDraftSession(
        sessionDeletion.sessionId,
        sessionDeletion.draftScheduleId,
        sessionDeletion.draftRevision,
      )
      setSessionDeletion(null)
      const refreshed = await refreshOverview(result.semesterId, false)
      setProgressAnnouncement(refreshed
        ? `Draft Session deleted. ${result.remainingUnits} units remaining.`
        : `Draft Session deleted, but the overview could not be refreshed. ${result.remainingUnits} units remain in the saved state.`)
    } catch (error) {
      const failures = toFailures(error, 'Could not delete the Draft Session.')
      if (failures.some((failure) => failure.code === 'STALE_DRAFT')) {
        setSessionDeletion(null)
        const refreshed = selectedSemesterId ? await refreshOverview(selectedSemesterId, false) : false
        setDeletionNotice(refreshed
          ? 'The Draft Schedule changed. Review the refreshed state and open deletion again to confirm the current scope.'
          : 'The Draft Schedule changed, but the current state could not be refreshed. Retry refresh before opening deletion again.')
      } else {
        setDeletionErrors(failures)
      }
    } finally {
      setDeletionBusy(false)
    }
  }

  function beginCourseDeletion() {
    if (!selectedDraft || !selectedCourse || !selectedSemester) return
    const unitsRemoved = selectedDraft.sessions.reduce((sum, session) => sum + session.units, 0)
    setDeletionNotice('')
    setDeletionErrors([])
    setCourseDeletion({
      courseId: selectedCourse.id,
      semesterId: selectedSemester.id,
      draftScheduleId: selectedDraft.draftScheduleId,
      draftRevision: selectedDraft.revision,
      scope: {
        kind: 'courseDraft',
        courseName: selectedDraft.context.course.name,
        semesterName: selectedSemester.name,
        sessionCount: selectedDraft.sessions.length,
        unitsRemoved,
        resultingRemainingUnits: selectedCourse.totalUnits,
      },
    })
  }

  async function confirmCourseDeletion() {
    if (!courseDeletion) return
    setDeletionBusy(true)
    setDeletionErrors([])
    try {
      const result = await clearCourseDraft(
        courseDeletion.courseId,
        courseDeletion.semesterId,
        courseDeletion.draftScheduleId,
        courseDeletion.draftRevision,
      )
      setCourseDeletion(null)
      const refreshed = await refreshOverview(result.semesterId, false)
      setProgressAnnouncement(refreshed
        ? `Course Draft Schedule cleared. ${result.remainingUnits} units remaining.`
        : `Course Draft Schedule cleared, but the overview could not be refreshed. ${result.remainingUnits} units remain in the saved state.`)
    } catch (error) {
      const failures = toFailures(error, 'Could not clear the course Draft Schedule.')
      if (failures.some((failure) => failure.code === 'STALE_DRAFT')) {
        setCourseDeletion(null)
        const refreshed = selectedSemesterId ? await refreshOverview(selectedSemesterId, false) : false
        setDeletionNotice(refreshed
          ? 'The Draft Schedule changed. Review the refreshed state and open deletion again to confirm the current scope.'
          : 'The Draft Schedule changed, but the current state could not be refreshed. Retry refresh before opening deletion again.')
      } else {
        setDeletionErrors(failures)
      }
    } finally {
      setDeletionBusy(false)
    }
  }

  return (
    <>
      <section className="workbench">
        <header className="page-header">
          <div><h1>Resource Planner</h1><p>Draft schedule generation for one or several courses</p></div>
          <div className="metadata-pill">{selectedSemester?.name ?? 'No semester selected'}</div>
        </header>

        <div className="planner-grid">
          <section className="input-summary" aria-labelledby="input-summary-title">
            <h2 id="input-summary-title">Planning inputs</h2>
            {planningOptions ? (
              <>
                <div className="mode-switch" aria-label="Generation mode">
                  <button type="button" className={mode === 'single' ? 'active' : ''} onClick={() => setMode('single')}>One course</button>
                  <button type="button" className={mode === 'batch' ? 'active' : ''} onClick={() => setMode('batch')}>Several courses</button>
                </div>
                <div className="planning-selectors">
                  {mode === 'single' && <SelectField label="Course" value={selectedCourseId ?? ''} options={selectableCourses} getLabel={(course) => `${course.name}${course.availability?.available === false ? ` — unavailable: ${course.availability.reasons.join(', ')}` : ''}${course.id === selectedCourseId && courseSelectionInvalid ? ' — not assigned to selected Semester' : ''}`} onChange={(value) => setSelectedCourseId(Number(value))} disabled={contextBusy} />}
                  <SelectField label="Semester" value={selectedSemesterId ?? ''} options={planningOptions.semesters} getLabel={(semester) => `${semester.name}${semester.id === selectedSemesterId && semesterSelectionMissing ? ' — unavailable' : ''}`} onChange={(value) => { setSemesterSelectionMissing(false); setSelectedSemesterId(Number(value)); setSelectedBatchCourseIds([]) }} disabled={contextBusy} />
                </div>
                {mode === 'single' ? (
                  <>
                    <PlanningSummary course={selectedCourse} semester={selectedSemester} progress={selectedProgress} progressUnavailableLabel={overviewRefreshError ? 'Unavailable' : 'Loading...'} />
                    {planningSelectionInvalid && <div className="refresh-error" role="alert">{semesterSelectionMissing ? 'The selected Semester is no longer available. Choose another Semester.' : courseSelectionInvalid ? 'This Course is not assigned to the selected Semester. Choose another Course.' : `This Course is unavailable: ${selectedCourse?.availability?.reasons.join(', ')}`}</div>}
                    {selectedCourse && selectedSemester && (
                      <ManualSessionEditor
                        key={`${selectedCourse.id}-${selectedSemester.id}-${loadedOverviewSemesterId ?? 'loading'}-${capacityValidRooms.map((room) => room.id).join('-')}`}
                        course={selectedCourse}
                        semester={selectedSemester}
                        rooms={capacityValidRooms}
                        remainingUnits={selectedProgress?.remainingUnits ?? 0}
                        isBusy={writeBusy || selectedProgress == null || planningSelectionInvalid}
                        isSaving={manualSaving}
                        errors={manualErrors}
                        onSubmit={handleCreateManualSession}
                      />
                    )}
                    <button type="button" className="destructive-button clear-course-draft" onClick={beginCourseDeletion} disabled={writeBusy || !selectedDraft}>Clear course draft</button>
                    {progressAnnouncement && <p className="mutation-feedback" role="status" aria-live="polite">{progressAnnouncement}</p>}
                    {generationConstraints && <GenerationConstraintEditor constraints={generationConstraints} isLoading={constraintsLoading || singleGenerating} onChange={setGenerationConstraints} onClear={handleClearGenerationConstraints} />}
                    {errors.length > 0 && <ErrorList errors={errors} />}
                    <button type="button" className="generate-button" onClick={handleGenerateSingle} disabled={writeBusy || constraintsLoading || planningSelectionInvalid}>
                      {singleGenerating ? 'Generating...' : 'Generate'}
                    </button>
                  </>
                ) : (
                  <MultiCourseGenerationPanel courses={semesterCourses} selectedCourseIds={selectedBatchCourseIds} unavailableDatesInput={unavailableDatesInput} onUnavailableDatesInputChange={setUnavailableDatesInput} onChange={setSelectedBatchCourseIds} onGenerate={() => void startBatch()} disabled={writeBusy} />
                )}
                {batchErrors.length > 0 && <ErrorList errors={batchErrors} />}
              </>
            ) : <p className="empty-state">{optionsLoading ? 'Loading planning options...' : 'Planning options are unavailable.'}</p>}
          </section>

          <div className="schedule-results">
            {batchResult && <BatchResultSummary result={batchResult} retryDisabled={writeBusy} onRetryFailed={() => void retryFailedCourses()} />}
            {overviewRefreshError && (
              <div className="refresh-error" role="alert">
                <span>Could not refresh the Courses overview. The last known schedules remain visible.</span>
                <button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId, false)} disabled={overviewLoading}>Retry refresh</button>
              </div>
            )}
            {deletionNotice && <div className="refresh-error" role="alert">{deletionNotice}</div>}
            <DraftSchedulePanel
              resetKey={overviewResetKey}
              schedules={schedules}
              rooms={planningOptions?.rooms ?? []}
              lecturers={planningOptions?.lecturers ?? []}
              courseResources={planningOptions?.courseResources ?? []}
              onUpdateSession={handleUpdateSession}
              onDeleteSession={beginSessionDeletion}
              isBusy={writeBusy}
            />
          </div>
        </div>
      </section>

      {batchPreparation && (
        <ReplacementConfirmationDialog
          preparation={batchPreparation}
          disabled={batchExecuting}
          onCancel={() => setBatchPreparation(null)}
          onConfirm={() => void executeBatch(batchPreparation, true)}
        />
      )}
      {sessionDeletion && (
        <ScheduleDeletionDialog
          scope={sessionDeletion.scope}
          isBusy={deletionBusy}
          error={deletionErrors.length > 0 ? deletionErrors.map((failure) => failure.message).join(' ') : undefined}
          onCancel={() => { setSessionDeletion(null); setDeletionErrors([]) }}
          onConfirm={() => void confirmSessionDeletion()}
        />
      )}
      {courseDeletion && (
        <ScheduleDeletionDialog
          scope={courseDeletion.scope}
          isBusy={deletionBusy}
          error={deletionErrors.length > 0 ? deletionErrors.map((failure) => failure.message).join(' ') : undefined}
          onCancel={() => { setCourseDeletion(null); setDeletionErrors([]) }}
          onConfirm={() => void confirmCourseDeletion()}
        />
      )}
    </>
  )
}

function ErrorList({ errors }: { errors: { code: string; message: string }[] }) {
  return <div className="alert-list" role="alert">{errors.map((error, index) => <div className="alert-item" key={`${error.code}-${index}`}><strong>{error.code.replaceAll('_', ' ')}</strong><span>{error.message}</span></div>)}</div>
}

function toFailures(error: unknown, fallback: string): GenerationFailure[] {
  return Array.isArray(error) ? error : [{ code: 'UNKNOWN', message: fallback }]
}

function toBatchErrors(error: unknown): OptimizationError[] {
  return Array.isArray(error) ? error : [{ code: 'OPTIMIZATION_OPERATION_FAILED', message: 'Semester optimization failed.' }]
}

type Selectable = { id: number }
type SelectFieldProps<T extends Selectable> = { label: string; value: number | ''; options: T[]; getLabel: (option: T) => string; onChange: (value: string) => void; disabled?: boolean }
function SelectField<T extends Selectable>({ label, value, options, getLabel, onChange, disabled = false }: SelectFieldProps<T>) {
  return <label className="selector-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)} disabled={disabled || options.length === 0}>{options.map((option) => <option value={option.id} key={option.id}>{getLabel(option)}</option>)}</select></label>
}

function PlanningSummary({ course, semester, progress, progressUnavailableLabel }: { course: CourseOption | null; semester: SemesterOption | null; progress: { scheduledUnits: number; remainingUnits: number } | null; progressUnavailableLabel: string }) {
  if (!course) return <p className="empty-state">No courses are available.</p>
  return <dl>
    <div><dt>Units</dt><dd>{course.totalUnits}</dd></div>
    <div><dt>Scheduled units</dt><dd>{progress?.scheduledUnits ?? progressUnavailableLabel}</dd></div>
    <div><dt>Remaining units</dt><dd>{progress?.remainingUnits ?? progressUnavailableLabel}</dd></div>
    <div><dt>Session preference</dt><dd>{course.minSessionUnits}-{course.maxSessionUnits} units</dd></div>
    <div><dt>Cohort</dt><dd>{course.cohort.name}</dd></div>
    <div><dt>Lecturer</dt><dd>{course.lecturer?.name ?? 'No eligible lecturer'}</dd></div>
    <div><dt>Room</dt><dd>{course.room?.name ?? 'No usable room'}</dd></div>
    <div><dt>Study type</dt><dd>{course.studyType.name}</dd></div>
    <div><dt>Semester dates</dt><dd>{semester ? `${semester.startDate} - ${semester.endDate}` : 'No semester selected'}</dd></div>
  </dl>
}

function ManualSessionEditor({
  course,
  semester,
  rooms,
  remainingUnits,
  isBusy,
  isSaving,
  errors,
  onSubmit,
}: {
  course: CourseOption
  semester: SemesterOption
  rooms: PlanningOptions['rooms']
  remainingUnits: number
  isBusy: boolean
  isSaving: boolean
  errors: GenerationFailure[]
  onSubmit: (payload: CreateManualDraftSessionRequest) => Promise<void>
}) {
  const initialUnits = Math.min(2, Math.max(remainingUnits, 1))
  const [sessionDate, setSessionDate] = useState(semester.startDate)
  const [startTime, setStartTime] = useState('08:00')
  const [units, setUnits] = useState(initialUnits)
  const [endTime, setEndTime] = useState(calculateDefaultEndTime('08:00', initialUnits) ?? '')
  const [roomId, setRoomId] = useState<number | null>(rooms[0]?.id ?? null)
  const [localError, setLocalError] = useState('')

  function submit() {
    if (!roomId || !Number.isInteger(units) || units <= 0 || units > remainingUnits || !isValidSessionTimeRange(startTime, endTime)) {
      setLocalError('Enter positive whole units within the remaining amount, a capacity-valid room, and an end time later than the start time.')
      return
    }
    setLocalError('')
    void onSubmit({ semesterId: semester.id, date: sessionDate, startTime, endTime, units, roomId })
  }

  return (
    <section className="manual-session-editor" aria-labelledby="manual-session-title">
      <div className="section-heading"><h3 id="manual-session-title">Add one Draft Session</h3></div>
      <label className="constraint-field"><span>Date</span><input name="manual-date" type="date" value={sessionDate} min={semester.startDate} max={semester.endDate} onChange={(event) => setSessionDate(event.target.value)} /></label>
      <div className="manual-time-grid">
        <label className="constraint-field"><span>Start time</span><input name="manual-start-time" type="time" value={startTime} onChange={(event) => { const value = event.target.value; setStartTime(value); setEndTime(calculateDefaultEndTime(value, units) ?? '') }} /></label>
        <label className="constraint-field"><span>Units</span><input name="manual-units" type="number" min="1" step="1" max={remainingUnits} value={units} onChange={(event) => { const value = Number(event.target.value); setUnits(value); setEndTime(calculateDefaultEndTime(startTime, value) ?? '') }} /></label>
        <label className="constraint-field"><span>End time</span><input name="manual-end-time" type="time" value={endTime} onChange={(event) => setEndTime(event.target.value)} /></label>
      </div>
      <label className="constraint-field"><span>Lecturer</span><input value={course.lecturer?.name ?? 'No course Lecturer'} readOnly /></label>
      <label className="constraint-field"><span>Cohort</span><input value={`${course.cohort.name} (${course.cohortSize})`} readOnly /></label>
      <label className="constraint-field"><span>Room</span><select value={roomId ?? ''} onChange={(event) => setRoomId(Number(event.target.value))}>{rooms.map((room) => <option key={room.id} value={room.id}>{room.name} ({room.capacity} seats)</option>)}</select></label>
      {localError && <div className="alert-item" role="alert">{localError}</div>}
      {errors.length > 0 && <ErrorList errors={errors} />}
      <button type="button" className="generate-button" onClick={submit} disabled={isBusy || !roomId || remainingUnits <= 0}>{isSaving ? 'Adding…' : 'Add Draft Session'}</button>
      <p className="sr-only" aria-live="polite">{endTime ? `Proposed end time ${endTime}.` : ''}</p>
    </section>
  )
}
