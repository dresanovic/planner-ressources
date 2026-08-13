import { afterEach, describe, expect, it, vi } from 'vitest'

import { acceptConflictAwareSchedules, generateConflictAwareSchedules, prepareConflictAwareGeneration } from './conflictAwareGeneration'
import { decisionRequiredGenerationFixture, directSavedGenerationFixture, optimizationPreparationFixture, optimizationResultFixture } from '../test/optimizationFixtures'

afterEach(() => vi.restoreAllMocks())

describe('conflict-aware generation API', () => {
  it('prepares 1-20 courses with future unavailable dates', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(optimizationPreparationFixture), { status: 200 }))
    const result = await prepareConflictAwareGeneration(1, 11, [1, 2], ['2026-10-26'])
    expect(result.sharedSnapshotToken).toBe('shared-snapshot')
    expect(result.courses[0].effectiveConstraints.studyType.name).toBe('Full-time')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ semesterId: 1, scheduleRevisionId: 11, courseIds: [1, 2], unavailableDates: ['2026-10-26'] })
  })

  it('echoes snapshot tokens without a pre-generation replacement decision', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }))
    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)
    expect(result.mode).toBe('direct_saved')
    if (result.mode !== 'direct_saved') throw new Error('Expected direct save')
    expect(result.summary).toEqual(expect.objectContaining({
      total: 2,
      complete: 1,
      improvedPartial: 1,
      unchanged: 0,
      failed: 0,
      stale: 0,
      scheduledUnits: 14,
      remainingUnits: 2,
      elapsedMilliseconds: 245,
      optimalForPreparedSnapshot: true,
    }))
    expect(result.outcomes[1].reasons[0]).toMatchObject({ sourceKind: 'active_exam', sourceId: 44 })
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload.sharedSnapshotToken).toBe('shared-snapshot')
    expect(payload).not.toHaveProperty('replacementConfirmed')
    expect(payload.courses[1].inputSnapshotToken).toBe('course-2')
  })

  it('returns the server-owned post-generation comparison and fingerprint', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(decisionRequiredGenerationFixture), { status: 200 }))

    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)

    expect(result.mode).toBe('decision_required')
    if (result.mode !== 'decision_required') throw new Error('Expected decision preview')
    expect(result.saved).toBe(false)
    expect(result.candidateFingerprint).toHaveLength(64)
    expect(result.comparison.generated.scheduledUnits).toBe(14)
    expect(result.comparison.courses[1].resolvedCurrentWarnings).toEqual([{ code: 'OUTSIDE_ALLOWED_WINDOW', count: 1 }])
  })

  it('accepts only the server-owned prepared evidence and candidate fingerprint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }),
    )

    const result = await acceptConflictAwareSchedules(decisionRequiredGenerationFixture)

    expect(result.mode).toBe('direct_saved')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/draft-schedules/optimization/accept')
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload).toEqual({
      ...decisionRequiredGenerationFixture.preparedEvidence,
      candidateFingerprint: decisionRequiredGenerationFixture.candidateFingerprint,
    })
    expect(payload).not.toHaveProperty('comparison')
    expect(payload).not.toHaveProperty('sessions')
  })

  it('accepts mixed prepared evidence when an unplanned course omits nullable draft identity fields', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }),
    )
    const preview = {
      ...decisionRequiredGenerationFixture,
      preparedEvidence: {
        ...decisionRequiredGenerationFixture.preparedEvidence,
        courses: [
          decisionRequiredGenerationFixture.preparedEvidence.courses[0],
          { courseId: 2, inputSnapshotToken: 'course-2' },
        ],
      },
    }

    await acceptConflictAwareSchedules(preview)

    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload.courses[1]).toEqual({
      courseId: 2,
      inputSnapshotToken: 'course-2',
    })
  })

  it('preserves actionable stale acceptance errors for the planner workflow', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      errors: [{ code: 'STALE_PLANNING_INPUT', message: 'Generate a new alternative.' }],
    }), { status: 409 }))

    await expect(acceptConflictAwareSchedules(decisionRequiredGenerationFixture)).rejects.toEqual([
      { code: 'STALE_PLANNING_INPUT', message: 'Generate a new alternative.' },
    ])
  })

  it('preserves paired holiday blocking context', async () => {
    const payload = {
      ...optimizationResultFixture,
      outcomes: [{
        ...optimizationResultFixture.outcomes[0],
        reasons: [{ code: 'INSTITUTION_HOLIDAY', message: 'Founders Day.', relatedCount: 1, holidayDate: '2026-09-07', holidayName: 'Founders Day' }],
      }],
    }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }))

    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)
    if (result.mode !== 'direct_saved') throw new Error('Expected direct save')
    expect(result.outcomes[0].reasons[0]).toMatchObject({ holidayDate: '2026-09-07', holidayName: 'Founders Day' })
  })

  it('parses validation and solver failures and normalizes network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ errors: [{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }] }), { status: 422 }))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }])
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }), { status: 503 }))
    await expect(generateConflictAwareSchedules(optimizationPreparationFixture)).rejects.toEqual([{ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }])
    vi.mocked(fetch).mockRejectedValueOnce(new Error('offline'))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }])
  })
})
