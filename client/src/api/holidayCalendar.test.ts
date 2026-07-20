import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  HolidayCalendarApiError,
  createHoliday,
  deleteHoliday,
  listHolidays,
  updateHoliday,
} from './holidayCalendar'

afterEach(() => vi.unstubAllGlobals())

describe('holiday calendar API', () => {
  it('uses the collection and revisioned item contracts', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    await listHolidays()
    await createHoliday({ date: '2026-12-25', name: 'Winter Holiday' })
    await updateHoliday(7, { date: '2026-12-24', name: 'Winter Break', expectedRevision: 2 })
    await deleteHoliday(7, 3, true)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/holidays')
    expect(fetchMock.mock.calls[2][0]).toBe('/api/holidays/7')
    expect(fetchMock.mock.calls[3][0]).toBe('/api/holidays/7?expectedRevision=3&confirmed=true')
  })

  it('retains structured stale metadata', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false,
      status: 409,
      json: async () => ({ errors: [{ code: 'STALE_REVISION', message: 'Refresh.', meta: { currentRevision: 2 } }] }),
    }))
    await expect(createHoliday({ date: '2026-12-25', name: 'Holiday' })).rejects.toBeInstanceOf(HolidayCalendarApiError)
    await expect(createHoliday({ date: '2026-12-25', name: 'Holiday' })).rejects.toMatchObject({
      status: 409,
      errors: [{ code: 'STALE_REVISION', meta: { currentRevision: 2 } }],
    })
  })
})

