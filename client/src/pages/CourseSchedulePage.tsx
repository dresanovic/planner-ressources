import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
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
import {
  createExamPlacementDraft,
  examPlacementDraftsEqual,
  type ExamPlacementDraft,
  type ExamPlacementInput,
} from '../components/examPlacementModel'
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
import { snapshotExamCourseNames, snapshotExams, snapshotSchedules } from './scheduleSnapshot'
import {
  getCalendarWorkspace,
  type CalendarWorkspace,
} from '../api/calendarWorkspace'
import { CalendarPlanningWorkspace } from '../components/CalendarPlanningWorkspace'
import { calendarWorkspaceMatchesSelection } from './calendarWorkspaceSelection'
import { SessionPane } from '../components/SessionPane'
import { DiscardChangesDialog } from '../components/DiscardChangesDialog'
import { TeachingSessionEditor } from '../components/TeachingSessionEditor'
import {
  buildTeachingSessionEditModels,
  createTeachingSessionDraft,
  teachingDraftsEqual,
  type EditableDraftSessionRequest,
} from '../components/sessionEditModel'
import { ScheduleContextHeader } from '../components/ScheduleContextHeader'
import type { ScheduleDestination } from '../components/ApplicationNavigation'
import {
  getLecturerReviewOverview,
  issueLecturerReviewLink,
  replaceLecturerReviewLink,
  revokeLecturerReviewLink,
  type LecturerReviewOverview,
} from '../api/lecturerReview'
import { LecturerReviewManagement } from '../components/LecturerReviewManagement'

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
type PaneMode = 'detail' | 'editing'
type PendingPaneIntent = {
  label: string
  commit: () => void
  restoreFocusTo?: HTMLElement | null
  focusAfterCommit?: () => void
}

export type ScheduleNavigationRequest = PendingPaneIntent
type CourseSchedulePageProps = {
  catalogRevision?: number
  destination?: ScheduleDestination
  active?: boolean
  onNavigationRequesterChange?: (
    requester: ((request: ScheduleNavigationRequest) => void) | null,
  ) => void
  onScheduleDestinationChange?: (
    destination: ScheduleDestination,
  ) => void
}

