export type ExamIssue = { code: string; message: string; relatedDate: string | null; relatedResource: ResourceReference | null; relatedSessionId: number | null; holidayName: string | null }
export type ResourceReference = { id: number; name: string; referenceCode: string | null }
export type RoomReference = ResourceReference & { capacity: number }
export type FinalTeachingAnchor = { date: string; endTime: string; teachingSessionId: number }
export type GenerationEligibility = { eligible: boolean; code: 'ELIGIBLE' | 'DISABLED' | 'CONFIGURATION_INCOMPLETE' | 'FINAL_TEACHING_SESSION_MISSING' | 'AUTOMATIC_START_TIME_UNAVAILABLE' | 'ACTIVE_EXAM_EXISTS' | 'CONFIGURATION_CONSUMED' | null; message: string | null }
export type ExamConfigurationInput = { identifier: string; durationMinutes: number; recommendedStartOverride: string | null; recommendedEndOverride: string | null; requiredCapacity: number; examType: string; responsibleLecturerId: number }
export type ExamConfiguration = ExamConfigurationInput & { id: number; revision: number; configurationConsumed: boolean; recommendedStartDate: string | null; recommendedEndDate: string | null; recommendationWasOverridden: boolean }
export type ExamSession = { id: number; revision: number; courseId: number; semesterId: number; configurationIdentifier: string; examType: string; durationMinutes: number; requiredCapacity: number; recommendedStartDate: string; recommendedEndDate: string; recommendationWasOverridden: boolean; outsideRecommendedWindow: boolean; finalTeachingAnchor: FinalTeachingAnchor; date: string; startTime: string; endTime: string; lecturer: ResourceReference; cohort: ResourceReference; room: RoomReference; lifecycleStatus: 'active' | 'past'; source: 'generated' | 'manual'; validityIssues: ExamIssue[]; inputSnapshotToken: string }
export type ExamCoursePlanningState = { courseId: number; courseName: string; semesterId: number; cohortId: number; cohortName: string; enabled: boolean; configuration: ExamConfiguration | null; finalTeachingAnchor: FinalTeachingAnchor | null; activeExam: ExamSession | null; pastExams: ExamSession[]; generationEligibility: GenerationEligibility; inputSnapshotToken: string }
export type ExamPlanningOverview = { semesterId: number; institutionToday: string; courses: ExamCoursePlanningState[] }
export type SaveExamConfigurationRequest = { semesterId: number; enabled: boolean; expectedRevision: number | null; configuration: ExamConfigurationInput | null }
export type PreparedExamCourse = { courseId: number; courseName: string; configurationId: number | null; configurationRevision: number | null; inputSnapshotToken: string; eligibility: GenerationEligibility }
export type ExamGenerationPreparation = { semesterId: number; scheduleRevisionId: number; institutionToday: string; sharedSnapshotToken: string; courses: PreparedExamCourse[] }
export type PreparedExamCourseInput = Omit<PreparedExamCourse, 'courseName' | 'eligibility'>
export type GenerateExamsRequest = { semesterId: number; scheduleRevisionId: number; institutionToday: string; sharedSnapshotToken: string; courses: PreparedExamCourseInput[] }
export type ExamGenerationOutcome = { courseId: number; courseName: string; configurationId: number | null; configurationIdentifier: string | null; status: 'scheduled' | 'failed' | 'stale' | 'skipped_active' | 'skipped_disabled'; saved: boolean; exam: ExamSession | null; reasons: ExamIssue[] }
export type ExamGenerationResult = { semesterId: number; summary: { total: number; scheduled: number; failed: number; stale: number; skippedActive: number; skippedDisabled: number; elapsedMilliseconds: number; optimalForPreparedSnapshot: boolean }; outcomes: ExamGenerationOutcome[] }
export type CreateManualExamRequest = { semesterId: number; scheduleRevisionId: number; date: string; startTime: string; lecturerId: number; roomId: number; expectedConfigurationRevision: number; inputSnapshotToken: string }
export type UpdateExamRequest = { scheduleRevisionId: number; date: string; startTime: string; lecturerId: number; roomId: number; expectedExamRevision: number; inputSnapshotToken: string }
export type DeleteExamRequest = { scheduleRevisionId: number; confirmed: true; expectedExamRevision: number; inputSnapshotToken: string }
export type DeleteExamResponse = { deletedExamId: number; deletedLifecycleStatus: 'active' | 'past'; consequence: 'configuration_enabled_unscheduled' | 'historical_exam_only'; state: ExamCoursePlanningState }
export type ExamOperationError = { code: string; message: string; field: string | null; meta?: Record<string, unknown> | null }

export class ExamSchedulingApiError extends Error {
  status: number
  errors: ExamOperationError[]
  currentState: ExamCoursePlanningState | null
  constructor(status: number, errors: ExamOperationError[], currentState: ExamCoursePlanningState | null = null) {
    super(errors[0]?.message ?? 'Exam scheduling request failed.')
    this.status = status; this.errors = errors; this.currentState = currentState
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const json = (method: string, body: unknown): RequestInit => ({ method, headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(body) })

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, init)
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new ExamSchedulingApiError(response.status, payload?.errors ?? [{ code: 'REQUEST_FAILED', message: 'Exam scheduling request failed.', field: null }], payload?.currentState ?? null)
  return payload as T
}

export const getExamPlanningOverview = (semesterId: number) => request<ExamPlanningOverview>(`/api/exam-planning?semesterId=${semesterId}`)
export const saveExamConfiguration = (courseId: number, input: SaveExamConfigurationRequest) => request<ExamCoursePlanningState>(`/api/courses/${courseId}/exam-configuration`, json('PUT', input))
export function prepareExamGeneration(semesterId: number, scheduleRevisionId: number, courseIds: number[]) {
  if (courseIds.length < 1 || courseIds.length > 100 || new Set(courseIds).size !== courseIds.length) return Promise.reject(new ExamSchedulingApiError(422, [{ code: 'INVALID_SELECTION', message: 'Select 1 to 100 unique courses.', field: 'courseIds' }]))
  return request<ExamGenerationPreparation>('/api/exams/generation/prepare', json('POST', { semesterId, scheduleRevisionId, courseIds }))
}
export const generateExams = (input: GenerateExamsRequest) => request<ExamGenerationResult>('/api/exams/generation', json('POST', input))
export const createManualExam = (courseId: number, input: CreateManualExamRequest) => request<ExamCoursePlanningState>(`/api/courses/${courseId}/exam-sessions`, json('POST', input))
export const updateExam = (examId: number, input: UpdateExamRequest) => request<ExamCoursePlanningState>(`/api/exam-sessions/${examId}`, json('PATCH', input))
export const deleteExam = (examId: number, input: DeleteExamRequest) => request<DeleteExamResponse>(`/api/exam-sessions/${examId}`, json('DELETE', input))
