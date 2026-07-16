import { describe, expect, it } from 'vitest'

import { calculateDefaultEndTime, deriveCourseProgress, isValidSessionTimeRange } from './manualSessionUtils'
import { draftScheduleFixture } from '../test/draftScheduleFixtures'

describe('manual session calculations', () => {
  it('calculates one or several units with established inter-unit breaks', () => {
    expect(calculateDefaultEndTime('08:00', 1)).toBe('08:45')
    expect(calculateDefaultEndTime('08:00', 2)).toBe('09:40')
    expect(calculateDefaultEndTime('08:00', 4)).toBe('11:30')
  })

  it('rejects invalid input and midnight overflow', () => {
    expect(calculateDefaultEndTime('', 2)).toBeNull()
    expect(calculateDefaultEndTime('23:30', 2)).toBeNull()
    expect(calculateDefaultEndTime('08:00', 0)).toBeNull()
    expect(calculateDefaultEndTime('08:00', 1.5)).toBeNull()
  })

  it('accepts both earlier and later overrides while units remain authoritative', () => {
    expect(isValidSessionTimeRange('08:00', '09:00')).toBe(true)
    expect(isValidSessionTimeRange('08:00', '11:00')).toBe(true)
    expect(isValidSessionTimeRange('08:00', '08:00')).toBe(false)
    expect(deriveCourseProgress(12, [{ ...draftScheduleFixture, sessions: [{ ...draftScheduleFixture.sessions[0], units: 4 }] }], 1, 1))
      .toEqual({ totalUnits: 12, scheduledUnits: 4, remainingUnits: 8 })
  })

  it('clamps an over-scheduled course to zero remaining', () => {
    expect(deriveCourseProgress(2, [draftScheduleFixture], 1, 1).remainingUnits).toBe(0)
  })
})
