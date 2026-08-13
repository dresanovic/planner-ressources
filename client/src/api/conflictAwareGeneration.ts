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
  mode: 'decision_required'
  saved: false
  candidateFingerprint: string
  preparedEvidence: PreparedGenerationEvidence
  comparison: RegenerationComparison
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
    return await fetch(input, init)
  } catch {
    throw [{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }]
  }
}
import type { GenerationConstraints } from './draftSchedule'
