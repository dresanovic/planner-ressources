export type ResourceType = 'lecturers' | 'rooms'
export type ResourceStatus = 'active' | 'inactive' | 'all'
export type ResourceError = { code: string; message: string; field?: string | null; meta?: Record<string, unknown> | null }
export type LecturerRecord = { id: number; name: string; referenceCode: string; isActive: boolean; revision: number }
export type RoomRecord = LecturerRecord & { capacity: number }
export type ResourceRecord = LecturerRecord | RoomRecord
export type ResourcePage<T> = { page: number; pageSize: number; total: number; items: T[] }
export type CourseIdentity = { id: number; name: string }
export type SessionUsage = { draftSessionCount: number; draftScheduleCount: number }
export type ExamUsage = { examSessionCount: number; currentConfigurationCount: number }
export type ResourceUsageAssessment = { resourceId: number; revision: number; disposition: 'delete' | 'inactivate'; activeCourses: CourseIdentity[]; inactiveCourses: CourseIdentity[]; sessionUsage: SessionUsage; examUsage: ExamUsage }
export type RelationshipStatus = { course: CourseIdentity; resourceId: number; usable: boolean; reasons: string[] }
export type DeletedResourceResult = { outcome: 'deleted'; resourceId: number; removedInactiveCourseLinks: CourseIdentity[] }
export type InactivatedResourceResult<T extends ResourceRecord = ResourceRecord> = { outcome: 'inactivated'; resource: T; activeCourses: CourseIdentity[]; sessionUsage: SessionUsage; examUsage: ExamUsage }
export type ResourceRemovalResult<T extends ResourceRecord = ResourceRecord> = DeletedResourceResult | InactivatedResourceResult<T>
export type ResourceReactivationResult<T extends ResourceRecord = ResourceRecord> = { resource: T; restoredRelationships: CourseIdentity[]; unusableRelationships: RelationshipStatus[] }
export type RoomMutationResult = { room: RoomRecord; affectedRelationships: RelationshipStatus[] }
export type LecturerInput = { name: string; referenceCode: string }
export type RoomInput = LecturerInput & { capacity: number }
export type RecurringUnavailability = { id: number; resourceType: 'lecturer' | 'room'; resourceId: number; kind: 'recurring'; weekdays: number[]; startTime: string; endTime: string; revision: number }
export type DatedUnavailability = { id: number; resourceType: 'lecturer' | 'room'; resourceId: number; kind: 'dated'; startDate: string; startTime: string; endDate: string; endTime: string; revision: number }
export type UnavailabilityPeriod = RecurringUnavailability | DatedUnavailability
export type RecurringUnavailabilityInput = Omit<RecurringUnavailability, 'id' | 'resourceType' | 'resourceId' | 'revision'>
export type DatedUnavailabilityInput = Omit<DatedUnavailability, 'id' | 'resourceType' | 'resourceId' | 'revision'>
export type UnavailabilityInput = RecurringUnavailabilityInput | DatedUnavailabilityInput
export type UnavailabilityUpdate = UnavailabilityInput & { expectedRevision: number }
export type ResourceCandidate = { id: number; name: string; referenceCode: string; kind: 'lecturer' | 'room'; capacity: number | null; isActive: boolean; isEligible: boolean; isUsable: boolean; reasons: string[] }
export type CourseResourceCandidate = ResourceCandidate & { unavailabilityPeriods: UnavailabilityPeriod[]; courseSessionUsage: SessionUsage }
export type CourseResourceConfiguration = { courseId: number; courseRevision: number; cohortSize: number; eligibleLecturerIds: number[]; eligibleRoomIds: number[]; lecturerCandidates: CourseResourceCandidate[]; roomCandidates: CourseResourceCandidate[]; preferences: { minimizeLecturerChanges: true; minimizeRoomChanges: true } }
export type CourseResourceEligibilityUpdate = { expectedRevision: number; lecturerIds: number[]; roomIds: number[] }

export class ResourceCatalogApiError extends Error {
  status: number
  errors: ResourceError[]

