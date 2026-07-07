import type { DraftSession, ReviewFilters } from '../api/draftSchedule'

export type WeeklySessionGroup = {
  weekStart: string
  days: Array<{
    date: string
    sessions: DraftSession[]
  }>
}

export function filterSessions(sessions: DraftSession[], filters: ReviewFilters): DraftSession[] {
  return sessions.filter((session) => {
    return (
      matchesFilter(session.courseId, filters.courseId) &&
      matchesFilter(session.cohortId, filters.cohortId) &&
      matchesFilter(session.lecturerId, filters.lecturerId) &&
      matchesFilter(session.roomId, filters.roomId) &&
      matchesFilter(session.studyTypeId, filters.studyTypeId)
    )
  })
}

export function groupSessionsByWeek(sessions: DraftSession[]): WeeklySessionGroup[] {
  const groups = new Map<string, Map<string, DraftSession[]>>()

  for (const session of sessions) {
    const weekStart = getWeekStart(session.date)
    const week = groups.get(weekStart) ?? new Map<string, DraftSession[]>()
    const day = week.get(session.date) ?? []

    day.push(session)
    week.set(session.date, day)
    groups.set(weekStart, week)
  }

  return [...groups.entries()]
    .sort(([left], [right]) => left.localeCompare(right))
    .map(([weekStart, days]) => ({
      weekStart,
      days: [...days.entries()]
        .sort(([left], [right]) => left.localeCompare(right))
        .map(([date, daySessions]) => ({
          date,
          sessions: [...daySessions].sort(compareSessions),
        })),
    }))
}

export function sortSessionsChronologically(sessions: DraftSession[]): DraftSession[] {
  return [...sessions].sort(compareSessions)
}

function matchesFilter(value: number, filterValue?: number): boolean {
  return filterValue === undefined || value === filterValue
}

function compareSessions(left: DraftSession, right: DraftSession): number {
  return `${left.date}T${left.startTime}`.localeCompare(`${right.date}T${right.startTime}`)
}

function getWeekStart(dateValue: string): string {
  const [year, month, dayOfMonth] = dateValue.split('-').map(Number)
  const date = new Date(year, month - 1, dayOfMonth)
  const day = date.getDay()
  const mondayOffset = day === 0 ? -6 : 1 - day
  date.setDate(date.getDate() + mondayOffset)
  return formatDate(date)
}

function formatDate(date: Date): string {
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  return `${year}-${month}-${day}`
}
