import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  clearCourseDraft,
  createManualDraftSession,
  deleteDraftSession,
  getDraftSchedule,
  updateDraftSession,
} from './draftSchedule'

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

describe('manual Draft Session mutation contracts', () => {
  it('parses a nullable mutation result', async () => {
    const payload = { courseId: 1, semesterId: 1, scheduledUnits: 0, remainingUnits: 12, draftSchedule: null }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => payload }))

    await expect(deleteDraftSession(9, 4, 2)).resolves.toEqual(payload)
  })

  it('sends the manual create body and maps structured validation errors', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 422,
      json: async () => ({ errors: [{ code: 'UNITS_EXCEED_REMAINING', message: 'Only 2 units remain.' }] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    const payload = { semesterId: 1, date: '2026-09-07', startTime: '08:00', endTime: '09:45', units: 4, roomId: 3 }
    await expect(createManualDraftSession(1, payload)).rejects.toEqual([
      { code: 'UNITS_EXCEED_REMAINING', message: 'Only 2 units remain.' },
    ])
    expect(fetchMock).toHaveBeenCalledWith('/api/courses/1/draft-schedule/sessions', expect.objectContaining({
      method: 'POST',
      body: JSON.stringify(payload),
    }))
  })

  it('maps stale deletion and includes exact confirmation query parameters', async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ errors: [{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 3 }] }),
    })
    vi.stubGlobal('fetch', fetchMock)

    await expect(clearCourseDraft(1, 2, 7, 4)).rejects.toEqual([
      { code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 3 },
    ])
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/courses/1/draft-schedule?semesterId=2&expectedDraftScheduleId=7&expectedDraftRevision=4',
      expect.objectContaining({ method: 'DELETE' }),
    )
  })

  it('maps network failures without reporting success', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('offline')))
    await expect(deleteDraftSession(9, 4, 2)).rejects.toEqual([
      expect.objectContaining({ code: 'NETWORK_ERROR' }),
    ])
  })
})
