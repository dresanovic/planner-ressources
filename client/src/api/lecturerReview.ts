export type ReviewRevisionState =
  | 'draft'
  | 'ready_for_review'
  | 'published'
  | 'abandoned'
  | 'superseded'
export type ReviewLinkStatus =
  | 'active'
  | 'expired'
  | 'revoked'
  | 'replaced'
  | 'revision_ended'
export type ReviewFeedbackAvailability = 'complete' | 'partial' | 'unavailable'
export type ReviewFeedbackKind =
  | 'revision_comment'
  | 'session_comment'
  | 'impossible_session'
export type ReviewSessionKind = 'teaching' | 'exam'
export type ReviewFeedbackSessionStatus =
  | 'current'
  | 'changed'
  | 'unavailable'

export type ReviewRevision = {
  id: number
  semesterId: number
  semesterName: string
  label: string
  state: ReviewRevisionState
}
export type ReviewCourseIdentity = {
  sourceCourseId: number
  code: string
  title: string
}
export type LecturerAssignmentSummary = {
  lecturerId: number
  lecturerName: string
  sessionCount: number
  courses: ReviewCourseIdentity[]
  initialIssueAllowed: boolean
}
export type LecturerReviewLinkSummary = {
  id: number
  revisionId: number
  lecturerId: number
  intendedLecturerName: string
  durationDays: 1 | 2 | 3
  issuedAt: string
  expiresAt: string
  timeZone: string
  status: ReviewLinkStatus
  endedAt: string | null
  replaceAllowed: boolean
}
export type LecturerReviewSessionContext = {
  sessionRef: string
  sessionKind: ReviewSessionKind
  sourceSessionId: number
  sessionType: string
  courseSourceId: number
  courseCode: string
  courseTitle: string
  date: string
  startTime: string
  endTime: string
  timeZone: string
  roomName: string
  cohortName: string
  studyType?: string | null
  teachingUnits?: number | null
  examDurationMinutes?: number | null
}
export type PlannerReviewFeedbackItem = {
  id: number
  intendedLecturerId: number
  intendedLecturerName: string
  attribution: string
  kind: ReviewFeedbackKind
  comment: string | null
  sessionContext: LecturerReviewSessionContext | null
  sessionStatus: ReviewFeedbackSessionStatus | null
  submittedAt: string
  timeZone: string
}
export type PlannerReviewFeedbackGroup = {
  groupRef: string
  level: 'revision' | 'session'
  sessionContext: LecturerReviewSessionContext | null
  currentNavigation: { revisionId: number; occurrenceRef: string } | null
  impossibleFlagCount: number
  items: PlannerReviewFeedbackItem[]
}
export type LecturerReviewOverview = {
  revision: ReviewRevision
  lecturers: LecturerAssignmentSummary[]
  links: LecturerReviewLinkSummary[]
  feedbackAvailability: ReviewFeedbackAvailability
  totalFeedbackCount: number | null
  impossibleFlagCount: number | null
  feedbackGroups: PlannerReviewFeedbackGroup[]
}
export type IssuedLecturerReviewLink = {
  secret: string
  issuedLink: LecturerReviewLinkSummary
  overview: LecturerReviewOverview
}
export type PublicReviewSession = {
  sessionRef: string
  sessionKind: ReviewSessionKind
  sourceSessionId: number
  courseRef: string
  sessionType: string
  date: string
  startTime: string
  endTime: string
  timeZone: string
  roomName: string
  roomRef: string
  cohortName: string
  teachingUnits: number | null
  examDurationMinutes: number | null
  validationFindingRefs: string[]
}
export type PublicReviewCourse = ReviewCourseIdentity & {
  courseRef: string
  cohortName: string
  studyType: string
  sessions: PublicReviewSession[]
}
export type PublicReviewValidationFinding = {
  findingRef: string
  category:
    | 'lecturer_conflict'
    | 'room_conflict'
    | 'cohort_conflict'
    | 'room_capacity'
    | 'holiday'
    | 'exam_validity'
    | 'other'
  message: string
  affectedSessionRefs: string[]
}
export type PublicReviewFacetValue = {
  value: string
  label: string
}
export type PublicReviewFilterFacets = {
  courses: PublicReviewFacetValue[]
  cohorts: PublicReviewFacetValue[]
  rooms: PublicReviewFacetValue[]
  studyTypes: PublicReviewFacetValue[]
  sessionTypes: PublicReviewFacetValue[]
  lifecycleContexts: PublicReviewFacetValue[]
  validationCategories: PublicReviewFacetValue[]
}
export type PublicReviewFeedbackItem = {
  id: number
  kind: ReviewFeedbackKind
  sessionRef: string | null
  comment: string | null
  submittedAt: string
  timeZone: string
}
export type PublicLecturerReview = {
  intendedLecturer: string
  identityDisclaimer: string
  revision: ReviewRevision
  accessExpiresAt: string
  timeZone: string
  semesterStartDate: string
  semesterEndDate: string
  validationAvailability: ReviewFeedbackAvailability
  validationFindings: PublicReviewValidationFinding[]
  filterFacets: PublicReviewFilterFacets
  courses: PublicReviewCourse[]
  submittedFeedback: PublicReviewFeedbackItem[]
}
export type IssueLecturerReviewInput = {
  lecturerId: number
  durationDays?: 1 | 2 | 3
}
export type ReplaceLecturerReviewInput = {
  durationDays?: 1 | 2 | 3
}
export type LecturerReviewFeedbackInput = {
  clientSubmissionId: string
  kind: ReviewFeedbackKind
  sessionRef?: string
  comment?: string
}
export type LecturerReviewFeedbackResult = {
  outcome: 'created' | 'already_accepted'
  item: PublicReviewFeedbackItem
}
export type LecturerCalendarDownload = {
  blob: Blob
  filename: string
}

