export type WorkspaceAvailability = 'available' | 'partial' | 'unavailable' | 'not_applicable'
export type CalendarMode = 'week' | 'day' | 'month' | 'list'
export type RevisionDesignation = 'active_working' | 'current_published'
export type WorkspaceMetric = {
  availability: WorkspaceAvailability
  scope: 'complete_revision' | 'no_revision'
  contributorRefs: string[]
  remainingTeachingUnits?: number
  remainingInstructionalMinutes?: number
  contributingCourseCount?: number
  distinctFindingCount?: number
  countByType?: { lecturer: number; room: number; cohort: number }
  affectedOccurrenceCount?: number
  coverage?: { eligibleCourseCount: number; coveredCourseCount: number; coverageComplete: boolean }
  failedOutcomeCount?: number
  staleOutcomeCount?: number
  unchangedOutcomeCount?: number
  distinctCourseCount?: number
  unavailableReason?: string
  notApplicableReason?: string
}
export type WorkspaceSummary = {
  unscheduledWork: WorkspaceMetric
  conflicts: WorkspaceMetric
  capacityIssues: WorkspaceMetric
  planningFailures: WorkspaceMetric
  needsReview: WorkspaceMetric
}
export type WorkspaceCourse = {
  courseRef: string
  courseId: number
  code: string
  name: string
  cohort: string
  lecturerRefs: string[]
  studyType: string
  planningEligible: boolean
  totalTeachingUnits: number
  scheduledTeachingUnits: number
  remainingTeachingUnits: number
  remainingInstructionalMinutes: number
  occurrenceRefs: string[]
  findingRefs: string[]
  outcomeRefs: string[]
  needsReviewReasonRefs: string[]
}
export type WorkspaceOccurrenceBase = {
  occurrenceRef: string
  courseRef: string
  date: string
  startTime: string
  endTime: string
  cohort: string
  lecturerRefs: string[]
  roomRef: string
  findingRefs: string[]
}
export type TeachingOccurrence = WorkspaceOccurrenceBase & {
  kind: 'teaching'
  teachingUnits: number
  source: string
}
export type ExamValidityContext = {
  configurationIdentifier: string
  configurationRevision: number
  finalTeachingDate: string
  finalTeachingEndTime: string
  source: string
  capturedIssues?: unknown[]
}
export type ExamRecommendationContext = {
  recommendedStartDate: string
  recommendedEndDate: string
  recommendationWasOverridden: boolean
  outsideRecommendedWindow: boolean
}
export type ExamOccurrence = WorkspaceOccurrenceBase & {
  kind: 'exam'
  examType: string
  durationMinutes: number
  requiredCapacity: number
  assignedRoomName: string
  currentRoomCapacity: number | null
  validityContext: ExamValidityContext
  recommendationContext?: ExamRecommendationContext | null
}
export type WorkspaceOccurrence = TeachingOccurrence | ExamOccurrence
export type ConflictFindingDetails = {
  kind: 'conflict'
  conflictType: 'lecturer' | 'room' | 'cohort'
  occurrenceRefs: string[]
  subjectRef: string
}
export type CapacityFindingDetails = {
  kind: 'capacity'
  occurrenceRef: string
  requiredCapacity: number
  roomRef: string
  roomName: string
  currentCapacity: number
}
export type HolidayFindingDetails = {
  kind: 'holiday'
  holidayRef: string
  holidayDate: string
  holidayName: string
  occurrenceRefs: string[]
}
export type ExamValidityFindingDetails = {
  kind: 'exam_validity'
  examOccurrenceRef: string
  issueCode: string
  supportingValues: Record<string, string | number | boolean>
}
export type OtherFindingDetails = {
  kind: 'other'
  issueCode: string
  occurrenceRefs: string[]
  roomRef?: string | null
  subjectRef?: string | null
}
export type ValidationFindingDetails =
  | ConflictFindingDetails
  | CapacityFindingDetails
  | HolidayFindingDetails
  | ExamValidityFindingDetails
  | OtherFindingDetails
