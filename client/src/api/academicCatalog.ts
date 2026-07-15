export type CatalogError = { code: string; message: string; field?: string | null; meta?: Record<string, unknown> | null }
export type UsageCount = { type: string; count: number }
export type UsageSummary = { recordId: number; revision: number; canDelete: boolean; dependentRecords: UsageCount[]; savedSchedules: UsageCount; blockers: Array<{ kind: 'dependent' | 'saved_schedule'; type: string; count: number; message: string; prerequisiteAction?: string | null }> }
export type CatalogAudit = { isActive: boolean; revision: number }
export type SemesterRecord = CatalogAudit & { id: number; name: string; nameRepairRequired: boolean; startDate: string; endDate: string; usage: UsageSummary }
export type CohortRecord = CatalogAudit & { id: number; name: string; nameRepairRequired: boolean; studentCount: number; usage: UsageSummary }
export type EntitySummary = { id: number; name: string }
export type Availability = { available: boolean; reasons: string[] }
export type TimeWindowRecord = CatalogAudit & { id: number; studyTypeId: number; weekday: number; startTime: string; endTime: string; sortOrder: number; availability: Availability; usage: UsageSummary }
export type StudyTypeRecord = CatalogAudit & { id: number; name: string; nameRepairRequired: boolean; timeWindows: TimeWindowRecord[]; usage: UsageSummary }
export type CourseRecord = CatalogAudit & { id: number; name: string; nameRepairRequired: boolean; totalUnits: number; minSessionUnits: number; maxSessionUnits: number; semester: EntitySummary | null; cohort: EntitySummary; studyType: EntitySummary; lecturer: EntitySummary; room: EntitySummary; availability: Availability; usage: UsageSummary }
export type CatalogPage<T> = { page: number; pageSize: number; total: number; items: T[] }
export type CourseInput = { name: string; totalUnits: number; minSessionUnits: number; maxSessionUnits: number; semesterId: number; cohortId: number; studyTypeId: number; lecturerId: number; roomId: number }
export type SemesterInput = { name: string; startDate: string; endDate: string }
export type CohortInput = { name: string; studentCount: number }
export type StudyTypeInput = { name: string }
export type TimeWindowInput = { weekday: number; startTime: string; endTime: string; sortOrder: number }

export class AcademicCatalogApiError extends Error {
  status: number
  errors: CatalogError[]

  constructor(status: number, errors: CatalogError[]) {
    super(errors[0]?.message ?? 'Academic catalog request failed.')
    this.status = status
    this.errors = errors
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ errors: [{ code: 'REQUEST_FAILED', message: 'Academic catalog request failed.' }] }))
    throw new AcademicCatalogApiError(response.status, payload.errors ?? [])
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const json = (method: string, body: unknown): RequestInit => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

const listPath = (resource: string, status: 'all' | 'active' | 'inactive' = 'all', page = 1, pageSize = 50) => {
  const params = new URLSearchParams({ page: String(page), pageSize: String(pageSize) })
  if (status !== 'all') params.set('status', status)
  return `/api/academic/${resource}?${params}`
}

export function listSemesters(status: 'all' | 'active' | 'inactive' = 'all', page = 1, pageSize = 50): Promise<CatalogPage<SemesterRecord>> {
  return request(listPath('semesters', status, page, pageSize))
}

export function createSemester(input: SemesterInput): Promise<SemesterRecord> {
  return request('/api/academic/semesters', json('POST', input))
}

export function listCohorts(status: 'all' | 'active' | 'inactive' = 'all', page = 1, pageSize = 50): Promise<CatalogPage<CohortRecord>> {
  return request(listPath('cohorts', status, page, pageSize))
}

export function createCohort(input: CohortInput): Promise<CohortRecord> {
  return request('/api/academic/cohorts', json('POST', input))
}

export function listStudyTypes(status: 'all' | 'active' | 'inactive' = 'all', page = 1, pageSize = 50): Promise<CatalogPage<StudyTypeRecord>> {
  return request(listPath('study-types', status, page, pageSize))
}

export function createStudyType(input: StudyTypeInput): Promise<StudyTypeRecord> {
  return request('/api/academic/study-types', json('POST', input))
}

export function listTimeWindows(studyTypeId: number): Promise<TimeWindowRecord[]> {
  return request(`/api/academic/study-types/${studyTypeId}/time-windows`)
}

export function createTimeWindow(studyTypeId: number, input: TimeWindowInput): Promise<TimeWindowRecord> {
  return request(`/api/academic/study-types/${studyTypeId}/time-windows`, json('POST', input))
}

export function listCourses(status: 'all' | 'active' | 'inactive' = 'all', page = 1, pageSize = 50): Promise<CatalogPage<CourseRecord>> {
  return request(listPath('courses', status, page, pageSize))
}

export function createCourse(input: CourseInput): Promise<CourseRecord> {
  return request('/api/academic/courses', json('POST', input))
}

export function updateCourse(recordId: number, input: CourseInput & { expectedRevision: number }): Promise<CourseRecord> {
  return request(`/api/academic/courses/${recordId}`, json('PATCH', input))
}

export function deleteAcademicRecord(resource: string, recordId: number, expectedRevision: number): Promise<void> {
  return request(`/api/academic/${resource}/${recordId}?expectedRevision=${expectedRevision}`, { method: 'DELETE' })
}

export function getAcademicUsage(resource: string, recordId: number): Promise<UsageSummary> {
  return request(`/api/academic/${resource}/${recordId}/usage`)
}

export function setAcademicLifecycle(resource: string, recordId: number, command: 'archive' | 'reactivate', expectedRevision: number): Promise<unknown> {
  return request(`/api/academic/${resource}/${recordId}/${command}`, json('POST', { expectedRevision }))
}

export function updateSemester(recordId: number, input: SemesterInput & { expectedRevision: number }): Promise<SemesterRecord> {
  return request(`/api/academic/semesters/${recordId}`, json('PATCH', input))
}

export function updateCohort(recordId: number, input: CohortInput & { expectedRevision: number }): Promise<CohortRecord> {
  return request(`/api/academic/cohorts/${recordId}`, json('PATCH', input))
}

export function updateStudyType(recordId: number, input: StudyTypeInput & { expectedRevision: number }): Promise<StudyTypeRecord> {
  return request(`/api/academic/study-types/${recordId}`, json('PATCH', input))
}

export function updateTimeWindow(recordId: number, input: TimeWindowInput & { expectedRevision: number }): Promise<TimeWindowRecord> {
  return request(`/api/academic/time-windows/${recordId}`, json('PATCH', input))
}
