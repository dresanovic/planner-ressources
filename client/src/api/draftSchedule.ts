export type DraftSession = {
  id: number
  date: string
  startTime: string
  endTime: string
  units: number
  timeWindowId: number
}

export type DraftSchedule = {
  draftScheduleId: number
  courseId: number
  semesterId: number
  selectedTimeWindowId: number
  sessions: DraftSession[]
}

export type GenerationFailure = {
  code: string
  message: string
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function generateDraftSchedule(
  courseId: number,
  semesterId: number,
  selectedTimeWindowId: number,
): Promise<DraftSchedule> {
  const response = await request(
    `${API_BASE}/api/courses/${courseId}/draft-schedule/generate`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ semesterId, selectedTimeWindowId }),
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

export async function getDraftSchedule(courseId: number): Promise<DraftSchedule> {
  const response = await request(`${API_BASE}/api/courses/${courseId}/draft-schedule`)
  if (!response.ok) {
    throw [{ code: 'NOT_FOUND', message: 'No generated draft schedule exists.' }]
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
