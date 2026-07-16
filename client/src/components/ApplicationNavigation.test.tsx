import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  ACADEMIC_DATA_CATEGORIES,
  ApplicationNavigation,
  type AcademicDataCategory,
  type PlannerView,
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
  const [expanded, setExpanded] = useState(false)
  const [open, setOpen] = useState(false)
  return <ApplicationNavigation
    view={view}
    selectedCategory={category}
    academicExpanded={expanded}
    navigationOpen={open}
    onToggleAcademic={() => setExpanded((value) => view === 'academic' ? true : !value)}
    onSelectSchedule={() => setView('schedule')}
    onSelectCategory={(next) => { setCategory(next); setExpanded(true); setView('academic') }}
    onNavigationOpenChange={setOpen}
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

afterEach(() => vi.unstubAllGlobals())

describe('ApplicationNavigation', () => {
  it('defines the exact fixed Academic Data metadata', () => {
    expect(ACADEMIC_DATA_CATEGORIES.map(({ id, label }) => ({ id, label }))).toEqual([
      { id: 'semesters', label: 'Semesters' },
      { id: 'cohorts', label: 'Cohorts' },
      { id: 'courses', label: 'Courses' },
      { id: 'study-types', label: 'Study types' },
      { id: 'time-windows', label: 'Time windows' },
      { id: 'lecturers', label: 'Lecturers' },
      { id: 'rooms', label: 'Rooms' },
    ])
  })

  it('exposes one primary hierarchy and no unavailable destinations', async () => {
    await renderNavigation()
    expect(document.querySelectorAll('nav[aria-label="Primary navigation"]')).toHaveLength(1)
    expect(button('Schedule').getAttribute('aria-current')).toBe('page')
    expect(button('Academic Data').getAttribute('aria-expanded')).toBe('false')
    expect(document.body.textContent).not.toContain('Dashboard')
    act(() => button('Academic Data').click())
    expect(ACADEMIC_DATA_CATEGORIES.map(({ label }) => button(label).textContent?.trim())).toEqual(ACADEMIC_DATA_CATEGORIES.map(({ label }) => label))
  })

  it('uses the parent as disclosure only and retains sole parent/child context', async () => {
    await renderNavigation()
    act(() => button('Academic Data').click())
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    act(() => button('Courses').click())
    expect(button('Academic Data').getAttribute('aria-expanded')).toBe('true')
    expect(button('Academic Data').className).toContain('is-active')
    expect(button('Courses').getAttribute('aria-current')).toBe('page')
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    act(() => button('Academic Data').click())
    expect(button('Academic Data').getAttribute('aria-expanded')).toBe('true')
  })

  it('removes collapsed children from keyboard traversal', async () => {
    await renderNavigation()
    act(() => button('Academic Data').focus())
    expect(document.activeElement).toBe(button('Academic Data'))
    expect(button('Semesters')).toBeUndefined()
    act(() => button('Academic Data').click())
    expect(button('Semesters').tabIndex).toBe(0)
  })

  it('provides a named narrow modal with initial focus and complete dismissal', async () => {
    await renderNavigation(true)
    expect(button('Menu')).toBeDefined()
    act(() => button('Menu').click())
    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.getAttribute('aria-labelledby')).toBe('navigation-title')
    expect(document.activeElement).toBe(button('Close menu'))
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(button('Academic Data'))
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(button('Close menu'))
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(document.activeElement).toBe(button('Menu'))
    act(() => button('Menu').click())
    act(() => button('Close menu').click())
    expect(document.activeElement).toBe(button('Menu'))
  })

  it('cleans up an open narrow panel when the presentation becomes wide', async () => {
    const media = installMatchMedia(true)
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => root.render(<Harness />))
    act(() => button('Menu').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(true)
    await act(async () => { media.dispatch(false); await Promise.resolve() })
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.activeElement).toBe(button('Schedule'))
  })

  it('dismisses the narrow panel on current and changed leaf selections', async () => {
    await renderNavigation(true)
    act(() => button('Menu').click())
    act(() => button('Schedule').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    act(() => button('Menu').click())
    act(() => button('Academic Data').click())
    act(() => button('Rooms').click())
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    expect(button('Rooms').getAttribute('aria-current')).toBe('page')
  })
})
