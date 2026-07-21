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
import {
  createManualExam,
  deleteExam,
  getExamPlanningOverview,
  saveExamConfiguration,
  updateExam,
  type CreateManualExamRequest,
  type ExamPlanningOverview,
  type ExamSession,
  type ExamSchedulingApiError,
  type SaveExamConfigurationRequest,
  type UpdateExamRequest,
} from '../api/examScheduling'
import { ExamRequirementEditor } from '../components/ExamRequirementEditor'
import { ExamGenerationPanel } from '../components/ExamGenerationPanel'
import { ExamManualSessionEditor } from '../components/ExamManualSessionEditor'
import { ExamDeletionDialog } from '../components/ExamDeletionDialog'
import {
  createWorkingRevision,
  getScheduleLifecycle,
  getScheduleRevision,
  prepareSchedulePublication,
  transitionScheduleRevision,
  type PublicationPreparation,
  type ScheduleLifecycleApiError,
  type ScheduleLifecycleOverview,
  type ScheduleRevisionSummary,
  type ScheduleRevisionContent,
} from '../api/scheduleLifecycle'
import { ScheduleLifecyclePanel } from '../components/ScheduleLifecyclePanel'
import { PublicationConfirmationDialog } from '../components/PublicationConfirmationDialog'
import { AbandonRevisionDialog } from '../components/AbandonRevisionDialog'

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
  const [examOverview, setExamOverview] = useState<ExamPlanningOverview | null>(null)
  const [examRefreshError, setExamRefreshError] = useState(false)
  const [examBusy, setExamBusy] = useState(false)
  const [examError, setExamError] = useState('')
  const [examEditor, setExamEditor] = useState<'create' | ExamSession | null>(null)
  const [examDeletion, setExamDeletion] = useState<ExamSession | null>(null)
  const [lifecycleOverview, setLifecycleOverview] = useState<ScheduleLifecycleOverview | null>(null)
  const [selectedLifecycleRevisionId, setSelectedLifecycleRevisionId] = useState<number | null>(null)
  const [publicationPreparation, setPublicationPreparation] = useState<PublicationPreparation | null>(null)
  const [lifecycleBusy, setLifecycleBusy] = useState(false)
  const [lifecycleRefreshError, setLifecycleRefreshError] = useState(false)
  const [lifecycleError, setLifecycleError] = useState('')
  const [selectedRevisionContent, setSelectedRevisionContent] = useState<ScheduleRevisionContent | null>(null)
  const [abandonRevision, setAbandonRevision] = useState<ScheduleRevisionSummary | null>(null)
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
  const activeScheduleRevisionId = lifecycleOverview?.activeWorkingRevision?.revisionId ?? null
  const selectedLifecycleRevision = lifecycleOverview?.revisions.find((item) => item.revisionId === selectedLifecycleRevisionId) ?? lifecycleOverview?.activeWorkingRevision ?? lifecycleOverview?.currentPublication ?? null
  const mutationBusy = singleGenerating || batchPreparing || batchExecuting || manualSaving || sessionUpdating || deletionBusy || lifecycleBusy
  const contextBusy = mutationBusy || overviewLoading || examBusy
  const writeBusy = contextBusy || overviewRefreshError || examRefreshError || lifecycleRefreshError || activeScheduleRevisionId == null
  const currentExamOverview = examOverview?.semesterId === selectedSemesterId ? examOverview : null
  const selectedExamState = useMemo(() => currentExamOverview?.courses.find((course) => course.courseId === selectedCourseId) ?? null, [currentExamOverview, selectedCourseId])
  const selectedCourseResources = useMemo(() => planningOptions?.courseResources.find((item) => item.courseId === selectedCourseId), [planningOptions, selectedCourseId])
  const examLecturers = useMemo(() => (selectedCourseResources?.eligibleLecturers ?? []).filter((item) => item.isEligible && item.isUsable).map((item) => ({ id: item.id, name: item.name, referenceCode: item.referenceCode })), [selectedCourseResources])
  const examRooms = useMemo(() => (selectedCourseResources?.eligibleRooms ?? []).filter((item) => item.isEligible && item.isUsable).map((item) => ({ id: item.id, name: item.name, capacity: item.capacity ?? undefined })), [selectedCourseResources])
  const allExams = useMemo(() => currentExamOverview?.courses.flatMap((course) => [...(course.activeExam ? [course.activeExam] : []), ...course.pastExams]) ?? [], [currentExamOverview])
  const examCourseNames = useMemo(() => Object.fromEntries((currentExamOverview?.courses ?? []).map((course) => [course.courseId, course.courseName])), [currentExamOverview])
  const displayedRevisionContent = selectedRevisionContent?.revision.revisionId === selectedLifecycleRevision?.revisionId ? selectedRevisionContent : null
  const displaySchedules = displayedRevisionContent ? snapshotSchedules(displayedRevisionContent) : schedules
  const displayExams = displayedRevisionContent ? snapshotExams(displayedRevisionContent) : allExams

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
  }, [selectedSemesterId, catalogRevision])

  useEffect(() => {
    if (!selectedSemesterId) return
    let current = true
    void getScheduleLifecycle(selectedSemesterId)
      .then((value) => {
        if (!current) return
        setLifecycleOverview(value)
        setSelectedLifecycleRevisionId(value.activeWorkingRevision?.revisionId ?? value.currentPublication?.revisionId ?? null)
      })
      .catch(() => { if (current) setLifecycleRefreshError(true) })
      .finally(() => { if (current) setLifecycleBusy(false) })
    return () => { current = false }
  }, [selectedSemesterId, catalogRevision])

  useEffect(() => {
    if (!selectedSemesterId) return
    let current = true
    void getExamPlanningOverview(selectedSemesterId).then((value) => { if (current) { setExamOverview(value); setExamRefreshError(false) } }).catch(() => { if (current) setExamRefreshError(true) })
    return () => { current = false }
  }, [selectedSemesterId, catalogRevision])

  useEffect(() => {
    const revisionId = selectedLifecycleRevision?.revisionId
    if (!revisionId || selectedLifecycleRevision?.isActiveWorking) return
    let current = true
    void getScheduleRevision(revisionId)
      .then((content) => { if (current) { setSelectedRevisionContent(content); setLifecycleError('') } })
      .catch((reason: ScheduleLifecycleApiError) => { if (current) setLifecycleError(reason.errors?.map((item) => item.message).join(' ') || 'Could not load the selected revision.') })
    return () => { current = false }
  }, [selectedLifecycleRevision?.revisionId, selectedLifecycleRevision?.isActiveWorking])

  async function refreshExamOverview(semesterId = selectedSemesterId) {
    if (!semesterId) return false
    try { const value = await getExamPlanningOverview(semesterId); if (selectedSemesterIdRef.current === semesterId) { setExamOverview(value); setExamRefreshError(false) }; return true } catch { if (selectedSemesterIdRef.current === semesterId) setExamRefreshError(true); return false }
  }

  async function handleExamConfiguration(request: SaveExamConfigurationRequest) {
    if (!selectedCourseId) return
    setExamBusy(true); setExamError('')
    try { const state=await saveExamConfiguration(selectedCourseId, request); if (!await refreshExamOverview(state.semesterId)) setExamError('The exam requirement was saved, but the semester review could not be refreshed. Retry the exam refresh before continuing.'); setExamEditor(null) } catch (reason) { const failure = reason as ExamSchedulingApiError; setExamError(failure.errors?.map((item) => item.message).join(' ') || 'Could not save exam requirement.'); if (failure.status === 409) await refreshExamOverview(failure.currentState?.semesterId ?? request.semesterId) } finally { setExamBusy(false) }
  }

  async function handleExamPlacement(request: Omit<CreateManualExamRequest, 'scheduleRevisionId'> | Omit<UpdateExamRequest, 'scheduleRevisionId'>) {
    if (!selectedCourseId || !activeScheduleRevisionId) return
    setExamBusy(true); setExamError('')
    try { const guarded = { ...request, scheduleRevisionId: activeScheduleRevisionId }; const state = examEditor === 'create' ? await createManualExam(selectedCourseId, guarded as CreateManualExamRequest) : await updateExam((examEditor as ExamSession).id, guarded as UpdateExamRequest); if (!await refreshExamOverview(state.semesterId)) setExamError('The exam placement was saved, but the semester review could not be refreshed. Retry the exam refresh before continuing.'); setExamEditor(null) } catch (reason) { const failure = reason as ExamSchedulingApiError; setExamError(failure.errors?.map((item) => item.message).join(' ') || 'Could not save exam placement.'); if (failure.status === 409) { setExamEditor(null); await refreshExamOverview(failure.currentState?.semesterId ?? selectedSemesterId) } } finally { setExamBusy(false) }
  }

  async function confirmExamDeletion() {
    if (!examDeletion || !activeScheduleRevisionId) return
    setExamBusy(true); setExamError('')
    try { const result = await deleteExam(examDeletion.id, { scheduleRevisionId: activeScheduleRevisionId, confirmed: true, expectedExamRevision: examDeletion.revision, inputSnapshotToken: examDeletion.inputSnapshotToken }); if (!await refreshExamOverview(result.state.semesterId)) setExamError('The exam was deleted, but the semester review could not be refreshed. Retry the exam refresh before continuing.'); setExamDeletion(null) } catch (reason) { const failure = reason as ExamSchedulingApiError; setExamError(failure.errors?.map((item) => item.message).join(' ') || 'Could not delete exam.'); if (failure.status === 409) { setExamDeletion(null); await refreshExamOverview(failure.currentState?.semesterId ?? selectedSemesterId) } } finally { setExamBusy(false) }
  }

  async function refreshOverview(semesterId: number, resetInteractions = true) {
    setOverviewLoading(true)
    setOverviewRefreshError(false)
    try {
      const [current, currentExams, currentLifecycle] = await Promise.all([
        getDraftSchedules(semesterId),
        getExamPlanningOverview(semesterId),
        getScheduleLifecycle(semesterId),
      ])
      setSchedules(current)
      setExamOverview(currentExams)
      setExamRefreshError(false)
      setLifecycleOverview(currentLifecycle)
      setLifecycleRefreshError(false)
      setSelectedLifecycleRevisionId((selected) => currentLifecycle.revisions.some((item) => item.revisionId === selected) ? selected : currentLifecycle.activeWorkingRevision?.revisionId ?? currentLifecycle.currentPublication?.revisionId ?? null)
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

  async function startInitialDraft() {
    if (!selectedSemesterId || !lifecycleOverview) return
    setLifecycleBusy(true); setLifecycleError('')
    try {
      const current = await createWorkingRevision(selectedSemesterId, lifecycleOverview.stateToken)
      setLifecycleOverview(current)
      setSelectedLifecycleRevisionId(current.activeWorkingRevision?.revisionId ?? null)
      await refreshOverview(selectedSemesterId, false)
    } catch (reason) {
      const failure = reason as ScheduleLifecycleApiError
      if (failure.currentOverview) setLifecycleOverview(failure.currentOverview)
      setLifecycleError(failure.errors?.map((item) => item.message).join(' ') || 'Could not start the Draft revision.')
    } finally { setLifecycleBusy(false) }
  }

  async function preparePublication(revision: ScheduleRevisionSummary) {
    if (!lifecycleOverview) return
    setLifecycleBusy(true); setLifecycleError('')
    try { setPublicationPreparation(await prepareSchedulePublication(revision.revisionId, revision.revisionVersion, lifecycleOverview.stateToken)) }
    catch (reason) {
      const failure = reason as ScheduleLifecycleApiError
      if (failure.currentOverview) setLifecycleOverview(failure.currentOverview)
      setLifecycleError(failure.errors?.map((item) => item.message).join(' ') || 'Could not prepare publication.')
    } finally { setLifecycleBusy(false) }
  }

  async function confirmPublication() {
    if (!publicationPreparation || !lifecycleOverview || !selectedSemesterId) return
    setLifecycleBusy(true); setLifecycleError('')
    try {
      const current = await transitionScheduleRevision(publicationPreparation.targetRevision.revisionId, { action: 'publish', expectedRevisionVersion: publicationPreparation.targetRevision.revisionVersion, expectedStateToken: lifecycleOverview.stateToken, confirmed: true, publicationToken: publicationPreparation.preparationToken })
      setLifecycleOverview(current)
      setSelectedLifecycleRevisionId(current.currentPublication?.revisionId ?? null)
      setPublicationPreparation(null)
      await refreshOverview(selectedSemesterId, false)
      setProgressAnnouncement(`Revision ${current.currentPublication?.revisionNumber} is now the current publication.`)
    } catch (reason) {
      const failure = reason as ScheduleLifecycleApiError
      setPublicationPreparation(null)
      if (failure.currentOverview) setLifecycleOverview(failure.currentOverview)
      setLifecycleError(failure.errors?.map((item) => item.message).join(' ') || 'Could not publish the revision. Review the refreshed state and retry.')
      await refreshOverview(selectedSemesterId, false)
    } finally { setLifecycleBusy(false) }
  }

  async function handleLifecycleTransition(revision: ScheduleRevisionSummary, action: 'mark_ready' | 'return_to_draft' | 'restore' | 'abandon') {
    if (!lifecycleOverview || !selectedSemesterId) return
    setLifecycleBusy(true); setLifecycleError('')
    try {
      const current = await transitionScheduleRevision(revision.revisionId, { action, expectedRevisionVersion: revision.revisionVersion, expectedStateToken: lifecycleOverview.stateToken, confirmed: action === 'abandon' || action === 'restore' })
      setLifecycleOverview(current)
      setSelectedLifecycleRevisionId(current.activeWorkingRevision?.revisionId ?? current.currentPublication?.revisionId ?? revision.revisionId)
      setAbandonRevision(null)
      await refreshOverview(selectedSemesterId, false)
      setProgressAnnouncement(action === 'mark_ready' ? 'Revision marked Ready for review.' : action === 'return_to_draft' ? 'Revision returned to Draft.' : action === 'restore' ? 'Abandoned revision restored as the active Draft.' : 'Revision abandoned. The current publication is unchanged.')
    } catch (reason) {
      const failure = reason as ScheduleLifecycleApiError
      if (failure.currentOverview) setLifecycleOverview(failure.currentOverview)
      setLifecycleError(failure.errors?.map((item) => item.message).join(' ') || 'Could not change the revision state.')
    } finally { setLifecycleBusy(false) }
  }

  async function handleGenerateSingle() {
    if (planningSelectionInvalid) {
      const code = semesterSelectionMissing ? 'SEMESTER_NO_LONGER_AVAILABLE' : courseSelectionInvalid ? 'COURSE_SEMESTER_MISMATCH' : (selectedCourse?.availability?.reasons[0] ?? 'COURSE_UNAVAILABLE')
      setErrors([{ code, message: 'Choose an available Course and Semester before generating.' }])
      return
    }
    if (!selectedCourseId || !selectedSemesterId || !generationConstraints || !activeScheduleRevisionId) {
      setErrors([{ code: 'MISSING_SELECTION', message: 'Select a course and semester.' }])
      return
    }
    setSingleGenerating(true)
    setErrors([])
    try {
      await generateDraftSchedule(
        selectedCourseId,
        selectedSemesterId,
        activeScheduleRevisionId,
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
    if (!selectedSemesterId || !activeScheduleRevisionId) return
    setBatchPreparing(true)
    setBatchErrors([])
    try {
      const prepared = await prepareConflictAwareGeneration(selectedSemesterId, activeScheduleRevisionId, courseIds, unavailableDates)
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
      if (!activeScheduleRevisionId) return
      const prepared = await prepareConflictAwareGeneration(semesterId, activeScheduleRevisionId, courseIds, unavailableDates)
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

  async function handleUpdateSession(sessionId: number, payload: Omit<UpdateDraftSessionRequest, 'scheduleRevisionId'>) {
    if (!activeScheduleRevisionId) return
    setSessionUpdating(true)
    try {
      await updateDraftSession(sessionId, { ...payload, scheduleRevisionId: activeScheduleRevisionId })
      if (selectedSemesterId) await refreshOverview(selectedSemesterId, false)
    } finally {
      setSessionUpdating(false)
    }
  }

  async function handleCreateManualSession(payload: Omit<CreateManualDraftSessionRequest, 'scheduleRevisionId'>) {
    if (!selectedCourseId || !selectedSemesterId || !activeScheduleRevisionId) return
    setManualSaving(true)
    setManualErrors([])
    try {
      const result = await createManualDraftSession(selectedCourseId, { ...payload, scheduleRevisionId: activeScheduleRevisionId })
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
    if (!sessionDeletion || !activeScheduleRevisionId) return
    setDeletionBusy(true)
    setDeletionErrors([])
    try {
      const result = await deleteDraftSession(
        sessionDeletion.sessionId,
        sessionDeletion.draftScheduleId,
        sessionDeletion.draftRevision,
        activeScheduleRevisionId,
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
    if (!courseDeletion || !activeScheduleRevisionId) return
    setDeletionBusy(true)
    setDeletionErrors([])
    try {
      const result = await clearCourseDraft(
        courseDeletion.courseId,
        courseDeletion.semesterId,
        courseDeletion.draftScheduleId,
        courseDeletion.draftRevision,
        activeScheduleRevisionId,
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
                    {selectedExamState && <ExamRequirementEditor key={`${selectedExamState.courseId}-${selectedExamState.configuration?.revision ?? 0}-${selectedExamState.activeExam?.revision ?? 0}`} state={selectedExamState} lecturers={examLecturers} busy={writeBusy || examBusy} onSave={handleExamConfiguration} />}
                    {selectedExamState?.configuration && selectedExamState.finalTeachingAnchor && !selectedExamState.activeExam && <button type="button" className="secondary-button" disabled={writeBusy || examBusy} onClick={()=>setExamEditor('create')}>Place exam manually</button>}
                    {examError && <div className="alert-item" role="alert">{examError}</div>}
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
            {lifecycleOverview && <ScheduleLifecyclePanel overview={lifecycleOverview} selectedRevisionId={selectedLifecycleRevision?.revisionId ?? null} busy={lifecycleBusy} onStartDraft={() => void startInitialDraft()} onSelectRevision={setSelectedLifecycleRevisionId} onPreparePublication={(revision) => void preparePublication(revision)} onTransition={(revision, action) => void handleLifecycleTransition(revision, action as 'mark_ready' | 'return_to_draft' | 'restore')} onAbandon={setAbandonRevision} />}
            {lifecycleError && <div className="refresh-error" role="alert">{lifecycleError}</div>}
            {lifecycleRefreshError && <div className="refresh-error" role="alert"><span>Could not refresh schedule lifecycle. Schedule changes are unavailable.</span><button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId, false)}>Retry lifecycle refresh</button></div>}
            {batchResult && <BatchResultSummary result={batchResult} retryDisabled={writeBusy} onRetryFailed={() => void retryFailedCourses()} />}
            {overviewRefreshError && (
              <div className="refresh-error" role="alert">
                <span>Could not refresh the Courses overview. The last known schedules remain visible.</span>
                <button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId, false)} disabled={overviewLoading}>Retry refresh</button>
              </div>
            )}
            {deletionNotice && <div className="refresh-error" role="alert">{deletionNotice}</div>}
            {examRefreshError && <div className="refresh-error" role="alert"><span>Could not refresh exam planning. The last complete exam view remains visible.</span><button type="button" onClick={()=>void refreshExamOverview()}>Retry exam refresh</button></div>}
            {selectedSemesterId && activeScheduleRevisionId && currentExamOverview && <ExamGenerationPanel semesterId={selectedSemesterId} scheduleRevisionId={activeScheduleRevisionId} courses={currentExamOverview.courses} disabled={writeBusy || examBusy} onChanged={async()=>{ await refreshOverview(selectedSemesterId, false) }} />}
            <DraftSchedulePanel
              resetKey={overviewResetKey}
              schedules={displaySchedules}
              rooms={planningOptions?.rooms ?? []}
              lecturers={planningOptions?.lecturers ?? []}
              courseResources={planningOptions?.courseResources ?? []}
              onUpdateSession={handleUpdateSession}
              onDeleteSession={beginSessionDeletion}
              isBusy={writeBusy}
              exams={displayExams}
              onEditExam={(exam)=>{ setSelectedCourseId(exam.courseId); setExamEditor(exam) }}
              onDeleteExam={setExamDeletion}
              examCourseNames={examCourseNames}
              readOnly={selectedLifecycleRevision?.revisionId !== activeScheduleRevisionId}
              contextLabel={selectedLifecycleRevision ? `${selectedLifecycleRevision.isCurrentPublication ? 'Current publication' : selectedLifecycleRevision.isActiveWorking ? 'Active working revision' : 'Historical revision'} · Revision ${selectedLifecycleRevision.revisionNumber}` : undefined}
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
      {examEditor && selectedExamState && (examEditor !== 'create' || selectedExamState.configuration) && (
        <div className="dialog-backdrop"><div className="replacement-dialog"><ExamManualSessionEditor mode={examEditor === 'create' ? 'create' : 'edit'} configuration={selectedExamState.configuration ?? undefined} exam={examEditor === 'create' ? undefined : examEditor} snapshotToken={examEditor === 'create' ? selectedExamState.inputSnapshotToken : examEditor.inputSnapshotToken} semesterId={selectedExamState.semesterId} lecturers={examLecturers} rooms={examRooms} busy={examBusy} serverError={examError || undefined} onCancel={()=>setExamEditor(null)} onSubmit={handleExamPlacement}/></div></div>
      )}
      {examDeletion && <ExamDeletionDialog courseName={examCourseNames[examDeletion.courseId] ?? `Course #${examDeletion.courseId}`} exam={examDeletion} busy={examBusy} error={examError || undefined} onCancel={()=>setExamDeletion(null)} onConfirm={confirmExamDeletion}/>}
      {publicationPreparation && <PublicationConfirmationDialog preparation={publicationPreparation} busy={lifecycleBusy} onCancel={() => setPublicationPreparation(null)} onConfirm={() => void confirmPublication()} />}
      {abandonRevision && lifecycleOverview && <AbandonRevisionDialog semesterName={lifecycleOverview.semesterName} revision={abandonRevision} currentPublication={lifecycleOverview.currentPublication} busy={lifecycleBusy} onCancel={() => setAbandonRevision(null)} onConfirm={() => void handleLifecycleTransition(abandonRevision, 'abandon')} />}
    </>
  )
}

function snapshotSchedules(content: ScheduleRevisionContent): DraftSchedule[] {
  return content.snapshot.courses.filter((course) => course.draftStatus != null || course.teachingSessions.length > 0).map((course) => ({
    draftScheduleId: -course.sourceCourseId,
    revision: content.revision.revisionVersion,
    courseId: course.sourceCourseId,
    semesterId: content.revision.semesterId,
    context: { course: { id: course.sourceCourseId, name: course.name }, cohort: { id: course.cohort.sourceId, name: course.cohort.name }, cohortSize: course.cohort.size, lecturer: { id: course.teachingSessions[0]?.lecturer.sourceId ?? 0, name: course.teachingSessions[0]?.lecturer.name ?? 'Captured lecturer' }, room: { id: course.teachingSessions[0]?.room.sourceId ?? 0, name: course.teachingSessions[0]?.room.name ?? 'Captured room' }, studyType: { id: course.studyType.sourceId, name: course.studyType.name } },
    sessions: course.teachingSessions.map((session) => ({ id: session.sourceSessionId, date: session.date, startTime: session.startTime, endTime: session.endTime, units: session.units, courseId: course.sourceCourseId, lecturerId: session.lecturer.sourceId, lecturerName: session.lecturer.name, lecturerReferenceCode: session.lecturer.referenceCode, cohortId: course.cohort.sourceId, roomId: session.room.sourceId, roomName: session.room.name, roomReferenceCode: session.room.referenceCode, studyTypeId: course.studyType.sourceId, timeWindowId: session.timeWindowId, constraintWindowIndex: session.constraintWindowIndex, validationAlerts: [], lecturer: { id: session.lecturer.sourceId, name: session.lecturer.name, referenceCode: session.lecturer.referenceCode }, room: { id: session.room.sourceId, name: session.room.name, referenceCode: session.room.referenceCode } })),
  }))
}

function snapshotExams(content: ScheduleRevisionContent): ExamSession[] {
  return content.snapshot.examSessions.map((exam) => ({ id: exam.sourceExamId, revision: content.revision.revisionVersion, courseId: exam.course.sourceId, semesterId: content.revision.semesterId, configurationIdentifier: exam.configurationIdentifier, examType: exam.examType, durationMinutes: exam.durationMinutes, requiredCapacity: exam.requiredCapacity, recommendedStartDate: exam.recommendedStartDate, recommendedEndDate: exam.recommendedEndDate, recommendationWasOverridden: exam.recommendationWasOverridden, outsideRecommendedWindow: exam.outsideRecommendedWindow, finalTeachingAnchor: { date: exam.finalTeachingDate, endTime: exam.finalTeachingEndTime, teachingSessionId: 0 }, date: exam.examDate, startTime: exam.startTime, endTime: exam.endTime, lecturer: { id: exam.lecturer.sourceId, name: exam.lecturer.name, referenceCode: exam.lecturer.referenceCode }, cohort: { id: exam.cohort.sourceId, name: exam.cohort.name, referenceCode: null }, room: { id: exam.room.sourceId, name: exam.room.name, referenceCode: exam.room.referenceCode, capacity: exam.room.capacity ?? 0 }, lifecycleStatus: 'active', source: exam.source, validityIssues: [], inputSnapshotToken: '' }))
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
  onSubmit: (payload: Omit<CreateManualDraftSessionRequest, 'scheduleRevisionId'>) => Promise<void>
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