export class LecturerReviewApiError extends Error {
  status: number
  retryable: boolean
  code: string | null

  constructor(
    status: number,
    message: string,
    retryable = status === 0 || status >= 500,
    code: string | null = null,
  ) {
    super(message)
    this.name = 'LecturerReviewApiError'
    this.status = status
    this.retryable = retryable
    this.code = code
  }
}

const SECRET_SHAPE = /^[A-Za-z0-9_-]{43}$/
const SESSION_REF = /^(teaching|exam):[1-9][0-9]*$/
const OFFSET_TIMESTAMP = /(?:Z|[+-]\d{2}:\d{2})$/
const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const MAX_CALENDAR_DISPOSITION_LENGTH = 4096
const REVIEW_STATES = new Set([
  'draft',
  'ready_for_review',
  'published',
  'abandoned',
  'superseded',
])
const LINK_STATES = new Set([
  'active',
  'expired',
  'revoked',
  'replaced',
  'revision_ended',
])
const FEEDBACK_KINDS = new Set([
  'revision_comment',
  'session_comment',
  'impossible_session',
])

export function buildLecturerReviewUrl(secret: string, origin = window.location.origin) {
  if (!SECRET_SHAPE.test(secret)) {
    throw new LecturerReviewApiError(422, 'The review link could not be created.')
  }
  return `${origin.replace(/\/+$/, '')}/lecturer-review/#/${secret}`
}

export async function getLecturerReviewOverview(
  revisionId: number,
): Promise<LecturerReviewOverview> {
  const payload = await plannerRequest(
    `/api/schedule-revisions/${positiveId(revisionId)}/lecturer-review`,
  )
  validateOverview(payload)
  return payload
}

export async function issueLecturerReviewLink(
  revisionId: number,
  input: IssueLecturerReviewInput,
): Promise<IssuedLecturerReviewLink> {
  const payload = await plannerRequest(
    `/api/schedule-revisions/${positiveId(revisionId)}/lecturer-review-links`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        lecturerId: positiveId(input.lecturerId),
        durationDays: input.durationDays ?? 3,
      }),
    },
  )
  assertExactKeys(payload, ['secret', 'issuedLink', 'overview'])
  if (typeof payload.secret !== 'string' || !SECRET_SHAPE.test(payload.secret)) {
    invalidResponse()
  }
  validateLink(payload.issuedLink)
  validateOverview(payload.overview)
  return payload as IssuedLecturerReviewLink
}

