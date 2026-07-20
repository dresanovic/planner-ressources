export type BatchOperationKind = 'initial' | 'retry'

export type PreparedCourseSnapshot = {
  courseId: number
  courseName: string | null
  available: boolean
  draftScheduleId: number | null
  draftRevision: number | null
  replacementRequired: boolean
}

export type BatchPreparation = {
  semesterId: number
  operationKind: BatchOperationKind
  courses: PreparedCourseSnapshot[]
  replacementCourseIds: number[]
}

export type PreparedCourseInput = {
  courseId: number
  expectedDraftScheduleId: number | null
  expectedDraftRevision: number | null
}

export type CourseGenerationFailure = {
  code: string
  message: string
  holidayDate?: string
  holidayName?: string
}

export type CourseGenerationOutcome = {
  courseId: number
  courseName: string | null
  status: 'succeeded' | 'failed'
  draftScheduleId: number | null
  draftRevision: number | null
  errors: CourseGenerationFailure[]
}

export type BatchGenerationResult = {
  semesterId: number
  operationKind: BatchOperationKind
  summary: { total: number; succeeded: number; failed: number }
  outcomes: CourseGenerationOutcome[]
}

export type BatchApiError = {
  code: string
  message: string
  replacementCourseIds?: number[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function prepareMultiCourseGeneration(
  semesterId: number,
  operationKind: BatchOperationKind,
  courseIds: number[],
): Promise<BatchPreparation> {
  validateSelection(operationKind, courseIds)
  const response = await request(`${API_BASE}/api/draft-schedules/batch/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semesterId, operationKind, courseIds }),
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

export async function generateMultiCourseDrafts(
  preparation: BatchPreparation,
  replacementConfirmed: boolean,
): Promise<BatchGenerationResult> {
  validateSelection(
    preparation.operationKind,
    preparation.courses.map((course) => course.courseId),
  )
  const response = await request(`${API_BASE}/api/draft-schedules/batch/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      semesterId: preparation.semesterId,
      operationKind: preparation.operationKind,
      replacementConfirmed,
      courses: preparation.courses.map((course) => ({
        courseId: course.courseId,
        expectedDraftScheduleId: course.draftScheduleId,
        expectedDraftRevision: course.draftRevision,
      })),
    }),
  })
  if (!response.ok) throw await parseError(response)
  return response.json()
}

function validateSelection(operationKind: BatchOperationKind, courseIds: number[]) {
  const minimum = operationKind === 'initial' ? 2 : 1
  if (courseIds.length < minimum || courseIds.length > 50) {
    throw [{ code: 'INVALID_BATCH_SIZE', message: `${operationKind} generation requires ${minimum}-50 courses.` }]
  }
  if (new Set(courseIds).size !== courseIds.length) {
    throw [{ code: 'DUPLICATE_COURSE_SELECTION', message: 'Select each course only once.' }]
  }
}

async function parseError(response: Response): Promise<BatchApiError[]> {
  try {
    const body = await response.json()
    if (Array.isArray(body.errors)) return body.errors
    if (body.code) return [body]
  } catch {
    // Fall through to the safe generic error.
  }
  return [{ code: 'REQUEST_FAILED', message: 'Could not complete multi-course generation.' }]
}

async function request(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch {
    throw [{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }]
  }
}
