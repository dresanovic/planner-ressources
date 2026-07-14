import { useEffect, useMemo, useState } from 'react'
import {
  clearGenerationConstraints,
  generateDraftSchedule,
  getDraftSchedules,
  getGenerationConstraints,
  type DraftSchedule,
  type GenerationConstraints,
  type GenerationFailure,
  type UpdateDraftSessionRequest,
  updateDraftSession,
} from '../api/draftSchedule'
import {
  generateMultiCourseDrafts,
  prepareMultiCourseGeneration,
  type BatchApiError,
  type BatchGenerationResult,
  type BatchPreparation,
} from '../api/multiCourseDraftGeneration'
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

type GenerationMode = 'single' | 'batch'

export function CourseSchedulePage() {
  const [planningOptions, setPlanningOptions] = useState<PlanningOptions | null>(null)
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [selectedSemesterId, setSelectedSemesterId] = useState<number | null>(null)
  const [generationConstraints, setGenerationConstraints] = useState<GenerationConstraints | null>(null)
  const [schedules, setSchedules] = useState<DraftSchedule[]>([])
  const [mode, setMode] = useState<GenerationMode>('single')
  const [selectedBatchCourseIds, setSelectedBatchCourseIds] = useState<number[]>([])
  const [errors, setErrors] = useState<GenerationFailure[]>([])
  const [batchErrors, setBatchErrors] = useState<BatchApiError[]>([])
  const [batchPreparation, setBatchPreparation] = useState<BatchPreparation | null>(null)
  const [batchResult, setBatchResult] = useState<BatchGenerationResult | null>(null)
  const [optionsLoading, setOptionsLoading] = useState(true)
  const [constraintsLoading, setConstraintsLoading] = useState(false)
  const [overviewLoading, setOverviewLoading] = useState(false)
  const [singleGenerating, setSingleGenerating] = useState(false)
  const [batchPreparing, setBatchPreparing] = useState(false)
  const [batchExecuting, setBatchExecuting] = useState(false)
  const [overviewRefreshError, setOverviewRefreshError] = useState(false)
  const [overviewResetKey, setOverviewResetKey] = useState(0)

  const selectedCourse = useMemo(
    () => planningOptions?.courses.find((course) => course.id === selectedCourseId) ?? null,
    [planningOptions, selectedCourseId],
  )
  const selectedSemester = useMemo(
    () => planningOptions?.semesters.find((semester) => semester.id === selectedSemesterId) ?? null,
    [planningOptions, selectedSemesterId],
  )
  const writeBusy = singleGenerating || batchPreparing || batchExecuting

  useEffect(() => {
    let current = true
    void getPlanningOptions()
      .then((options) => {
        if (!current) return
        setPlanningOptions(options)
        setSelectedCourseId(options.courses[0]?.id ?? null)
        setSelectedSemesterId(options.semesters[0]?.id ?? null)
      })
      .catch(() => current && setErrors([{ code: 'REQUEST_FAILED', message: 'Could not load planning options.' }]))
      .finally(() => current && setOptionsLoading(false))
    return () => { current = false }
  }, [])

  useEffect(() => {
    if (!selectedCourseId || !selectedSemesterId) return
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
  }, [selectedCourseId, selectedSemesterId])

  useEffect(() => {
    if (!selectedSemesterId) return
    let current = true
    async function loadOverview() {
      setOverviewLoading(true)
      setOverviewRefreshError(false)
      try {
        const value = await getDraftSchedules(selectedSemesterId as number)
        if (current) setSchedules(value)
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
      if (resetInteractions) setOverviewResetKey((key) => key + 1)
    } catch {
      setOverviewRefreshError(true)
    } finally {
      setOverviewLoading(false)
    }
  }

  async function handleGenerateSingle() {
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

  async function startBatch(courseIds = selectedBatchCourseIds, operationKind: 'initial' | 'retry' = 'initial') {
    if (!selectedSemesterId) return
    setBatchPreparing(true)
    setBatchErrors([])
    try {
      const prepared = await prepareMultiCourseGeneration(selectedSemesterId, operationKind, courseIds)
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

  async function executeBatch(preparation: BatchPreparation, confirmed: boolean) {
    setBatchExecuting(true)
    setBatchErrors([])
    try {
      const result = await generateMultiCourseDrafts(preparation, confirmed)
      setBatchResult(result)
      setBatchPreparation(null)
      if (selectedSemesterId !== result.semesterId) setSelectedSemesterId(result.semesterId)
      await refreshOverview(result.semesterId)
    } catch (error) {
      setBatchErrors(toBatchErrors(error))
    } finally {
      setBatchExecuting(false)
    }
  }

  async function retryFailedCourses() {
    if (!batchResult) return
    const failedIds = batchResult.outcomes.filter((outcome) => outcome.status === 'failed').map((outcome) => outcome.courseId)
    setSelectedSemesterId(batchResult.semesterId)
    setSelectedBatchCourseIds(failedIds)
    await startBatchForSemester(batchResult.semesterId, failedIds)
  }

  async function startBatchForSemester(semesterId: number, courseIds: number[]) {
    setBatchPreparing(true)
    setBatchErrors([])
    try {
      const prepared = await prepareMultiCourseGeneration(semesterId, 'retry', courseIds)
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
    await updateDraftSession(sessionId, payload)
    if (selectedSemesterId) await refreshOverview(selectedSemesterId, false)
  }

  return (
    <main className="planner-shell">
      <aside className="sidebar">
        <div className="brand-mark">RP</div>
        <nav aria-label="Planner navigation">
          <a href="#dashboard">Dashboard</a><a href="#courses">Courses</a><a href="#cohorts">Cohorts</a>
          <a href="#rooms">Rooms</a><a className="active" href="#schedule">Schedule</a>
        </nav>
      </aside>

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
                  {mode === 'single' && <SelectField label="Course" value={selectedCourseId ?? ''} options={planningOptions.courses} getLabel={(course) => course.name} onChange={(value) => setSelectedCourseId(Number(value))} />}
                  <SelectField label="Semester" value={selectedSemesterId ?? ''} options={planningOptions.semesters} getLabel={(semester) => semester.name} onChange={(value) => setSelectedSemesterId(Number(value))} />
                </div>
                {mode === 'single' ? (
                  <>
                    <PlanningSummary course={selectedCourse} semester={selectedSemester} />
                    {generationConstraints && <GenerationConstraintEditor constraints={generationConstraints} isLoading={constraintsLoading || singleGenerating} onChange={setGenerationConstraints} onClear={handleClearGenerationConstraints} />}
                    {errors.length > 0 && <ErrorList errors={errors} />}
                    <button type="button" className="generate-button" onClick={handleGenerateSingle} disabled={writeBusy || constraintsLoading}>
                      {singleGenerating ? 'Generating...' : 'Generate'}
                    </button>
                  </>
                ) : (
                  <MultiCourseGenerationPanel courses={planningOptions.courses} selectedCourseIds={selectedBatchCourseIds} onChange={setSelectedBatchCourseIds} onGenerate={() => void startBatch()} disabled={writeBusy} />
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
                <button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId)} disabled={overviewLoading}>Retry refresh</button>
              </div>
            )}
            <DraftSchedulePanel resetKey={overviewResetKey} schedules={schedules} rooms={planningOptions?.rooms ?? []} onUpdateSession={handleUpdateSession} isBusy={overviewLoading} />
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
    </main>
  )
}

function ErrorList({ errors }: { errors: { code: string; message: string }[] }) {
  return <div className="alert-list" role="alert">{errors.map((error, index) => <div className="alert-item" key={`${error.code}-${index}`}><strong>{error.code.replaceAll('_', ' ')}</strong><span>{error.message}</span></div>)}</div>
}

function toFailures(error: unknown, fallback: string): GenerationFailure[] {
  return Array.isArray(error) ? error : [{ code: 'UNKNOWN', message: fallback }]
}

function toBatchErrors(error: unknown): BatchApiError[] {
  return Array.isArray(error) ? error : [{ code: 'BATCH_OPERATION_FAILED', message: 'Multi-course generation failed.' }]
}

type Selectable = { id: number }
type SelectFieldProps<T extends Selectable> = { label: string; value: number | ''; options: T[]; getLabel: (option: T) => string; onChange: (value: string) => void }
function SelectField<T extends Selectable>({ label, value, options, getLabel, onChange }: SelectFieldProps<T>) {
  return <label className="selector-field"><span>{label}</span><select value={value} onChange={(event) => onChange(event.target.value)} disabled={options.length === 0}>{options.map((option) => <option value={option.id} key={option.id}>{getLabel(option)}</option>)}</select></label>
}

function PlanningSummary({ course, semester }: { course: CourseOption | null; semester: SemesterOption | null }) {
  if (!course) return <p className="empty-state">No courses are available.</p>
  return <dl>
    <div><dt>Units</dt><dd>{course.totalUnits}</dd></div>
    <div><dt>Session preference</dt><dd>{course.minSessionUnits}-{course.maxSessionUnits} units</dd></div>
    <div><dt>Cohort</dt><dd>{course.cohort.name}</dd></div>
    <div><dt>Lecturer</dt><dd>{course.lecturer.name}</dd></div>
    <div><dt>Room</dt><dd>{course.room.name}</dd></div>
    <div><dt>Study type</dt><dd>{course.studyType.name}</dd></div>
    <div><dt>Semester dates</dt><dd>{semester ? `${semester.startDate} - ${semester.endDate}` : 'No semester selected'}</dd></div>
  </dl>
}
