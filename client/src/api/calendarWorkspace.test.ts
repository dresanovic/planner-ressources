import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  CalendarWorkspaceApiError,
  getCalendarWorkspace,
  type FacetValue,
  type LoadedCalendarWorkspace,
  type ValidationFinding,
} from './calendarWorkspace'
import {
  loadedCalendarWorkspaceFixture,
  noRevisionWorkspaceFixture,
  partialCalendarWorkspaceFixture,
} from '../test/calendarWorkspaceFixtures'


describe('calendar workspace API', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('parses loaded and no-revision variants', async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(new Response(JSON.stringify(loadedCalendarWorkspaceFixture()), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(noRevisionWorkspaceFixture()), { status: 200 }))
      .mockResolvedValueOnce(new Response(JSON.stringify(partialCalendarWorkspaceFixture()), { status: 200 }))
    vi.stubGlobal('fetch', fetchMock)

    expect((await getCalendarWorkspace(1, 11)).workspaceState).toBe('loaded')
    expect((await getCalendarWorkspace(1)).workspaceState).toBe('no_revision')
    const partial = await getCalendarWorkspace(1, 11)
    expect(partial.workspaceState === 'loaded' && partial.summary.conflicts.availability).toBe('unavailable')
    expect(fetchMock).toHaveBeenNthCalledWith(1, '/api/semesters/1/calendar-workspace?revisionId=11')
  })

  it('rejects mixed or conditionally invalid response shapes', async () => {
    const mixed = {
      ...noRevisionWorkspaceFixture(),
      courses: loadedCalendarWorkspaceFixture().courses,
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify(mixed), { status: 200 })))

    await expect(getCalendarWorkspace(1)).rejects.toBeInstanceOf(CalendarWorkspaceApiError)
  })

  it('rejects malformed identity, collection, facet, and reference fields', async () => {
    const invalidToken = { ...loadedCalendarWorkspaceFixture(), workspaceToken: '' }
    const invalidRevision = loadedCalendarWorkspaceFixture()
    invalidRevision.selectedRevision = {
      ...invalidRevision.selectedRevision,
      designation: 'current_published',
      readOnly: false,
    } as unknown as typeof invalidRevision.selectedRevision
    const invalidExam = loadedCalendarWorkspaceFixture()
    invalidExam.occurrences = invalidExam.occurrences.map((occurrence) => (
      occurrence.kind === 'exam'
        ? { ...occurrence, currentRoomCapacity: '40' }
        : occurrence
    )) as typeof invalidExam.occurrences
    const invalidFacets = {
      ...loadedCalendarWorkspaceFixture(),
      filterFacets: {
        ...loadedCalendarWorkspaceFixture().filterFacets,
        rooms: [{ value: 1, label: 'Room 1' }],
      },
    }
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(invalidToken), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(invalidRevision), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(invalidExam), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(invalidFacets), { status: 200 })),
    )

    await expect(getCalendarWorkspace(1)).rejects.toThrow('token')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('revision')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('exam')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('facets')
  })

  it('enforces typed finding details and forbids values on unavailable metrics', async () => {
    const mismatchedFinding = loadedCalendarWorkspaceFixture()
    mismatchedFinding.validationFindings = [{
      findingRef: 'finding:1',
      category: 'holiday',
      validationBasis: 'current',
      affectedCourseRefs: ['course:1'],
      affectedOccurrenceRefs: ['teaching:1'],
      details: {
        kind: 'capacity',
        occurrenceRef: 'teaching:1',
        requiredCapacity: 30,
        roomRef: 'room:1',
        roomName: 'R1',
        currentCapacity: 20,
      },
    // The fixture is intentionally malformed to exercise runtime validation.
    }] as typeof mismatchedFinding.validationFindings
    const unavailableWithValue = loadedCalendarWorkspaceFixture()
    unavailableWithValue.summary.conflicts = {
      availability: 'unavailable',
      scope: 'complete_revision',
      contributorRefs: [],
      unavailableReason: 'Current validation could not be loaded.',
      distinctFindingCount: 0,
    } as unknown as typeof unavailableWithValue.summary.conflicts
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(mismatchedFinding), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(unavailableWithValue), { status: 200 })),
    )

    await expect(getCalendarWorkspace(1)).rejects.toThrow('detail kind')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('unavailable values')
  })

  it('rejects unknown metric contributors, holiday links, and no-revision facets', async () => {
    const unknownContributor = loadedCalendarWorkspaceFixture()
    unknownContributor.summary.unscheduledWork.contributorRefs = ['course:999']
    const unknownHoliday = {
      ...loadedCalendarWorkspaceFixture(),
      validationFindings: [{
        findingRef: 'finding:holiday:1',
        category: 'holiday',
        validationBasis: 'current',
        affectedCourseRefs: ['course:1'],
        affectedOccurrenceRefs: ['teaching:1'],
        details: {
          kind: 'holiday',
          holidayRef: 'holiday:999',
          holidayDate: '2026-10-26',
          holidayName: 'Unknown holiday',
          occurrenceRefs: ['teaching:1'],
        },
      }] as ValidationFinding[],
    }
    const noRevisionWithFacet = {
      ...noRevisionWorkspaceFixture(),
      filterFacets: {
        ...noRevisionWorkspaceFixture().filterFacets,
        courses: [{ value: 'course:1', label: 'Algorithms' }] as FacetValue[],
      },
    }
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(unknownContributor), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(unknownHoliday), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(noRevisionWithFacet), { status: 200 })),
    )

    await expect(getCalendarWorkspace(1)).rejects.toThrow('unknown contributor')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('unknown holiday')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('revision-owned facets')
  })

  it('rejects incomplete sections, mismatched contexts, shallow exam detail, and inconsistent metrics', async () => {
    const missingSection = loadedCalendarWorkspaceFixture()
    delete (missingSection.sectionStatus as Partial<typeof missingSection.sectionStatus>).summary
    const mismatchedContext = loadedCalendarWorkspaceFixture()
    mismatchedContext.availableContexts.activeWorking = {
      ...mismatchedContext.availableContexts.activeWorking!,
      revisionNumber: 99,
    }
    const shallowExam = loadedCalendarWorkspaceFixture()
    shallowExam.occurrences = shallowExam.occurrences.map((occurrence) => (
      occurrence.kind === 'exam'
        ? { ...occurrence, validityContext: {} }
        : occurrence
    )) as typeof shallowExam.occurrences
    const malformedFinding = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    malformedFinding.validationFindings = [{
      findingRef: 'finding:capacity:teaching:1',
      category: 'room_capacity',
      validationBasis: 'current',
      affectedCourseRefs: ['course:1'],
      affectedOccurrenceRefs: ['teaching:1'],
      details: {
        kind: 'capacity',
        occurrenceRef: 'teaching:1',
        requiredCapacity: 30,
        roomRef: 'room:1',
        roomName: '',
        currentCapacity: 20,
      },
    }] as ValidationFinding[]
    const inconsistentMetric = loadedCalendarWorkspaceFixture()
    inconsistentMetric.summary.conflicts = {
      ...inconsistentMetric.summary.conflicts,
      distinctFindingCount: 2,
      countByType: { lecturer: 0, room: 0, cohort: 0 },
    }
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockResolvedValueOnce(new Response(JSON.stringify(missingSection), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(mismatchedContext), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(shallowExam), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(malformedFinding), { status: 200 }))
        .mockResolvedValueOnce(new Response(JSON.stringify(inconsistentMetric), { status: 200 })),
    )

    await expect(getCalendarWorkspace(1)).rejects.toThrow('section status')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('available context')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('validity')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('capacity')
    await expect(getCalendarWorkspace(1)).rejects.toThrow('conflicts')
  })

  it('preserves structured problem detail', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: 'Historical revision is not a workspace context.' }), { status: 422 })))

    await expect(getCalendarWorkspace(1, 7)).rejects.toMatchObject({
      status: 422,
      message: 'Historical revision is not a workspace context.',
      retryable: false,
    })
  })

  it('classifies transport and changed-context failures as retryable', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn()
        .mockRejectedValueOnce(new TypeError('offline'))
        .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Context changed.' }), { status: 409 })),
    )

    await expect(getCalendarWorkspace(1)).rejects.toMatchObject({
      status: 0,
      retryable: true,
    })
    await expect(getCalendarWorkspace(1)).rejects.toMatchObject({
      status: 409,
      retryable: true,
    })
  })
})
