import { afterEach, describe, expect, it, vi } from 'vitest'

import { getPlanningOptions } from './planningOptions'

afterEach(() => vi.unstubAllGlobals())

describe('planning options resource extensions', () => {
  it('retains coded eligible sets, readiness, and fixed preference metadata', async () => {
    const payload = {
      courses: [{ id: 1, name: 'Course', cohortSize: 24, availability: { available: false, reasons: ['NO_USABLE_ELIGIBLE_ROOM'] } }],
      semesters: [], timeWindows: [],
      lecturers: [{ id: 2, name: 'Ada', referenceCode: 'LEC-002', isActive: true, revision: 1 }],
      rooms: [{ id: 3, name: 'Lab', referenceCode: 'ROOM-003', capacity: 30, isActive: true, revision: 1 }],
      courseResources: [{
        courseId: 1,
        eligibleLecturers: [{ id: 2, name: 'Ada', referenceCode: 'LEC-002', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        eligibleRooms: [{ id: 3, name: 'Lab', referenceCode: 'ROOM-003', kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: false, reasons: ['INSUFFICIENT_CAPACITY'] }],
        preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
      }],
    }
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true, json: async () => payload }))

    const result = await getPlanningOptions(4)

    expect(result.courses[0].availability?.reasons).toContain('NO_USABLE_ELIGIBLE_ROOM')
    expect(result.courses[0].cohortSize).toBe(24)
    expect(result.courseResources[0].eligibleRooms[0].referenceCode).toBe('ROOM-003')
    expect(result.courseResources[0].preferences).toEqual({ minimizeLecturerChanges: true, minimizeRoomChanges: true })
  })
})
