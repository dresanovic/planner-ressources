import { describe, expect, it } from 'vitest'
import { enumerateDates, layoutIntervals, outsideIntervals, minuteOffset, cohortAbbreviation, calendarGroups, monthDates, monthEntries, occurrenceFacts } from './calendarTimeGridLayout'
import { timeGridWorkspaceFixture } from '../test/calendarWorkspaceFixtures'

describe('hourly presentation geometry', () => {
  it('retains the single-source finding when adjacent paint covers the whole interval', () => {
    const w = timeGridWorkspaceFixture()
    const context = w.teachingWindowContexts[0]
    context.windows = [
      { ...context.windows[0], endTime: '13:00' },
      { ...context.windows[0], windowRef: 'window:2', startTime: '13:00', endTime: '18:00' },
    ]
    context.days.find(d => d.date === '2027-06-26')!.applicableWindowRefs = ['window:1', 'window:2']
    const facts = occurrenceFacts(w, w.occurrences[0])
    expect(facts).toContain('einzelnes Quellfenster')
    expect(facts).not.toContain('0 Std. 0 Min.')
  })
  it('enumerates complete Monday-based month weeks across years and leap dates', () => {
    expect(monthDates('2027-06-26')).toHaveLength(35)
    expect(monthDates('2027-06-26')[0]).toBe('2027-05-31')
    expect(monthDates('2027-06-26').at(-1)).toBe('2027-07-04')
    expect(monthDates('2028-02-10')).toContain('2028-02-29')
    expect(monthDates('2027-01-01')[0]).toBe('2026-12-28')
  })
  it('counts affected occurrences once, ignores unrelated findings and sorts entries', () => {
    const w = timeGridWorkspaceFixture()
    const occurrence = w.occurrences[0]
    const result = monthEntries([occurrence, { ...occurrence, occurrenceRef: 'teaching:2', startTime: '08:00', findingRefs: [] }],
      [w.validationFindings[0], { ...w.validationFindings[0], findingRef: 'another' }])
    expect(result.entries.map(o => o.occurrenceRef)).toEqual(['teaching:2', 'teaching:1'])
    expect(result.affectedCount).toBe(1)
  })
  it('groups by stable identity and effective profile; never guesses unknown identities', () => {
    const w = timeGridWorkspaceFixture()
    const course = w.courses[0], context = w.teachingWindowContexts[0]
    const second = { ...course, courseRef: 'course:2', courseId: 2 }
    expect(calendarGroups([course, second], [context, { ...context, courseRef: 'course:2' }])).toHaveLength(1)
    expect(calendarGroups([course, { ...second, cohort: 'Other cohort' }], [context, { ...context, courseRef: 'course:2' }])).toHaveLength(2)
    expect(calendarGroups([course, { ...second, cohortCalendarRef: 'calendar:2' }], [context, { ...context, calendarRef: 'calendar:2', courseRef: 'course:2' }])).toHaveLength(2)
    expect(calendarGroups([course, second], [context, { ...context, courseRef: 'course:2', planningEndDate: '2027-06-20' }])).toHaveLength(2)
    expect(calendarGroups([{ ...course, cohortCalendarRef: null }, { ...second, cohortCalendarRef: null }], [])).toHaveLength(2)
  })
  it('abbreviates cohort names while preserving existing codes and semester identity', () => {
    expect(cohortAbbreviation('CS-26')).toBe('CS-26')
    expect(cohortAbbreviation('Business Analytics & AI - 2.Semester')).toBe('BA & AI - 2.Sem.')
    expect(cohortAbbreviation('MA IT & Wirtschaftsinformatik - 2.Semester')).toBe('MA IT & W - 2.Sem.')
  })
  it('enumerates all empty dates including weekends', () => {
    expect(enumerateDates('2027-06-21', '2027-06-27')).toHaveLength(7)
  })
  it('preserves exact minutes and break-inclusive duration at 72px/hour', () => {
    const [block] = layoutIntervals([{ occurrenceRef: 'a', startTime: '12:15', endTime: '17:20' }])
    expect(block.top).toBe(882)
    expect(block.height).toBe(366)
    expect(minuteOffset('09:00:30')).toBe(540.5)
  })
  it('uses stable lowest-free lanes, endpoint reuse and connected group width', () => {
    const blocks = layoutIntervals([
      { occurrenceRef: 'c', startTime: '09:00', endTime: '10:00' },
      { occurrenceRef: 'b', startTime: '09:00', endTime: '10:00' },
      { occurrenceRef: 'a', startTime: '09:00', endTime: '10:00' },
      { occurrenceRef: 'd', startTime: '10:00', endTime: '11:00' },
    ])
    expect(blocks.map(b => [b.occurrenceRef, b.lane, b.laneCount])).toEqual([
      ['a', 0, 3], ['b', 1, 3], ['c', 2, 3], ['d', 0, 1],
    ])
    const connected = layoutIntervals([
      { occurrenceRef: 'a', startTime: '08:00', endTime: '10:00' },
      { occurrenceRef: 'b', startTime: '09:00', endTime: '11:00' },
      { occurrenceRef: 'c', startTime: '10:00', endTime: '12:00' },
    ])
    expect(connected.map(b => [b.lane, b.laneCount])).toEqual([[0, 2], [1, 2], [0, 2]])
  })
  it('explains only known outside coverage without inferring unknown permission', () => {
    expect(outsideIntervals('12:15', '17:20', [{ startTime: '08:00', endTime: '16:00' }])).toEqual([{ start: 960, end: 1040, minutes: 80 }])
    expect(outsideIntervals('12:15', '17:20', null)).toEqual([])
    expect(outsideIntervals('08:00', '16:00', [{ startTime: '08:00', endTime: '16:00' }])).toEqual([])
    expect(outsideIntervals('09:00', '13:00', [{ startTime: '08:00', endTime: '10:00' }, { startTime: '12:00', endTime: '16:00' }])).toEqual([{ start: 600, end: 720, minutes: 120 }])
  })
})
