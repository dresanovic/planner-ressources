import type { CalendarMode, LoadedCalendarWorkspace, WorkspaceCourse, WorkspaceOccurrence } from '../api/calendarWorkspace'
import type { PublicLecturerReview } from '../api/lecturerReview'

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

export function adaptLecturerReviewToWorkspace(
  review: PublicLecturerReview,
): LoadedCalendarWorkspace {
  const courseRefBySession = new Map<string, string>()
  for (const course of review.courses) {
    for (const session of course.sessions) {
      courseRefBySession.set(session.sessionRef, course.courseRef)
    }
  }
  const findings = review.validationFindings.map((finding) => ({
    findingRef: finding.findingRef,
    category: finding.category,
    validationBasis: 'current' as const,
    affectedCourseRefs: [
      ...new Set(
        finding.affectedSessionRefs
          .map((ref) => courseRefBySession.get(ref))
          .filter((ref): ref is string => ref !== undefined),
      ),
    ],
    affectedOccurrenceRefs: [...finding.affectedSessionRefs],
    details: {
      kind: 'other' as const,
      issueCode: finding.message,
      occurrenceRefs: [...finding.affectedSessionRefs],
    },
  }))
  const courses = review.courses.map((course) => {
    const teachingUnits = course.sessions.reduce(
      (total, session) => total + (session.teachingUnits ?? 0),
      0,
    )
    const findingRefs = [
      ...new Set(
        course.sessions.flatMap((session) => session.validationFindingRefs),
      ),
    ]
    return {
      courseRef: course.courseRef,
      courseId: course.sourceCourseId,
      code: course.code,
      name: course.title,
      cohort: course.cohortName,
      lecturerRefs: [],
      studyType: course.studyType,
      planningEligible: false,
      totalTeachingUnits: teachingUnits,
      scheduledTeachingUnits: teachingUnits,
      remainingTeachingUnits: 0,
      remainingInstructionalMinutes: 0,
      occurrenceRefs: course.sessions.map((session) => session.sessionRef),
      findingRefs,
      outcomeRefs: [],
      needsReviewReasonRefs: findingRefs,
    }
  })
  const occurrences = review.courses.flatMap((course) =>
    course.sessions.map((session): WorkspaceOccurrence => {
      const common = {
        occurrenceRef: session.sessionRef,
        courseRef: course.courseRef,
        date: session.date,
        startTime: session.startTime,
        endTime: session.endTime,
        cohort: session.cohortName,
        lecturerRefs: [],
        roomRef: session.roomRef,
        findingRefs: [...session.validationFindingRefs],
      }
      if (session.sessionKind === 'teaching') {
        if (session.teachingUnits === null) {
          throw new Error('A teaching review session requires teaching units.')
        }
        return {
          ...common,
          kind: 'teaching',
          teachingUnits: session.teachingUnits,
        }
      }
      if (session.examDurationMinutes === null) {
        throw new Error('An exam review session requires a duration.')
      }
      return {
        ...common,
        kind: 'exam',
        examType: session.sessionType,
        durationMinutes: session.examDurationMinutes,
        assignedRoomName: session.roomName,
      }
    }),
  )
  const contributorRefs = findings.flatMap(
    (finding) => finding.affectedOccurrenceRefs,
  )
  const completeMetric = {
    availability: review.validationAvailability === 'complete'
      ? 'available' as const
      : review.validationAvailability,
    scope: 'complete_revision' as const,
    contributorRefs,
  }
  const designation = review.revision.state === 'published'
    ? 'current_published' as const
    : 'active_working' as const
  const selector = {
    revisionId: review.revision.id,
    revisionNumber: null,
    revisionLabel: review.revision.label,
    lifecycleState: review.revision.state as 'draft' | 'ready_for_review' | 'published',
    designation,
  }
  return {
    presentationSource: 'lecturer-review',
    semester: {
      semesterId: review.revision.semesterId,
      name: review.revision.semesterName,
      startDate: review.semesterStartDate,
      endDate: review.semesterEndDate,
    },
    workspaceState: 'loaded',
    selectedRevision: {
      ...selector,
      readOnly: true,
      contentSource: designation === 'active_working'
        ? 'active_working'
        : 'captured_published',
      validationBasis: 'current',
      snapshotSchemaVersion: null,
    },
    availableContexts: {
      activeWorking: designation === 'active_working' ? selector : null,
      currentPublished: designation === 'current_published' ? selector : null,
    },
    workspaceToken: `lecturer-review:${review.revision.id}`,
    sectionStatus: {
      courses: { availability: 'available' },
      occurrences: { availability: 'available' },
      holidays: { availability: 'available' },
      validationFindings: {
        availability: review.validationAvailability === 'complete'
          ? 'available'
          : review.validationAvailability,
      },
      planningOutcomes: { availability: 'unavailable' },
      summary: { availability: 'unavailable' },
    },
    courses,
    occurrences,
    holidays: [],
    validationFindings: findings,
    planningOutcomes: [],
    summary: {
      unscheduledWork: {
        availability: 'not_applicable',
        scope: 'complete_revision',
        contributorRefs: [],
        notApplicableReason: 'Die Planungsverantwortung ist in der Terminprüfung nicht verfügbar.',
      },
      conflicts: {
        ...completeMetric,
        contributorRefs: findings
          .filter((finding) => finding.category.endsWith('_conflict'))
          .map((finding) => finding.findingRef),
        distinctFindingCount: findings.filter((finding) =>
          finding.category.endsWith('_conflict'),
        ).length,
      },
      capacityIssues: {
        ...completeMetric,
        contributorRefs: findings
          .filter((finding) => finding.category === 'room_capacity')
          .flatMap((finding) => finding.affectedOccurrenceRefs),
        affectedOccurrenceCount: new Set(
          findings
            .filter((finding) => finding.category === 'room_capacity')
            .flatMap((finding) => finding.affectedOccurrenceRefs),
        ).size,
      },
      planningFailures: {
        availability: 'not_applicable',
        scope: 'complete_revision',
        contributorRefs: [],
        notApplicableReason: 'Planungsergebnisse sind nicht Bestandteil der Terminprüfung.',
      },
      needsReview: {
        ...completeMetric,
        contributorRefs: [
          ...new Set(findings.flatMap((finding) => finding.affectedCourseRefs)),
        ],
        distinctCourseCount: new Set(
          findings.flatMap((finding) => finding.affectedCourseRefs),
        ).size,
      },
    },
    filterFacets: {
      ...review.filterFacets,
      validationCategories: review.validationAvailability === 'complete'
        ? review.filterFacets.validationCategories
        : review.filterFacets.validationCategories.filter(
            (facet) => facet.value !== 'none',
          ),
      lecturers: [],
    },
  }
}

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
