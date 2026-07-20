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
}

export type PreparedOptimizationCourse = {
  courseId: number
  courseName: string | null
  available: boolean
  draftScheduleId: number | null
  draftRevision: number | null
  scheduledUnits: number
  remainingUnits: number
  replacementRequired: boolean
  inputSnapshotToken: string
}

export type OptimizationPreparation = {
  semesterId: number
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

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function prepareConflictAwareGeneration(
  semesterId: number,
  courseIds: number[],
  unavailableDates: string[] = [],
): Promise<OptimizationPreparation> {
  validateSelection(courseIds)
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semesterId, courseIds, unavailableDates }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

export async function generateConflictAwareSchedules(
  preparation: OptimizationPreparation,
  replacementConfirmed: boolean,
): Promise<OptimizationGenerationResult> {
  validateSelection(preparation.courses.map((course) => course.courseId))
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      semesterId: preparation.semesterId,
      unavailableDates: preparation.unavailableDates,
      sharedSnapshotToken: preparation.sharedSnapshotToken,
      replacementConfirmed,
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
