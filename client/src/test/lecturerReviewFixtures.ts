export const LECTURER_REVIEW_SECRET_CANARY =
  'FS015LecturerReviewSecretCanary000000000000'

export const LECTURER_REVIEW_REPLACEMENT_SECRET_CANARY =
  'FS015ReplacementSecretCanary111111111111111'

export const LECTURER_REVIEW_COMMENT_CANARY =
  '<script>FS015 lecturer feedback stays plain text</script>'

const TIME_ZONE = 'Europe/Vienna'
const ISSUED_AT = '2026-09-28T08:00:00Z'
const EXPIRES_AT = '2026-10-01T08:00:00Z'
const SUBMITTED_AT = '2026-09-28T09:30:00Z'

export function lecturerReviewRevisionFixture() {
  return {
    id: 15,
    semesterId: 1,
    semesterName: 'Winter semester 2026',
    label: 'Working R2',
    state: 'ready_for_review' as const,
  }
}

export function lecturerReviewSessionContextFixture() {
  return {
    sessionRef: 'teaching:101',
    sessionKind: 'teaching' as const,
    sourceSessionId: 101,
    sessionType: 'Lecture',
    courseSourceId: 42,
    courseCode: 'COURSE-42',
    courseTitle: 'Algorithms',
    date: '2026-10-05',
    startTime: '09:00',
    endTime: '11:25',
    timeZone: TIME_ZONE,
    roomName: 'Room A-101',
    cohortName: 'CS-26',
    studyType: 'Full-time',
    teachingUnits: 3,
    examDurationMinutes: null,
  }
}

export function lecturerReviewLinkFixture() {
  return {
    id: 501,
    revisionId: 15,
    lecturerId: 7,
    intendedLecturerName: 'Dr Ada Lecturer',
    durationDays: 3 as const,
    issuedAt: ISSUED_AT,
    expiresAt: EXPIRES_AT,
    timeZone: TIME_ZONE,
    status: 'active' as const,
    endedAt: null,
    replaceAllowed: true,
  }
}

export function publicLecturerFeedbackFixture() {
  return [
    {
      id: 701,
      kind: 'revision_comment' as const,
      sessionRef: null,
      comment: 'Tuesday and Thursday are generally preferable.',
      submittedAt: SUBMITTED_AT,
      timeZone: TIME_ZONE,
    },
    {
      id: 702,
      kind: 'session_comment' as const,
      sessionRef: 'teaching:101',
      comment: 'Could this session start at 10:00?',
      submittedAt: '2026-09-28T09:35:00Z',
      timeZone: TIME_ZONE,
    },
    {
      id: 703,
      kind: 'impossible_session' as const,
      sessionRef: 'exam:202',
      comment: LECTURER_REVIEW_COMMENT_CANARY,
      submittedAt: '2026-09-28T09:40:00Z',
      timeZone: TIME_ZONE,
    },
  ]
}

export function publicLecturerReviewFixture() {
  return {
    intendedLecturer: 'Dr Ada Lecturer',
    identityDisclaimer:
      'Dieser Link ist für Dr Ada Lecturer bestimmt; die Identität der verwendenden Person wird nicht authentifiziert.',
    revision: lecturerReviewRevisionFixture(),
    accessExpiresAt: EXPIRES_AT,
    timeZone: TIME_ZONE,
    semesterStartDate: '2026-09-01',
    semesterEndDate: '2026-12-20',
    validationAvailability: 'complete' as const,
    validationFindings: [
      {
        findingRef: 'public-finding:room-capacity',
        category: 'room_capacity' as const,
        message: 'Betroffen: Data Structures, Termin am 14.12.2026 von 13:00 bis 15:00. Die Raumkapazität reicht möglicherweise nicht aus. Dieser Hinweis blockiert die Rückmeldung nicht.',
        affectedSessionRefs: ['exam:202'],
      },
    ],
    filterFacets: {
      courses: [
        { value: 'course:42', label: 'COURSE-42 — Algorithms' },
        { value: 'course:43', label: 'COURSE-43 — Data Structures' },
      ],
      cohorts: [{ value: 'CS-26', label: 'CS-26' }],
      rooms: [
        { value: 'room:101', label: 'Room A-101' },
        { value: 'room:202', label: 'Auditorium B' },
      ],
      studyTypes: [{ value: 'Full-time', label: 'Full-time' }],
      sessionTypes: [
        { value: 'exam', label: 'Prüfungstermin' },
        { value: 'teaching', label: 'Lehrtermin' },
      ],
      lifecycleContexts: [
        { value: 'ready_for_review', label: 'Bereit zur Prüfung' },
      ],
      validationCategories: [
        { value: 'none', label: 'Kein aktueller Hinweis' },
        { value: 'room_capacity', label: 'Raumkapazität' },
      ],
    },
    courses: [
      {
        sourceCourseId: 42,
        courseRef: 'course:42',
        code: 'COURSE-42',
        title: 'Algorithms',
        cohortName: 'CS-26',
        studyType: 'Full-time',
        sessions: [
          {
            sessionRef: 'teaching:101',
            sessionKind: 'teaching' as const,
            sourceSessionId: 101,
            courseRef: 'course:42',
            sessionType: 'Lecture',
            date: '2026-10-05',
            startTime: '09:00',
            endTime: '11:25',
            timeZone: TIME_ZONE,
            roomName: 'Room A-101',
            roomRef: 'room:101',
            cohortName: 'CS-26',
            teachingUnits: 3,
            examDurationMinutes: null,
            validationFindingRefs: [],
          },
        ],
      },
      {
        sourceCourseId: 43,
        courseRef: 'course:43',
        code: 'COURSE-43',
        title: 'Data Structures',
        cohortName: 'CS-26',
        studyType: 'Full-time',
        sessions: [
          {
            sessionRef: 'exam:202',
            sessionKind: 'exam' as const,
            sourceSessionId: 202,
            courseRef: 'course:43',
            sessionType: 'Written exam',
            date: '2026-12-14',
            startTime: '13:00',
            endTime: '15:00',
            timeZone: TIME_ZONE,
            roomName: 'Auditorium B',
            roomRef: 'room:202',
            cohortName: 'CS-26',
            teachingUnits: null,
            examDurationMinutes: 120,
            validationFindingRefs: ['public-finding:room-capacity'],
          },
        ],
      },
    ],
    submittedFeedback: publicLecturerFeedbackFixture(),
  }
}

