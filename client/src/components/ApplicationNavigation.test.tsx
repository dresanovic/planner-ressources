import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ACADEMIC_DATA_CATEGORIES,
  ApplicationNavigation,
  type AcademicDataCategory,
  type PlannerView,
  type ScheduleDestination,
} from './ApplicationNavigation'

function installMatchMedia(matches = false) {
  const listeners = new Set<() => void>()
  const media = {
    matches,
    media: '(max-width: 820px)',
    addEventListener: (_name: string, listener: () => void) => listeners.add(listener),
    removeEventListener: (_name: string, listener: () => void) => listeners.delete(listener),
    dispatch(value: boolean) { media.matches = value; listeners.forEach((listener) => listener()) },
  }
  vi.stubGlobal('matchMedia', () => media)
  return media
}

function Harness() {
  const [view, setView] = useState<PlannerView>('schedule')
  const [category, setCategory] = useState<AcademicDataCategory>('semesters')
  const [destination, setDestination] = useState<ScheduleDestination>('calendar')
  const [scheduleExpanded, setScheduleExpanded] = useState(true)
  const [expanded, setExpanded] = useState(false)
  const [open, setOpen] = useState(false)
  const [pinned, setPinned] = useState(true)
  return <ApplicationNavigation
    view={view}
    selectedCategory={category}
    selectedScheduleDestination={destination}
    scheduleExpanded={scheduleExpanded}
    academicExpanded={expanded}
    navigationOpen={open}
    navigationPinned={pinned}
    onToggleAcademic={() => setExpanded((value) => view === 'academic' ? true : !value)}
    onToggleSchedule={() => setScheduleExpanded((value) => view === 'schedule' ? true : !value)}
    onSelectScheduleDestination={(next) => { setDestination(next); setScheduleExpanded(true); setView('schedule') }}
    onSelectCategory={(next) => { setCategory(next); setExpanded(true); setView('academic') }}
    onNavigationOpenChange={setOpen}
    onNavigationPinnedChange={setPinned}
  />
}

async function renderNavigation(narrow = false) {
  installMatchMedia(narrow)
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<Harness />))
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.trim().startsWith(label)) as HTMLButtonElement
}

afterEach(() => { document.body.innerHTML = ''; vi.unstubAllGlobals() })