export function CourseSchedulePage({
  catalogRevision = 0,
  destination = 'calendar',
  active = true,
  onNavigationRequesterChange,
  onScheduleDestinationChange,
}: CourseSchedulePageProps) {
  const [planningOptions, setPlanningOptions] = useState<PlanningOptions | null>(null)
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [selectedSemesterId, setSelectedSemesterId] = useState<number | null>(null)
  const [generationConstraints, setGenerationConstraints] = useState<GenerationConstraints | null>(null)
  const [schedules, setSchedules] = useState<DraftSchedule[]>([])
  const [mode, setMode] = useState<GenerationMode>('single')
  const [planningInputsVisible, setPlanningInputsVisible] = useState(true)
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
  const [selectedOccurrenceRef, setSelectedOccurrenceRef] = useState<string | null>(null)
  const [pendingReviewNavigation, setPendingReviewNavigation] = useState<{
    revisionId: number
    occurrenceRef: string
  } | null>(null)
  const [paneMode, setPaneMode] = useState<PaneMode>('detail')
  const [teachingPaneDraft, setTeachingPaneDraft] = useState<EditableDraftSessionRequest | null>(null)
  const [teachingPaneBaseline, setTeachingPaneBaseline] = useState<EditableDraftSessionRequest | null>(null)
  const [teachingPaneErrors, setTeachingPaneErrors] = useState<GenerationFailure[]>([])
  const [examPaneDraft, setExamPaneDraft] = useState<ExamPlacementDraft | null>(null)
  const [examPaneBaseline, setExamPaneBaseline] = useState<ExamPlacementDraft | null>(null)
  const [paneStatus, setPaneStatus] = useState('')
  const [calendarNavigationStatus, setCalendarNavigationStatus] = useState('')
  const [paneError, setPaneError] = useState('')
  const [pendingPaneIntent, setPendingPaneIntent] = useState<PendingPaneIntent | null>(null)
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
  const [lecturerReviewOverview, setLecturerReviewOverview] = useState<LecturerReviewOverview | null>(null)
  const [lecturerReviewBusy, setLecturerReviewBusy] = useState(false)
  const [lecturerReviewError, setLecturerReviewError] = useState('')
  const [selectedRevisionContent, setSelectedRevisionContent] = useState<ScheduleRevisionContent | null>(null)
  const [revisionLoadFailure, setRevisionLoadFailure] = useState<{ revisionId: number; message: string } | null>(null)
  const [revisionLoadAttempt, setRevisionLoadAttempt] = useState(0)
  const [abandonRevision, setAbandonRevision] = useState<ScheduleRevisionSummary | null>(null)
  const [calendarWorkspace, setCalendarWorkspace] = useState<CalendarWorkspace | null>(null)
  const [calendarWorkspaceLoading, setCalendarWorkspaceLoading] = useState(false)
  const [calendarWorkspaceError, setCalendarWorkspaceError] = useState('')
  const [calendarWorkspaceRefresh, setCalendarWorkspaceRefresh] = useState(0)
  const scheduleContextHeadingRef = useRef<HTMLHeadingElement>(null)
  const calendarRequestSequence = useRef(0)
  const overviewRefreshSequence = useRef(0)
  const lecturerReviewRequestSequence = useRef(0)
  const selectedCourseIdRef = useRef<number | null>(null)
  const selectedSemesterIdRef = useRef<number | null>(null)
  const selectedLifecycleRevisionIdRef = useRef<number | null>(null)

  useEffect(() => { selectedCourseIdRef.current = selectedCourseId }, [selectedCourseId])
  useEffect(() => { selectedSemesterIdRef.current = selectedSemesterId }, [selectedSemesterId])

  useEffect(() => {
    if (!calendarNavigationStatus) return
    const focusResults = () => {
      document
        .querySelector<HTMLElement>('[data-workspace-results-heading]')
        ?.focus({ preventScroll: true })
    }
    focusResults()
    const focusTimer = window.setTimeout(focusResults, 0)
    return () => window.clearTimeout(focusTimer)
  }, [calendarNavigationStatus])

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
  const batchCourseDraftStatuses = useMemo(
    () => selectedSemesterId && loadedOverviewSemesterId === selectedSemesterId && !overviewLoading && !overviewRefreshError
      ? Object.fromEntries(semesterCourses.map((course) => {
          const progress = deriveCourseProgress(course.totalUnits, schedules, course.id, selectedSemesterId)
          return [course.id, {
            hasDraft: schedules.some((schedule) => schedule.courseId === course.id && schedule.semesterId === selectedSemesterId),
            scheduledUnits: progress.scheduledUnits,
            totalUnits: progress.totalUnits,
          }]
        }))
      : undefined,
    [semesterCourses, selectedSemesterId, loadedOverviewSemesterId, overviewLoading, overviewRefreshError, schedules],
  )
  const unavailableDates = useMemo(
    () => [...new Set(unavailableDatesInput.split(',').map((value) => value.trim()).filter(Boolean))].sort(),
    [unavailableDatesInput],
  )
  const selectedDraft = useMemo(
    () => schedules.find((schedule) => schedule.courseId === selectedCourseId && schedule.semesterId === selectedSemesterId) ?? null,
    [schedules, selectedCourseId, selectedSemesterId],
  )
  const activeScheduleRevisionId = lifecycleOverview?.activeWorkingRevision?.revisionId ?? null
  const selectedLifecycleRevision = lifecycleOverview?.revisions.find((item) => item.revisionId === selectedLifecycleRevisionId) ?? lifecycleOverview?.activeWorkingRevision ?? lifecycleOverview?.currentPublication ?? null
  useEffect(() => {
    selectedLifecycleRevisionIdRef.current = selectedLifecycleRevision?.revisionId ?? null
    lecturerReviewRequestSequence.current += 1
  }, [selectedLifecycleRevision?.revisionId])
  const mutationBusy = singleGenerating || batchPreparing || batchExecuting || manualSaving || sessionUpdating || deletionBusy || lifecycleBusy
  const contextBusy = mutationBusy || overviewLoading || examBusy
  const writeBusy = contextBusy || overviewRefreshError || examRefreshError || lifecycleRefreshError || activeScheduleRevisionId == null
  const examConfigurationBusy = contextBusy || overviewRefreshError || examRefreshError
  const currentExamOverview = examOverview?.semesterId === selectedSemesterId ? examOverview : null
  const selectedExamState = useMemo(() => currentExamOverview?.courses.find((course) => course.courseId === selectedCourseId) ?? null, [currentExamOverview, selectedCourseId])
  const selectedCourseResources = useMemo(() => planningOptions?.courseResources.find((item) => item.courseId === selectedCourseId), [planningOptions, selectedCourseId])
  const examLecturers = useMemo(() => (selectedCourseResources?.eligibleLecturers ?? []).filter((item) => item.isEligible && item.isUsable).map((item) => ({ id: item.id, name: item.name, referenceCode: item.referenceCode })), [selectedCourseResources])
  const examRooms = useMemo(() => (selectedCourseResources?.eligibleRooms ?? []).filter((item) => item.isEligible && item.isUsable).map((item) => ({ id: item.id, name: item.name, capacity: item.capacity ?? undefined })), [selectedCourseResources])
  const allExams = useMemo(() => currentExamOverview?.courses.flatMap((course) => [...(course.activeExam ? [course.activeExam] : []), ...course.pastExams]) ?? [], [currentExamOverview])
  const examCourseNames = useMemo(() => Object.fromEntries((currentExamOverview?.courses ?? []).map((course) => [course.courseId, course.courseName])), [currentExamOverview])
  const displayedRevisionContent = selectedRevisionContent?.revision.revisionId === selectedLifecycleRevision?.revisionId ? selectedRevisionContent : null
  const selectedRevisionNeedsSnapshot = selectedLifecycleRevision != null && !selectedLifecycleRevision.isActiveWorking
  const selectedRevisionAvailable = !selectedRevisionNeedsSnapshot || displayedRevisionContent != null
  const selectedRevisionLoading = selectedRevisionNeedsSnapshot && !selectedRevisionAvailable && revisionLoadFailure?.revisionId !== selectedLifecycleRevision?.revisionId
  const displaySchedules = useMemo(
    () => selectedRevisionNeedsSnapshot
      ? (displayedRevisionContent ? snapshotSchedules(displayedRevisionContent) : [])
      : schedules,
    [displayedRevisionContent, schedules, selectedRevisionNeedsSnapshot],
  )
  const displayExams = useMemo(
    () => selectedRevisionNeedsSnapshot
      ? (displayedRevisionContent ? snapshotExams(displayedRevisionContent) : [])
      : allExams,
    [allExams, displayedRevisionContent, selectedRevisionNeedsSnapshot],
  )
  const displayExamCourseNames = useMemo(
    () => displayedRevisionContent ? snapshotExamCourseNames(displayedRevisionContent) : examCourseNames,
    [displayedRevisionContent, examCourseNames],
  )
  const calendarWorkspaceMatchesIntended = calendarWorkspaceMatchesSelection(
    calendarWorkspace,
    selectedSemesterId,
    selectedLifecycleRevision,
  )
  const displayedCalendarWorkspace = calendarWorkspaceMatchesIntended ? calendarWorkspace : null
  const loadedCalendarWorkspace = displayedCalendarWorkspace?.workspaceState === 'loaded'
    ? displayedCalendarWorkspace
    : null
  const selectedOccurrence = loadedCalendarWorkspace?.occurrences.find(
    (item) => item.occurrenceRef === selectedOccurrenceRef,
  ) ?? null
  const displayedLecturerReviewOverview =
    lecturerReviewOverview?.revision.id ===
    selectedLifecycleRevision?.revisionId
      ? lecturerReviewOverview
      : null

  useEffect(() => {
    if (
      pendingReviewNavigation === null ||
      destination !== 'calendar' ||
      selectedLifecycleRevision?.revisionId !==
        pendingReviewNavigation.revisionId ||
      loadedCalendarWorkspace === null
    ) {
      return
    }
    const targetExists = loadedCalendarWorkspace.occurrences.some(
      (item) =>
        item.occurrenceRef === pendingReviewNavigation.occurrenceRef,
    )
    queueMicrotask(() => {
      setPendingReviewNavigation(null)
      if (targetExists) {
        setCalendarNavigationStatus('')
        setSelectedOccurrenceRef(pendingReviewNavigation.occurrenceRef)
        setPaneStatus('Opened the current session from lecturer feedback.')
      } else {
        setSelectedOccurrenceRef(null)
        setPaneStatus('')
        setCalendarNavigationStatus(
          'The current session is no longer available in this revision.',
        )
      }
    })
  }, [
    destination,
    loadedCalendarWorkspace,
    pendingReviewNavigation,
    selectedLifecycleRevision?.revisionId,
  ])
  const teachingEditModels = useMemo(
    () => buildTeachingSessionEditModels(
      displaySchedules,
      planningOptions?.rooms ?? [],
      planningOptions?.lecturers ?? [],
      planningOptions?.courseResources ?? [],
    ),
    [displaySchedules, planningOptions],
  )
  const selectedTeachingModel = selectedOccurrence?.kind === 'teaching'
    ? teachingEditModels.find((item) => item.id === Number(selectedOccurrence.occurrenceRef.split(':')[1])) ?? null
    : null
  const selectedPaneExam = selectedOccurrence?.kind === 'exam'
    ? displayExams.find((item) => item.id === Number(selectedOccurrence.occurrenceRef.split(':')[1])) ?? null
    : null
  const selectedPaneExamState = currentExamOverview?.courses.find(
    (course) => course.courseId === selectedPaneExam?.courseId,
  ) ?? null
  const selectedPaneResources = planningOptions?.courseResources.find(
    (item) => item.courseId === selectedPaneExam?.courseId,
  )
  const paneExamLecturers = (selectedPaneResources?.eligibleLecturers ?? [])
    .filter((item) => item.isEligible && item.isUsable)
    .map((item) => ({ id: item.id, name: item.name }))
  const paneExamRooms = (selectedPaneResources?.eligibleRooms ?? [])
    .filter((item) => item.isEligible && item.isUsable)
    .map((item) => ({ id: item.id, name: item.name, capacity: item.capacity ?? undefined }))
  const paneActionModelAvailable = selectedOccurrence != null && (
    selectedOccurrence.kind === 'teaching'
      ? selectedTeachingModel != null
      : selectedPaneExam != null && selectedPaneExamState != null
  )
  const paneDirty = paneMode === 'editing' && (
    (teachingPaneDraft != null && teachingPaneBaseline != null && !teachingDraftsEqual(teachingPaneDraft, teachingPaneBaseline))
    || (examPaneDraft != null && examPaneBaseline != null && !examPlacementDraftsEqual(examPaneDraft, examPaneBaseline))
  )
  const requestGuardedNavigation = useCallback((intent: ScheduleNavigationRequest) => {
    if (paneDirty) {
      const paneFocusTarget = document.querySelector<HTMLElement>(
        '.session-pane input:not([disabled]), .session-pane select:not([disabled]), .session-pane button:not([disabled]), #session-pane-title',
      )
      setPendingPaneIntent({
        ...intent,
        restoreFocusTo: intent.restoreFocusTo ?? paneFocusTarget,
      })
    }
    else intent.commit()
  }, [paneDirty])

  useEffect(() => {
    onNavigationRequesterChange?.(requestGuardedNavigation)
    return () => onNavigationRequesterChange?.(null)
  }, [onNavigationRequesterChange, requestGuardedNavigation])

  useEffect(() => {
    if (paneMode !== 'editing' || selectedOccurrence == null || paneActionModelAvailable) return
    let current = true
    queueMicrotask(() => {
      if (!current) return
      setPaneMode('detail')
      setTeachingPaneDraft(null)
      setTeachingPaneBaseline(null)
      setTeachingPaneErrors([])
      setExamPaneDraft(null)
      setExamPaneBaseline(null)
      setPaneError('')
      setPaneStatus('Editing ended because the current editable session details are no longer available. Review the refreshed session detail before continuing.')
    })
    return () => { current = false }
  }, [paneActionModelAvailable, paneMode, selectedOccurrence])

  const intendedCalendarContext = selectedSemester
    ? `${selectedSemester.name} · ${selectedLifecycleRevision ? `Revision ${selectedLifecycleRevision.revisionNumber} · ${selectedLifecycleRevision.isCurrentPublication ? 'Current Published' : 'Active Working'}` : 'No revision'}`
    : undefined

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
      .then((content) => { if (current) { setSelectedRevisionContent(content); setRevisionLoadFailure(null) } })
      .catch((reason: ScheduleLifecycleApiError) => { if (current) setRevisionLoadFailure({ revisionId, message: reason.errors?.map((item) => item.message).join(' ') || 'Could not load the selected revision.' }) })
    return () => { current = false }
  }, [selectedLifecycleRevision?.revisionId, selectedLifecycleRevision?.isActiveWorking, revisionLoadAttempt])

  useEffect(() => {
    const revisionId = selectedLifecycleRevision?.revisionId
    if (destination !== 'reviews' || !revisionId) return
    let current = true
    const requestSequence = ++lecturerReviewRequestSequence.current
    const requestIsCurrent = () =>
      current &&
      lecturerReviewRequestSequence.current === requestSequence &&
      selectedLifecycleRevisionIdRef.current === revisionId
    queueMicrotask(() => {
      if (!requestIsCurrent()) return
      setLecturerReviewBusy(true)
      setLecturerReviewError('')
    })
    void getLecturerReviewOverview(revisionId)
      .then((value) => {
        if (requestIsCurrent()) setLecturerReviewOverview(value)
      })
      .catch(() => {
        if (requestIsCurrent()) {
          setLecturerReviewOverview(null)
          setLecturerReviewError('Could not load lecturer review links and feedback.')
        }
      })
      .finally(() => {
        if (requestIsCurrent()) setLecturerReviewBusy(false)
      })
    return () => {
      current = false
    }
  }, [destination, selectedLifecycleRevision?.revisionId])

  useEffect(() => {
    if (!selectedSemesterId) return
    const permittedRevision = selectedLifecycleRevision?.isActiveWorking || selectedLifecycleRevision?.isCurrentPublication
      ? selectedLifecycleRevision.revisionId
      : undefined
    if (selectedLifecycleRevision && !permittedRevision) {
      return
    }
    const sequence = ++calendarRequestSequence.current
    queueMicrotask(() => {
      if (calendarRequestSequence.current !== sequence) return
      setCalendarWorkspaceLoading(true)
      setCalendarWorkspaceError('')
    })
    void getCalendarWorkspace(selectedSemesterId, permittedRevision)
      .then((value) => {
        if (calendarRequestSequence.current === sequence) setCalendarWorkspace(value)
      })
      .catch((reason) => {
        if (calendarRequestSequence.current === sequence) {
          setCalendarWorkspaceError(reason instanceof Error ? reason.message : 'Could not load the calendar workspace.')
        }
      })
      .finally(() => {
        if (calendarRequestSequence.current === sequence) setCalendarWorkspaceLoading(false)
      })
  }, [selectedSemesterId, selectedLifecycleRevision, calendarWorkspaceRefresh])

  async function refreshExamOverview(semesterId = selectedSemesterId) {
    if (!semesterId) return false
    try { const value = await getExamPlanningOverview(semesterId); if (selectedSemesterIdRef.current === semesterId) { setExamOverview(value); setExamRefreshError(false) }; return true } catch { if (selectedSemesterIdRef.current === semesterId) setExamRefreshError(true); return false }
  }

  async function handleIssueLecturerReview(input: {
    lecturerId: number
    durationDays: 1 | 2 | 3
  }) {
    if (!selectedLifecycleRevision) throw new Error('No revision selected.')
    const revisionId = selectedLifecycleRevision.revisionId
    const requestSequence = ++lecturerReviewRequestSequence.current
    const requestIsCurrent = () =>
      lecturerReviewRequestSequence.current === requestSequence &&
      selectedLifecycleRevisionIdRef.current === revisionId
    setLecturerReviewBusy(true)
    setLecturerReviewError('')
    try {
      const result = await issueLecturerReviewLink(
        revisionId,
        input,
      )
      if (requestIsCurrent()) setLecturerReviewOverview(result.overview)
      return result
    } catch (reason) {
      if (requestIsCurrent()) {
        setLecturerReviewError(
          reason instanceof Error
            ? reason.message
            : 'Could not issue the lecturer review link.',
        )
      }
      throw reason
    } finally {
      if (requestIsCurrent()) setLecturerReviewBusy(false)
    }
  }

  async function handleRevokeLecturerReview(linkId: number) {
    if (!selectedLifecycleRevision) throw new Error('No revision selected.')
    const revisionId = selectedLifecycleRevision.revisionId
    const requestSequence = ++lecturerReviewRequestSequence.current
    const requestIsCurrent = () =>
      lecturerReviewRequestSequence.current === requestSequence &&
      selectedLifecycleRevisionIdRef.current === revisionId
    setLecturerReviewBusy(true)
    setLecturerReviewError('')
    try {
      const result = await revokeLecturerReviewLink(linkId)
      if (requestIsCurrent()) setLecturerReviewOverview(result)
      return result
    } catch (reason) {
      if (requestIsCurrent()) {
        setLecturerReviewError(
          reason instanceof Error
            ? reason.message
            : 'Could not revoke the lecturer review link.',
        )
      }
      throw reason
    } finally {
      if (requestIsCurrent()) setLecturerReviewBusy(false)
    }
  }

  async function handleReplaceLecturerReview(
    linkId: number,
    input: { durationDays: 1 | 2 | 3 },
  ) {
    if (!selectedLifecycleRevision) throw new Error('No revision selected.')
    const revisionId = selectedLifecycleRevision.revisionId
    const requestSequence = ++lecturerReviewRequestSequence.current
    const requestIsCurrent = () =>
      lecturerReviewRequestSequence.current === requestSequence &&
      selectedLifecycleRevisionIdRef.current === revisionId
    setLecturerReviewBusy(true)
    setLecturerReviewError('')
    try {
      const result = await replaceLecturerReviewLink(linkId, input)
      if (requestIsCurrent()) setLecturerReviewOverview(result.overview)
      return result
    } catch (reason) {
      if (requestIsCurrent()) {
        setLecturerReviewError(
          reason instanceof Error
            ? reason.message
            : 'The replacement result could not be confirmed.',
        )
      }
      throw reason
    } finally {
      if (requestIsCurrent()) setLecturerReviewBusy(false)
    }
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
    if (selectedSemesterIdRef.current !== semesterId) return true
    const refreshSequence = ++overviewRefreshSequence.current
    setOverviewLoading(true)
    setOverviewRefreshError(false)
    const contextIsCurrent = () => (
      selectedSemesterIdRef.current === semesterId
      && overviewRefreshSequence.current === refreshSequence
    )
    try {
      const criticalWorkspaceRefresh = Promise.all([
        getScheduleLifecycle(semesterId),
        getCalendarWorkspace(semesterId),
      ]).then(([currentLifecycle, currentCalendarWorkspace]) => {
        if (!contextIsCurrent()) return currentLifecycle
        calendarRequestSequence.current += 1
        setLifecycleOverview(currentLifecycle)
        setLifecycleRefreshError(false)
        setCalendarWorkspace(currentCalendarWorkspace)
        setCalendarWorkspaceError('')
        setCalendarWorkspaceLoading(false)
        setSelectedLifecycleRevisionId((selected) => currentLifecycle.revisions.some((item) => item.revisionId === selected) ? selected : currentLifecycle.activeWorkingRevision?.revisionId ?? currentLifecycle.currentPublication?.revisionId ?? null)
        return currentLifecycle
      })
      const [[current, currentExams]] = await Promise.all([
        Promise.all([
          getDraftSchedules(semesterId),
          getExamPlanningOverview(semesterId),
        ]),
        criticalWorkspaceRefresh,
      ])
      if (!contextIsCurrent()) return true
      setSchedules(current)
      setExamOverview(currentExams)
      setExamRefreshError(false)
      setLoadedOverviewSemesterId(semesterId)
      setDeletionNotice('')
      if (resetInteractions) setOverviewResetKey((key) => key + 1)
      return true
    } catch {
      if (!contextIsCurrent()) return true
      setOverviewRefreshError(true)
      return false
    } finally {
      if (contextIsCurrent()) setOverviewLoading(false)
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

  function beginCalendarTeachingDeletion(occurrenceRef: string) {
    const sessionId = Number(occurrenceRef.split(':')[1])
    for (const schedule of displaySchedules) {
      const session = schedule.sessions.find((item) => item.id === sessionId)
      if (session) {
        beginSessionDeletion(session, schedule)
        return
      }
    }
  }

  function clearPaneEditor() {
    setPaneMode('detail')
    setTeachingPaneDraft(null)
    setTeachingPaneBaseline(null)
    setTeachingPaneErrors([])
    setExamPaneDraft(null)
    setExamPaneBaseline(null)
    setPaneError('')
  }

  function commitPaneSelection(reference: string | null) {
    clearPaneEditor()
    setPaneStatus('')
    setCalendarNavigationStatus('')
    setSelectedOccurrenceRef(reference)
  }

  function requestPaneIntent(intent: PendingPaneIntent) {
    requestGuardedNavigation(intent)
  }

  function requestCourseChange(courseId: number | null) {
    requestPaneIntent({
      label: 'another course',
      commit: () => {
        commitPaneSelection(null)
        setSelectedCourseId(courseId)
      },
      focusAfterCommit: () => scheduleContextHeadingRef.current?.focus({ preventScroll: true }),
    })
  }

  function requestSemesterChange(semesterId: number) {
    requestPaneIntent({
      label: 'another semester',
      commit: () => {
        commitPaneSelection(null)
        overviewRefreshSequence.current += 1
        lecturerReviewRequestSequence.current += 1
        selectedLifecycleRevisionIdRef.current = null
        selectedSemesterIdRef.current = semesterId
        setLecturerReviewBusy(false)
        setLecturerReviewError('')
        setSemesterSelectionMissing(false)
        setSelectedSemesterId(semesterId)
        setSelectedBatchCourseIds([])
      },
      focusAfterCommit: () => scheduleContextHeadingRef.current?.focus({ preventScroll: true }),
    })
  }

  function requestRevisionChange(revisionId: number) {
    requestPaneIntent({
      label: 'another schedule revision',
      commit: () => {
        commitPaneSelection(null)
        lecturerReviewRequestSequence.current += 1
        selectedLifecycleRevisionIdRef.current = revisionId
        setLecturerReviewBusy(false)
        setLecturerReviewError('')
        setSelectedLifecycleRevisionId(revisionId)
      },
      focusAfterCommit: () => scheduleContextHeadingRef.current?.focus({ preventScroll: true }),
    })
  }

  function requestOccurrenceSelection(reference: string | null) {
    if (reference === selectedOccurrenceRef) return
    const selectionWasRemovedAuthoritatively = reference == null
      && selectedOccurrenceRef != null
      && !loadedCalendarWorkspace?.occurrences.some((item) => item.occurrenceRef === selectedOccurrenceRef)
    if (selectionWasRemovedAuthoritatively) {
      commitPaneSelection(null)
      return
    }
    requestPaneIntent({
      label: reference == null ? 'the calendar' : 'another session',
      commit: () => commitPaneSelection(reference),
    })
  }

  function openLecturerFeedbackSession(navigation: {
    revisionId: number
    occurrenceRef: string
  }) {
    requestPaneIntent({
      label: 'the current lecturer-feedback session',
      commit: () => {
        commitPaneSelection(null)
        setPendingReviewNavigation(navigation)
        setSelectedLifecycleRevisionId(navigation.revisionId)
        onScheduleDestinationChange?.('calendar')
      },
    })
  }

  function beginPaneEdit() {
    setPaneStatus('')
    setPaneError('')
    setTeachingPaneErrors([])
    if (selectedTeachingModel) {
      const draft = createTeachingSessionDraft(selectedTeachingModel)
      setTeachingPaneBaseline(draft)
      setTeachingPaneDraft(draft)
      setExamPaneBaseline(null)
      setExamPaneDraft(null)
      setPaneMode('editing')
      return
    }
    if (selectedPaneExam) {
      const draft = createExamPlacementDraft({
        exam: selectedPaneExam,
        configuration: selectedPaneExamState?.configuration ?? undefined,
        lecturers: paneExamLecturers,
        rooms: paneExamRooms,
      })
      setExamPaneBaseline(draft)
      setExamPaneDraft(draft)
      setTeachingPaneBaseline(null)
      setTeachingPaneDraft(null)
      setPaneMode('editing')
    }
  }

  function requestCancelPaneEdit() {
    requestPaneIntent({
      label: 'session detail',
      commit: clearPaneEditor,
    })
  }

  async function saveTeachingPane() {
    if (!selectedTeachingModel || !teachingPaneDraft || !activeScheduleRevisionId) return
    setSessionUpdating(true)
    setTeachingPaneErrors([])
    setPaneError('')
    try {
      await updateDraftSession(selectedTeachingModel.id, {
        ...teachingPaneDraft,
        scheduleRevisionId: activeScheduleRevisionId,
      })
      const refreshed = selectedSemesterId ? await refreshOverview(selectedSemesterId, false) : false
      setPaneStatus(refreshed
        ? 'Teaching session saved.'
        : 'Teaching session saved, but the workspace could not be refreshed. Retry refresh before continuing.')
      setPaneMode('detail')
      setTeachingPaneBaseline(teachingPaneDraft)
      setTeachingPaneDraft(null)
    } catch (reason) {
      const failures = Array.isArray(reason)
        ? reason as GenerationFailure[]
        : [{ code: 'SESSION_UPDATE_FAILED', message: 'Could not save the teaching session.' }]
      setTeachingPaneErrors(failures)
    } finally {
      setSessionUpdating(false)
    }
  }

  async function saveExamPane(request: ExamPlacementInput) {
    if (!selectedPaneExam || !activeScheduleRevisionId) return
    setExamBusy(true)
    setPaneError('')
    try {
      const state = await updateExam(selectedPaneExam.id, {
        ...request,
        scheduleRevisionId: activeScheduleRevisionId,
      } as UpdateExamRequest)
      const refreshed = await refreshOverview(state.semesterId, false)
      setPaneStatus(refreshed
        ? 'Exam session saved.'
        : 'Exam session saved, but the workspace could not be refreshed. Retry refresh before continuing.')
      setPaneMode('detail')
      setExamPaneBaseline(examPaneDraft)
      setExamPaneDraft(null)
    } catch (reason) {
      const failure = reason as ExamSchedulingApiError
      setPaneError(failure.errors?.map((item) => item.message).join(' ') || 'Could not save the exam session.')
      const conflictSemesterId = failure.currentState?.semesterId ?? selectedSemesterId
      if (failure.status === 409 && conflictSemesterId != null) {
        await refreshOverview(conflictSemesterId, false)
      }
    } finally {
      setExamBusy(false)
    }
  }

  function deleteCalendarExam(occurrenceRef: string) {
    const examId = Number(occurrenceRef.split(':')[1])
    const exam = displayExams.find((item) => item.id === examId)
    if (exam) setExamDeletion(exam)
  }

  function renderCalendarSessionPane(
    occurrence: NonNullable<typeof selectedOccurrence>,
  ) {
    if (!loadedCalendarWorkspace) return null
    const editor = occurrence.kind === 'teaching'
      ? selectedTeachingModel && teachingPaneDraft
        ? <TeachingSessionEditor
            session={selectedTeachingModel}
            draft={teachingPaneDraft}
            isSaving={sessionUpdating}
            isDisabled={writeBusy && !sessionUpdating}
            errors={teachingPaneErrors}
            onChange={setTeachingPaneDraft}
            onCancel={requestCancelPaneEdit}
            onSave={() => void saveTeachingPane()}
          />
        : null
      : selectedPaneExam && selectedPaneExamState && examPaneDraft && examPaneBaseline
        ? <ExamManualSessionEditor
            mode="edit"
            configuration={selectedPaneExamState.configuration ?? undefined}
            exam={selectedPaneExam}
            snapshotToken={selectedPaneExam.inputSnapshotToken}
            semesterId={selectedPaneExamState.semesterId}
            lecturers={paneExamLecturers}
            rooms={paneExamRooms}
            busy={examBusy}
            serverError={paneError || undefined}
            draft={examPaneDraft}
            baseline={examPaneBaseline}
            onDraftChange={setExamPaneDraft}
            headingLevel="h3"
            headingId="session-pane-exam-editor"
            actionsClassName="session-pane-actions"
            onCancel={requestCancelPaneEdit}
            onSubmit={saveExamPane}
          />
        : null
    return <SessionPane
      occurrence={occurrence}
      workspace={loadedCalendarWorkspace}
      mode={paneMode}
      editor={editor}
      busy={sessionUpdating || examBusy}
      status={paneStatus}
      error={occurrence.kind === 'teaching' ? paneError : undefined}
      decisionOpen={pendingPaneIntent != null}
      actionUnavailableReason={!loadedCalendarWorkspace.selectedRevision.readOnly && !paneActionModelAvailable
        ? 'Session actions are unavailable because the editable schedule details could not be loaded. Retry refresh before continuing.'
        : undefined}
      onRequestClose={() => requestPaneIntent({
        label: 'the calendar',
        commit: () => {
          commitPaneSelection(null)
          window.setTimeout(() => {
            const origin = [...document.querySelectorAll<HTMLButtonElement>('[data-occurrence-ref]')]
              .find((item) => item.dataset.occurrenceRef === occurrence.occurrenceRef)
            origin?.focus({ preventScroll: true })
          }, 0)
        },
      })}
      onRequestEdit={paneMode === 'detail' && paneActionModelAvailable ? beginPaneEdit : undefined}
      onRequestDelete={paneActionModelAvailable
        ? () => occurrence.kind === 'teaching'
          ? beginCalendarTeachingDeletion(occurrence.occurrenceRef)
          : deleteCalendarExam(occurrence.occurrenceRef)
        : undefined}
    />
  }

  return (
    <>
      <section className="workbench">
        <header className="page-header">
          <div><h1>Resource Planner</h1><p>Draft schedule generation for one or several courses</p></div>
          <div className="metadata-pill">{selectedSemester?.name ?? 'No semester selected'}</div>
        </header>

        <ScheduleContextHeader
          destination={destination}
          semesterId={selectedSemesterId}
          semesters={(planningOptions?.semesters ?? []).map((semester) => ({
            id: semester.id,
            label: semester.name,
            unavailable: semester.id === selectedSemesterId && semesterSelectionMissing,
          }))}
          revisionId={selectedLifecycleRevision?.revisionId ?? null}
          revisions={(lifecycleOverview?.revisions ?? []).map((revision) => ({
            id: revision.revisionId,
            label: `Revision ${revision.revisionNumber} · ${revision.state.replaceAll('_', ' ')}`,
          }))}
          courseId={selectedCourseId}
          courses={selectableCourses.map((course) => ({
            id: course.id,
            label: course.name,
            unavailable: course.availability?.available === false,
            statusLabel: course.id === selectedCourseId && courseSelectionInvalid
              ? 'not assigned to selected semester'
              : undefined,
          }))}
          headingRef={scheduleContextHeadingRef}
          onSemesterChange={requestSemesterChange}
          onRevisionChange={requestRevisionChange}
          onCourseChange={requestCourseChange}
        />
        {destination === 'calendar' && <div className="planning-input-visibility">
          <button type="button" className="secondary-button" aria-expanded={planningInputsVisible} aria-controls="planning-inputs" onClick={() => setPlanningInputsVisible((visible) => !visible)}>
            {planningInputsVisible ? 'Hide Planning inputs' : 'Show Planning inputs'}
          </button>
        </div>}

        <div className="planner-grid" data-planning-inputs-visible={destination === 'calendar' && planningInputsVisible ? 'true' : 'false'}>
          <section id="planning-inputs" className="input-summary" aria-labelledby="input-summary-title" hidden={destination !== 'calendar' || !planningInputsVisible} inert={destination !== 'calendar' || !planningInputsVisible || undefined}>
            <h2 id="input-summary-title">Planning inputs</h2>
            {planningOptions ? (
              <>
                <div className="mode-switch" aria-label="Generation mode">
                  <button type="button" className={mode === 'single' ? 'active' : ''} onClick={() => setMode('single')}>One course</button>
                  <button type="button" className={mode === 'batch' ? 'active' : ''} onClick={() => setMode('batch')}>Several courses</button>
                </div>
                <div className="planning-selectors">
                  {mode === 'single' && <SelectField label="Course" value={selectedCourseId ?? ''} options={selectableCourses} getLabel={(course) => `${course.name}${course.availability?.available === false ? ` — unavailable: ${course.availability.reasons.join(', ')}` : ''}${course.id === selectedCourseId && courseSelectionInvalid ? ' — not assigned to selected Semester' : ''}`} onChange={(value) => requestCourseChange(Number(value))} disabled={contextBusy} />}
                  <SelectField label="Semester" value={selectedSemesterId ?? ''} options={planningOptions.semesters} getLabel={(semester) => `${semester.name}${semester.id === selectedSemesterId && semesterSelectionMissing ? ' — unavailable' : ''}`} onChange={(value) => requestSemesterChange(Number(value))} disabled={contextBusy} />
                </div>
                {mode === 'single' ? (
                  <>
                    <PlanningSummary course={selectedCourse} semester={selectedSemester} progress={selectedProgress} progressUnavailableLabel={overviewRefreshError ? 'Unavailable' : 'Loading...'} />
                    {selectedExamState && <ExamRequirementEditor key={`${selectedExamState.courseId}-${selectedExamState.configuration?.revision ?? 0}-${selectedExamState.activeExam?.revision ?? 0}`} state={selectedExamState} lecturers={examLecturers} busy={examConfigurationBusy} saving={examBusy} onSave={handleExamConfiguration} />}
                    {selectedExamState?.configuration && selectedExamState.finalTeachingAnchor && !selectedExamState.activeExam && <button type="button" className="secondary-button" disabled={writeBusy || examBusy} onClick={()=>setExamEditor('create')}>Place exam manually</button>}
                    {examError && <div className="alert-item" role="alert">{examError}</div>}
                    {planningSelectionInvalid && <div className="refresh-error" role="alert">{semesterSelectionMissing ? 'The selected Semester is no longer available. Choose another Semester.' : courseSelectionInvalid ? 'This Course is not assigned to the selected Semester. Choose another Course.' : `This Course is unavailable: ${selectedCourse?.availability?.reasons.join(', ')}`}</div>}
                    {selectedCourse && selectedSemester && (
                      <ManualSessionEditor
                        key={`${selectedCourse.id}-${selectedSemester.id}-${loadedOverviewSemesterId ?? 'loading'}-${planningOptions.lecturers.map((item) => item.id).join('-')}-${planningOptions.cohorts.map((item) => item.id).join('-')}-${planningOptions.rooms.map((item) => item.id).join('-')}`}
                        course={selectedCourse}
                        semester={selectedSemester}
                        lecturers={planningOptions.lecturers}
                        cohorts={planningOptions.cohorts}
                        rooms={planningOptions.rooms}
                        remainingUnits={selectedProgress?.remainingUnits ?? 0}
                        isBusy={writeBusy || selectedProgress == null || planningSelectionInvalid}
                        isSaving={manualSaving}
                        requiresDraft={activeScheduleRevisionId == null}
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
                  <MultiCourseGenerationPanel courses={semesterCourses} courseDraftStatuses={batchCourseDraftStatuses} selectedCourseIds={selectedBatchCourseIds} unavailableDatesInput={unavailableDatesInput} onUnavailableDatesInputChange={setUnavailableDatesInput} onChange={setSelectedBatchCourseIds} onGenerate={() => void startBatch()} disabled={writeBusy} />
                )}
                {batchErrors.length > 0 && <ErrorList errors={batchErrors} />}
              </>
            ) : <p className="empty-state">{optionsLoading ? 'Loading planning options...' : 'Planning options are unavailable.'}</p>}
          </section>

          <div className="schedule-results">
            <section className="schedule-workspace-region calendar-workspace-region" aria-label="Calendar workspace" hidden={destination !== 'calendar'} inert={destination !== 'calendar' || undefined}>
            {calendarNavigationStatus && (
              <p
                className="mutation-feedback calendar-navigation-status"
                role="status"
                aria-live="polite"
              >
                {calendarNavigationStatus}
              </p>
            )}
            {selectedRevisionAvailable && (!selectedLifecycleRevision || selectedLifecycleRevision.isActiveWorking || selectedLifecycleRevision.isCurrentPublication) && <CalendarPlanningWorkspace
              key={selectedSemesterId ?? 'no-semester'}
              workspace={displayedCalendarWorkspace}
              loading={calendarWorkspaceLoading || (!calendarWorkspaceMatchesIntended && !calendarWorkspaceError)}
              error={calendarWorkspaceError || undefined}
              lastKnown={calendarWorkspaceMatchesIntended}
              intendedContext={intendedCalendarContext}
              onRetry={() => setCalendarWorkspaceRefresh((key) => key + 1)}
              onStartDraft={() => void startInitialDraft()}
              onSelectRevision={requestRevisionChange}
              onDeleteTeaching={beginCalendarTeachingDeletion}
              onDeleteExam={deleteCalendarExam}
              selectedCourseId={selectedCourseId}
              onTraceCourse={requestCourseChange}
              selectedOccurrenceRef={selectedOccurrenceRef}
              onSelectedOccurrenceChange={requestOccurrenceSelection}
              renderSessionPane={renderCalendarSessionPane}
              listContent={(workspaceListContext) => <DraftSchedulePanel
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
                examCourseNames={displayExamCourseNames}
                readOnly={selectedLifecycleRevision?.revisionId !== activeScheduleRevisionId}
                contextLabel={selectedLifecycleRevision ? `${selectedLifecycleRevision.isCurrentPublication ? 'Current publication' : 'Active working revision'} · Revision ${selectedLifecycleRevision.revisionNumber}` : undefined}
                workspaceListContext={workspaceListContext}
              />}
            />}
            </section>
            <section className="schedule-workspace-region versions-workspace-region" aria-labelledby="versions-region-title" hidden={destination !== 'versions'} inert={destination !== 'versions' || undefined}>
              <h2 id="versions-region-title">Versions</h2>
            {lifecycleOverview && <ScheduleLifecyclePanel overview={lifecycleOverview} selectedRevisionId={selectedLifecycleRevision?.revisionId ?? null} busy={lifecycleBusy} onStartDraft={() => void startInitialDraft()} onSelectRevision={requestRevisionChange} onPreparePublication={(revision) => void preparePublication(revision)} onTransition={(revision, action) => void handleLifecycleTransition(revision, action as 'mark_ready' | 'return_to_draft' | 'restore')} onAbandon={setAbandonRevision} />}
            {lifecycleError && <div className="refresh-error" role="alert">{lifecycleError}</div>}
            {revisionLoadFailure && revisionLoadFailure.revisionId === selectedLifecycleRevision?.revisionId && <div className="refresh-error" role="alert"><span>{revisionLoadFailure.message}</span><button type="button" onClick={() => { setRevisionLoadFailure(null); setRevisionLoadAttempt((attempt) => attempt + 1) }}>Retry selected revision</button></div>}
            {lifecycleRefreshError && <div className="refresh-error" role="alert"><span>Could not refresh schedule lifecycle. Schedule changes are unavailable.</span><button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId, false)}>Retry lifecycle refresh</button></div>}
            </section>
            <section className="schedule-workspace-region lecturer-reviews-region" aria-labelledby="lecturer-reviews-region-title" hidden={destination !== 'reviews'} inert={destination !== 'reviews' || undefined}>
              <h2 id="lecturer-reviews-region-title">Lecturer coordination</h2>
              {destination === 'reviews' && selectedLifecycleRevision && displayedLecturerReviewOverview == null && !lecturerReviewError && <p role="status">Loading lecturer coordination…</p>}
              {lecturerReviewError && <div className="refresh-error" role="alert">{lecturerReviewError}</div>}
              {active && destination === 'reviews' && displayedLecturerReviewOverview && (
                <LecturerReviewManagement
                  key={displayedLecturerReviewOverview.revision.id}
                  overview={displayedLecturerReviewOverview}
                  busy={lecturerReviewBusy}
                  onIssue={handleIssueLecturerReview}
                  onRevoke={handleRevokeLecturerReview}
                  onReplace={handleReplaceLecturerReview}
                  onOpenCurrentSession={openLecturerFeedbackSession}
                />
              )}
              {!selectedLifecycleRevision && <p>Select a Working or Current Published revision to review lecturer access.</p>}
            </section>
            <section className="schedule-workspace-region calendar-feedback-region" aria-label="Calendar feedback" hidden={destination !== 'calendar'} inert={destination !== 'calendar' || undefined}>
            {batchResult && <BatchResultSummary result={batchResult} retryDisabled={writeBusy} onRetryFailed={() => void retryFailedCourses()} />}
            {overviewRefreshError && (
              <div className="refresh-error" role="alert">
                <span>Could not refresh the Courses overview. The last known schedules remain visible.</span>
                <button type="button" onClick={() => selectedSemesterId && void refreshOverview(selectedSemesterId, false)} disabled={overviewLoading}>Retry refresh</button>
              </div>
            )}
            {deletionNotice && <div className="refresh-error" role="alert">{deletionNotice}</div>}
            </section>
            <section className="schedule-workspace-region exams-workspace-region" aria-labelledby="exams-region-title" hidden={destination !== 'exams'} inert={destination !== 'exams' || undefined}>
              <h2 id="exams-region-title">Exams</h2>
              {selectedExamState && <div className="focused-exam-requirement">
                <ExamRequirementEditor key={`${selectedExamState.courseId}-${selectedExamState.configuration?.revision ?? 0}-${selectedExamState.activeExam?.revision ?? 0}`} state={selectedExamState} lecturers={examLecturers} busy={examConfigurationBusy} saving={examBusy} onSave={handleExamConfiguration} />
                {selectedExamState.configuration && selectedExamState.finalTeachingAnchor && !selectedExamState.activeExam && <button type="button" className="secondary-button" disabled={writeBusy || examBusy} onClick={()=>setExamEditor('create')}>Place exam manually</button>}
              </div>}
              {examError && <div className="alert-item" role="alert">{examError}</div>}
              {examRefreshError && <div className="refresh-error" role="alert"><span>Could not refresh exam planning. The last complete exam view remains visible.</span><button type="button" onClick={()=>void refreshExamOverview()}>Retry exam refresh</button></div>}
              {selectedSemesterId && activeScheduleRevisionId && currentExamOverview && <ExamGenerationPanel semesterId={selectedSemesterId} scheduleRevisionId={activeScheduleRevisionId} courses={currentExamOverview.courses} disabled={writeBusy || examBusy} onChanged={async()=>{ await refreshOverview(selectedSemesterId, false) }} />}
            </section>
            <section className="schedule-workspace-region calendar-history-region" aria-label="Historical schedule content" hidden={destination !== 'calendar'} inert={destination !== 'calendar' || undefined}>
            {selectedRevisionAvailable && selectedLifecycleRevision && !selectedLifecycleRevision.isActiveWorking && !selectedLifecycleRevision.isCurrentPublication ? <DraftSchedulePanel
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
              examCourseNames={displayExamCourseNames}
              readOnly={selectedLifecycleRevision?.revisionId !== activeScheduleRevisionId}
              contextLabel={selectedLifecycleRevision ? `${selectedLifecycleRevision.isCurrentPublication ? 'Current publication' : selectedLifecycleRevision.isActiveWorking ? 'Active working revision' : 'Historical revision'} · Revision ${selectedLifecycleRevision.revisionNumber}` : undefined}
            /> : selectedRevisionLoading ? <p role="status">Loading selected revision…</p> : null}
            </section>
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
      {pendingPaneIntent && <DiscardChangesDialog
        destinationLabel={pendingPaneIntent.label}
        restoreFocusTo={pendingPaneIntent.restoreFocusTo}
        onKeepEditing={() => setPendingPaneIntent(null)}
        onDiscard={() => {
          const intent = pendingPaneIntent
          setPendingPaneIntent(null)
          intent.commit()
          window.setTimeout(() => intent.focusAfterCommit?.(), 0)
        }}
      />}
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
  lecturers,
  cohorts,
  rooms,
  remainingUnits,
  isBusy,
  isSaving,
  requiresDraft,
  errors,
  onSubmit,
}: {
  course: CourseOption
  semester: SemesterOption
  lecturers: PlanningOptions['lecturers']
  cohorts: PlanningOptions['cohorts']
  rooms: PlanningOptions['rooms']
  remainingUnits: number
  isBusy: boolean
  isSaving: boolean
  requiresDraft: boolean
  errors: GenerationFailure[]
  onSubmit: (payload: Omit<CreateManualDraftSessionRequest, 'scheduleRevisionId'>) => Promise<void>
}) {
  const initialUnits = Math.min(2, Math.max(remainingUnits, 1))
  const initialLecturerId = (
    course.lecturer != null && lecturers.some((item) => item.id === course.lecturer!.id)
      ? course.lecturer.id
      : lecturers[0]?.id
  ) ?? null
  const initialCohortId = (
    cohorts.some((item) => item.id === course.cohort.id)
      ? course.cohort.id
      : cohorts[0]?.id
  ) ?? null
  const initialCohortSize = cohorts.find((item) => item.id === initialCohortId)?.studentCount ?? course.cohortSize
  const initialRooms = rooms.filter((room) => room.capacity >= initialCohortSize)
  const initialRoomId = (
    course.room != null && initialRooms.some((item) => item.id === course.room!.id)
      ? course.room.id
      : initialRooms[0]?.id
  ) ?? null
  const [sessionDate, setSessionDate] = useState(semester.startDate)
  const [startTime, setStartTime] = useState('08:00')
  const [units, setUnits] = useState(initialUnits)
  const [endTime, setEndTime] = useState(calculateDefaultEndTime('08:00', initialUnits) ?? '')
  const [lecturerId, setLecturerId] = useState<number | null>(initialLecturerId)
  const [cohortId, setCohortId] = useState<number | null>(initialCohortId)
  const [roomId, setRoomId] = useState<number | null>(initialRoomId)
  const [localError, setLocalError] = useState('')
  const selectedCohort = cohorts.find((item) => item.id === cohortId)
  const capacityValidRooms = rooms.filter(
    (room) => selectedCohort != null && room.capacity >= selectedCohort.studentCount,
  )

  function submit() {
    if (!lecturerId || !cohortId || !roomId || !capacityValidRooms.some((room) => room.id === roomId) || !Number.isInteger(units) || units <= 0 || units > remainingUnits || !isValidSessionTimeRange(startTime, endTime)) {
      setLocalError('Select a Lecturer, Cohort, and capacity-valid Room; enter positive whole units within the remaining amount and an end time later than the start time.')
      return
    }
    setLocalError('')
    void onSubmit({ semesterId: semester.id, date: sessionDate, startTime, endTime, units, lecturerId, cohortId, roomId })
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
      <label className="constraint-field"><span>Lecturer</span><select name="manual-lecturer" value={lecturerId ?? ''} onChange={(event) => setLecturerId(Number(event.target.value))}>{lecturers.map((lecturer) => <option key={lecturer.id} value={lecturer.id}>{lecturer.name}</option>)}</select></label>
      <label className="constraint-field"><span>Cohort</span><select name="manual-cohort" value={cohortId ?? ''} onChange={(event) => {
        const nextCohortId = Number(event.target.value)
        const nextCohortSize = cohorts.find((item) => item.id === nextCohortId)?.studentCount
        const nextRooms = rooms.filter((room) => nextCohortSize != null && room.capacity >= nextCohortSize)
        setCohortId(nextCohortId)
        setRoomId((current) => (
          current != null && nextRooms.some((room) => room.id === current)
            ? current
            : course.room != null && nextRooms.some((room) => room.id === course.room!.id)
              ? course.room.id
              : nextRooms[0]?.id ?? null
        ))
      }}>{cohorts.map((cohort) => <option key={cohort.id} value={cohort.id}>{cohort.name} ({cohort.studentCount})</option>)}</select></label>
      <label className="constraint-field"><span>Room</span><select name="manual-room" value={roomId ?? ''} onChange={(event) => setRoomId(Number(event.target.value))}>{capacityValidRooms.map((room) => <option key={room.id} value={room.id}>{room.name} ({room.capacity} seats)</option>)}</select></label>
      {localError && <div className="alert-item" role="alert">{localError}</div>}
      {errors.length > 0 && <ErrorList errors={errors} />}
      {requiresDraft && <p className="constraint-note">Start a Draft before adding sessions.</p>}
      <button type="button" className="generate-button" onClick={submit} disabled={isBusy || !lecturerId || !cohortId || !roomId || remainingUnits <= 0} aria-busy={isSaving || undefined}>{isSaving ? 'Adding…' : 'Add Draft Session'}</button>
      <p className="sr-only" aria-live="polite">{endTime ? `Proposed end time ${endTime}.` : ''}</p>
    </section>
  )
}