export function mixedPublicLecturerReviewFixture() {
  return publicLecturerReviewFixture()
}

export function emptyPublicLecturerReviewFixture() {
  const value = publicLecturerReviewFixture()
  value.courses = []
  value.validationFindings = []
  value.submittedFeedback = []
  value.filterFacets = {
    courses: [],
    cohorts: [],
    rooms: [],
    studyTypes: [],
    sessionTypes: [],
    lifecycleContexts: value.filterFacets.lifecycleContexts,
    validationCategories: [],
  }
  return value
}

export function lecturerCalendarDownloadFixture() {
  return {
    blob: new Blob(
      [
        'BEGIN:VCALENDAR\r\n',
        'VERSION:2.0\r\n',
        'PRODID:-//Resource Planner//Lecturer Calendar Export 1.0//EN\r\n',
        'END:VCALENDAR\r\n',
      ],
      { type: 'text/calendar;charset=utf-8' },
    ),
    filename: 'Terminplan-Wintersemester-2026-Working-R2.ics',
  }
}

export const lecturerCalendarDownloadErrorFixtures = {
  terminal: {
    status: 404,
    code: 'REVIEW_UNAVAILABLE',
  },
  throttled: {
    status: 429,
    code: 'REVIEW_TEMPORARILY_UNAVAILABLE',
  },
  retryable: {
    status: 503,
    code: 'CALENDAR_EXPORT_UNAVAILABLE',
  },
  unsafeFilename: 'Ada/secret.ics',
  wrongMediaType: 'application/json',
} as const

export function longLabelPublicLecturerReviewFixture() {
  const value = publicLecturerReviewFixture()
  value.intendedLecturer =
    'Dr Ada Lecturer with a deliberately long fixed-context display name'
  value.identityDisclaimer =
    'Dieser Link ist für Dr Ada Lecturer with a deliberately long fixed-context display name bestimmt; die Identität der verwendenden Person wird nicht authentifiziert.'
  value.courses[0].title =
    'Algorithms and computational problem solving across extended programme titles'
  value.courses[0].sessions[0].roomName =
    'Building North, fourth floor, seminar room with a deliberately long name'
  return value
}

