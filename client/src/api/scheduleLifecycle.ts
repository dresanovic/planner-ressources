export type LifecycleState = 'draft' | 'ready_for_review' | 'published' | 'superseded' | 'abandoned'
export type LifecycleEventType = 'created' | 'marked_ready' | 'returned_to_draft' | 'published' | 'superseded' | 'abandoned' | 'restored'
export type TransitionAction = 'mark_ready' | 'return_to_draft' | 'publish' | 'abandon' | 'restore'
export type LifecycleEvent = { eventSequence: number; eventType: LifecycleEventType; fromState: LifecycleState | null; toState: LifecycleState; occurredAt: string }
export type RevisionAllowedActions = { markReady: boolean; returnToDraft: boolean; preparePublication: boolean; abandon: boolean; restore: boolean; editSchedule: boolean }
export type ScheduleRevisionSummary = { revisionId: number; semesterId: number; revisionNumber: number; revisionVersion: number; state: LifecycleState; originRevisionId: number | null; isActiveWorking: boolean; isCurrentPublication: boolean; createdAt: string; stateChangedAt: string; publishedAt: string | null; events: LifecycleEvent[]; allowedActions: RevisionAllowedActions }
export type ScheduleLifecycleOverview = { semesterId: number; semesterName: string; stateToken: string; activeWorkingRevision: ScheduleRevisionSummary | null; currentPublication: ScheduleRevisionSummary | null; revisions: ScheduleRevisionSummary[]; allowedActions: { createWorkingRevision: boolean } }
export type PublicationCondition = { code: string; message: string; courseId: number | null; sessionKind: 'teaching' | 'exam' | null; sourceSessionId: number | null; details: Record<string, unknown> }
export type CapturedEntity = { sourceId: number; name: string }
export type CapturedResource = CapturedEntity & { referenceCode: string; capacity: number | null }
export type CapturedIssue = { code: string; message: string; details: Record<string, unknown> }
export type CapturedTeachingSession = { sourceSessionId: number; date: string; startTime: string; endTime: string; units: number; timeWindowId: number | null; constraintWindowIndex: number; lecturer: CapturedResource; room: CapturedResource; validationAlerts: CapturedIssue[] }
export type CapturedCourseSchedule = { sourceCourseId: number; name: string; cohort: CapturedEntity & { size: number }; studyType: CapturedEntity; totalUnits: number; scheduledUnits: number; remainingUnits: number; draftStatus: string | null; teachingSessions: CapturedTeachingSession[] }
export type CapturedExamSession = { sourceExamId: number; course: CapturedEntity; cohort: CapturedEntity; lecturer: CapturedResource; room: CapturedResource; examDate: string; startTime: string; endTime: string; source: 'generated' | 'manual'; configurationIdentifier: string; configurationRevision: number; durationMinutes: number; examType: string; requiredCapacity: number; recommendedStartDate: string; recommendedEndDate: string; recommendationWasOverridden: boolean; finalTeachingDate: string; finalTeachingEndTime: string; validityIssues: CapturedIssue[]; outsideRecommendedWindow: boolean }
export type SemesterScheduleSnapshot = { schemaVersion: number; capturedAt: string; semester: { sourceId: number; name: string; startDate: string; endDate: string }; courses: CapturedCourseSchedule[]; examSessions: CapturedExamSession[]; capturedConditions: PublicationCondition[] }
export type ScheduleRevisionContent = { revision: ScheduleRevisionSummary; contentSource: 'active_working' | 'captured_snapshot'; snapshot: SemesterScheduleSnapshot }
export type PublicationPreparation = { preparationToken: string; preparedAt: string; semesterId: number; semesterName: string; targetRevision: ScheduleRevisionSummary; consequence: 'first_publication' | 'replacement_publication'; currentPublication: ScheduleRevisionSummary | null; courseCount: number; totalUnits: number; scheduledUnits: number; remainingUnits: number; conditions: PublicationCondition[] }
export type TransitionScheduleRevisionRequest = { action: TransitionAction; expectedRevisionVersion: number; expectedStateToken: string; confirmed: boolean; publicationToken?: string | null }
export type LifecycleErrorItem = { code: string; message: string; field: string | null; meta: Record<string, unknown> | null }

export class ScheduleLifecycleApiError extends Error {
  status: number
  errors: LifecycleErrorItem[]
  currentOverview: ScheduleLifecycleOverview | null
  constructor(status: number, errors: LifecycleErrorItem[], currentOverview: ScheduleLifecycleOverview | null = null) {
    super(errors[0]?.message ?? 'Schedule lifecycle request failed.')
    this.status = status
    this.errors = errors
    this.currentOverview = currentOverview
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const json = (method: string, body: unknown): RequestInit => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })
const OFFSET_TIMESTAMP = /(?:Z|[+-]\d{2}:\d{2})$/

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ScheduleLifecycleApiError(response.status, payload?.errors ?? [{ code: 'REQUEST_FAILED', message: 'Schedule lifecycle request failed.', field: null, meta: null }], payload?.currentOverview ?? null)
  }
  try {
    validateTimestamps(payload)
  } catch {
    throw new ScheduleLifecycleApiError(502, [{ code: 'INVALID_LIFECYCLE_TIMESTAMP', message: 'The lifecycle response contained an ambiguous timestamp.', field: null, meta: null }])
  }
  return payload as T
}

function validateTimestamps(value: unknown): void {
  if (Array.isArray(value)) {
    value.forEach(validateTimestamps)
    return
  }
  if (value == null || typeof value !== 'object') return
  for (const [key, item] of Object.entries(value)) {
    if (key.endsWith('At') && item != null && (typeof item !== 'string' || !OFFSET_TIMESTAMP.test(item))) throw new Error('Ambiguous timestamp')
    validateTimestamps(item)
  }
}

export const getScheduleLifecycle = (semesterId: number) => request<ScheduleLifecycleOverview>(`/api/semesters/${semesterId}/schedule-lifecycle`)
export const createWorkingRevision = (semesterId: number, expectedStateToken: string) => request<ScheduleLifecycleOverview>(`/api/semesters/${semesterId}/schedule-revisions`, json('POST', { expectedStateToken }))
export const getScheduleRevision = (revisionId: number) => request<ScheduleRevisionContent>(`/api/schedule-revisions/${revisionId}`)
export const prepareSchedulePublication = (revisionId: number, expectedRevisionVersion: number, expectedStateToken: string) => request<PublicationPreparation>(`/api/schedule-revisions/${revisionId}/publication-preparation`, json('POST', { expectedRevisionVersion, expectedStateToken }))
export const transitionScheduleRevision = (revisionId: number, input: TransitionScheduleRevisionRequest) => request<ScheduleLifecycleOverview>(`/api/schedule-revisions/${revisionId}/transitions`, json('POST', input))
