import { act, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { AcademicDataCategory } from './components/ApplicationNavigation'

const mocks = vi.hoisted(() => ({ scheduleMount: vi.fn(), revisions: vi.fn(), academic: vi.fn() }))
vi.mock('./pages/CourseSchedulePage', () => ({
  CourseSchedulePage: ({ catalogRevision }: { catalogRevision: number }) => {
    useEffect(() => { mocks.scheduleMount() }, [])
    mocks.revisions(catalogRevision)
    return <div>Schedule view</div>
  },
}))
vi.mock('./pages/AcademicDataPage', () => ({
  AcademicDataPage: ({ category, onCatalogChanged }: { category: AcademicDataCategory; onCatalogChanged: () => void }) => {
    mocks.academic(category)
    return <div><span>Academic category: {category}</span><button onClick={onCatalogChanged}>Mutate catalog</button></div>
  },
}))

import App from './App'

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

async function renderApp() {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<App />))
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.trim().startsWith(label)) as HTMLButtonElement
}

beforeEach(() => installMatchMedia())
afterEach(() => { vi.clearAllMocks(); vi.unstubAllGlobals() })

describe('App unified navigation', () => {
  it('starts on Schedule with one primary navigation and no duplicate or dead destinations', async () => {
    await renderApp()
    expect(document.body.textContent).toContain('Schedule view')
    expect(document.querySelectorAll('nav[aria-label="Primary navigation"]')).toHaveLength(1)
    expect(document.querySelectorAll('.view-navigation')).toHaveLength(0)
    expect(document.querySelectorAll('a[href^="#"]')).toHaveLength(0)
    expect(document.body.textContent).not.toContain('Dashboard')
  })

  it('reaches every Academic Data leaf through the ordered hierarchy', async () => {
    await renderApp()
    act(() => button('Academic Data').click())
    const destinations: Array<[string, AcademicDataCategory]> = [
      ['Semesters', 'semesters'], ['Cohorts', 'cohorts'], ['Courses', 'courses'],
      ['Study types', 'study-types'], ['Time windows', 'time-windows'],
      ['Lecturers', 'lecturers'], ['Rooms', 'rooms'],
    ]
    for (const [label, id] of destinations) {
      act(() => button(label).click())
      expect(document.body.textContent).toContain(`Academic category: ${id}`)
      expect(button(label).getAttribute('aria-current')).toBe('page')
    }
  })

  it('retains category and expansion state across Schedule round trips', async () => {
    await renderApp()
    act(() => button('Academic Data').click())
    act(() => button('Courses').click())
    act(() => button('Schedule').click())
    expect(button('Academic Data').getAttribute('aria-expanded')).toBe('true')
    expect(button('Courses')).toBeDefined()
    act(() => button('Courses').click())
    expect(document.body.textContent).toContain('Academic category: courses')
  })

  it('keeps Schedule mounted and refreshes it after catalog mutations', async () => {
    await renderApp()
    act(() => button('Academic Data').click())
    act(() => button('Semesters').click())
    act(() => button('Mutate catalog').click())
    act(() => button('Schedule').click())
    expect(mocks.scheduleMount).toHaveBeenCalledTimes(1)
    expect(mocks.revisions).toHaveBeenCalledWith(1)
  })

  it('moves focus only after an actual destination change', async () => {
    await renderApp()
    act(() => button('Academic Data').click())
    act(() => button('Semesters').click())
    expect(document.activeElement).toBe(document.querySelector('.application-content'))
    act(() => button('Semesters').focus())
    const renderCount = mocks.academic.mock.calls.length
    act(() => button('Semesters').click())
    expect(document.activeElement).toBe(button('Semesters'))
    expect(mocks.academic).toHaveBeenCalledTimes(renderCount)
  })

  it('blocks background interaction and preserves state through narrow transitions', async () => {
    const media = installMatchMedia(true)
    await renderApp()
    act(() => button('Menu').click())
    const content = document.querySelector('.application-content') as HTMLElement
    expect(content.hasAttribute('inert')).toBe(true)
    expect(content.getAttribute('aria-hidden')).toBe('true')
    act(() => button('Academic Data').click())
    act(() => button('Rooms').click())
    expect(document.activeElement).toBe(content)
    expect(content.hasAttribute('inert')).toBe(false)
    act(() => media.dispatch(false))
    act(() => media.dispatch(true))
    act(() => button('Menu').click())
    expect(button('Rooms').getAttribute('aria-current')).toBe('page')
    expect(button('Academic Data').getAttribute('aria-expanded')).toBe('true')
  })
})
