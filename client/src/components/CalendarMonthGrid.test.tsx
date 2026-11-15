import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { describe, it, expect, vi } from 'vitest'
import { crowdedTimeGridWorkspaceFixture, timeGridWorkspaceFixture } from '../test/calendarWorkspaceFixtures'
import { CalendarMonthGrid } from './CalendarMonthGrid'

describe('CalendarMonthGrid', () => {
  it('keeps hidden affected-entry cues and leaves empty days free of calendar placeholders', () => {
    const host = document.createElement('div'), root = createRoot(host)
    const workspace = timeGridWorkspaceFixture()
    const original = workspace.occurrences[0]
    const occurrences = Array.from({ length: 5 }, (_, i) => ({ ...original, occurrenceRef: `teaching:${i}`, findingRefs: i === 4 ? original.findingRefs : [] }))
    act(() => root.render(<CalendarMonthGrid anchor="2027-06-26" workspace={workspace} occurrences={occurrences} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} onDate={vi.fn()} />))
    const cell = host.querySelector('[data-month-date="2027-06-26"]')!
    expect(cell.textContent).toContain('1 Termine mit Lehrzeitfensterhinweisen')
    expect(host.querySelector('details')).toBeNull()
    const empty = host.querySelector('[data-month-date="2027-06-25"]')!
    expect(empty.textContent).toBe('25. Juni')
    expect(cell.querySelector('.month-cohort-label')?.textContent).toBe('CS-26')
    expect(cell.querySelector('.month-cohort-label')?.getAttribute('title')).toBe('CS-26')
    act(() => root.unmount())
  })
  it.each([0, 1, 5, 20] as const)('shows complete dates, first three entries and exact overflow for %i entries', count => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    const workspace = crowdedTimeGridWorkspaceFixture(count)
    const occurrences = workspace.occurrences
    const onSelect = vi.fn(), onDate = vi.fn()
    act(() => root.render(<CalendarMonthGrid anchor="2027-06-26" workspace={workspace} occurrences={occurrences} courses={workspace.courses} selectedRef={null} onSelect={onSelect} onDate={onDate} />))
    expect(host.querySelectorAll('[data-month-date]')).toHaveLength(35)
    expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(Math.min(3, count))
    expect(host.textContent).toContain('Mai')
    expect(host.textContent).toContain('Juni')
    const cell = host.querySelector('[data-month-date="2027-06-26"]')!
    if (count > 3) {
      const more = cell.querySelector<HTMLButtonElement>('[aria-expanded]')!
      expect(more.textContent).toContain(`+${count - 3}`)
      more.focus()
      act(() => more.click())
      expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(count)
      expect(document.activeElement).toBe(more)
      act(() => more.click())
      expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(3)
    }
    act(() => cell.querySelector<HTMLButtonElement>('.month-date-button')!.click())
    expect(onDate).toHaveBeenCalledWith('2027-06-26')
    if (count) {
      expect(cell.textContent).toContain('12:15–17:20')
      act(() => cell.querySelector<HTMLButtonElement>('[data-occurrence-ref]')!.click())
      expect(onSelect).toHaveBeenCalledWith('teaching:1')
    }
    act(() => root.unmount())
    host.remove()
  })
})
