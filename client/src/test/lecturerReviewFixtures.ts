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
      'This link is intended for Dr Ada Lecturer; it does not authenticate the person using it.',
    revision: lecturerReviewRevisionFixture(),
    accessExpiresAt: EXPIRES_AT,
    timeZone: TIME_ZONE,
    courses: [
      {
        sourceCourseId: 42,
        code: 'COURSE-42',
        title: 'Algorithms',
        sessions: [
          {
            sessionRef: 'teaching:101',
            sessionKind: 'teaching' as const,
            sourceSessionId: 101,
            sessionType: 'Lecture',
            date: '2026-10-05',
            startTime: '09:00',
            endTime: '11:25',
            timeZone: TIME_ZONE,
            roomName: 'Room A-101',
            cohortName: 'CS-26',
          },
        ],
      },
      {
        sourceCourseId: 43,
        code: 'COURSE-43',
        title: 'Data Structures',
        sessions: [
          {
            sessionRef: 'exam:202',
            sessionKind: 'exam' as const,
            sourceSessionId: 202,
            sessionType: 'Written exam',
            date: '2026-12-14',
            startTime: '13:00',
            endTime: '15:00',
            timeZone: TIME_ZONE,
            roomName: 'Auditorium B',
            cohortName: 'CS-26',
          },
        ],
      },
    ],
    submittedFeedback: publicLecturerFeedbackFixture(),
  }
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
            },
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
      'The schedule changed. Refresh the review before submitting feedback.',
  },
  invalidFeedback: {
    code: 'INVALID_FEEDBACK',
    message: 'Feedback must match the current review session.',
  },
} as const