export type ValidationFinding = {
  findingRef: string
  category: 'lecturer_conflict' | 'room_conflict' | 'cohort_conflict' | 'room_capacity' | 'holiday' | 'exam_validity' | 'other'
  validationBasis: 'current'
  affectedCourseRefs: string[]
  affectedOccurrenceRefs: string[]
  details: ValidationFindingDetails
}
export type PlanningOutcome = {
  outcomeRef: string
  revisionId: number
  courseRef: string
  operationKind: 'single_course_generation' | 'multi_course_generation' | 'semester_optimization' | 'exam_generation'
  classification: 'successful' | 'failed' | 'stale' | 'unchanged' | 'skipped'
  sourceStatus: string
  reasons: Record<string, unknown>[]
  completedAt: string
}
export type FacetValue = { value: string; label: string }
export type FilterFacets = {
  courses: FacetValue[]
  cohorts: FacetValue[]
  lecturers: FacetValue[]
  rooms: FacetValue[]
  studyTypes: FacetValue[]
  sessionTypes: FacetValue[]
  lifecycleContexts: FacetValue[]
  validationCategories: FacetValue[]
}
export type RevisionSelector = {
  revisionId: number
  revisionNumber: number
  lifecycleState: 'draft' | 'ready_for_review' | 'published'
  designation: RevisionDesignation
}
export type CalendarWorkspaceBase = {
  semester: { semesterId: number; name: string; startDate: string; endDate: string }
  availableContexts: { activeWorking: RevisionSelector | null; currentPublished: RevisionSelector | null }
  workspaceToken: string
  sectionStatus: Record<string, { availability: 'available' | 'partial' | 'unavailable'; reason?: string; coverage?: string }>
  courses: WorkspaceCourse[]
  occurrences: WorkspaceOccurrence[]
  holidays: { holidayRef: string; date: string; name: string }[]
  validationFindings: ValidationFinding[]
  planningOutcomes: PlanningOutcome[]
  summary: WorkspaceSummary
  filterFacets: FilterFacets
}
export type LoadedCalendarWorkspace = CalendarWorkspaceBase & {
  workspaceState: 'loaded'
  selectedRevision: RevisionSelector & {
    readOnly: boolean
    contentSource: 'active_working' | 'captured_published'
    validationBasis: 'current'
    snapshotSchemaVersion: 1 | 2 | null
  }
}
export type NoRevisionCalendarWorkspace = CalendarWorkspaceBase & {
  workspaceState: 'no_revision'
  selectedRevision: null
}
export type CalendarWorkspace = LoadedCalendarWorkspace | NoRevisionCalendarWorkspace

export class CalendarWorkspaceApiError extends Error {
  status: number
  retryable: boolean

