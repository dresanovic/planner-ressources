export type DraftSession = {
  id: number
  date: string
  startTime: string
  endTime: string
  units: number
  courseId: number
  lecturerId: number
  lecturerName: string
  lecturerReferenceCode: string
  cohortId: number
  roomId: number
  roomName: string
  roomReferenceCode: string
  studyTypeId: number
  timeWindowId: number | null
  constraintWindowIndex: number
  validationAlerts: ValidationAlert[]
  lecturer: PlanningResource
  room: PlanningResource
}

export type RelatedSession = {
  sessionId: number
  draftScheduleId: number
  courseId: number
  courseName: string
  date: string
  startTime: string
  endTime: string
  cohortName: string
  lecturerName: string
  roomName: string
}

export type ValidationAlert = {
  code: ValidationAlertCode
  message: string
  relatedSessions: RelatedSession[]
  holidayDate?: string | null
  holidayName?: string | null
}

export type ValidationAlertCode =
  | 'LECTURER_OVERLAP' | 'ROOM_OVERLAP' | 'COHORT_OVERLAP' | 'ROOM_CAPACITY'
  | 'GENERATION_CONSTRAINT_VIOLATION' | 'STUDY_TYPE_WINDOW_VIOLATION' | 'VALIDATION_DATA_MISSING'
  | 'LECTURER_UNAVAILABLE' | 'ROOM_UNAVAILABLE' | 'LECTURER_INELIGIBLE' | 'ROOM_INELIGIBLE'
  | 'INSTITUTION_HOLIDAY'

export type PlanningPeriod = {
  startDate: string
  endDate: string
}

export type AllowedTeachingWindow = {
  weekday: number
  startTime: string
  endTime: string
  sourceTimeWindowId?: number | null
}

export type GenerationConstraints = {
  courseId: number
  semesterId: number
  isCustom: boolean
  revision?: number | null
  planningPeriod: PlanningPeriod
  allowedTeachingWindows: AllowedTeachingWindow[]
}

export type PlanningEntity = {
  id: number
  name: string
}

export type PlanningResource = PlanningEntity & { referenceCode: string }

export type DraftScheduleContext = {
  course: PlanningEntity
  cohort: PlanningEntity
  cohortSize: number
  lecturer: PlanningEntity
  room: PlanningEntity
  studyType: PlanningEntity
}

export type DraftSchedule = {
  draftScheduleId: number
  revision: number
  courseId: number
  semesterId: number
  context: DraftScheduleContext
  sessions: DraftSession[]
}

export type ReviewFilters = {
  courseId?: number
  cohortId?: number
  lecturerId?: number
  roomId?: number
  studyTypeId?: number
}

export type ViewMode = 'list' | 'weekly'

export type GenerationFailure = {
  code: string
  message: string
  holidayDate?: string
  holidayName?: string
}

export type UpdateDraftSessionRequest = {
  date: string
  startTime: string
  endTime: string
  lecturerId: number
  roomId: number
}

export type SessionEditFailure = {
  code: string
  message: string
}

export type CourseSemesterProgress = {
  totalUnits: number
  scheduledUnits: number
  remainingUnits: number
}

export type DraftScheduleMutationResult = {
  courseId: number
  semesterId: number
  scheduledUnits: number
  remainingUnits: number
  draftSchedule: DraftSchedule | null
}

export type MutationFailure = {
  code: string
  message: string
  currentRevision?: number | null
}

