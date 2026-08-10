import { act, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AcademicDataCategory } from './components/ApplicationNavigation'

const mocks = vi.hoisted(() => ({
  scheduleMount: vi.fn(),
  revisions: vi.fn(),
  academic: vi.fn(),
  navigationRequest: vi.fn(),
  pendingNavigation: null as { label: string; commit: () => void } | null,
  guardNavigation: false,
}))
vi.mock('./pages/CourseSchedulePage', () => ({
  CourseSchedulePage: ({ catalogRevision, destination, onNavigationRequesterChange }: { catalogRevision: number; destination: string; onNavigationRequesterChange?: (requester: ((request: { label: string; commit: () => void }) => void) | null) => void }) => {
    useEffect(() => { mocks.scheduleMount() }, [])
    useEffect(() => {
      onNavigationRequesterChange?.((request) => {
        if (mocks.guardNavigation) {
          mocks.pendingNavigation = request
          mocks.navigationRequest(request.label)
        } else {
          request.commit()
        }
      })
      return () => onNavigationRequesterChange?.(null)
    }, [onNavigationRequesterChange])
    mocks.revisions(catalogRevision)
    return <div>Schedule view: {destination}</div>
  },
}))
vi.mock('./pages/AcademicDataPage', () => ({
  AcademicDataPage: ({ category, onCatalogChanged }: { category: AcademicDataCategory; onCatalogChanged: () => void }) => {
    mocks.academic(category)
    return <div><span>Academic category: {category}</span><button onClick={onCatalogChanged}>Mutate catalog</button></div>
  },
}))

import App from './App'
import {
  NAVIGATION_PINNED_STORAGE_KEY,
  readNavigationPinned,
  writeNavigationPinned,
} from './navigationPreference'

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

function installLocalStorage() {
  const values = new Map<string, string>()
  const storage = {
    getItem: vi.fn((key: string) => values.get(key) ?? null),
    setItem: vi.fn((key: string, value: string) => { values.set(key, value) }),
    removeItem: vi.fn((key: string) => { values.delete(key) }),
    clear: vi.fn(() => values.clear()),
  }
  vi.stubGlobal('localStorage', storage)
  return storage
}

async function renderApp() {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<App />))
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.trim().startsWith(label)) as HTMLButtonElement
}

beforeEach(() => { installLocalStorage(); installMatchMedia() })
afterEach(() => { mocks.pendingNavigation = null; mocks.guardNavigation = false; vi.clearAllMocks(); vi.unstubAllGlobals() })

