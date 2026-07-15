import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createSemester,
  deleteAcademicRecord,
  listSemesters,
  updateCourse,
  getAcademicUsage,
  setAcademicLifecycle,
} from './academicCatalog'

afterEach(() => vi.unstubAllGlobals())

describe('academic catalog API', () => {
  it('parses paginated lifecycle and name-repair fields', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: true,
      json: async () => ({
        page: 1, pageSize: 50, total: 1,
        items: [{ id: 1, name: 'Fall', nameRepairRequired: true, startDate: '2026-09-01', endDate: '2026-12-20', isActive: true, revision: 3, usage: { recordId: 1, revision: 3, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] } }],
      }),
    }))
    const page = await listSemesters()
    expect(page.items[0].nameRepairRequired).toBe(true)
    expect(page.items[0].revision).toBe(3)
    expect(vi.mocked(fetch).mock.calls[0][0]).toBe('/api/academic/semesters?page=1&pageSize=50')
  })

  it('sends canonical create and revisioned update/delete requests', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 204, json: async () => ({ id: 1 }) })
    vi.stubGlobal('fetch', fetchMock)
    await createSemester({ name: 'Fall', startDate: '2026-09-01', endDate: '2026-12-20' })
    await updateCourse(4, { name: 'C', totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, semesterId: 1, cohortId: 2, studyTypeId: 3, lecturerId: 4, roomId: 5, expectedRevision: 6 })
    await deleteAcademicRecord('courses', 4, 7)
    expect(fetchMock.mock.calls[1][1]).toMatchObject({ method: 'PATCH' })
    expect(fetchMock.mock.calls[2][0]).toBe('/api/academic/courses/4?expectedRevision=7')
  })

  it('preserves structured validation and stale metadata', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({
      ok: false, status: 409,
      json: async () => ({ errors: [{ code: 'STALE_REVISION', message: 'Refresh.', field: null, meta: { currentRevision: 8 } }] }),
    }))
    await expect(createSemester({ name: 'Fall', startDate: '2026-09-01', endDate: '2026-12-20' })).rejects.toMatchObject({
      status: 409,
      errors: [{ code: 'STALE_REVISION', meta: { currentRevision: 8 } }],
    })
  })

  it('loads usage and sends revisioned lifecycle commands', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true, status: 200, json: async () => ({ recordId: 2, revision: 4, canDelete: false, dependentRecords: [{ type: 'course', count: 1 }], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }) })
    vi.stubGlobal('fetch', fetchMock)
    await getAcademicUsage('cohorts', 2)
    await setAcademicLifecycle('cohorts', 2, 'archive', 4)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/academic/cohorts/2/usage')
    expect(fetchMock.mock.calls[1]).toEqual(['/api/academic/cohorts/2/archive', expect.objectContaining({ method: 'POST', body: JSON.stringify({ expectedRevision: 4 }) })])
  })
})