  constructor(status: number, errors: ResourceError[]) {
    super(errors[0]?.message ?? 'Resource catalog request failed.')
    this.status = status
    this.errors = errors
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  if (!response.ok) {
    const payload = await response.json().catch(() => ({ errors: [{ code: 'REQUEST_FAILED', message: 'Resource catalog request failed.' }] }))
    throw new ResourceCatalogApiError(response.status, payload.errors ?? [])
  }
  if (response.status === 204) return undefined as T
  return response.json()
}

const json = (method: string, body: unknown): RequestInit => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

function listPath(resource: ResourceType, options: { status?: ResourceStatus; query?: string; page?: number; pageSize?: number } = {}) {
  const params = new URLSearchParams()
  params.set('status', options.status ?? 'active')
  if (options.query?.trim()) params.set('query', options.query.trim())
  params.set('page', String(options.page ?? 1))
  params.set('pageSize', String(options.pageSize ?? 50))
  return `/api/resources/${resource}?${params}`
}

export function listLecturers(options?: { status?: ResourceStatus; query?: string; page?: number; pageSize?: number }): Promise<ResourcePage<LecturerRecord>> {
  return request(listPath('lecturers', options))
}

export function listRooms(options?: { status?: ResourceStatus; query?: string; page?: number; pageSize?: number }): Promise<ResourcePage<RoomRecord>> {
  return request(listPath('rooms', options))
}

export function getLecturer(id: number): Promise<LecturerRecord> { return request(`/api/resources/lecturers/${id}`) }
export function getRoom(id: number): Promise<RoomRecord> { return request(`/api/resources/rooms/${id}`) }
export function createLecturer(input: LecturerInput): Promise<LecturerRecord> { return request('/api/resources/lecturers', json('POST', input)) }
export function createRoom(input: RoomInput): Promise<RoomRecord> { return request('/api/resources/rooms', json('POST', input)) }
export function updateLecturer(id: number, input: LecturerInput & { expectedRevision: number }): Promise<LecturerRecord> { return request(`/api/resources/lecturers/${id}`, json('PATCH', input)) }
export function updateRoom(id: number, input: RoomInput & { expectedRevision: number }): Promise<RoomMutationResult> { return request(`/api/resources/rooms/${id}`, json('PATCH', input)) }
export function getResourceUsage(resource: ResourceType, id: number): Promise<ResourceUsageAssessment> { return request(`/api/resources/${resource}/${id}/usage`) }
export function removeResource(resource: ResourceType, id: number, expectedRevision: number): Promise<ResourceRemovalResult> { return request(`/api/resources/${resource}/${id}?expectedRevision=${expectedRevision}&confirmed=true`, { method: 'DELETE' }) }
export function reactivateResource(resource: ResourceType, id: number, expectedRevision: number): Promise<ResourceReactivationResult> { return request(`/api/resources/${resource}/${id}/reactivate`, json('POST', { expectedRevision })) }
export function listUnavailability(resource: ResourceType, id: number): Promise<UnavailabilityPeriod[]> { return request(`/api/resources/${resource}/${id}/unavailability`) }
export function createUnavailability(resource: ResourceType, id: number, input: UnavailabilityInput): Promise<UnavailabilityPeriod> { return request(`/api/resources/${resource}/${id}/unavailability`, json('POST', input)) }
export function updateUnavailability(resource: ResourceType, id: number, periodId: number, input: UnavailabilityUpdate): Promise<UnavailabilityPeriod> { return request(`/api/resources/${resource}/${id}/unavailability/${periodId}`, json('PATCH', input)) }
export function deleteUnavailability(resource: ResourceType, id: number, periodId: number, expectedRevision: number): Promise<void> { return request(`/api/resources/${resource}/${id}/unavailability/${periodId}?expectedRevision=${expectedRevision}`, { method: 'DELETE' }) }
export function getCourseResourceConfiguration(courseId: number): Promise<CourseResourceConfiguration> { return request(`/api/academic/courses/${courseId}/resource-eligibility`) }
export function updateCourseResourceEligibility(courseId: number, input: CourseResourceEligibilityUpdate): Promise<CourseResourceConfiguration> { return request(`/api/academic/courses/${courseId}/resource-eligibility`, json('PUT', input)) }
