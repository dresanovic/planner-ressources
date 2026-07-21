import { afterEach, describe, expect, it, vi } from 'vitest'

import { generateMultiCourseDrafts, prepareMultiCourseGeneration } from './multiCourseDraftGeneration'
import { batchPreparationFixture, batchResultFixture } from '../test/draftScheduleFixtures'

afterEach(() => vi.unstubAllGlobals())

describe('multi-course generation API', () => {
  it('serializes preparation in selected order', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => batchPreparationFixture })
    vi.stubGlobal('fetch', fetchMock)
    await prepareMultiCourseGeneration(1, 11, 'initial', [2, 1])
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({ semesterId: 1, scheduleRevisionId: 11, operationKind: 'initial', courseIds: [2, 1] })
  })

  it('serializes immutable draft snapshots and confirmation', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, json: async () => batchResultFixture })
    vi.stubGlobal('fetch', fetchMock)
    await generateMultiCourseDrafts(batchPreparationFixture, true)
    expect(JSON.parse(fetchMock.mock.calls[0][1].body)).toEqual({
      semesterId: 1,
      scheduleRevisionId: 11,
      operationKind: 'initial',
      replacementConfirmed: true,
      courses: [
        { courseId: 1, expectedDraftScheduleId: 1, expectedDraftRevision: 1 },
        { courseId: 2, expectedDraftScheduleId: null, expectedDraftRevision: null },
      ],
    })
  })

  it('preserves paired per-course holiday evidence', async () => {
    const result = {
      ...batchResultFixture,
      outcomes: [{
        ...batchResultFixture.outcomes[0],
        status: 'failed' as const,
        errors: [{ code: 'INSTITUTION_HOLIDAY', message: 'Founders Day.', holidayDate: '2026-09-07', holidayName: 'Founders Day' }],
      }, batchResultFixture.outcomes[1]],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => result }))

    const received = await generateMultiCourseDrafts(batchPreparationFixture, true)

    expect(received.outcomes[0].errors[0]).toMatchObject({ holidayDate: '2026-09-07', holidayName: 'Founders Day' })
  })

  it('rejects malformed initial and retry sizes before a request', async () => {
    vi.stubGlobal('fetch', vi.fn())
    await expect(prepareMultiCourseGeneration(1, 11, 'initial', [1])).rejects.toEqual([
      expect.objectContaining({ code: 'INVALID_BATCH_SIZE' }),
    ])
    await expect(prepareMultiCourseGeneration(1, 11, 'retry', [])).rejects.toEqual([
      expect.objectContaining({ code: 'INVALID_BATCH_SIZE' }),
    ])
  })
})
