import { plannerFetch } from './plannerFetch'

export type OptimizationStatus = 'complete' | 'improved_partial' | 'unchanged' | 'failed' | 'stale'

export type OptimizationError = {
  code: string
  message: string
  replacementCourseIds?: number[]
}

export type BlockingReason = {
  code: string
  message: string
  relatedCount: number
  holidayDate?: string
  holidayName?: string
  sourceKind?: 'teaching_session' | 'active_exam'
  sourceId?: number
}

export type PreparedOptimizationCourse = {
  courseId: number
  courseName: string | null
  available: boolean
  unavailableReasons: BlockingReason[]
  draftScheduleId: number | null
  draftRevision: number | null
  scheduledUnits: number
  remainingUnits: number
  replacementRequired: boolean
  effectiveConstraints: GenerationConstraints
  inputSnapshotToken: string
}

export type OptimizationPreparation = {
  semesterId: number
  scheduleRevisionId: number
  unavailableDates: string[]
  sharedSnapshotToken: string
  courses: PreparedOptimizationCourse[]
  replacementCourseIds: number[]
  budgetPolicy: OptimizationBudgetPolicy
}

export type OptimizationBudgetPolicy = {
  defaultSeconds: number
  ceilingSeconds: number
  policyFingerprint: string
}

export type OptimizationOperationPhase =
  | 'preparing' | 'optimizing' | 'checking' | 'ready_to_save' | 'awaiting_decision'
  | 'saving' | 'saved' | 'cancelled' | 'timeout_no_candidate' | 'failed' | 'stale' | 'interrupted'

/** Live authority is memory-only and never part of a status or saved receipt. */
export type OptimizationOperationContext = { operationId: string; contextSecret: string }
export type OptimizationOutcomeIdentity = { operationId: string }
export type OptimizationOperationStatus = {
  operationId: string
  semesterId: number
  scheduleRevisionId: number
  selectedCourseIds: number[]
  selectionCount: number
  phase: OptimizationOperationPhase
  budgetSeconds: number
  elapsedMilliseconds: number
  budgetExhausted: boolean
  currentObjectiveKey: string | null
  saved: boolean
  canAccept: boolean
  canFinalize: boolean
  review: OptimizationDecisionRequiredResult | null
  result: OptimizationGenerationResult | null
  errors: OptimizationError[]
  terminalCode: string | null
}

export type OptimizationOperationStart = OptimizationOperationContext & {
  policyFingerprint: string
  preparation: PreparedGenerationEvidence
}

export async function startOptimizationOperation(preparation: OptimizationPreparation, context: OptimizationOperationContext, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  validateSelection(preparation.courses.map(course=>course.courseId))
  return operationRequest('/operations', {
    method:'POST', signal, body:JSON.stringify({...context,policyFingerprint:preparation.budgetPolicy.policyFingerprint,
      preparation:{semesterId:preparation.semesterId,scheduleRevisionId:preparation.scheduleRevisionId,
        unavailableDates:preparation.unavailableDates,sharedSnapshotToken:preparation.sharedSnapshotToken,
        courses:preparation.courses.map(course=>({courseId:course.courseId,expectedDraftScheduleId:course.draftScheduleId,
          expectedDraftRevision:course.draftRevision,inputSnapshotToken:course.inputSnapshotToken}))}}),
  }, true)
}

export function getOptimizationOperation(operationId: string, secret?: string, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(operationId)}`, {
    signal, headers:secret ? {'X-Optimization-Context':secret} : {},
  })
}

export function decideOptimizationOperation(context: OptimizationOperationContext, candidateFingerprint: string, finalize=false, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(context.operationId)}/${finalize ? 'finalize' : 'accept'}`, {
    method:'POST',signal,body:JSON.stringify({contextSecret:context.contextSecret,candidateFingerprint}),
  }, true)
}

