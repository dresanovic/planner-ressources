import type { DraftSchedule, DraftScheduleMutationResult, GenerationConstraints, MutationFailure } from '../api/draftSchedule'
import type { RoomOption } from '../api/planningOptions'
import type { BatchGenerationResult, BatchPreparation } from '../api/multiCourseDraftGeneration'

export const generationConstraintsFixture: GenerationConstraints = {
  courseId: 1,
  semesterId: 1,
  isCustom: false,
  revision: null,
  planningPeriod: {
    startDate: '2026-09-07',
    endDate: '2026-12-20',
  },
  allowedTeachingWindows: [
    {
      weekday: 0,
      startTime: '08:00',
      endTime: '12:00',
      sourceTimeWindowId: 1,
    },
    {
      weekday: 2,
      startTime: '08:00',
      endTime: '12:00',
      sourceTimeWindowId: 2,
    },
  ],
}

export const draftScheduleFixture: DraftSchedule = {
  draftScheduleId: 1,
  revision: 1,
  courseId: 1,
  semesterId: 1,
  context: {
    course: { id: 1, name: 'Planning 101' },
    cohort: { id: 1, name: 'AI 1' },
    cohortSize: 30,
    lecturer: { id: 1, name: 'Ada Lovelace' },
    room: { id: 1, name: 'R1' },
    studyType: { id: 1, name: 'Full-time' },
  },
  sessions: [
    {
      id: 2,
      date: '2026-09-14',
      startTime: '08:00',
      endTime: '11:30',
      units: 4,
      courseId: 1,
      lecturerId: 1,
      lecturerName: 'Ada Lovelace',
      lecturerReferenceCode: 'LEC-001',
      cohortId: 1,
      roomId: 1,
      roomName: 'R1',
      roomReferenceCode: 'ROOM-001',
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
      validationAlerts: [],
      lecturer: { id: 1, name: 'Ada Lovelace', referenceCode: 'LEC-001' },
      room: { id: 1, name: 'R1', referenceCode: 'ROOM-001' },
    },
    {
      id: 1,
      date: '2026-09-07',
      startTime: '08:00',
      endTime: '11:30',
      units: 4,
      courseId: 1,
      lecturerId: 1,
      lecturerName: 'Ada Lovelace',
      lecturerReferenceCode: 'LEC-001',
      cohortId: 1,
      roomId: 1,
      roomName: 'R1',
      roomReferenceCode: 'ROOM-001',
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
      validationAlerts: [],
      lecturer: { id: 1, name: 'Ada Lovelace', referenceCode: 'LEC-001' },
      room: { id: 1, name: 'R1', referenceCode: 'ROOM-001' },
    },
  ],
}

export const emptyDraftScheduleFixture: DraftSchedule = {
  ...draftScheduleFixture,
  draftScheduleId: 2,
  sessions: [],
}

export const secondDraftScheduleFixture: DraftSchedule = {
  draftScheduleId: 3,
  revision: 1,
  courseId: 2,
  semesterId: 1,
  context: {
    course: { id: 2, name: 'Scheduling 201' },
    cohort: { id: 2, name: 'AI 2' },
    cohortSize: 30,
    lecturer: { id: 2, name: 'Grace Hopper' },
    room: { id: 2, name: 'R2' },
    studyType: { id: 1, name: 'Full-time' },
  },
  sessions: [
    {
      id: 3,
      date: '2026-09-21',
      startTime: '09:00',
      endTime: '12:30',
      units: 4,
      courseId: 2,
      lecturerId: 2,
      lecturerName: 'Grace Hopper',
      lecturerReferenceCode: 'LEC-002',
      cohortId: 2,
      roomId: 2,
      roomName: 'R2',
      roomReferenceCode: 'ROOM-002',
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
      validationAlerts: [],
      lecturer: { id: 2, name: 'Grace Hopper', referenceCode: 'LEC-002' },
      room: { id: 2, name: 'R2', referenceCode: 'ROOM-002' },
    },
  ],
}

export const otherSemesterDraftScheduleFixture: DraftSchedule = {
  ...draftScheduleFixture,
  draftScheduleId: 4,
  revision: 3,
  semesterId: 2,
  sessions: draftScheduleFixture.sessions.map((session, index) => ({
    ...session,
    id: 20 + index,
    date: index === 0 ? '2027-02-22' : '2027-02-15',
  })),
}

export const relatedSessionFixture = {
  sessionId: 3,
  draftScheduleId: 3,
  courseId: 2,
  courseName: 'Scheduling 201',
  date: '2026-09-07',
  startTime: '09:00',
  endTime: '12:30',
  cohortName: 'AI 2',
  lecturerName: 'Grace Hopper',
  roomName: 'R2',
}

export const alertDraftScheduleFixture: DraftSchedule = {
  ...draftScheduleFixture,
  sessions: [
    {
      ...draftScheduleFixture.sessions[1],
      validationAlerts: [
        {
          code: 'LECTURER_OVERLAP',
          message: 'Lecturer overlaps with 1 session.',
          relatedSessions: [relatedSessionFixture],
        },
      ],
    },
    {
      ...draftScheduleFixture.sessions[0],
      validationAlerts: [
        {
          code: 'ROOM_CAPACITY',
          message: 'Room capacity 20 is lower than Cohort size 30.',
          relatedSessions: [],
        },
        {
          code: 'STUDY_TYPE_WINDOW_VIOLATION',
          message: 'Session is outside the Study Type Time Window.',
          relatedSessions: [],
        },
      ],
    },
  ],
}

export const roomOptionsFixture: RoomOption[] = [
  { id: 1, name: 'R1', capacity: 40 },
  { id: 2, name: 'R2', capacity: 32 },
  { id: 3, name: 'Auditorium', capacity: 80 },
  { id: 4, name: 'Tiny', capacity: 20 },
]

export const selectedCourseProgressFixture = {
  totalUnits: 12,
  scheduledUnits: 8,
  remainingUnits: 4,
}

export const manualMutationFixture: DraftScheduleMutationResult = {
  courseId: 1,
  semesterId: 1,
  scheduledUnits: 10,
  remainingUnits: 2,
  draftSchedule: draftScheduleFixture,
}

export const nullableDraftMutationFixture: DraftScheduleMutationResult = {
  courseId: 1,
  semesterId: 1,
  scheduledUnits: 0,
  remainingUnits: 12,
  draftSchedule: null,
}

export const staleDraftFailureFixture: MutationFailure = {
  code: 'STALE_DRAFT',
  message: 'The Draft Schedule changed. Review the refreshed state and confirm again.',
  currentRevision: 3,
}

export const batchPreparationFixture: BatchPreparation = {
  semesterId: 1,
  operationKind: 'initial',
  courses: [
    { courseId: 1, courseName: 'Planning 101', available: true, draftScheduleId: 1, draftRevision: 1, replacementRequired: true },
    { courseId: 2, courseName: 'Scheduling 201', available: true, draftScheduleId: null, draftRevision: null, replacementRequired: false },
  ],
  replacementCourseIds: [1],
}

export const batchResultFixture: BatchGenerationResult = {
  semesterId: 1,
  operationKind: 'initial',
  summary: { total: 2, succeeded: 1, failed: 1 },
  outcomes: [
    { courseId: 1, courseName: 'Planning 101', status: 'succeeded', draftScheduleId: 1, draftRevision: 2, errors: [] },
    { courseId: 2, courseName: 'Scheduling 201', status: 'failed', draftScheduleId: null, draftRevision: null, errors: [{ code: 'INSUFFICIENT_ROOM_CAPACITY', message: 'Room is too small.' }] },
  ],
}
