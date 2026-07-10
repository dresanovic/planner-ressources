export type DraftSession = {
  id: number
  date: string
  startTime: string
  endTime: string
  units: number
  courseId: number
  lecturerId: number
  cohortId: number
  roomId: number
  studyTypeId: number
  timeWindowId: number | null
  constraintWindowIndex: number
}

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
  planningPeriod: PlanningPeriod
  allowedTeachingWindows: AllowedTeachingWindow[]
}

export type PlanningEntity = {
  id: number
  name: string
}

export type DraftScheduleContext = {
  course: PlanningEntity
  cohort: PlanningEntity
  lecturer: PlanningEntity
  room: PlanningEntity
  studyType: PlanningEntity
}

export type DraftSchedule = {
  draftScheduleId: number
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
  if (response.status === 422) {
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

export async function getDraftSchedule(courseId: number): Promise<DraftSchedule> {
  const response = await request(`${API_BASE}/api/courses/${courseId}/draft-schedule`)
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