export function cancelOptimizationOperation(operationId: string, reason='cancel', keepalive=false): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(operationId)}/cancel`,{
    method:'POST',body:JSON.stringify({reason}),keepalive,
  },true)
}

async function operationRequest(path: string, init: RequestInit, activity=false): Promise<OptimizationOperationStatus> {
  const response=await plannerFetch(`/api/draft-schedules/optimization${path}`, {...init,...(activity ? {activity:'user' as const} : {})})
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

export type ArrangementImprovement = {
  addedUnits: number
  reducedConflicts: number
  reducedLecturerChanges: number
  reducedRoomChanges: number
}

export type CourseOptimizationOutcome = {
  courseId: number
  courseName: string | null
  status: OptimizationStatus
  draftScheduleId: number | null
  draftRevision: number | null
  scheduledUnits: number
  remainingUnits: number
  saved: boolean
  improvement: ArrangementImprovement | null
  reasons: BlockingReason[]
  errors: OptimizationError[]
}

export type OptimizationGenerationResult = {
  proof?: CandidateProof | null
  mode: 'direct_saved'
  semesterId: number
  summary: {
    total: number
    complete: number
    improvedPartial: number
    unchanged: number
    failed: number
    stale: number
    scheduledUnits: number
    remainingUnits: number
    elapsedMilliseconds: number
    optimalForPreparedSnapshot: boolean
  }
  outcomes: CourseOptimizationOutcome[]
}

export type CoverageFacts = {
  requiredUnits: number
  scheduledUnits: number
  remainingUnits: number
  status: 'complete' | 'partial'
}

export type ResolvedWarning = { code: string; count: number }

export type CourseRegenerationComparison = {
  courseId: number
  courseName: string | null
  current: CoverageFacts
  generated: CoverageFacts
  resolvedCurrentWarnings: ResolvedWarning[]
  remainingReasons: BlockingReason[]
}

export type RegenerationComparison = {
  selectedCourseIds: number[]
  current: CoverageFacts
  generated: CoverageFacts
  courses: CourseRegenerationComparison[]
  replacesAllSelectedSessions: true
  mayReplacePlannerEdits: true
}

export type PreparedGenerationEvidence = {
  semesterId: number
  scheduleRevisionId: number
  unavailableDates: string[]
  sharedSnapshotToken: string
  courses: {
    courseId: number
    expectedDraftScheduleId?: number | null
    expectedDraftRevision?: number | null
    inputSnapshotToken: string
  }[]
}

export type OptimizationDecisionRequiredResult = {
  proof?: CandidateProof | null
  hasSavedSessions?: boolean
  mode: 'decision_required'
  saved: false
  candidateFingerprint: string
  preparedEvidence: PreparedGenerationEvidence
  comparison: RegenerationComparison
}

export type ObjectiveProof = {
  objectiveKey: string
  direction: 'max' | 'min'
  proofStatus: 'proven' | 'unfinished' | 'not_attempted' | 'conditional'
  value: number | null
  preparedSnapshotToken: string
  candidateFingerprint: string
  condition: Record<string, number> | null
}

export type CandidateProof = {
  preparedSnapshotToken: string
  candidateFingerprint: string
  selectedCourseIds: number[]
  requiredUnits: number
  scheduledUnits: number
  coverageProven: boolean
  preferencesProven: boolean
  objectives: ObjectiveProof[]
  unitUpperBound: number | null
  additionalPossibleUnits: number | null
  gapKnown: boolean
}

export type OptimizationGenerationResponse =
  | OptimizationGenerationResult
  | OptimizationDecisionRequiredResult

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function prepareConflictAwareGeneration(
  semesterId: number,
  scheduleRevisionId: number,
  courseIds: number[],
  unavailableDates: string[] = [],
): Promise<OptimizationPreparation> {
  validateSelection(courseIds)
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semesterId, scheduleRevisionId, courseIds, unavailableDates }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

export async function generateConflictAwareSchedules(
  preparation: OptimizationPreparation,
): Promise<OptimizationGenerationResponse> {
  validateSelection(preparation.courses.map((course) => course.courseId))
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      semesterId: preparation.semesterId,
      scheduleRevisionId: preparation.scheduleRevisionId,
      unavailableDates: preparation.unavailableDates,
      sharedSnapshotToken: preparation.sharedSnapshotToken,
      courses: preparation.courses.map((course) => ({
        courseId: course.courseId,
        expectedDraftScheduleId: course.draftScheduleId,
        expectedDraftRevision: course.draftRevision,
        inputSnapshotToken: course.inputSnapshotToken,
      })),
    }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

export async function acceptConflictAwareSchedules(
  preview: OptimizationDecisionRequiredResult,
): Promise<OptimizationGenerationResult> {
  const evidence = preview.preparedEvidence
  validateSelection(evidence.courses.map((course) => course.courseId))
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...evidence,
      candidateFingerprint: preview.candidateFingerprint,
    }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

function validateSelection(courseIds: number[]) {
  if (courseIds.length < 1 || courseIds.length > 20) {
    throw [{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Semester optimization requires 1-20 courses.' }]
  }
  if (new Set(courseIds).size !== courseIds.length) {
    throw [{ code: 'DUPLICATE_COURSE_SELECTION', message: 'Select each course only once.' }]
  }
}

async function parseOptimizationError(response: Response): Promise<OptimizationError[]> {
  try {
    const body = await response.json()
    if (Array.isArray(body.errors)) return body.errors
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { msg?: string }) => ({ code: 'INVALID_REQUEST', message: item.msg ?? 'The optimization request is invalid.' }))
    }
    if (body.code) return [body]
  } catch {
    // Use the safe fallback below.
  }
  return [{ code: 'REQUEST_FAILED', message: 'Could not complete semester optimization.' }]
}

async function request(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await plannerFetch(input, { ...init, activity: 'user' })
  } catch {
    throw [{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }]
  }
}
import type { GenerationConstraints } from './draftSchedule'
