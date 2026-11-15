import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { describe, it, expect, vi } from 'vitest'
import { multiCalendarTimeGridFixture, timeGridWorkspaceFixture } from '../test/calendarWorkspaceFixtures'
import { CalendarTimeGrid } from './CalendarTimeGrid'

describe('CalendarTimeGrid', () => {
  it('keeps A and B permission separate and retains all overlap lanes', () => {
    const workspace = multiCalendarTimeGridFixture()
    workspace.occurrences.push({ ...workspace.occurrences[0], occurrenceRef: 'teaching:3' }, { ...workspace.occurrences[0], occurrenceRef: 'teaching:4' })
    const host = document.createElement('div'), root = createRoot(host)
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-26']} workspace={workspace} occurrences={workspace.occurrences} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} />))
    expect(host.querySelectorAll('.time-grid-column')).toHaveLength(2)
    expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(4)
    expect(host.querySelector('[data-occurrence-ref="teaching:1"]')?.getAttribute('aria-label')).toContain('16:00–17:20')
    expect(host.querySelector('[data-occurrence-ref="teaching:2"]')?.getAttribute('aria-label')).not.toContain('Außerhalb:')
    expect(host.querySelectorAll('[data-occurrence-ref="teaching:1"] .time-grid-outside-segment')).toHaveLength(1)
    act(() => root.unmount())
  })
  it('shows only session-bearing cohort columns per date and keeps other dates empty', () => {
    const workspace = multiCalendarTimeGridFixture()
    const host = document.createElement('div'), root = createRoot(host)
    const render = () => act(() => root.render(<CalendarTimeGrid dates={['2027-06-25', '2027-06-26', '2027-06-27']} workspace={workspace} occurrences={workspace.occurrences} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} />))
    render()
    expect(host.querySelectorAll('.time-grid-column')).toHaveLength(4)
    expect(host.querySelector('.time-grid-source-overview')).toBeNull()
    expect(host.querySelector('details')).toBeNull()
    workspace.occurrences[1].date = '2027-06-27'
    render()
    expect(host.querySelectorAll('.time-grid-column')).toHaveLength(3)
    expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(2)
    expect(host.querySelector('.time-grid-column')?.textContent).not.toContain('Calendar')
    act(() => root.unmount())
  })
  it('uses 08:00 fallback, earliest content, and distinct exam/unknown states', () => {
    const workspace = timeGridWorkspaceFixture()
    const host = document.createElement('div'), root = createRoot(host)
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-25']} workspace={workspace} occurrences={[]} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} />))
    expect(host.querySelector('.time-grid-scroll')?.scrollTop).toBe(576)
    workspace.occurrences[0].startTime = '00:15'
    workspace.occurrences[0].endTime = '01:00'
    workspace.teachingWindowContexts = []
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-26']} workspace={workspace} occurrences={workspace.occurrences} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} />))
    expect(host.querySelector('.time-grid-scroll')?.scrollTop).toBe(18)
    expect(host.querySelector('.window-unknown')).not.toBeNull()
    expect(host.querySelector('.time-grid-outside-segment')).toBeNull()
    expect(host.textContent).toContain('Lehrzeitfenster unbekannt')
    act(() => root.unmount())
  })
  it('retains date labels when no calendar is identifiable without inventing permission', () => {
    const host = document.createElement('div'), root = createRoot(host)
    const workspace = timeGridWorkspaceFixture()
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-26', '2027-06-27']} workspace={workspace} occurrences={[]} courses={[]} selectedRef={null} onSelect={vi.fn()} />))
    expect(host.querySelectorAll('.time-grid-column')).toHaveLength(2)
    expect(host.querySelector('.window-known')).toBeNull()
    expect(host.textContent).not.toContain('Wählen Sie einen Kohortenkalender')
    expect(host.querySelector('details')).toBeNull()
    act(() => root.unmount())
  })
  it('has chronological native controls, decorative paint, and named keyboard scroll regions', () => {
    const host = document.createElement('div'), root = createRoot(host)
    const workspace = timeGridWorkspaceFixture()
    const original = workspace.occurrences[0]
    const occurrences = [original, { ...original, occurrenceRef: 'teaching:2', startTime: '09:00', endTime: '10:30' }]
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-26']} workspace={workspace} occurrences={occurrences} courses={workspace.courses} selectedRef={null} onSelect={vi.fn()} />))
    expect([...host.querySelectorAll('[data-occurrence-ref]')].map(e => e.getAttribute('data-occurrence-ref'))).toEqual(['teaching:2', 'teaching:1'])
    expect(host.querySelector('[role="grid"]')).toBeNull()
    expect(host.querySelector('.time-grid-paint')?.getAttribute('aria-hidden')).toBe('true')
    expect(host.querySelector('.time-grid-scroll')?.getAttribute('tabindex')).toBe('0')
    const label = host.querySelector('[data-occurrence-ref="teaching:1"]')?.getAttribute('aria-label')
    expect(label).toContain('26.06.2027')
    expect(label).toContain('Calendar A')
    expect(label).toContain('08:00–16:00')
    expect(label).toContain('Aktuelle Arbeitsrevision')
    act(() => root.unmount())
  })
  it('renders proportional full-day blocks with non-hover facts and original selection', () => {
    const host = document.createElement('div')
    const root = createRoot(host)
    const workspace = timeGridWorkspaceFixture()
    const onSelect = vi.fn()
    act(() => root.render(<CalendarTimeGrid dates={['2027-06-26']} workspace={workspace} occurrences={workspace.occurrences} courses={workspace.courses} selectedRef={null} onSelect={onSelect} />))
    const block = host.querySelector<HTMLButtonElement>('[data-occurrence-ref]')!
    expect(block.style.top).toBe('882px')
    expect(block.style.height).toBe('366px')
    expect(block.querySelector<HTMLElement>('.time-grid-outside-segment')?.style.height).toBe('96px')
    expect(host.querySelector<HTMLElement>('.time-grid-canvas')?.style.height).toBe('1728px')
    expect(host.textContent).toContain('16:00–17:20')
    expect(host.textContent).toContain('1 Std. 20 Min.')
    expect(host.textContent).toContain('08:00–16:00')
    expect(host.textContent).toContain('24:00')
    act(() => block.click())
    expect(onSelect).toHaveBeenCalledWith('teaching:1')
    act(() => root.unmount())
  })
})