export async function revokeLecturerReviewLink(
  linkId: number,
): Promise<LecturerReviewOverview> {
  const payload = await plannerRequest(
    `/api/lecturer-review-links/${positiveId(linkId)}/revoke`,
    { method: 'POST' },
  )
  validateOverview(payload)
  return payload
}

export async function replaceLecturerReviewLink(
  linkId: number,
  input: ReplaceLecturerReviewInput = {},
): Promise<IssuedLecturerReviewLink> {
  const payload = await plannerRequest(
    `/api/lecturer-review-links/${positiveId(linkId)}/replace`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ durationDays: input.durationDays ?? 3 }),
    },
  )
  assertExactKeys(payload, ['secret', 'issuedLink', 'overview'])
  if (typeof payload.secret !== 'string' || !SECRET_SHAPE.test(payload.secret)) {
    invalidResponse()
  }
  validateLink(payload.issuedLink)
  validateOverview(payload.overview)
  return payload as IssuedLecturerReviewLink
}

export async function getPublicLecturerReview(
  secret: string,
): Promise<PublicLecturerReview> {
  if (!SECRET_SHAPE.test(secret)) {
    throw new LecturerReviewApiError(404, 'This review is unavailable.')
  }
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/public/lecturer-review`, {
      method: 'GET',
      credentials: 'omit',
      headers: { Authorization: `Bearer ${secret}` },
    })
  } catch {
    throw new LecturerReviewApiError(
      0,
      'The review could not be reached. Try again.',
      true,
    )
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new LecturerReviewApiError(
      response.status,
      response.status === 429
        ? 'This review is temporarily unavailable. Try again later.'
        : 'This review is unavailable.',
      response.status === 429 || response.status >= 500,
    )
  }
  validatePublicReview(payload)
  return payload
}

export async function downloadPublicLecturerCalendar(
  secret: string,
): Promise<LecturerCalendarDownload> {
  if (!SECRET_SHAPE.test(secret)) {
    throw new LecturerReviewApiError(
      404,
      'This review is unavailable.',
      false,
      'REVIEW_UNAVAILABLE',
    )
  }
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/public/lecturer-review/calendar`, {
      method: 'GET',
      credentials: 'omit',
      headers: {
        Authorization: `Bearer ${secret}`,
        Accept: 'text/calendar',
      },
    })
  } catch {
    throw new LecturerReviewApiError(
      0,
      'The calendar could not be reached. Try again.',
      true,
    )
  }
  if (!response.ok) {
    const retryable = response.status === 429 || response.status >= 500
    throw new LecturerReviewApiError(
      response.status,
      retryable
        ? 'The calendar is temporarily unavailable. Try again.'
        : 'This review is unavailable.',
      retryable,
      response.status === 404
        ? 'REVIEW_UNAVAILABLE'
        : 'CALENDAR_EXPORT_UNAVAILABLE',
    )
  }
  if (!/^text\/calendar\s*;\s*charset=utf-8$/i.test(
    response.headers.get('Content-Type')?.trim() ?? '',
  )) {
    throw new LecturerReviewApiError(
      502,
      'The calendar response is invalid.',
      true,
      'CALENDAR_EXPORT_UNAVAILABLE',
    )
  }
  const filename = calendarFilename(response.headers.get('Content-Disposition'))
  const blob = await response.blob().catch(() => {
    invalidCalendarResponse()
  })
  if (blob.size === 0) invalidCalendarResponse()
  return { blob, filename }
}

