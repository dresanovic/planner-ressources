export type ExamFixture = {
  id: number
  revision: number
  courseId: number
  semesterId: number
  configurationIdentifier: string
  lifecycleStatus: 'active' | 'past'
  validityIssues: Array<{ code: string; message: string }>
  inputSnapshotToken: string
}

export const examConfigurationFixture = {
  id: 1,
  revision: 1,
  identifier: 'Final exam',
  durationMinutes: 120,
  recommendedStartOverride: null,
  recommendedEndOverride: null,
  requiredCapacity: 40,
  examType: 'Written',
  responsibleLecturerId: 1,
  configurationConsumed: false,
  recommendedStartDate: '2026-10-09',
  recommendedEndDate: '2026-10-16',
  recommendationWasOverridden: false,
} as const

export const activeExamFixture: ExamFixture = {
  id: 1,
  revision: 1,
  courseId: 1,
  semesterId: 1,
  configurationIdentifier: 'Final exam',
  lifecycleStatus: 'active',
  validityIssues: [],
  inputSnapshotToken: 'exam-active-token',
}

export const pastExamFixture: ExamFixture = {
  ...activeExamFixture,
  id: 2,
  lifecycleStatus: 'past',
  inputSnapshotToken: 'exam-past-token',
}

export const validityIssueFixture = {
  code: 'INSTITUTION_HOLIDAY',
  message: 'The exam is on Public holiday.',
  relatedDate: '2026-10-12',
  relatedResource: null,
  relatedSessionId: null,
  holidayName: 'Public holiday',
} as const

export const mixedExamOutcomesFixture = [
  { courseId: 1, courseName: 'Course 1', status: 'scheduled', saved: true, reasons: [] },
  { courseId: 2, courseName: 'Course 2', status: 'failed', saved: false, reasons: [validityIssueFixture] },
  { courseId: 3, courseName: 'Course 3', status: 'stale', saved: false, reasons: [] },
  { courseId: 4, courseName: 'Course 4', status: 'skipped_active', saved: false, reasons: [] },
  { courseId: 5, courseName: 'Course 5', status: 'skipped_disabled', saved: false, reasons: [] },
] as const

export const staleExamStateFixture = {
  code: 'STALE_INPUT_SNAPSHOT',
  message: 'Exam planning inputs changed. Refresh and try again.',
  currentState: null,
} as const
