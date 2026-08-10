import { describe, expect, it } from 'vitest'

import {
  formatCalendarDate,
  formatCalendarDateRange,
  formatViennaDateTime,
  institutionLocalToday,
  isIsoCalendarDate,
  parseEuropeanDate,
} from './datePresentation'

describe('datePresentation', () => {
  it('round-trips strict calendar dates without constructing an instant', () => {
    for (const [iso, display] of [
      ['2026-09-11', '11.09.2026'],
      ['2028-02-29', '29.02.2028'],
      ['2000-02-29', '29.02.2000'],
      ['1900-02-28', '28.02.1900'],
      ['0001-01-01', '01.01.0001'],
      ['9999-12-31', '31.12.9999'],
    ]) {
      expect(formatCalendarDate(iso)).toBe(display)
      expect(parseEuropeanDate(display)).toBe(iso)
    }
  })

  it('rejects impossible, incomplete, normalized, and non-zero-padded input', () => {
    for (const value of [
      '',
      '1.09.2026',
      '01.9.2026',
      '2026-09-11',
      '31.04.2026',
      '29.02.2027',
      '00.01.2026',
      '01.13.2026',
      '01.01.0000',
    ]) {
      expect(parseEuropeanDate(value)).toBeNull()
    }
    expect(isIsoCalendarDate('2026-02-29')).toBe(false)
    expect(isIsoCalendarDate('2028-02-29')).toBe(true)
    expect(() => formatCalendarDate('2026-02-29')).toThrow(RangeError)
  })

  it('formats complete and open date ranges without inventing endpoints', () => {
    expect(formatCalendarDateRange('2026-09-11', '2026-10-02')).toBe(
      '11.09.2026–02.10.2026',
    )
    expect(formatCalendarDateRange('2026-09-11', null)).toBe('ab 11.09.2026')
    expect(formatCalendarDateRange(null, '2026-10-02')).toBe('bis 02.10.2026')
    expect(formatCalendarDateRange(null, null)).toBe('Zeitraum nicht verfügbar')
  })

  it('formats instants explicitly in Vienna across DST boundaries', () => {
    expect(formatViennaDateTime('2026-03-29T00:30:00Z')).toBe(
      '29.03.2026, 01:30',
    )
    expect(formatViennaDateTime('2026-03-29T01:30:00Z')).toBe(
      '29.03.2026, 03:30',
    )
    expect(formatViennaDateTime('2026-10-25T01:30:00Z')).toBe(
      '25.10.2026, 02:30',
    )
  })

  it('derives today from the institution timezone instead of UTC slicing', () => {
    expect(institutionLocalToday(new Date('2026-12-31T23:30:00Z'))).toBe(
      '2027-01-01',
    )
    expect(institutionLocalToday(new Date('2026-01-01T00:30:00Z'))).toBe(
      '2026-01-01',
    )
  })
})
