import type { DraftSchedule, GenerationConstraints } from '../api/draftSchedule'
import type { RoomOption } from '../api/planningOptions'

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

export const secondDraftScheduleFixture: DraftSchedule = {
  draftScheduleId: 3,
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
      cohortId: 2,
      roomId: 2,
      studyTypeId: 1,
      timeWindowId: 1,
      constraintWindowIndex: 0,
    },
  ],
}

export const roomOptionsFixture: RoomOption[] = [
  { id: 1, name: 'R1', capacity: 40 },
  { id: 2, name: 'R2', capacity: 32 },
  { id: 3, name: 'Auditorium', capacity: 80 },
  { id: 4, name: 'Tiny', capacity: 20 },
]
