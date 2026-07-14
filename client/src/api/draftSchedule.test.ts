import { afterEach, describe, expect, it, vi } from 'vitest'

import { getDraftSchedule } from './draftSchedule'

afterEach(() => vi.unstubAllGlobals())

describe('getDraftSchedule', () => {
  it('requires the semester context and parses the revision', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({ draftScheduleId: 4, revision: 7, courseId: 2, semesterId: 3, context: {}, sessions: [] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const result = await getDraftSchedule(2, 3)

    expect(fetchMock).toHaveBeenCalledWith('/api/courses/2/draft-schedule?semesterId=3', undefined)
    expect(result.revision).toBe(7)
  })
})
