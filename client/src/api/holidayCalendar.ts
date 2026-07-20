export type HolidayRecord = { id: number; date: string; name: string; revision: number }
export type HolidayInput = { date: string; name: string }
export type HolidayUpdateInput = HolidayInput & { expectedRevision: number }
export type HolidayError = { code: string; message: string; field?: string | null; meta?: Record<string, unknown> | null }

export class HolidayCalendarApiError extends Error {
  status: number
  errors: HolidayError[]

  constructor(status: number, errors: HolidayError[]) {
    super(errors[0]?.message ?? 'Holiday calendar request failed.')
    this.status = status
    this.errors = errors
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ errors: [] }))
    throw new HolidayCalendarApiError(response.status, payload.errors ?? [])
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const json = (method: string, body: unknown): RequestInit => ({
  method,
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(body),
})

export const listHolidays = (): Promise<HolidayRecord[]> => request('/api/holidays')
export const createHoliday = (input: HolidayInput): Promise<HolidayRecord> => request('/api/holidays', json('POST', input))
export const updateHoliday = (id: number, input: HolidayUpdateInput): Promise<HolidayRecord> => request(`/api/holidays/${id}`, json('PATCH', input))
export const deleteHoliday = (id: number, expectedRevision: number, confirmed: boolean): Promise<void> => request(`/api/holidays/${id}?expectedRevision=${expectedRevision}&confirmed=${confirmed}`, { method: 'DELETE' })

