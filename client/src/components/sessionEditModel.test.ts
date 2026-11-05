import { expect, it } from 'vitest'
import { teachingDraftsEqual, teachingEndTime } from './sessionEditModel'

it('handles minute carry and rejects fractional units and midnight overflow', () => {
  expect(teachingEndTime('13:15', 2)).toBe('14:55')
  expect(teachingEndTime('13:15', 3)).toBe('15:50')
  expect(teachingEndTime('13:15', 1)).toBe('14:00')
  expect(teachingEndTime('23:30', 1)).toBe('')
  expect(teachingEndTime('13:15', 1.5)).toBe('')
  expect(teachingEndTime('', 2)).toBe('')
})

it('keeps unit-only edits dirty after a manual end-time override restores the old time', () => {
  const before = { date: '2027-02-20', startTime: '13:15', endTime: '14:55', units: 2, lecturerId: 1, roomId: 1 }
  expect(teachingDraftsEqual(before, { ...before, units: 3 })).toBe(false)
})
