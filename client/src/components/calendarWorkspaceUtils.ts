import type { CalendarMode, LoadedCalendarWorkspace, WorkspaceCourse, WorkspaceOccurrence } from '../api/calendarWorkspace'

export type WorkspaceFilters = {
  course?: string
  cohort?: string
  lecturer?: string
  room?: string
  studyType?: string
  sessionType?: 'teaching' | 'exam'
  lifecycle?: string
  validation?: string
}

const DAY_MS = 86_400_000

export function parseIsoDate(value: string): Date {
  const [year, month, day] = value.split('-').map(Number)
  return new Date(Date.UTC(year, month - 1, day, 12))
}

export function isoDate(value: Date): string {
  return value.toISOString().slice(0, 10)
}

export function addDays(value: string, days: number): string {
  return isoDate(new Date(parseIsoDate(value).getTime() + days * DAY_MS))
}

export function currentPeriodDate(today: string, semesterStart: string, semesterEnd: string): { date: string; substituted: boolean } {
  if (today < semesterStart) return { date: semesterStart, substituted: true }
  if (today > semesterEnd) return { date: semesterEnd, substituted: true }
  return { date: today, substituted: false }
}

export function visibleRange(mode: CalendarMode, anchor: string): { start: string; end: string } | null {
  if (mode === 'list') return null
  if (mode === 'day') return { start: anchor, end: anchor }
  const date = parseIsoDate(anchor)
  if (mode === 'week') {
    const mondayOffset = (date.getUTCDay() + 6) % 7
    const start = addDays(anchor, -mondayOffset)
    return { start, end: addDays(start, 6) }
  }
  const year = date.getUTCFullYear()
  const month = date.getUTCMonth()
  return {
    start: isoDate(new Date(Date.UTC(year, month, 1, 12))),
    end: isoDate(new Date(Date.UTC(year, month + 1, 0, 12))),
  }
}

export function movePeriod(mode: CalendarMode, anchor: string, direction: -1 | 1): string {
  if (mode === 'day') return addDays(anchor, direction)
  if (mode === 'week') return addDays(anchor, direction * 7)
  if (mode === 'month') {
    const date = parseIsoDate(anchor)
    return isoDate(new Date(Date.UTC(date.getUTCFullYear(), date.getUTCMonth() + direction, 1, 12)))
  }
  return anchor
}

export function projectWorkspace(workspace: LoadedCalendarWorkspace, filters: WorkspaceFilters) {
  if (
    filters.lifecycle != null
    && filters.lifecycle !== workspace.selectedRevision.designation
    && filters.lifecycle !== workspace.selectedRevision.lifecycleState
  ) {
    return { courses: [], occurrences: [] }
  }
  const findingsByRef = new Map(workspace.validationFindings.map((item) => [item.findingRef, item]))
  const outcomeCourseRefs = new Set(
    workspace.planningOutcomes
      .filter((outcome) => (
        (filters.validation === 'planning_failure' && outcome.classification === 'failed')
        || (filters.validation === 'stale_outcome' && outcome.classification === 'stale')
      ))
      .map((outcome) => outcome.courseRef),
  )
  const outcomeIssueCourseRefs = new Set(
    workspace.planningOutcomes
      .filter((outcome) => (
        outcome.classification === 'failed'
        || outcome.classification === 'stale'
      ))
      .map((outcome) => outcome.courseRef),
  )
  const courses = workspace.courses.filter((course) => matchesCourseContext(course, filters))
  const courseRefs = new Set(courses.map((course) => course.courseRef))
  const occurrences = workspace.occurrences.filter((occurrence) => (
    courseRefs.has(occurrence.courseRef)
    && (filters.lecturer == null || occurrence.lecturerRefs.includes(filters.lecturer))
    && (filters.room == null || occurrence.roomRef === filters.room)
    && (filters.sessionType == null || occurrence.kind === filters.sessionType)
    && (
      filters.validation == null
      || (
        filters.validation === 'none'
        && occurrence.findingRefs.length === 0
        && !outcomeIssueCourseRefs.has(occurrence.courseRef)
      )
      || (
        (filters.validation === 'planning_failure' || filters.validation === 'stale_outcome')
        && outcomeCourseRefs.has(occurrence.courseRef)
      )
      || occurrence.findingRefs.some((ref) => findingsByRef.get(ref)?.category === filters.validation)
    )
  ))
  const occurrenceCourseRefs = new Set(occurrences.map((item) => item.courseRef))
  const keepUnscheduled = filters.room == null && filters.sessionType !== 'exam' && (
    filters.validation == null
    || filters.validation === 'none'
    || outcomeCourseRefs.size > 0
  )
  const visibleCourses = courses.filter((course) => (
    occurrenceCourseRefs.has(course.courseRef)
    || (
      keepUnscheduled
      && course.remainingTeachingUnits > 0
      && (
        filters.lecturer == null
        || course.lecturerRefs.includes(filters.lecturer)
      )
      && (
        filters.validation !== 'planning_failure'
        && filters.validation !== 'stale_outcome'
        || outcomeCourseRefs.has(course.courseRef)
      )
      && (
        filters.validation !== 'none'
        || (
          course.findingRefs.length === 0
          && !outcomeIssueCourseRefs.has(course.courseRef)
        )
      )
    )
  ))
  return { courses: visibleCourses, occurrences }
}

function matchesCourseContext(course: WorkspaceCourse, filters: WorkspaceFilters): boolean {
  return (
    (filters.course == null || course.courseRef === filters.course)
    && (filters.cohort == null || course.cohort === filters.cohort)
    && (filters.studyType == null || course.studyType === filters.studyType)
  )
}

export function occurrencesInRange(occurrences: WorkspaceOccurrence[], range: { start: string; end: string } | null): WorkspaceOccurrence[] {
  if (range == null) return occurrences
  return occurrences.filter((item) => item.date >= range.start && item.date <= range.end)
}
