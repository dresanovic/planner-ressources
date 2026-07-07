import type { DraftSchedule } from '../api/draftSchedule'

export const draftScheduleFixture: DraftSchedule = {
  draftScheduleId: 1,
  courseId: 1,
  semesterId: 1,
  selectedTimeWindowId: 1,
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
    },
  ],
}

export const emptyDraftScheduleFixture: DraftSchedule = {
  ...draftScheduleFixture,
  draftScheduleId: 2,
  sessions: [],
}
