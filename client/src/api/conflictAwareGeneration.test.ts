import { afterEach, describe, expect, it, vi } from 'vitest'

import { generateConflictAwareSchedules, prepareConflictAwareGeneration } from './conflictAwareGeneration'
import { optimizationPreparationFixture, optimizationResultFixture } from '../test/optimizationFixtures'

afterEach(() => vi.restoreAllMocks())

describe('conflict-aware generation API', () => {
  it('prepares 1-20 courses with future unavailable dates', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(optimizationPreparationFixture), { status: 200 }))
    const result = await prepareConflictAwareGeneration(1, 11, [1, 2], ['2026-10-26'])
    expect(result.sharedSnapshotToken).toBe('shared-snapshot')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ semesterId: 1, scheduleRevisionId: 11, courseIds: [1, 2], unavailableDates: ['2026-10-26'] })
  })

  it('echoes snapshot tokens and confirmed replacement scope', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(optimizationResultFixture), { status: 200 }))
    const result = await generateConflictAwareSchedules(optimizationPreparationFixture, true)
    expect(result.summary.complete).toBe(1)
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload.sharedSnapshotToken).toBe('shared-snapshot')
    expect(payload.replacementConfirmed).toBe(true)
    expect(payload.courses[1].inputSnapshotToken).toBe('course-2')
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

    const result = await generateConflictAwareSchedules(optimizationPreparationFixture, true)

    expect(result.outcomes[0].reasons[0]).toMatchObject({ holidayDate: '2026-09-07', holidayName: 'Founders Day' })
  })

  it('parses validation and solver failures and normalizes network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ errors: [{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }] }), { status: 422 }))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }])
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }), { status: 503 }))
    await expect(generateConflictAwareSchedules(optimizationPreparationFixture, true)).rejects.toEqual([{ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }])
    vi.mocked(fetch).mockRejectedValueOnce(new Error('offline'))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }])
  })
})
