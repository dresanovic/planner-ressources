import { afterEach, describe, expect, it, vi } from 'vitest'

import { getDraftSchedule, updateDraftSession } from './draftSchedule'

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

describe('resource-aware Draft Sessions', () => {
  it('sends exactly one Lecturer and Room edit and retains coded session identity', async () => {
    const payload = {
      draftScheduleId: 4, revision: 8, courseId: 2, semesterId: 3, context: {},
      sessions: [{
        id: 9, lecturerId: 5, roomId: 6,
        lecturer: { id: 5, name: 'Ada', referenceCode: 'LEC-005' },
        room: { id: 6, name: 'Lab', referenceCode: 'ROOM-006' },
        validationAlerts: [{ code: 'LECTURER_UNAVAILABLE', message: 'Unavailable.', relatedSessions: [] }],
      }],
    }
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload })
    vi.stubGlobal('fetch', fetchMock)

    const result = await updateDraftSession(9, {
      date: '2026-09-07', startTime: '09:00', endTime: '10:00', lecturerId: 5, roomId: 6,
    })

    expect(fetchMock).toHaveBeenCalledWith('/api/draft-sessions/9', expect.objectContaining({
      method: 'PATCH',
      body: JSON.stringify({ date: '2026-09-07', startTime: '09:00', endTime: '10:00', lecturerId: 5, roomId: 6 }),
    }))
    expect(result.sessions[0].lecturer.referenceCode).toBe('LEC-005')
    expect(result.sessions[0].validationAlerts[0].code).toBe('LECTURER_UNAVAILABLE')
  })
})