export type CreateManualDraftSessionRequest = {
  semesterId: number
  date: string
  startTime: string
  endTime: string
  units: number
  roomId: number
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function generateDraftSchedule(
  courseId: number,
  semesterId: number,
  planningPeriod: PlanningPeriod,
  allowedTeachingWindows: AllowedTeachingWindow[],
): Promise<DraftSchedule> {
  const response = await request(
    `${API_BASE}/api/courses/${courseId}/draft-schedule/generate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ semesterId, planningPeriod, allowedTeachingWindows }),
    },
  )
  if (response.status === 422 || response.status === 409) {
    const payload = await response.json()
    throw payload.errors as GenerationFailure[]
  }
  if (!response.ok) {
    throw [{ code: 'REQUEST_FAILED', message: await response.text() }]
  }
  return response.json()
}

export async function getGenerationConstraints(
  courseId: number,
  semesterId: number,
): Promise<GenerationConstraints> {
  const response = await request(
    `${API_BASE}/api/courses/${courseId}/generation-constraints?semesterId=${semesterId}`,
  )
  if (!response.ok) {
    throw [{ code: 'REQUEST_FAILED', message: 'Could not load generation constraints.' }]
  }
  return response.json()
}

export async function clearGenerationConstraints(courseId: number, semesterId: number): Promise<void> {
  const response = await request(
    `${API_BASE}/api/courses/${courseId}/generation-constraints?semesterId=${semesterId}`,
    { method: 'DELETE' },
  )
  if (!response.ok) {
    throw [{ code: 'REQUEST_FAILED', message: 'Could not clear generation constraints.' }]
  }
}

export async function getDraftSchedule(courseId: number, semesterId: number): Promise<DraftSchedule> {
  const response = await request(
    `${API_BASE}/api/courses/${courseId}/draft-schedule?semesterId=${semesterId}`,
  )
  if (!response.ok) {
    throw [{ code: 'NOT_FOUND', message: 'No generated draft schedule exists.' }]
  }
  return response.json()
}

export async function getDraftSchedules(semesterId: number): Promise<DraftSchedule[]> {
  const response = await request(`${API_BASE}/api/draft-schedules?semesterId=${semesterId}`)
  if (!response.ok) {
    throw [{ code: 'REQUEST_FAILED', message: 'Could not load generated draft schedules.' }]
  }
  return response.json()
}

export async function updateDraftSession(
  sessionId: number,
  payload: UpdateDraftSessionRequest,
): Promise<DraftSchedule> {
  const response = await request(`${API_BASE}/api/draft-sessions/${sessionId}`, {
    method: 'PATCH',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (response.status === 422) {
    const body = await response.json()
    throw body.errors as SessionEditFailure[]
  }
  if (!response.ok) {
    throw [{ code: 'REQUEST_FAILED', message: await response.text() }]
  }
  return response.json()
}

export async function createManualDraftSession(
  courseId: number,
  payload: CreateManualDraftSessionRequest,
): Promise<DraftScheduleMutationResult> {
  const response = await request(`${API_BASE}/api/courses/${courseId}/draft-schedule/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  return parseMutationResponse(response)
}

export async function deleteDraftSession(
  sessionId: number,
  expectedDraftScheduleId: number,
  expectedDraftRevision: number,
): Promise<DraftScheduleMutationResult> {
  const query = new URLSearchParams({
    expectedDraftScheduleId: String(expectedDraftScheduleId),
    expectedDraftRevision: String(expectedDraftRevision),
  })
  const response = await request(`${API_BASE}/api/draft-sessions/${sessionId}?${query}`, { method: 'DELETE' })
  return parseMutationResponse(response)
}

export async function clearCourseDraft(
  courseId: number,
  semesterId: number,
  expectedDraftScheduleId: number,
  expectedDraftRevision: number,
): Promise<DraftScheduleMutationResult> {
  const query = new URLSearchParams({
    semesterId: String(semesterId),
    expectedDraftScheduleId: String(expectedDraftScheduleId),
    expectedDraftRevision: String(expectedDraftRevision),
  })
  const response = await request(`${API_BASE}/api/courses/${courseId}/draft-schedule?${query}`, { method: 'DELETE' })
  return parseMutationResponse(response)
}

async function parseMutationResponse(response: Response): Promise<DraftScheduleMutationResult> {
  if (response.ok) return response.json()
  let payload: { errors?: MutationFailure[]; detail?: string } = {}
  try {
    payload = await response.json()
  } catch {
    // Use the stable fallback below when the backend did not return JSON.
  }
  if (payload.errors?.length) throw payload.errors
  throw [{
    code: response.status === 404 ? 'NOT_FOUND' : 'REQUEST_FAILED',
    message: payload.detail ?? 'The requested Draft Schedule change could not be completed.',
  }] satisfies MutationFailure[]
}

async function request(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await fetch(input, init)
  } catch {
    throw [
      {
        code: 'NETWORK_ERROR',
        message: 'Could not reach the backend API. Check that FastAPI is running and CORS is enabled.',
      },
    ]
  }
}