describe('ApplicationNavigation', () => {
  it('defines the exact fixed Academic Data metadata', () => {
    expect(ACADEMIC_DATA_CATEGORIES.map(({ id, label }) => ({ id, label }))).toEqual([
      { id: 'semesters', label: 'Semester' },
      { id: 'holidays', label: 'Feiertage' },
      { id: 'cohorts', label: 'Kohorten' },
      { id: 'courses', label: 'Lehrveranstaltungen' },
      { id: 'study-types', label: 'Studienformen' },
      { id: 'time-windows', label: 'Zeitfenster' },
      { id: 'lecturers', label: 'Lehrende' },
      { id: 'rooms', label: 'Räume' },
    ])
  })

  it('exposes one primary hierarchy and no unavailable destinations', async () => {
    await renderNavigation()
    expect(document.querySelectorAll('nav[aria-label="Hauptnavigation"]')).toHaveLength(1)
    expect(button('Planung').getAttribute('aria-expanded')).toBe('true')
    expect(button('Kalender').getAttribute('aria-current')).toBe('page')
    expect(button('Stammdaten').getAttribute('aria-expanded')).toBe('false')
    expect(document.body.textContent).not.toContain('Dashboard')
    act(() => button('Stammdaten').click())
    expect(ACADEMIC_DATA_CATEGORIES.map(({ label }) => button(label).textContent?.trim())).toEqual(ACADEMIC_DATA_CATEGORIES.map(({ label }) => label))
  })

  it('exposes ordered Schedule children with exactly one current destination', async () => {
    await renderNavigation()
    expect(['Kalender', 'Versionen', 'Prüfungen', 'Abstimmung mit Lehrenden'].map((label) => button(label).textContent?.trim())).toEqual(['Kalender', 'Versionen', 'Prüfungen', 'Abstimmung mit Lehrenden'])
    act(() => button('Versionen').click())
    expect(button('Versionen').getAttribute('aria-current')).toBe('page')
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    act(() => button('Prüfungen').click())
    expect(button('Prüfungen').getAttribute('aria-current')).toBe('page')
    act(() => button('Abstimmung mit Lehrenden').click())
    expect(button('Abstimmung mit Lehrenden').getAttribute('aria-current')).toBe('page')
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    expect(button('Planung').className).toContain('is-active')
  })

  it('uses the parent as disclosure only and retains sole parent/child context', async () => {
    await renderNavigation()
    act(() => button('Stammdaten').click())
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    act(() => button('Lehrveranstaltungen').click())
    expect(button('Stammdaten').getAttribute('aria-expanded')).toBe('true')
    expect(button('Stammdaten').className).toContain('is-active')
    expect(button('Lehrveranstaltungen').getAttribute('aria-current')).toBe('page')
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    act(() => button('Stammdaten').click())
    expect(button('Stammdaten').getAttribute('aria-expanded')).toBe('true')
  })

  it('removes collapsed children from keyboard traversal', async () => {
    await renderNavigation()
    act(() => button('Stammdaten').focus())
    expect(document.activeElement).toBe(button('Stammdaten'))
    expect(button('Semester')).toBeUndefined()
    act(() => button('Stammdaten').click())
    expect(button('Semester').tabIndex).toBe(0)
  })

  it('provides a named narrow modal with initial focus and complete dismissal', async () => {
    await renderNavigation(true)
    expect(button('Menü')).toBeDefined()
    act(() => button('Menü').click())
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.getAttribute('aria-labelledby')).toBe('navigation-title')
    expect(document.activeElement).toBe(button('Menü schließen'))
    expect(button('Menü').hasAttribute('inert')).toBe(true)
    expect(button('Menü').getAttribute('aria-hidden')).toBe('true')
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(button('Stammdaten'))
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(button('Menü schließen'))
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(document.activeElement).toBe(button('Menü'))
    expect(button('Menü').hasAttribute('inert')).toBe(false)
    expect(button('Menü').getAttribute('aria-hidden')).toBeNull()
    act(() => button('Menü').click())
    act(() => button('Menü schließen').click())
    expect(document.activeElement).toBe(button('Menü'))
  })

  it('cleans up an open narrow panel when the presentation becomes wide', async () => {
    const media = installMatchMedia(true)
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => root.render(<Harness />))
    act(() => button('Menü').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(true)
    await act(async () => { media.dispatch(false); await Promise.resolve() })
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(true)
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(button('Kalender'))
  })

  it('unpins wide navigation into a modal overlay and can pin it persistently again', async () => {
    await renderNavigation()
    act(() => button('Navigation lösen').click())
    expect(button('Navigation öffnen')).toBeDefined()
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    act(() => button('Navigation öffnen').click())
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(document.querySelector('.navigation-backdrop')).not.toBeNull()
    expect(document.activeElement).toBe(button('Menü schließen'))
    expect(button('Navigation öffnen').hasAttribute('inert')).toBe(true)
    expect(button('Navigation öffnen').getAttribute('aria-hidden')).toBe('true')
    act(() => button('Versionen').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    expect(button('Navigation öffnen').hasAttribute('inert')).toBe(false)
    expect(button('Navigation öffnen').getAttribute('aria-hidden')).toBeNull()
    act(() => button('Navigation öffnen').click())
    act(() => button('Navigation anheften').click())
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(button('Navigation lösen')).toBeDefined()
    expect(button('Navigation öffnen').className).not.toContain('is-unpinned')
  })

  it('omits pin controls from the narrow navigation presentation', async () => {
    await renderNavigation(true)
    act(() => button('Menü').click())
    expect(button('Navigation anheften')).toBeUndefined()
    expect(button('Navigation lösen')).toBeUndefined()
  })

  it('dismisses the narrow panel on current and changed leaf selections', async () => {
    await renderNavigation(true)
    act(() => button('Menü').click())
    act(() => button('Kalender').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    act(() => button('Menü').click())
    act(() => button('Stammdaten').click())
    act(() => button('Räume').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    expect(button('Räume').getAttribute('aria-current')).toBe('page')
  })
})