export function plannerLecturerReviewOverviewFixture() {
  return {
    revision: lecturerReviewRevisionFixture(),
    lecturers: [
      {
        lecturerId: 7,
        lecturerName: 'Dr Ada Lecturer',
        sessionCount: 2,
        courses: [
          { sourceCourseId: 42, code: 'COURSE-42', title: 'Algorithms' },
          {
            sourceCourseId: 43,
            code: 'COURSE-43',
            title: 'Data Structures',
          },
        ],
        initialIssueAllowed: false,
      },
      {
        lecturerId: 8,
        lecturerName: 'Prof Grace Lecturer',
        sessionCount: 1,
        courses: [
          {
            sourceCourseId: 44,
            code: 'COURSE-44',
            title: 'Operating Systems',
          },
        ],
        initialIssueAllowed: true,
      },
    ],
    links: [lecturerReviewLinkFixture()],
    feedbackAvailability: 'complete' as const,
    totalFeedbackCount: 3,
    impossibleFlagCount: 1,
    feedbackGroups: [
      {
        groupRef: 'revision',
        level: 'revision' as const,
        sessionContext: null,
        currentNavigation: null,
        impossibleFlagCount: 0,
        items: [
          {
            id: 701,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'revision_comment' as const,
            comment: 'Tuesday and Thursday are generally preferable.',
            sessionContext: null,
            sessionStatus: null,
            submittedAt: SUBMITTED_AT,
            timeZone: TIME_ZONE,
          },
        ],
      },
      {
        groupRef: 'teaching:101',
        level: 'session' as const,
        sessionContext: lecturerReviewSessionContextFixture(),
        currentNavigation: {
          revisionId: 15,
          occurrenceRef: 'teaching:101',
        },
        impossibleFlagCount: 0,
        items: [
          {
            id: 702,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'session_comment' as const,
            comment: 'Could this session start at 10:00?',
            sessionContext: lecturerReviewSessionContextFixture(),
            sessionStatus: 'current' as const,
            submittedAt: '2026-09-28T09:35:00Z',
            timeZone: TIME_ZONE,
          },
        ],
      },
      {
        groupRef: 'exam:202',
        level: 'session' as const,
        sessionContext: {
          sessionRef: 'exam:202',
          sessionKind: 'exam' as const,
          sourceSessionId: 202,
          sessionType: 'Written exam',
          courseSourceId: 43,
          courseCode: 'COURSE-43',
          courseTitle: 'Data Structures',
          date: '2026-12-14',
          startTime: '13:00',
          endTime: '15:00',
          timeZone: TIME_ZONE,
          roomName: 'Auditorium B',
          cohortName: 'CS-26',
          studyType: 'Full-time',
          teachingUnits: null,
          examDurationMinutes: 120,
        },
        currentNavigation: {
          revisionId: 15,
          occurrenceRef: 'exam:202',
        },
        impossibleFlagCount: 1,
        items: [
          {
            id: 703,
            intendedLecturerId: 7,
            intendedLecturerName: 'Dr Ada Lecturer',
            attribution:
              'Submitted through the review link intended for Dr Ada Lecturer; identity was not authenticated.',
            kind: 'impossible_session' as const,
            comment: LECTURER_REVIEW_COMMENT_CANARY,
            sessionContext: {
              sessionRef: 'exam:202',
              sessionKind: 'exam' as const,
              sourceSessionId: 202,
              sessionType: 'Written exam',
              courseSourceId: 43,
              courseCode: 'COURSE-43',
              courseTitle: 'Data Structures',
              date: '2026-12-14',
              startTime: '13:00',
              endTime: '15:00',
              timeZone: TIME_ZONE,
              roomName: 'Auditorium B',
              cohortName: 'CS-26',
              studyType: 'Full-time',
              teachingUnits: null,
              examDurationMinutes: 120,
            },
            sessionStatus: 'current' as const,
            submittedAt: '2026-09-28T09:40:00Z',
            timeZone: TIME_ZONE,
          },
        ],
      },
    ],
  }
}

export function issuedLecturerReviewLinkFixture(
  secret = LECTURER_REVIEW_SECRET_CANARY,
) {
  return {
    secret,
    issuedLink: lecturerReviewLinkFixture(),
    overview: plannerLecturerReviewOverviewFixture(),
  }
}

export function lecturerReviewFeedbackInputFixtures() {
  return {
    revisionComment: {
      clientSubmissionId: '00000000-0000-4000-8000-000000000701',
      kind: 'revision_comment' as const,
      comment: 'Tuesday and Thursday are generally preferable.',
    },
    sessionComment: {
      clientSubmissionId: '00000000-0000-4000-8000-000000000702',
      kind: 'session_comment' as const,
      sessionRef: 'teaching:101',
      comment: 'Could this session start at 10:00?',
    },
    impossibleSession: {
      clientSubmissionId: '00000000-0000-4000-8000-000000000703',
      kind: 'impossible_session' as const,
      sessionRef: 'exam:202',
      comment: LECTURER_REVIEW_COMMENT_CANARY,
    },
  }
}

export function lecturerReviewFeedbackResultFixture(
  outcome: 'created' | 'already_accepted' = 'created',
) {
  return {
    outcome,
    item: publicLecturerFeedbackFixture()[2],
  }
}

export const lecturerReviewPublicErrorFixtures = {
  unavailable: {
    code: 'REVIEW_UNAVAILABLE',
    message:
      'This review is unavailable. Contact the planner for a new link.',
  },
  throttled: {
    code: 'REVIEW_TEMPORARILY_UNAVAILABLE',
    message: 'This review is temporarily unavailable. Try again later.',
  },
  refreshRequired: {
    code: 'REVIEW_REFRESH_REQUIRED',
    message:
      'The schedule changed. Reload the browser page or reopen the link before submitting feedback.',
  },
  invalidFeedback: {
    code: 'INVALID_FEEDBACK',
    message: 'Feedback must match the current review session.',
  },
} as const
