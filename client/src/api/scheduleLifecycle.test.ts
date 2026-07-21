import { afterEach, describe, expect, it, vi } from 'vitest'

import {
  createWorkingRevision,
  getScheduleLifecycle,
  getScheduleRevision,
  prepareSchedulePublication,
  transitionScheduleRevision,
} from './scheduleLifecycle'
import { lifecycleOverviewFixture, publicationFixture, snapshotFixture } from '../test/lifecycleFixtures'


afterEach(() => vi.unstubAllGlobals())


describe('schedule lifecycle API', () => {
  it('uses exact lifecycle paths and serializes state, version, confirmation, and tokens', async () => {
    const overview = lifecycleOverviewFixture()
    const responses = [overview, overview, { revision: overview.activeWorkingRevision, contentSource: 'active_working', snapshot: snapshotFixture() }, publicationFixture(), overview]
    const fetchMock = vi.fn().mockImplementation(async () => ({ ok: true, status: 200, json: async () => responses.shift() }))
    vi.stubGlobal('fetch', fetchMock)

    await getScheduleLifecycle(1)
    await createWorkingRevision(1, 'state-1')
    await getScheduleRevision(11)
    await prepareSchedulePublication(11, 1, 'state-1')
    await transitionScheduleRevision(11, { action: 'publish', expectedRevisionVersion: 1, expectedStateToken: 'state-1', confirmed: true, publicationToken: 'publication-1' })

    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      '/api/semesters/1/schedule-lifecycle',
      '/api/semesters/1/schedule-revisions',
      '/api/schedule-revisions/11',
      '/api/schedule-revisions/11/publication-preparation',
      '/api/schedule-revisions/11/transitions',
    ])
    expect(JSON.parse(fetchMock.mock.calls[1][1].body)).toEqual({ expectedStateToken: 'state-1' })
    expect(JSON.parse(fetchMock.mock.calls[4][1].body)).toEqual({ action: 'publish', expectedRevisionVersion: 1, expectedStateToken: 'state-1', confirmed: true, publicationToken: 'publication-1' })
  })

  it('accepts offset-bearing timestamps and rejects ambiguous lifecycle timestamps', async () => {
    const fetchMock = vi.fn()
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => lifecycleOverviewFixture('2026-07-20T12:00:00+02:00') })
      .mockResolvedValueOnce({ ok: true, status: 200, json: async () => lifecycleOverviewFixture('2026-07-20T12:00:00') })
    vi.stubGlobal('fetch', fetchMock)
    await expect(getScheduleLifecycle(1)).resolves.toMatchObject({ activeWorkingRevision: { createdAt: '2026-07-20T12:00:00+02:00' } })
    await expect(getScheduleLifecycle(1)).rejects.toMatchObject({ errors: [{ code: 'INVALID_LIFECYCLE_TIMESTAMP' }] })
  })

  it('retains structured conflict state for authoritative refresh', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ errors: [{ code: 'stale_lifecycle_state', message: 'Changed', field: null, meta: null }], currentOverview: lifecycleOverviewFixture() }) }))
    await expect(createWorkingRevision(1, 'old')).rejects.toMatchObject({ status: 409, currentOverview: { semesterId: 1 } })
  })
})

