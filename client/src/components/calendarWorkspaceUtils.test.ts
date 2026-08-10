import { describe, expect, it } from 'vitest'

import { loadedCalendarWorkspaceFixture } from '../test/calendarWorkspaceFixtures'
import { publicLecturerReviewFixture } from '../test/lecturerReviewFixtures'
import type { LoadedCalendarWorkspace } from '../api/calendarWorkspace'
import {
  currentPeriodDate,
  adaptLecturerReviewToWorkspace,
  movePeriod,
  projectWorkspace,
  visibleRange,
} from './calendarWorkspaceUtils'


describe('calendarWorkspaceUtils', () => {
  it('adapts the strict public DTO once into a restricted shared workspace', () => {
    const review = publicLecturerReviewFixture()

    const workspace = adaptLecturerReviewToWorkspace(review)

    expect(workspace.occurrences.map((item) => item.occurrenceRef)).toEqual([
      'teaching:101',
      'exam:202',
    ])
    expect(workspace.filterFacets.lecturers).toEqual([])
    expect(workspace.filterFacets.courses).toEqual(review.filterFacets.courses)
    expect(workspace.validationFindings[0]).toMatchObject({
      findingRef: 'public-finding:room-capacity',
      affectedOccurrenceRefs: ['exam:202'],
      details: {
        kind: 'other',
        issueCode:
          'Betroffen: Data Structures, Termin am 14.12.2026 von 13:00 bis 15:00. Die Raumkapazität reicht möglicherweise nicht aus. Dieser Hinweis blockiert die Rückmeldung nicht.',
      },
    })
    expect(workspace.selectedRevision).toMatchObject({
      revisionNumber: null,
      revisionLabel: review.revision.label,
    })
    expect(workspace.presentationSource).toBe('lecturer-review')
    const teaching = workspace.occurrences.find(
      (item) => item.kind === 'teaching',
    )!
    const exam = workspace.occurrences.find((item) => item.kind === 'exam')!
    expect(teaching).not.toHaveProperty('source')
    expect(exam).not.toHaveProperty('requiredCapacity')
    expect(exam).not.toHaveProperty('currentRoomCapacity')
    expect(exam).not.toHaveProperty('validityContext')
    expect(exam).not.toHaveProperty('recommendationContext')
    expect(JSON.stringify(workspace)).not.toContain('plannerNotes')
  })

  it('removes the no-issue facet when public validation is incomplete', () => {
    const review = {
      ...publicLecturerReviewFixture(),
      validationAvailability: 'partial' as const,
    }

    const workspace = adaptLecturerReviewToWorkspace(review)

    expect(workspace.filterFacets.validationCategories).not.toContainEqual({
      value: 'none',
      label: 'Kein aktueller Hinweis',
    })
  })

  it('uses UTC-safe ISO ranges and semester-boundary current dates', () => {
    expect(visibleRange('week', '2026-10-07')).toEqual({
      start: '2026-10-05',
      end: '2026-10-11',
    })
    expect(visibleRange('day', '2026-10-07')).toEqual({
      start: '2026-10-07',
      end: '2026-10-07',
    })
    expect(visibleRange('month', '2026-10-31')).toEqual({
      start: '2026-10-01',
      end: '2026-10-31',
    })
    expect(visibleRange('list', '2026-10-07')).toBeNull()
    expect(currentPeriodDate('2026-01-01', '2026-09-01', '2026-12-20')).toEqual({
      date: '2026-09-01',
      substituted: true,
    })
    expect(currentPeriodDate('2027-01-01', '2026-09-01', '2026-12-20')).toEqual({
      date: '2026-12-20',
      substituted: true,
    })
    expect(currentPeriodDate('2026-10-07', '2026-09-01', '2026-12-20')).toEqual({
      date: '2026-10-07',
      substituted: false,
    })
    expect(movePeriod('day', '2026-10-05', -1)).toBe('2026-10-04')
    expect(movePeriod('week', '2026-10-05', 1)).toBe('2026-10-12')
    expect(movePeriod('month', '2026-01-31', 1)).toBe('2026-02-01')
    expect(movePeriod('month', '2026-03-31', -1)).toBe('2026-02-01')
    expect(movePeriod('list', '2026-10-05', 1)).toBe('2026-10-05')
  })

  it('intersects filters and does not assign unscheduled work to a room', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    expect(projectWorkspace(workspace, { sessionType: 'exam' }).occurrences).toHaveLength(1)
    const room = projectWorkspace(workspace, { room: 'room:999' })
    expect(room.occurrences).toEqual([])
    expect(room.courses).toEqual([])
    const course = projectWorkspace(workspace, { course: 'course:1', cohort: 'CS-26' })
    expect(course.courses.map((item) => item.courseRef)).toEqual(['course:1'])
    expect(workspace.occurrences).toHaveLength(2)
  })

  it('matches scheduled lecturers by assignment even when current eligibility changed', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses[0].lecturerRefs = []

    const result = projectWorkspace(workspace, { lecturer: 'lecturer:1' })

    expect(result.occurrences.map((item) => item.occurrenceRef)).toEqual([
      'teaching:1',
      'exam:1',
    ])
    expect(result.courses.map((item) => item.courseRef)).toEqual(['course:1'])
  })

  it('applies lifecycle, no-issue, failure, and stale-outcome filters without mutation', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses.push(
      {
        ...workspace.courses[0],
        courseRef: 'course:2',
        courseId: 2,
        code: 'C-002',
        name: 'Stale unscheduled',
        occurrenceRefs: [],
        findingRefs: [],
        outcomeRefs: ['outcome:2'],
        needsReviewReasonRefs: ['outcome:2'],
      },
      {
        ...workspace.courses[0],
        courseRef: 'course:3',
        courseId: 3,
        code: 'C-003',
        name: 'Clean unscheduled',
        occurrenceRefs: [],
        findingRefs: [],
        outcomeRefs: ['outcome:3'],
        needsReviewReasonRefs: ['remaining:course:3'],
      },
    )
    workspace.planningOutcomes = [
      {
        outcomeRef: 'outcome:1',
        revisionId: 11,
        courseRef: 'course:1',
        operationKind: 'single_course_generation',
        classification: 'failed',
        sourceStatus: 'no_feasible_slot',
        reasons: [],
        completedAt: '2026-10-01T10:00:00Z',
      },
      {
        outcomeRef: 'outcome:2',
        revisionId: 11,
        courseRef: 'course:2',
        operationKind: 'semester_optimization',
        classification: 'stale',
        sourceStatus: 'stale',
        reasons: [],
        completedAt: '2026-10-01T11:00:00Z',
      },
      {
        outcomeRef: 'outcome:3',
        revisionId: 11,
        courseRef: 'course:3',
        operationKind: 'single_course_generation',
        classification: 'successful',
        sourceStatus: 'complete',
        reasons: [],
        completedAt: '2026-10-01T12:00:00Z',
      },
    ]

    expect(projectWorkspace(workspace, { lifecycle: 'current_published' })).toEqual({
      courses: [],
      occurrences: [],
    })
    expect(projectWorkspace(workspace, { validation: 'none' })).toMatchObject({
      courses: [{ courseRef: 'course:3' }],
      occurrences: [],
    })
    expect(projectWorkspace(workspace, { validation: 'planning_failure' })).toMatchObject({
      courses: [{ courseRef: 'course:1' }],
      occurrences: [{ occurrenceRef: 'teaching:1' }, { occurrenceRef: 'exam:1' }],
    })
    expect(projectWorkspace(workspace, { validation: 'stale_outcome' })).toMatchObject({
      courses: [{ courseRef: 'course:2' }],
      occurrences: [],
    })
    expect(projectWorkspace(workspace, {
      validation: 'none',
      course: 'course:1',
    })).toEqual({ courses: [], occurrences: [] })
    expect(workspace.occurrences).toHaveLength(2)
  })

  it('covers every planning/resource dimension and retains an unscheduled matching course', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses.push({
      ...workspace.courses[0],
      courseRef: 'course:2',
      courseId: 2,
      code: 'C-002',
      name: 'Databases',
      cohort: 'DS-26',
      lecturerRefs: ['lecturer:2'],
      studyType: 'Part-time',
      occurrenceRefs: [],
      findingRefs: [],
      outcomeRefs: [],
      needsReviewReasonRefs: ['remaining:course:2'],
    })

    expect(projectWorkspace(workspace, { course: 'course:2' }).courses.map((item) => item.courseRef)).toEqual(['course:2'])
    expect(projectWorkspace(workspace, { cohort: 'DS-26' }).courses.map((item) => item.courseRef)).toEqual(['course:2'])
    expect(projectWorkspace(workspace, { lecturer: 'lecturer:2' }).courses.map((item) => item.courseRef)).toEqual(['course:2'])
    expect(projectWorkspace(workspace, { studyType: 'Part-time' }).courses.map((item) => item.courseRef)).toEqual(['course:2'])
    expect(projectWorkspace(workspace, { room: 'room:1' }).courses.map((item) => item.courseRef)).toEqual(['course:1'])
    expect(projectWorkspace(workspace, { sessionType: 'exam' }).courses.map((item) => item.courseRef)).toEqual(['course:1'])
    expect(projectWorkspace(workspace, { sessionType: 'teaching' }).courses.map((item) => item.courseRef)).toEqual(['course:1', 'course:2'])
    expect(projectWorkspace(workspace, { course: 'course:2', room: 'room:1' })).toEqual({
      courses: [],
      occurrences: [],
    })
  })
})
