import type { DraftSchedule, GenerationConstraints } from '../api/draftSchedule'

export const generationConstraintsFixture: GenerationConstraints = {
  courseId: 1,
  semesterId: 1,
  isCustom: false,
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
  courseId: 1,
  semesterId: 1,
  context: {
    course: { id: 1, name: 'Planning 101' },
    cohort: { id: 1, name: 'AI 1' },
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
      cohortId: 1,
      roomId: 1,
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
    },
    {
      id: 1,
      date: '2026-09-07',
      startTime: '08:00',
      endTime: '11:30',
      units: 4,
      courseId: 1,
      lecturerId: 1,
      cohortId: 1,
      roomId: 1,
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
    },
  ],
}

export const emptyDraftScheduleFixture: DraftSchedule = {
  ...draftScheduleFixture,
  draftScheduleId: 2,
  sessions: [],
}
