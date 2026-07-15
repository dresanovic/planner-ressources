import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createLecturer,
  createRoom,
  getResourceUsage,
  listLecturers,
  reactivateResource,
  removeResource,
  updateLecturer,
  createUnavailability,
  deleteUnavailability,
  listUnavailability,
  updateUnavailability,
  getCourseResourceConfiguration,
  updateCourseResourceEligibility,
} from './resourceCatalog'

afterEach(() => vi.unstubAllGlobals())

describe('resource catalog API', () => {
  it('defaults lists to active and sends name/code search parameters', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ page: 1, pageSize: 50, total: 0, items: [] }) })
    vi.stubGlobal('fetch', fetchMock)
    await listLecturers()
    await listLecturers({ status: 'inactive', query: 'Ada A-1', page: 2, pageSize: 20 })
    expect(fetchMock.mock.calls[0][0]).toBe('/api/resources/lecturers?status=active&page=1&pageSize=50')
    expect(fetchMock.mock.calls[1][0]).toBe('/api/resources/lecturers?status=inactive&query=Ada+A-1&page=2&pageSize=20')
  })

  it('sends typed create, revisioned update, usage, removal, and reactivation requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({}) })
    vi.stubGlobal('fetch', fetchMock)
    await createLecturer({ name: 'Ada', referenceCode: 'A-1' })
    await createRoom({ name: 'R1', referenceCode: 'R-1', capacity: 30 })
    await updateLecturer(4, { name: 'Ada L.', referenceCode: 'A-1', expectedRevision: 3 })
    await getResourceUsage('lecturers', 4)
    await removeResource('lecturers', 4, 3)
    await reactivateResource('lecturers', 4, 4)
    expect(fetchMock.mock.calls[2]).toEqual(['/api/resources/lecturers/4', expect.objectContaining({ method: 'PATCH', body: JSON.stringify({ name: 'Ada L.', referenceCode: 'A-1', expectedRevision: 3 }) })])
    expect(fetchMock.mock.calls[4][0]).toBe('/api/resources/lecturers/4?expectedRevision=3&confirmed=true')
    expect(fetchMock.mock.calls[5]).toEqual(['/api/resources/lecturers/4/reactivate', expect.objectContaining({ method: 'POST', body: JSON.stringify({ expectedRevision: 4 }) })])
  })

  it('preserves stale metadata and typed removal outcomes', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ errors: [{ code: 'STALE_REVISION', message: 'Review.', meta: { currentRevision: 7 } }] }) }))
    await expect(updateLecturer(1, { name: 'Ada', referenceCode: 'A', expectedRevision: 1 })).rejects.toMatchObject({ status: 409, errors: [expect.objectContaining({ meta: { currentRevision: 7 } })] })
  })

  it('sends discriminated recurring and dated availability requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => [] })
    vi.stubGlobal('fetch', fetchMock)
    await listUnavailability('lecturers', 2)
    await createUnavailability('lecturers', 2, { kind: 'recurring', weekdays: [0, 2], startTime: '09:00', endTime: '11:00' })
    await updateUnavailability('lecturers', 2, 4, { kind: 'dated', startDate: '2026-09-07', startTime: '09:00', endDate: '2026-09-07', endTime: '11:00', expectedRevision: 3 })
    await deleteUnavailability('lecturers', 2, 4, 4)
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'POST' })
    expect(fetchMock.mock.calls[2][1]).toMatchObject({ method: 'PATCH', body: expect.stringContaining('expectedRevision') })
    expect(fetchMock.mock.calls[3][0]).toContain('expectedRevision=4')
  })

  it('sends atomic Course eligibility sets and keeps fixed preference metadata', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ courseId: 3, courseRevision: 2, cohortSize: 30, eligibleLecturerIds: [1, 2], eligibleRoomIds: [4], lecturerCandidates: [], roomCandidates: [], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } }) })
    vi.stubGlobal('fetch', fetchMock)
    const current = await getCourseResourceConfiguration(3)
    await updateCourseResourceEligibility(3, { expectedRevision: current.courseRevision, lecturerIds: [1, 2], roomIds: [4] })
    expect(current.preferences).toEqual({ minimizeLecturerChanges: true, minimizeRoomChanges: true })
    expect(fetchMock.mock.calls[1]).toEqual(['/api/academic/courses/3/resource-eligibility', expect.objectContaining({ method: 'PUT', body: JSON.stringify({ expectedRevision: 2, lecturerIds: [1, 2], roomIds: [4] }) })])
  })
})