export async function submitPublicLecturerFeedback(
  secret: string,
  input: LecturerReviewFeedbackInput,
): Promise<LecturerReviewFeedbackResult> {
  if (!SECRET_SHAPE.test(secret)) {
    throw new LecturerReviewApiError(
      404,
      'This review is unavailable.',
      false,
      'REVIEW_UNAVAILABLE',
    )
  }
  let response: Response
  try {
    response = await fetch(`${API_BASE}/api/public/lecturer-review/feedback`, {
      method: 'POST',
      credentials: 'omit',
      headers: {
        Authorization: `Bearer ${secret}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(input),
    })
  } catch {
    throw new LecturerReviewApiError(
      0,
      'The feedback result is uncertain. Retry the same submission.',
      true,
    )
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    const safe = publicErrorForStatus(response.status)
    throw new LecturerReviewApiError(
      response.status,
      safe.message,
      response.status === 429 || response.status >= 500,
      safe.code,
    )
  }
  assertExactKeys(payload, ['outcome', 'item'])
  if (!['created', 'already_accepted'].includes(String(payload.outcome))) {
    invalidResponse()
  }
  validatePublicFeedback(payload.item)
  return payload as LecturerReviewFeedbackResult
}

async function plannerRequest(path: string, init?: RequestInit): Promise<unknown> {
  let response: Response
  try {
    response = await fetch(`${API_BASE}${path}`, init)
  } catch {
    throw new LecturerReviewApiError(
      0,
      'The lecturer review service could not be reached.',
      true,
    )
  }
  const payload = await response.json().catch(() => null)
  if (!response.ok) {
    throw new LecturerReviewApiError(
      response.status,
      'The lecturer review request failed.',
    )
  }
  return payload
}

function validateOverview(value: unknown): asserts value is LecturerReviewOverview {
  assertExactKeys(value, [
    'revision',
    'lecturers',
    'links',
    'feedbackAvailability',
    'totalFeedbackCount',
    'impossibleFlagCount',
    'feedbackGroups',
  ])
  validateRevision(value.revision)
  if (!Array.isArray(value.lecturers) || !Array.isArray(value.links)) invalidResponse()
  value.lecturers.forEach(validateLecturer)
  value.links.forEach(validateLink)
  if (
    !['complete', 'partial', 'unavailable'].includes(
      String(value.feedbackAvailability),
    ) ||
    !Array.isArray(value.feedbackGroups)
  ) invalidResponse()
  const complete = value.feedbackAvailability === 'complete'
  for (const count of [value.totalFeedbackCount, value.impossibleFlagCount]) {
    if (complete ? !isNonNegativeInteger(count) : count !== null) invalidResponse()
  }
  value.feedbackGroups.forEach(validateFeedbackGroup)
  if (complete) {
    const itemCount = value.feedbackGroups.reduce(
      (total, group) => total + group.items.length,
      0,
    )
    const flagCount = value.feedbackGroups.reduce(
      (total, group) => total + group.impossibleFlagCount,
      0,
    )
    if (
      value.totalFeedbackCount !== itemCount ||
      value.impossibleFlagCount !== flagCount
    ) {
      invalidResponse()
    }
  }
}

function validatePublicReview(value: unknown): asserts value is PublicLecturerReview {
  assertExactKeys(value, [
    'intendedLecturer',
    'identityDisclaimer',
    'revision',
    'accessExpiresAt',
    'timeZone',
    'semesterStartDate',
    'semesterEndDate',
    'validationAvailability',
    'validationFindings',
    'filterFacets',
    'courses',
    'submittedFeedback',
  ])
  requireStrings(
    value,
    [
      'intendedLecturer',
      'identityDisclaimer',
      'accessExpiresAt',
      'timeZone',
      'semesterStartDate',
      'semesterEndDate',
    ],
  )
  requireTimestamp(value.accessExpiresAt)
  validateRevision(value.revision)
  if (
    !['complete', 'partial', 'unavailable'].includes(
      String(value.validationAvailability),
    ) ||
    !Array.isArray(value.validationFindings) ||
    !Array.isArray(value.courses) ||
    !Array.isArray(value.submittedFeedback)
  ) {
    invalidResponse()
  }
  validatePublicFacets(value.filterFacets)
  value.validationFindings.forEach(validatePublicFinding)
  value.courses.forEach(validatePublicCourse)
  value.submittedFeedback.forEach(validatePublicFeedback)
  const courses = value.courses as PublicReviewCourse[]
  const findings =
    value.validationFindings as PublicReviewValidationFinding[]
  const sessionRefs = new Set(
    courses.flatMap((course) =>
      course.sessions.map((session) => session.sessionRef),
    ),
  )
  const findingRefs = new Set(
    findings.map((finding) => finding.findingRef),
  )
  if (
    findings.some((finding) =>
      finding.affectedSessionRefs.some((ref) => !sessionRefs.has(ref)),
    ) ||
    courses.some((course) =>
      course.sessions.some(
        (session) =>
          session.courseRef !== course.courseRef ||
          session.validationFindingRefs.some((ref) => !findingRefs.has(ref)),
      ),
    )
  ) {
    invalidResponse()
  }
}

function validateRevision(value: unknown): void {
  assertExactKeys(value, ['id', 'semesterId', 'semesterName', 'label', 'state'])
  requirePositiveIntegers(value, ['id', 'semesterId'])
  requireStrings(value, ['semesterName', 'label'])
  if (!REVIEW_STATES.has(String(value.state))) invalidResponse()
}

function validateLecturer(value: unknown): void {
  assertExactKeys(value, [
    'lecturerId',
    'lecturerName',
    'sessionCount',
    'courses',
    'initialIssueAllowed',
  ])
  requirePositiveIntegers(value, ['lecturerId'])
  requireStrings(value, ['lecturerName'])
  if (
    !isNonNegativeInteger(value.sessionCount) ||
    !Array.isArray(value.courses) ||
    typeof value.initialIssueAllowed !== 'boolean'
  ) invalidResponse()
  value.courses.forEach(validateCourseIdentity)
}

function validateCourseIdentity(value: unknown): void {
  assertExactKeys(value, ['sourceCourseId', 'code', 'title'])
  requirePositiveIntegers(value, ['sourceCourseId'])
  requireStrings(value, ['code', 'title'])
}

function validateLink(value: unknown): void {
  assertExactKeys(value, [
    'id',
    'revisionId',
    'lecturerId',
    'intendedLecturerName',
    'durationDays',
    'issuedAt',
    'expiresAt',
    'timeZone',
    'status',
    'endedAt',
    'replaceAllowed',
  ])
  requirePositiveIntegers(value, ['id', 'revisionId', 'lecturerId'])
  requireStrings(value, [
    'intendedLecturerName',
    'issuedAt',
    'expiresAt',
    'timeZone',
  ])
  requireTimestamp(value.issuedAt)
  requireTimestamp(value.expiresAt)
  if (
    ![1, 2, 3].includes(Number(value.durationDays)) ||
    !LINK_STATES.has(String(value.status)) ||
    (value.endedAt !== null &&
      (typeof value.endedAt !== 'string' ||
        !OFFSET_TIMESTAMP.test(value.endedAt))) ||
    typeof value.replaceAllowed !== 'boolean'
  ) invalidResponse()
}

function validateFeedbackGroup(value: unknown): void {
  assertExactKeys(value, [
    'groupRef',
    'level',
    'sessionContext',
    'currentNavigation',
    'impossibleFlagCount',
    'items',
  ])
  requireStrings(value, ['groupRef'])
  if (
    !['revision', 'session'].includes(String(value.level)) ||
    !isNonNegativeInteger(value.impossibleFlagCount) ||
    !Array.isArray(value.items)
  ) invalidResponse()
  value.items.forEach(validatePlannerFeedback)
  const flagCount = value.items.filter(
    (item) =>
      item.kind === 'impossible_session' && item.sessionStatus === 'current',
  ).length
  if (flagCount !== value.impossibleFlagCount) invalidResponse()

  if (value.level === 'revision') {
    if (
      value.groupRef !== 'revision' ||
      value.sessionContext !== null ||
      value.currentNavigation !== null ||
      value.items.some(
        (item) =>
          item.kind !== 'revision_comment' || item.sessionContext !== null,
      )
    ) {
      invalidResponse()
    }
    return
  }
  const sessionContext = value.sessionContext
  if (
    !SESSION_REF.test(String(value.groupRef)) ||
    !isRecord(sessionContext) ||
    value.items.some(
      (item) =>
        item.kind === 'revision_comment' ||
        !isRecord(item.sessionContext) ||
        item.sessionContext.sessionRef !== value.groupRef,
    )
  ) {
    invalidResponse()
  }
  validateSessionContext(sessionContext)
  if (sessionContext.sessionRef !== value.groupRef) invalidResponse()
  const currentNavigation = value.currentNavigation
  if (currentNavigation !== null) {
    if (!isRecord(currentNavigation)) invalidResponse()
    validatePlannerNavigation(currentNavigation)
    if (currentNavigation.occurrenceRef !== value.groupRef) {
      invalidResponse()
    }
  }
}

function validatePlannerFeedback(value: unknown): void {
  assertExactKeys(value, [
    'id',
    'intendedLecturerId',
    'intendedLecturerName',
    'attribution',
    'kind',
    'comment',
    'sessionContext',
    'sessionStatus',
    'submittedAt',
    'timeZone',
  ])
  requirePositiveIntegers(value, ['id', 'intendedLecturerId'])
  requireStrings(value, [
    'intendedLecturerName',
    'attribution',
    'submittedAt',
    'timeZone',
  ])
  requireTimestamp(value.submittedAt)
  if (
    !FEEDBACK_KINDS.has(String(value.kind)) ||
    (value.comment !== null &&
      (typeof value.comment !== 'string' || value.comment.length > 2000)) ||
    (value.sessionContext !== null && !isRecord(value.sessionContext)) ||
    ![null, 'current', 'changed', 'unavailable'].includes(
      value.sessionStatus as null | string,
    )
  ) {
    invalidResponse()
  }
  if (value.sessionContext !== null) validateSessionContext(value.sessionContext)
  if (
    value.kind === 'revision_comment'
      ? value.sessionContext !== null || value.sessionStatus !== null
      : value.sessionContext === null || value.sessionStatus === null
  ) invalidResponse()
}

function validateSessionContext(value: unknown): void {
  assertRequiredAndAllowedKeys(value, [
    'sessionRef',
    'sessionKind',
    'sourceSessionId',
    'sessionType',
    'courseSourceId',
    'courseCode',
    'courseTitle',
    'date',
    'startTime',
    'endTime',
    'timeZone',
    'roomName',
    'cohortName',
  ], [
    'sessionRef',
    'sessionKind',
    'sourceSessionId',
    'sessionType',
    'courseSourceId',
    'courseCode',
    'courseTitle',
    'date',
    'startTime',
    'endTime',
    'timeZone',
    'roomName',
    'cohortName',
    'studyType',
    'teachingUnits',
    'examDurationMinutes',
  ])
  requirePositiveIntegers(value, ['sourceSessionId', 'courseSourceId'])
  requireStrings(value, [
    'sessionRef',
    'sessionType',
    'courseCode',
    'courseTitle',
    'date',
    'startTime',
    'endTime',
    'timeZone',
    'roomName',
    'cohortName',
  ])
  if (
    !SESSION_REF.test(String(value.sessionRef)) ||
    !['teaching', 'exam'].includes(String(value.sessionKind)) ||
    value.sessionRef !== `${value.sessionKind}:${value.sourceSessionId}` ||
    (value.studyType !== undefined &&
      value.studyType !== null &&
      typeof value.studyType !== 'string') ||
    (value.teachingUnits !== undefined &&
      !isNullablePositiveInteger(value.teachingUnits)) ||
    (value.examDurationMinutes !== undefined &&
      !isNullablePositiveInteger(value.examDurationMinutes))
  ) {
    invalidResponse()
  }
}

function validatePlannerNavigation(value: unknown): void {
  assertExactKeys(value, ['revisionId', 'occurrenceRef'])
  requirePositiveIntegers(value, ['revisionId'])
  requireStrings(value, ['occurrenceRef'])
  if (!SESSION_REF.test(String(value.occurrenceRef))) invalidResponse()
}

function validatePublicCourse(value: unknown): void {
  assertExactKeys(value, [
    'sourceCourseId',
    'courseRef',
    'code',
    'title',
    'cohortName',
    'studyType',
    'sessions',
  ])
  requirePositiveIntegers(value, ['sourceCourseId'])
  requireStrings(value, [
    'courseRef',
    'code',
    'title',
    'cohortName',
    'studyType',
  ])
  if (value.courseRef !== `course:${value.sourceCourseId}`) invalidResponse()
  if (!Array.isArray(value.sessions)) invalidResponse()
  value.sessions.forEach(validatePublicSession)
}

function validatePublicSession(value: unknown): void {
  assertExactKeys(value, [
    'sessionRef',
    'sessionKind',
    'sourceSessionId',
    'courseRef',
    'sessionType',
    'date',
    'startTime',
    'endTime',
    'timeZone',
    'roomName',
    'roomRef',
    'cohortName',
    'teachingUnits',
    'examDurationMinutes',
    'validationFindingRefs',
  ])
  requirePositiveIntegers(value, ['sourceSessionId'])
  requireStrings(value, [
    'sessionRef',
    'courseRef',
    'sessionType',
    'date',
    'startTime',
    'endTime',
    'timeZone',
    'roomName',
    'roomRef',
    'cohortName',
  ])
  if (
    !SESSION_REF.test(String(value.sessionRef)) ||
    !['teaching', 'exam'].includes(String(value.sessionKind)) ||
    !/^course:[1-9][0-9]*$/.test(String(value.courseRef)) ||
    !/^room:[1-9][0-9]*$/.test(String(value.roomRef)) ||
    !isNullablePositiveInteger(value.teachingUnits) ||
    !isNullablePositiveInteger(value.examDurationMinutes) ||
    (value.sessionKind === 'teaching' &&
      (value.teachingUnits === null ||
        value.examDurationMinutes !== null)) ||
    (value.sessionKind === 'exam' &&
      (value.examDurationMinutes === null || value.teachingUnits !== null)) ||
    !Array.isArray(value.validationFindingRefs) ||
    value.validationFindingRefs.some(
      (ref) => typeof ref !== 'string' || ref.length === 0,
    )
  ) invalidResponse()
}

function validatePublicFinding(value: unknown): void {
  assertExactKeys(value, [
    'findingRef',
    'category',
    'message',
    'affectedSessionRefs',
  ])
  requireStrings(value, ['findingRef', 'message'])
  if (
    ![
      'lecturer_conflict',
      'room_conflict',
      'cohort_conflict',
      'room_capacity',
      'holiday',
      'exam_validity',
      'other',
    ].includes(String(value.category)) ||
    !Array.isArray(value.affectedSessionRefs) ||
    value.affectedSessionRefs.some(
      (ref) => typeof ref !== 'string' || !SESSION_REF.test(ref),
    )
  ) invalidResponse()
}

function validatePublicFacets(value: unknown): void {
  assertExactKeys(value, [
    'courses',
    'cohorts',
    'rooms',
    'studyTypes',
    'sessionTypes',
    'lifecycleContexts',
    'validationCategories',
  ])
  for (const key of Object.keys(value)) {
    const values = value[key]
    if (!Array.isArray(values)) invalidResponse()
    values.forEach((facet) => {
      assertExactKeys(facet, ['value', 'label'])
      requireStrings(facet, ['value', 'label'])
    })
  }
  if ((value.lifecycleContexts as unknown[]).length > 1) invalidResponse()
}

function validatePublicFeedback(value: unknown): void {
  assertExactKeys(value, [
    'id',
    'kind',
    'sessionRef',
    'comment',
    'submittedAt',
    'timeZone',
  ])
  requirePositiveIntegers(value, ['id'])
  requireStrings(value, ['submittedAt', 'timeZone'])
  requireTimestamp(value.submittedAt)
  if (
    !FEEDBACK_KINDS.has(String(value.kind)) ||
    (value.sessionRef !== null &&
      (typeof value.sessionRef !== 'string' ||
        !SESSION_REF.test(value.sessionRef))) ||
    (value.comment !== null && typeof value.comment !== 'string')
  ) invalidResponse()
}

function assertExactKeys(
  value: unknown,
  expected: readonly string[],
): asserts value is Record<string, unknown> {
  if (!isRecord(value)) invalidResponse()
  const keys = Object.keys(value).sort()
  if (
    keys.length !== expected.length ||
    keys.some((key, index) => key !== [...expected].sort()[index])
  ) invalidResponse()
}

function requireStrings(value: Record<string, unknown>, fields: string[]) {
  if (fields.some((field) => typeof value[field] !== 'string' || value[field] === '')) {
    invalidResponse()
  }
}

function requirePositiveIntegers(
  value: Record<string, unknown>,
  fields: string[],
) {
  if (fields.some((field) => !Number.isInteger(value[field]) || Number(value[field]) < 1)) {
    invalidResponse()
  }
}

function requireTimestamp(value: unknown) {
  if (typeof value !== 'string' || !OFFSET_TIMESTAMP.test(value)) invalidResponse()
}

function positiveId(value: number) {
  if (!Number.isInteger(value) || value < 1) {
    throw new LecturerReviewApiError(422, 'A positive identifier is required.')
  }
  return value
}

function isRecord(value: unknown): value is Record<string, unknown> {
  return value !== null && typeof value === 'object' && !Array.isArray(value)
}

function isNonNegativeInteger(value: unknown) {
  return Number.isInteger(value) && Number(value) >= 0
}

function assertRequiredAndAllowedKeys(
  value: unknown,
  required: readonly string[],
  allowed: readonly string[],
): asserts value is Record<string, unknown> {
  if (!isRecord(value)) invalidResponse()
  const keys = Object.keys(value)
  if (
    required.some((key) => !keys.includes(key)) ||
    keys.some((key) => !allowed.includes(key))
  ) invalidResponse()
}

function isNullablePositiveInteger(value: unknown) {
  return value === null || (Number.isInteger(value) && Number(value) >= 1)
}

function invalidResponse(): never {
  throw new LecturerReviewApiError(
    502,
    'The lecturer review response is invalid.',
  )
}

function publicErrorForStatus(status: number) {
  if (status === 409) {
    return {
      code: 'REVIEW_REFRESH_REQUIRED',
      message:
        'The schedule changed. Reload the browser page or reopen the link before submitting feedback.',
    }
  }
  if (status === 422) {
    return {
      code: 'INVALID_FEEDBACK',
      message: 'Feedback must match the current review session.',
    }
  }
  if (status === 429) {
    return {
      code: 'REVIEW_TEMPORARILY_UNAVAILABLE',
      message: 'This review is temporarily unavailable. Try again later.',
    }
  }
  return {
    code: 'REVIEW_UNAVAILABLE',
    message: 'This review is unavailable.',
  }
}

function calendarFilename(contentDisposition: string | null): string {
  if (
    contentDisposition === null
    || contentDisposition.length > MAX_CALENDAR_DISPOSITION_LENGTH
    || !/^attachment\s*;/i.test(contentDisposition)
  ) invalidCalendarResponse()
  const matches = [...contentDisposition.matchAll(
    /(?:^|;)\s*filename\*=UTF-8''([^;]+)(?=;|$)/gi,
  )]
  if (matches.length !== 1) invalidCalendarResponse()
  let filename: string
  try {
    filename = decodeURIComponent(matches[0][1].trim())
  } catch {
    invalidCalendarResponse()
  }
  const stem = filename.slice(0, -4)
  if (
    filename.length < 5
    || !filename.endsWith('.ics')
    || filename !== filename.normalize('NFC')
    || Array.from(stem).length > 180
    || !/^[\p{L}\p{N}._-]+$/u.test(stem)
    || /^[._-]|[._-]$/u.test(stem)
    || /[\\/]/u.test(filename)
    || Array.from(filename).some((character) => {
      const code = character.codePointAt(0) ?? 0
      return code <= 31 || code === 127
    })
    || /^(?:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])$/i.test(stem)
  ) {
    invalidCalendarResponse()
  }
  return filename
}

function invalidCalendarResponse(): never {
  throw new LecturerReviewApiError(
    502,
    'The calendar response is invalid.',
    true,
    'CALENDAR_EXPORT_UNAVAILABLE',
  )
}