  constructor(status: number, message: string, retryable = status === 0 || status === 409 || status >= 500) {
    super(message)
    this.status = status
    this.retryable = retryable
  }
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function getCalendarWorkspace(semesterId: number, revisionId?: number | null): Promise<CalendarWorkspace> {
  const query = revisionId == null ? '' : `?revisionId=${revisionId}`
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/semesters/${semesterId}/calendar-workspace${query}`)
  } catch {
    throw new CalendarWorkspaceApiError(0, 'Could not reach the calendar workspace service.', true)
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) throw new CalendarWorkspaceApiError(response.status, payload?.detail ?? 'Could not load the calendar workspace.')
  validateWorkspace(payload)
  return payload
}

function validateWorkspace(value: unknown): asserts value is CalendarWorkspace {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'The workspace response is invalid.')
  const record = value
  if (record.workspaceState !== 'loaded' && record.workspaceState !== 'no_revision') throw new CalendarWorkspaceApiError(502, 'The workspace state is invalid.')
  validateSemester(record.semester)
  if (typeof record.workspaceToken !== 'string' || record.workspaceToken.length === 0) throw new CalendarWorkspaceApiError(502, 'The workspace token is invalid.')
  validateSectionStatus(record.sectionStatus)
  const collections = ['courses', 'occurrences', 'holidays', 'validationFindings', 'planningOutcomes'] as const
  if (collections.some((key) => !Array.isArray(record[key]))) throw new CalendarWorkspaceApiError(502, 'The workspace record collections are invalid.')
  validateFacets(record.filterFacets)
  if (!isRecord(record.availableContexts)) throw new CalendarWorkspaceApiError(502, 'The available revision contexts are invalid.')
  validateOptionalRevisionSelector(record.availableContexts.activeWorking, 'active_working')
  validateOptionalRevisionSelector(record.availableContexts.currentPublished, 'current_published')
  if (record.workspaceState === 'loaded' && !isRecord(record.selectedRevision)) throw new CalendarWorkspaceApiError(502, 'A loaded workspace requires a selected revision.')
  if (record.workspaceState === 'no_revision') {
    if (
      record.selectedRevision !== null
      || record.availableContexts.activeWorking !== null
      || record.availableContexts.currentPublished !== null
      || collections.some((key) => (record[key] as unknown[]).length > 0)
    ) throw new CalendarWorkspaceApiError(502, 'A no-revision workspace cannot contain revision data.')
  } else {
    validateSelectedRevision(record.selectedRevision as Record<string, unknown>)
    const selected = record.selectedRevision as Record<string, unknown>
    const selector = selected.designation === 'active_working'
      ? record.availableContexts.activeWorking
      : record.availableContexts.currentPublished
    if (
      !isRecord(selector)
      || ['revisionId', 'revisionNumber', 'lifecycleState', 'designation']
        .some((field) => selector[field] !== selected[field])
    ) {
      throw new CalendarWorkspaceApiError(502, 'The selected revision does not match its available context.')
    }
  }
  const courses = record.courses as Record<string, unknown>[]
  const occurrences = record.occurrences as Record<string, unknown>[]
  const holidays = record.holidays as Record<string, unknown>[]
  const findings = record.validationFindings as Record<string, unknown>[]
  const outcomes = record.planningOutcomes as Record<string, unknown>[]
  const courseRefs = new Set(courses.map((course) => validateCourse(course)))
  const occurrenceRefs = new Set(occurrences.map((occurrence) => validateOccurrence(occurrence, courseRefs)))
  const holidayRefs = new Set(holidays.map((holiday) => validateHoliday(holiday)))
  const findingRefs = new Set(findings.map((finding) => {
    validateFinding(finding)
    requireStringArray(finding.affectedCourseRefs, 'A validation finding has invalid course references.').forEach((ref) => {
      if (!courseRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A validation finding references an unknown course.')
    })
    requireStringArray(finding.affectedOccurrenceRefs, 'A validation finding has invalid occurrence references.').forEach((ref) => {
      if (!occurrenceRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A validation finding references an unknown occurrence.')
    })
    validateFindingReferences(finding, occurrenceRefs, holidayRefs)
    return requireString(finding.findingRef, 'A validation finding reference is invalid.')
  }))
  const selectedRevisionId = record.workspaceState === 'loaded'
    ? (record.selectedRevision as Record<string, unknown>).revisionId
    : null
  const outcomeRefs = new Set(outcomes.map((outcome) => validateOutcome(outcome, courseRefs, selectedRevisionId)))
  if (
    courseRefs.size !== courses.length
    || occurrenceRefs.size !== occurrences.length
    || holidayRefs.size !== holidays.length
    || findingRefs.size !== findings.length
    || outcomeRefs.size !== outcomes.length
  ) throw new CalendarWorkspaceApiError(502, 'The workspace contains duplicate canonical references.')
  for (const course of courses) {
    requireStringArray(course.occurrenceRefs, 'A course has invalid occurrence references.').forEach((ref) => {
      if (!occurrenceRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A course references an unknown occurrence.')
    })
    requireStringArray(course.findingRefs, 'A course has invalid finding references.').forEach((ref) => {
      if (!findingRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A course references an unknown finding.')
    })
    requireStringArray(course.outcomeRefs, 'A course has invalid planning-outcome references.').forEach((ref) => {
      if (!outcomeRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A course references an unknown planning outcome.')
    })
  }
  const summary = record.summary as Record<string, WorkspaceMetric> | undefined
  const requiredFields: Record<string, (keyof WorkspaceMetric)[]> = {
    unscheduledWork: ['remainingTeachingUnits', 'remainingInstructionalMinutes', 'contributingCourseCount'],
    conflicts: ['distinctFindingCount', 'countByType'],
    capacityIssues: ['affectedOccurrenceCount'],
    planningFailures: ['coverage', 'failedOutcomeCount', 'staleOutcomeCount', 'unchangedOutcomeCount'],
    needsReview: ['distinctCourseCount'],
  }
  const valueFields: (keyof WorkspaceMetric)[] = [
    'remainingTeachingUnits',
    'remainingInstructionalMinutes',
    'contributingCourseCount',
    'distinctFindingCount',
    'countByType',
    'affectedOccurrenceCount',
    'failedOutcomeCount',
    'staleOutcomeCount',
    'unchangedOutcomeCount',
    'distinctCourseCount',
  ]
  for (const key of Object.keys(requiredFields)) {
    const metric = summary?.[key]
    if (!metric || !['available', 'partial', 'unavailable', 'not_applicable'].includes(metric.availability)) throw new CalendarWorkspaceApiError(502, `The ${key} summary is invalid.`)
    const expectedScope = record.workspaceState === 'loaded' ? 'complete_revision' : 'no_revision'
    if (metric.scope !== expectedScope || !Array.isArray(metric.contributorRefs) || metric.contributorRefs.some((ref) => typeof ref !== 'string')) throw new CalendarWorkspaceApiError(502, `The ${key} summary scope or contributors are invalid.`)
    if (metric.availability === 'unavailable' && !metric.unavailableReason) throw new CalendarWorkspaceApiError(502, `The ${key} unavailable reason is missing.`)
    if (metric.availability === 'not_applicable' && !metric.notApplicableReason) throw new CalendarWorkspaceApiError(502, `The ${key} not-applicable reason is missing.`)
    if (metric.availability === 'available' || metric.availability === 'partial') {
      if (requiredFields[key].some((field) => metric[field] == null)) throw new CalendarWorkspaceApiError(502, `The ${key} named values are missing.`)
      validateMetricValues(key, metric)
    } else if (valueFields.some((field) => metric[field] != null)) {
      throw new CalendarWorkspaceApiError(502, `The ${key} summary exposes unavailable values.`)
    }
    if (record.workspaceState === 'loaded' && key === 'planningFailures') validateCoverage(metric.coverage)
    if (record.workspaceState === 'no_revision' && (metric.availability !== 'not_applicable' || metric.contributorRefs.length > 0)) throw new CalendarWorkspaceApiError(502, `The ${key} no-revision summary is invalid.`)
    const allowedContributors = key === 'conflicts'
      ? findingRefs
      : key === 'capacityIssues'
        ? occurrenceRefs
        : key === 'planningFailures'
          ? outcomeRefs
          : courseRefs
    if (metric.contributorRefs.some((ref) => !allowedContributors.has(ref))) throw new CalendarWorkspaceApiError(502, `The ${key} summary references an unknown contributor.`)
  }
  if (record.workspaceState === 'no_revision' && Object.values(record.filterFacets as FilterFacets).some((values) => values.length > 0)) throw new CalendarWorkspaceApiError(502, 'A no-revision workspace cannot expose revision-owned facets.')
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value != null && typeof value === 'object' && !Array.isArray(value)
}

function requireString(value: unknown, message: string) {
  if (typeof value !== 'string' || value.length === 0) throw new CalendarWorkspaceApiError(502, message)
  return value
}

function requireNumber(value: unknown, message: string) {
  if (typeof value !== 'number' || !Number.isFinite(value)) throw new CalendarWorkspaceApiError(502, message)
  return value
}

function requireStringArray(value: unknown, message: string) {
  if (!Array.isArray(value) || value.some((item) => typeof item !== 'string')) throw new CalendarWorkspaceApiError(502, message)
  return value as string[]
}

function validateSemester(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'The workspace semester is invalid.')
  requireNumber(value.semesterId, 'The workspace semester identifier is invalid.')
  requireString(value.name, 'The workspace semester name is invalid.')
  const start = requireString(value.startDate, 'The workspace semester start date is invalid.')
  const end = requireString(value.endDate, 'The workspace semester end date is invalid.')
  if (!isIsoDate(start) || !isIsoDate(end) || start > end) throw new CalendarWorkspaceApiError(502, 'The workspace semester date range is invalid.')
}

function validateSectionStatus(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'The workspace section status is invalid.')
  const requiredSections = ['courses', 'occurrences', 'holidays', 'validationFindings', 'planningOutcomes', 'summary']
  if (requiredSections.some((section) => !Object.hasOwn(value, section))) throw new CalendarWorkspaceApiError(502, 'The workspace section status is incomplete.')
  for (const status of Object.values(value)) {
    if (!isRecord(status) || !['available', 'partial', 'unavailable'].includes(String(status.availability))) throw new CalendarWorkspaceApiError(502, 'A workspace section status is invalid.')
    if (status.reason != null && typeof status.reason !== 'string') throw new CalendarWorkspaceApiError(502, 'A workspace section reason is invalid.')
    if (status.coverage != null && typeof status.coverage !== 'string') throw new CalendarWorkspaceApiError(502, 'A workspace section coverage value is invalid.')
  }
}

function validateOptionalRevisionSelector(value: unknown, designation: RevisionDesignation) {
  if (value === null) return
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'An available revision selector is invalid.')
  requireNumber(value.revisionId, 'An available revision identifier is invalid.')
  requireNumber(value.revisionNumber, 'An available revision number is invalid.')
  const validState = designation === 'active_working'
    ? ['draft', 'ready_for_review'].includes(String(value.lifecycleState))
    : value.lifecycleState === 'published'
  if (!validState || value.designation !== designation) throw new CalendarWorkspaceApiError(502, 'An available revision selector is inconsistent.')
}

function validateSelectedRevision(value: Record<string, unknown>) {
  validateOptionalRevisionSelector(value, value.designation as RevisionDesignation)
  if (!['active_working', 'current_published'].includes(String(value.designation))) throw new CalendarWorkspaceApiError(502, 'The selected revision designation is invalid.')
  if (typeof value.readOnly !== 'boolean' || value.validationBasis !== 'current') throw new CalendarWorkspaceApiError(502, 'The selected revision access or validation basis is invalid.')
  if (value.designation === 'active_working') {
    if (value.readOnly || value.contentSource !== 'active_working' || !['draft', 'ready_for_review'].includes(String(value.lifecycleState)) || value.snapshotSchemaVersion !== null) throw new CalendarWorkspaceApiError(502, 'The selected Working revision is inconsistent.')
  } else if (!value.readOnly || value.contentSource !== 'captured_published' || value.lifecycleState !== 'published' || ![1, 2].includes(Number(value.snapshotSchemaVersion))) {
    throw new CalendarWorkspaceApiError(502, 'The selected Published revision is inconsistent.')
  }
}

function validateCourse(course: Record<string, unknown>) {
  const courseRef = requireString(course.courseRef, 'A workspace course reference is invalid.')
  if (!/^course:[1-9]\d*$/.test(courseRef)) throw new CalendarWorkspaceApiError(502, 'A workspace course reference is invalid.')
  for (const field of ['courseId', 'totalTeachingUnits', 'scheduledTeachingUnits', 'remainingTeachingUnits', 'remainingInstructionalMinutes']) requireNumber(course[field], 'A workspace course numeric field is invalid.')
  for (const field of ['code', 'name', 'cohort', 'studyType']) requireString(course[field], 'A workspace course text field is invalid.')
  if (typeof course.planningEligible !== 'boolean') throw new CalendarWorkspaceApiError(502, 'A workspace course planning-eligibility value is invalid.')
  for (const field of ['lecturerRefs', 'occurrenceRefs', 'findingRefs', 'outcomeRefs', 'needsReviewReasonRefs']) requireStringArray(course[field], 'A workspace course reference collection is invalid.')
  return courseRef
}

function validateOccurrence(occurrence: Record<string, unknown>, courseRefs: Set<string>) {
  const reference = requireString(occurrence.occurrenceRef, 'An occurrence reference is invalid.')
  if (!/^(teaching|exam):[1-9]\d*$/.test(reference) || occurrence.kind !== reference.split(':')[0]) throw new CalendarWorkspaceApiError(502, 'An occurrence reference or kind is invalid.')
  const courseRef = requireString(occurrence.courseRef, 'An occurrence course reference is invalid.')
  if (!courseRefs.has(courseRef)) throw new CalendarWorkspaceApiError(502, 'An occurrence references an unknown course.')
  for (const field of ['date', 'startTime', 'endTime', 'cohort', 'roomRef']) requireString(occurrence[field], 'An occurrence identifying field is invalid.')
  if (!isIsoDate(String(occurrence.date)) || !isClock(String(occurrence.startTime)) || !isClock(String(occurrence.endTime))) throw new CalendarWorkspaceApiError(502, 'An occurrence date or time is invalid.')
  requireStringArray(occurrence.lecturerRefs, 'An occurrence lecturer collection is invalid.')
  requireStringArray(occurrence.findingRefs, 'An occurrence finding collection is invalid.')
  if (occurrence.kind === 'teaching') {
    requireNumber(occurrence.teachingUnits, 'A teaching occurrence requires teaching units.')
    requireString(occurrence.source, 'A teaching occurrence requires a source.')
  } else if (occurrence.kind === 'exam') {
    requireString(occurrence.examType, 'An exam occurrence requires a type.')
    requireNumber(occurrence.durationMinutes, 'An exam occurrence requires a duration.')
    requireNumber(occurrence.requiredCapacity, 'An exam occurrence requires capacity context.')
    requireString(occurrence.assignedRoomName, 'An exam occurrence requires an assigned room name.')
    if (occurrence.currentRoomCapacity !== null) requireNumber(occurrence.currentRoomCapacity, 'An exam occurrence current room capacity is invalid.')
    validateExamValidityContext(occurrence.validityContext)
    if (occurrence.recommendationContext != null) validateExamRecommendationContext(occurrence.recommendationContext)
  }
  return reference
}

function validateOutcome(outcome: Record<string, unknown>, courseRefs: Set<string>, revisionId: unknown) {
  const reference = requireString(outcome.outcomeRef, 'A planning outcome reference is invalid.')
  if (!/^outcome:[1-9]\d*$/.test(reference)) throw new CalendarWorkspaceApiError(502, 'A planning outcome reference is invalid.')
  if (!courseRefs.has(String(outcome.courseRef)) || outcome.revisionId !== revisionId) throw new CalendarWorkspaceApiError(502, 'A planning outcome is associated with the wrong course or revision.')
  if (!['single_course_generation', 'multi_course_generation', 'semester_optimization', 'exam_generation'].includes(String(outcome.operationKind)) || !['successful', 'failed', 'stale', 'unchanged', 'skipped'].includes(String(outcome.classification))) throw new CalendarWorkspaceApiError(502, 'A planning outcome classification or operation kind is invalid.')
  requireString(outcome.sourceStatus, 'A planning outcome source status is invalid.')
  requireString(outcome.completedAt, 'A planning outcome completion time is invalid.')
  if (!Array.isArray(outcome.reasons) || outcome.reasons.some((reason) => !isRecord(reason))) throw new CalendarWorkspaceApiError(502, 'A planning outcome reason collection is invalid.')
  return reference
}

function validateHoliday(holiday: Record<string, unknown>) {
  const reference = requireString(holiday.holidayRef, 'A holiday reference is invalid.')
  if (!/^holiday:[1-9]\d*$/.test(reference)) throw new CalendarWorkspaceApiError(502, 'A holiday reference is invalid.')
  const date = requireString(holiday.date, 'A holiday date is invalid.')
  requireString(holiday.name, 'A holiday name is invalid.')
  if (!isIsoDate(date)) throw new CalendarWorkspaceApiError(502, 'A holiday date is invalid.')
  return reference
}

function validateFacets(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'The workspace facets are invalid.')
  for (const key of ['courses', 'cohorts', 'lecturers', 'rooms', 'studyTypes', 'sessionTypes', 'lifecycleContexts', 'validationCategories']) {
    const values = value[key]
    if (!Array.isArray(values) || values.some((facet) => !isRecord(facet) || typeof facet.value !== 'string' || typeof facet.label !== 'string')) throw new CalendarWorkspaceApiError(502, 'The workspace facets are invalid.')
  }
}

function validateCoverage(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'The planning-outcome coverage is invalid.')
  const eligible = requireNonNegativeInteger(value.eligibleCourseCount, 'The planning-outcome coverage is invalid.')
  const covered = requireNonNegativeInteger(value.coveredCourseCount, 'The planning-outcome coverage is invalid.')
  if (typeof value.coverageComplete !== 'boolean' || covered > eligible || value.coverageComplete !== (eligible > 0 && covered === eligible)) throw new CalendarWorkspaceApiError(502, 'The planning-outcome coverage is inconsistent.')
}

function isIsoDate(value: string) {
  return /^\d{4}-\d{2}-\d{2}$/.test(value) && !Number.isNaN(Date.parse(`${value}T00:00:00Z`))
}

function isClock(value: string) {
  return /^([01]\d|2[0-3]):[0-5]\d$/.test(value)
}

function validateFinding(finding: Record<string, unknown>) {
  const details = finding.details
  if (details == null || typeof details !== 'object') throw new CalendarWorkspaceApiError(502, 'A validation finding requires typed details.')
  const detail = details as Record<string, unknown>
  const expectedKind: Record<string, string> = {
    lecturer_conflict: 'conflict',
    room_conflict: 'conflict',
    cohort_conflict: 'conflict',
    room_capacity: 'capacity',
    holiday: 'holiday',
    exam_validity: 'exam_validity',
    other: 'other',
  }
  const findingRef = requireString(finding.findingRef, 'A validation finding reference is invalid.')
  if (!/^finding:[^:]+:.+/.test(findingRef) || finding.validationBasis !== 'current' || typeof finding.category !== 'string' || detail.kind !== expectedKind[finding.category]) throw new CalendarWorkspaceApiError(502, 'A validation finding category does not match its detail kind.')
  if (detail.kind === 'conflict') {
    const refs = requireStringArray(detail.occurrenceRefs, 'A conflict finding is invalid.')
    if (`${detail.conflictType}_conflict` !== finding.category || refs.length !== 2 || new Set(refs).size !== 2 || typeof detail.subjectRef !== 'string' || detail.subjectRef.length === 0) throw new CalendarWorkspaceApiError(502, 'A conflict finding is invalid.')
  } else if (detail.kind === 'capacity') {
    if (typeof detail.occurrenceRef !== 'string' || typeof detail.roomRef !== 'string' || detail.roomRef.length === 0 || typeof detail.roomName !== 'string' || detail.roomName.length === 0) throw new CalendarWorkspaceApiError(502, 'A capacity finding is invalid.')
    requireNonNegativeInteger(detail.requiredCapacity, 'A capacity finding is invalid.')
    requireNonNegativeInteger(detail.currentCapacity, 'A capacity finding is invalid.')
  } else if (detail.kind === 'holiday') {
    if (typeof detail.holidayRef !== 'string' || detail.holidayRef.length === 0 || typeof detail.holidayDate !== 'string' || !isIsoDate(detail.holidayDate) || typeof detail.holidayName !== 'string' || detail.holidayName.length === 0 || requireStringArray(detail.occurrenceRefs, 'A holiday finding is invalid.').length === 0) throw new CalendarWorkspaceApiError(502, 'A holiday finding is invalid.')
  } else if (detail.kind === 'exam_validity') {
    if (typeof detail.examOccurrenceRef !== 'string' || !detail.examOccurrenceRef.startsWith('exam:') || typeof detail.issueCode !== 'string' || detail.issueCode.length === 0 || !isRecord(detail.supportingValues) || Object.values(detail.supportingValues).some((item) => !['string', 'number', 'boolean'].includes(typeof item))) throw new CalendarWorkspaceApiError(502, 'An exam-validity finding is invalid.')
  } else if (detail.kind === 'other') {
    if (typeof detail.issueCode !== 'string' || detail.issueCode.length === 0 || requireStringArray(detail.occurrenceRefs, 'An additional validation finding is invalid.').length === 0) throw new CalendarWorkspaceApiError(502, 'An additional validation finding is invalid.')
  }
}

function validateFindingReferences(
  finding: Record<string, unknown>,
  occurrenceRefs: Set<string>,
  holidayRefs: Set<string>,
) {
  const detail = finding.details as Record<string, unknown>
  const requireKnownOccurrences = (value: unknown) => {
    requireStringArray(value, 'A finding detail has invalid occurrence references.').forEach((ref) => {
      if (!occurrenceRefs.has(ref)) throw new CalendarWorkspaceApiError(502, 'A finding detail references an unknown occurrence.')
    })
  }
  if (detail.kind === 'conflict' || detail.kind === 'holiday' || detail.kind === 'other') requireKnownOccurrences(detail.occurrenceRefs)
  if (detail.kind === 'capacity' && !occurrenceRefs.has(String(detail.occurrenceRef))) throw new CalendarWorkspaceApiError(502, 'A capacity finding references an unknown occurrence.')
  if (detail.kind === 'exam_validity' && !occurrenceRefs.has(String(detail.examOccurrenceRef))) throw new CalendarWorkspaceApiError(502, 'An exam-validity finding references an unknown occurrence.')
  if (detail.kind === 'holiday' && !holidayRefs.has(String(detail.holidayRef))) throw new CalendarWorkspaceApiError(502, 'A holiday finding references an unknown holiday.')
}

function requireNonNegativeInteger(value: unknown, message: string) {
  const number = requireNumber(value, message)
  if (!Number.isInteger(number) || number < 0) throw new CalendarWorkspaceApiError(502, message)
  return number
}

function validateExamValidityContext(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'An exam occurrence validity context is invalid.')
  requireString(value.configurationIdentifier, 'An exam occurrence validity context is invalid.')
  requireNonNegativeInteger(value.configurationRevision, 'An exam occurrence validity context is invalid.')
  const finalTeachingDate = requireString(value.finalTeachingDate, 'An exam occurrence validity context is invalid.')
  const finalTeachingEndTime = requireString(value.finalTeachingEndTime, 'An exam occurrence validity context is invalid.')
  requireString(value.source, 'An exam occurrence validity context is invalid.')
  if (!isIsoDate(finalTeachingDate) || !isClock(finalTeachingEndTime) || (value.capturedIssues != null && !Array.isArray(value.capturedIssues))) throw new CalendarWorkspaceApiError(502, 'An exam occurrence validity context is invalid.')
}

function validateExamRecommendationContext(value: unknown) {
  if (!isRecord(value)) throw new CalendarWorkspaceApiError(502, 'An exam occurrence recommendation context is invalid.')
  const start = requireString(value.recommendedStartDate, 'An exam occurrence recommendation context is invalid.')
  const end = requireString(value.recommendedEndDate, 'An exam occurrence recommendation context is invalid.')
  if (!isIsoDate(start) || !isIsoDate(end) || start > end || typeof value.recommendationWasOverridden !== 'boolean' || typeof value.outsideRecommendedWindow !== 'boolean') throw new CalendarWorkspaceApiError(502, 'An exam occurrence recommendation context is invalid.')
}

function validateMetricValues(key: string, metric: WorkspaceMetric) {
  const numericFields: (keyof WorkspaceMetric)[] = [
    'remainingTeachingUnits',
    'remainingInstructionalMinutes',
    'contributingCourseCount',
    'distinctFindingCount',
    'affectedOccurrenceCount',
    'failedOutcomeCount',
    'staleOutcomeCount',
    'unchangedOutcomeCount',
    'distinctCourseCount',
  ]
  for (const field of numericFields) {
    if (metric[field] != null) requireNonNegativeInteger(metric[field], `The ${key} summary has an invalid numeric value.`)
  }
  if (key === 'unscheduledWork') {
    if ((metric.remainingInstructionalMinutes ?? 0) !== (metric.remainingTeachingUnits ?? 0) * 45 || metric.contributingCourseCount !== metric.contributorRefs.length) throw new CalendarWorkspaceApiError(502, 'The unscheduledWork summary is inconsistent.')
  }
  if (key === 'conflicts') {
    if (!isRecord(metric.countByType)) throw new CalendarWorkspaceApiError(502, 'The conflicts summary is invalid.')
    const lecturer = requireNonNegativeInteger(metric.countByType.lecturer, 'The conflicts summary is invalid.')
    const room = requireNonNegativeInteger(metric.countByType.room, 'The conflicts summary is invalid.')
    const cohort = requireNonNegativeInteger(metric.countByType.cohort, 'The conflicts summary is invalid.')
    if (Object.keys(metric.countByType).some((field) => !['lecturer', 'room', 'cohort'].includes(field)) || lecturer + room + cohort !== metric.distinctFindingCount || metric.distinctFindingCount !== metric.contributorRefs.length) throw new CalendarWorkspaceApiError(502, 'The conflicts summary is inconsistent.')
  }
  if (key === 'capacityIssues' && metric.affectedOccurrenceCount !== metric.contributorRefs.length) throw new CalendarWorkspaceApiError(502, 'The capacityIssues summary is inconsistent.')
  if (key === 'needsReview' && metric.distinctCourseCount !== metric.contributorRefs.length) throw new CalendarWorkspaceApiError(502, 'The needsReview summary is inconsistent.')
  if (key === 'planningFailures') {
    validateCoverage(metric.coverage)
    const coverage = metric.coverage!
    const expectedAvailability = coverage.eligibleCourseCount === 0
      ? 'not_applicable'
      : coverage.coveredCourseCount === 0
        ? 'unavailable'
        : coverage.coverageComplete
          ? 'available'
          : 'partial'
    if (metric.availability !== expectedAvailability || (metric.failedOutcomeCount ?? 0) + (metric.staleOutcomeCount ?? 0) + (metric.unchangedOutcomeCount ?? 0) !== metric.contributorRefs.length) throw new CalendarWorkspaceApiError(502, 'The planningFailures summary coverage is inconsistent.')
  }
}