describe('App unified navigation', () => {
  it('starts on Schedule with one primary navigation and no duplicate or dead destinations', async () => {
    await renderApp()
    expect(document.body.textContent).toContain('Schedule view')
    expect(document.querySelectorAll('nav[aria-label="Hauptnavigation"]')).toHaveLength(1)
    expect(document.querySelectorAll('.view-navigation')).toHaveLength(0)
    expect(document.querySelectorAll('a[href^="#"]')).toHaveLength(0)
    expect(document.body.textContent).not.toContain('Dashboard')
  })

  it('defaults to Calendar and reaches all retained Schedule children', async () => {
    await renderApp()
    expect(document.body.textContent).toContain('Schedule view: calendar')
    act(() => button('Versionen').click())
    expect(document.body.textContent).toContain('Schedule view: versions')
    expect(button('Versionen').getAttribute('aria-current')).toBe('page')
    act(() => button('Prüfungen').click())
    expect(document.body.textContent).toContain('Schedule view: exams')
    act(() => button('Abstimmung mit Lehrenden').click())
    expect(document.body.textContent).toContain('Schedule view: reviews')
    expect(button('Abstimmung mit Lehrenden').getAttribute('aria-current')).toBe('page')
    act(() => button('Kalender').click())
    expect(document.body.textContent).toContain('Schedule view: calendar')
    expect(mocks.scheduleMount).toHaveBeenCalledTimes(1)
  })

  it('reaches every Academic Data leaf through the ordered hierarchy', async () => {
    await renderApp()
    act(() => button('Stammdaten').click())
    const destinations: Array<[string, AcademicDataCategory]> = [
      ['Semester', 'semesters'], ['Kohorten', 'cohorts'], ['Lehrveranstaltungen', 'courses'],
      ['Studienformen', 'study-types'], ['Zeitfenster', 'time-windows'],
      ['Lehrende', 'lecturers'], ['Räume', 'rooms'],
    ]
    for (const [label, id] of destinations) {
      act(() => button(label).click())
      expect(document.body.textContent).toContain(`Academic category: ${id}`)
      expect(button(label).getAttribute('aria-current')).toBe('page')
    }
  })

  it('retains category and expansion state across Schedule round trips', async () => {
    await renderApp()
    act(() => button('Stammdaten').click())
    act(() => button('Lehrveranstaltungen').click())
    act(() => button('Kalender').click())
    expect(button('Stammdaten').getAttribute('aria-expanded')).toBe('true')
    expect(button('Lehrveranstaltungen')).toBeDefined()
    act(() => button('Lehrveranstaltungen').click())
    expect(document.body.textContent).toContain('Academic category: courses')
  })

  it('keeps Schedule mounted and refreshes it after catalog mutations', async () => {
    await renderApp()
    act(() => button('Stammdaten').click())
    act(() => button('Semester').click())
    act(() => button('Mutate catalog').click())
    act(() => button('Kalender').click())
    expect(mocks.scheduleMount).toHaveBeenCalledTimes(1)
    expect(mocks.revisions).toHaveBeenCalledWith(1)
  })

  it('moves focus only after an actual destination change', async () => {
    await renderApp()
    act(() => button('Stammdaten').click())
    act(() => button('Semester').click())
    expect(document.activeElement).toBe(document.querySelector('.application-content'))
    act(() => button('Semester').focus())
    const renderCount = mocks.academic.mock.calls.length
    act(() => button('Semester').click())
    expect(document.activeElement).toBe(button('Semester'))
    expect(mocks.academic).toHaveBeenCalledTimes(renderCount)
  })

  it('does not change navigation or focus until the Schedule page approves a guarded request', async () => {
    mocks.guardNavigation = true
    await renderApp()
    const rooms = button('Stammdaten')
    act(() => rooms.focus())
    act(() => rooms.click())
    act(() => button('Räume').click())
    expect(mocks.navigationRequest).toHaveBeenLastCalledWith('Stammdaten: rooms')
    expect(document.body.textContent).toContain('Schedule view')
    expect(button('Kalender').getAttribute('aria-current')).toBe('page')
    expect(document.activeElement).not.toBe(document.querySelector('.application-content'))
    act(() => mocks.pendingNavigation?.commit())
    expect(document.body.textContent).toContain('Academic category: rooms')
    expect(document.activeElement).toBe(document.querySelector('.application-content'))
  })

  it('keeps Lecturer coordination pending until the Schedule page approves the guarded request', async () => {
    mocks.guardNavigation = true
    await renderApp()

    act(() => button('Abstimmung mit Lehrenden').click())

    expect(mocks.navigationRequest).toHaveBeenLastCalledWith('Planung: reviews')
    expect(document.body.textContent).toContain('Schedule view: calendar')
    expect(button('Kalender').getAttribute('aria-current')).toBe('page')
    expect(button('Abstimmung mit Lehrenden').getAttribute('aria-current')).toBeNull()

    act(() => mocks.pendingNavigation?.commit())

    expect(document.body.textContent).toContain('Schedule view: reviews')
    expect(button('Abstimmung mit Lehrenden').getAttribute('aria-current')).toBe('page')
    expect(document.querySelectorAll('[aria-current="page"]')).toHaveLength(1)
    expect(document.activeElement).toBe(document.querySelector('.application-content'))
  })

  it('blocks background interaction and preserves state through narrow transitions', async () => {
    const media = installMatchMedia(true)
    await renderApp()
    act(() => button('Menü').click())
    const content = document.querySelector('.application-content') as HTMLElement
    expect(content.hasAttribute('inert')).toBe(true)
    expect(content.getAttribute('aria-hidden')).toBe('true')
    act(() => button('Stammdaten').click())
    act(() => button('Räume').click())
    expect(document.activeElement).toBe(content)
    expect(content.hasAttribute('inert')).toBe(false)
    act(() => media.dispatch(false))
    act(() => media.dispatch(true))
    act(() => button('Menü').click())
    expect(button('Räume').getAttribute('aria-current')).toBe('page')
    expect(button('Stammdaten').getAttribute('aria-expanded')).toBe('true')
  })

  it('restores and persists the independent wide navigation pin preference', async () => {
    localStorage.setItem(NAVIGATION_PINNED_STORAGE_KEY, 'false')
    await renderApp()
    expect(document.querySelector('.application-shell')?.getAttribute('data-navigation-pinned')).toBe('false')
    act(() => button('Navigation öffnen').click())
    act(() => button('Navigation anheften').click())
    expect(localStorage.getItem(NAVIGATION_PINNED_STORAGE_KEY)).toBe('true')
    expect(document.querySelector('.application-shell')?.getAttribute('data-navigation-pinned')).toBe('true')
  })

  it('closes the wide temporary overlay and hands focus to a changed Schedule destination', async () => {
    localStorage.setItem(NAVIGATION_PINNED_STORAGE_KEY, 'false')
    await renderApp()
    act(() => button('Navigation öffnen').click())
    act(() => button('Versionen').click())
    expect(document.querySelector('.application-content')?.hasAttribute('inert')).toBe(false)
    expect(document.querySelector('.application-navigation')?.classList.contains('is-open')).toBe(false)
    expect(document.activeElement).toBe(document.querySelector('.application-content'))
  })

  it('uses pinned defaults for missing, invalid, or inaccessible storage', () => {
    expect(readNavigationPinned()).toBe(true)
    localStorage.setItem(NAVIGATION_PINNED_STORAGE_KEY, 'invalid')
    expect(readNavigationPinned()).toBe(true)
    const get = vi.spyOn(localStorage, 'getItem').mockImplementation(() => { throw new Error('blocked') })
    expect(readNavigationPinned()).toBe(true)
    get.mockRestore()
    const set = vi.spyOn(localStorage, 'setItem').mockImplementation(() => { throw new Error('blocked') })
    expect(() => writeNavigationPinned(false)).not.toThrow()
    set.mockRestore()
  })
})
