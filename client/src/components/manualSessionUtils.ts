import type { CourseSemesterProgress, DraftSchedule } from '../api/draftSchedule'

export function calculateDefaultEndTime(
  startTime: string,
  units: number,
  unitMinutes = 45,
  breakMinutes = 10,
): string | null {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(startTime) || !Number.isInteger(units) || units <= 0) return null
  const [hours, minutes] = startTime.split(':').map(Number)
  const start = hours * 60 + minutes
  const duration = units * unitMinutes + (units - 1) * breakMinutes
  const end = start + duration
  if (end >= 24 * 60) return null
  return `${String(Math.floor(end / 60)).padStart(2, '0')}:${String(end % 60).padStart(2, '0')}`
}

export function isValidSessionTimeRange(startTime: string, endTime: string): boolean {
  if (!/^([01]\d|2[0-3]):[0-5]\d$/.test(startTime) || !/^([01]\d|2[0-3]):[0-5]\d$/.test(endTime)) return false
  return endTime > startTime
}

export function deriveCourseProgress(
  totalUnits: number,
  schedules: DraftSchedule[],
  courseId: number,
  semesterId: number,
): CourseSemesterProgress {
  const scheduledUnits = schedules
    .filter((schedule) => schedule.courseId === courseId && schedule.semesterId === semesterId)
    .flatMap((schedule) => schedule.sessions)
    .reduce((sum, session) => sum + session.units, 0)
  return { totalUnits, scheduledUnits, remainingUnits: Math.max(totalUnits - scheduledUnits, 0) }
}
