import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MultiCourseGenerationPanel } from './MultiCourseGenerationPanel'
import { generationCatalog, targetCohort, otherCohort, emptyCohort } from '../test/fixtures/courseLists'
import type { CourseOption } from '../api/planningOptions'

const entity = (id: number, name: string) => ({ id, name })
const courses: CourseOption[] = [1, 2, 3].map((id) => ({
  id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
  lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), cohortCalendar: entity(1, 'Full-time'),
}))

afterEach(() => { document.body.innerHTML = '' })

describe('MultiCourseGenerationPanel', () => {
  it('announces the captured algorithm as read-only text', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<MultiCourseGenerationPanel courses={courses} selectedCourseIds={[1]} algorithm="cohort" onChange={vi.fn()} onGenerate={vi.fn()} />))
    expect(document.body.textContent).toContain('Algorithmus: Kohorte')
    expect(document.querySelector('select[aria-label="Algorithmus"]')).toBeNull()
    expect([...document.querySelectorAll('[role="status"]')].some(node => node.textContent?.includes('Algorithmus: Kohorte'))).toBe(true)
  })
  it('shows the optimized selection limit, unavailable dates, selection, and clear behavior', () => {
    const onChange = vi.fn()
    const onDates = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<MultiCourseGenerationPanel courses={courses} selectedCourseIds={[1, 2]} unavailableDatesInput="" onUnavailableDatesInputChange={onDates} onChange={onChange} onGenerate={vi.fn()} />))
    expect(document.body.textContent).toContain('2 ausgewählt — gemeinsame Planung')
    expect(document.body.textContent).toContain('Stundenpläne erzeugen')
    expect(document.body.textContent).toContain('Maximiert die geplanten Lehreinheiten')
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => boxes[2].click())
    expect(onChange).toHaveBeenCalledWith([1, 2, 3])
    const dates = document.querySelector<HTMLInputElement>('input[type="text"]')
    act(() => {
      if (dates) {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dates, '2026-10-26, 2026-10-26')
        dates.dispatchEvent(new Event('input', { bubbles: true }))
      }
    })
    expect(onDates).toHaveBeenCalledWith('2026-10-26, 2026-10-26')
    const clear = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Auswahl aufheben')
    act(() => clear?.click())
    expect(onChange).toHaveBeenCalledWith([])
  })

  it('shows informational draft status without changing course selection', () => {
    const onChange = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <MultiCourseGenerationPanel
        courses={courses}
        courseDraftStatuses={{
          1: { hasDraft: true, scheduledUnits: 4, totalUnits: 8 },
          2: { hasDraft: false, scheduledUnits: 0, totalUnits: 8 },
          3: { hasDraft: true, scheduledUnits: 8, totalUnits: 8 },
        }}
        selectedCourseIds={[]}
        onChange={onChange}
        onGenerate={vi.fn()}
      />,
    ))

    const statuses = [...document.querySelectorAll('.course-draft-status')].map((status) => status.textContent)
    expect(statuses).toEqual(['Entwurf · 4/8 Lehreinheiten', 'Kein Entwurf', 'Entwurf · 8/8 Lehreinheiten'])

    act(() => document.querySelector<HTMLInputElement>('input[type="checkbox"]')?.click())
    expect(onChange).toHaveBeenCalledWith([1])
  })

  it('allows two unavailable dates to be entered character by character', () => {
    function Harness() {
      const [datesInput, setDatesInput] = useState('')
      return <MultiCourseGenerationPanel courses={courses} selectedCourseIds={[1]} unavailableDatesInput={datesInput} onUnavailableDatesInputChange={setDatesInput} onChange={vi.fn()} onGenerate={vi.fn()} />
    }
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<Harness />))
    const input = document.querySelector<HTMLInputElement>('input[type="text"]')
    expect(input).not.toBeNull()

    for (const character of '2026-10-26, 2026-11-02') {
      act(() => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, `${input?.value ?? ''}${character}`)
        input?.dispatchEvent(new Event('input', { bubbles: true }))
      })
    }

    expect(input?.value).toBe('2026-10-26, 2026-11-02')
    expect(document.body.textContent).toContain('1 ausgewählt — Einzelplanung')
  })

  it('explains a constraint-mutation guard without claiming generation is running', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <MultiCourseGenerationPanel
        courses={courses}
        selectedCourseIds={[1]}
        disabled
        disabledReason="Die Datumsgrenzen werden gerade aktualisiert."
        onChange={vi.fn()}
        onGenerate={vi.fn()}
      />,
    ))

    expect(document.body.textContent).toContain('Die Datumsgrenzen werden gerade aktualisiert.')
    expect(document.body.textContent).toContain('Ausgewählte Lehrveranstaltungen optimieren')
    expect(document.body.textContent).not.toContain('werden optimiert')
    expect(document.querySelector<HTMLButtonElement>('.generate-button')?.disabled).toBe(true)
  })
})


describe('I-005 generation discovery', () => {
  it('matches eleven of 94 by cohort identity without selecting, and resets visibility only', () => {
    const changed = vi.fn()
    function Harness() {
      const [cohort, setCohort] = useState<number | null>(null)
      return <MultiCourseGenerationPanel courses={generationCatalog} cohorts={[targetCohort, otherCohort, emptyCohort]} cohortId={cohort} onCohortChange={setCohort} semesterName="2027 S" selectedCourseIds={[12, 13]} onChange={changed} onGenerate={vi.fn()} />
    }
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<Harness />))
    const filter = document.querySelector<HTMLSelectElement>('[aria-label="Kohorte filtern"]')!
    expect(filter).not.toBeNull()
    act(() => { filter.value = String(targetCohort.id); filter.dispatchEvent(new Event('change', { bubbles: true })) })
    expect(document.querySelectorAll('.course-picker input')).toHaveLength(11)
    expect(document.body.textContent).toContain('2 durch den Kohortenfilter verborgen')
    expect(document.body.textContent).toContain('Lehrveranstaltung 12')
    expect(document.body.textContent).toContain('2027 S')
    expect(changed).not.toHaveBeenCalled()
    act(() => document.querySelector<HTMLInputElement>('.course-picker input')!.click())
    expect(changed).toHaveBeenCalledWith([12, 13, 1])
    act(() => [...document.querySelectorAll('button')].find(b => b.textContent === 'Kohortenfilter zurücksetzen')!.click())
    expect(document.querySelectorAll('.course-picker input')).toHaveLength(94)
    expect(changed).toHaveBeenCalledTimes(1)
    act(() => root.unmount())
  })
})


it.each([0, 1, 20, 21])('I-005 retains complete selection validation at %i IDs, including all hidden', (count) => {
  const selected = Array.from({length: count}, (_, index) => index + 1)
  const changed = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(<MultiCourseGenerationPanel courses={generationCatalog} cohorts={[emptyCohort]} cohortId={emptyCohort.id} onCohortChange={vi.fn()} selectedCourseIds={selected} onChange={changed} onGenerate={vi.fn()} />))
  expect(document.querySelectorAll('.course-picker input')).toHaveLength(0)
  expect(document.body.textContent).toContain(`${count} durch den Kohortenfilter verborgen`)
  expect(document.querySelectorAll('.course-selection-review li')).toHaveLength(count)
  expect(document.querySelector<HTMLButtonElement>('.generate-button')!.disabled).toBe(count === 0 || count > 20)
  if (count) act(() => [...document.querySelectorAll('button')].find(b => b.textContent === 'Auswahl aufheben')!.click())
  if (count) expect(changed).toHaveBeenCalledWith([])
  act(() => root.unmount())
})

it('I-005 blocks new unavailable/21st choices, permits removal, and exposes missing identity', () => {
  const changed = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(<MultiCourseGenerationPanel courses={generationCatalog} selectedCourseIds={[94, 9999]} onChange={changed} onGenerate={vi.fn()} />))
  expect(document.body.textContent).toContain('Lehrveranstaltung #9999 — nicht verfügbar')
  const unavailable = document.querySelectorAll<HTMLInputElement>('.course-picker input')[93]
  expect(unavailable.disabled).toBe(false)
  act(() => unavailable.click())
  expect(changed).toHaveBeenCalledWith([9999])
  act(() => root.render(<MultiCourseGenerationPanel courses={generationCatalog} selectedCourseIds={Array.from({length: 20}, (_, i) => i + 1)} onChange={changed} onGenerate={vi.fn()} />))
  expect(document.querySelectorAll<HTMLInputElement>('.course-picker input')[20].disabled).toBe(true)
  expect(document.querySelectorAll<HTMLInputElement>('.course-picker input')[0].disabled).toBe(false)
  act(() => root.unmount())
})


it('I-005 distinguishes retained failed freshness from successful results and blocks generation', () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(<MultiCourseGenerationPanel courses={generationCatalog} selectedCourseIds={[1]} freshness="error" onChange={vi.fn()} onGenerate={vi.fn()} />))
  expect(document.body.textContent).toContain('Planungsoptionen konnten nicht aktualisiert werden')
  expect(document.body.textContent).not.toContain('94 Treffer')
  expect(document.querySelector<HTMLButtonElement>('.generate-button')!.disabled).toBe(true)
  expect(document.querySelectorAll('.course-selection-review li')).toHaveLength(1)
  act(() => root.unmount())
})

it('I-005 keeps meaningful focus when a focused course disappears during refresh', () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const props = { selectedCourseIds: [], onChange: vi.fn(), onGenerate: vi.fn(), onCohortChange: vi.fn() }
  act(() => root.render(<MultiCourseGenerationPanel {...props} courses={generationCatalog} />))
  act(() => document.querySelector<HTMLInputElement>('.course-picker input')!.focus())
  act(() => root.render(<MultiCourseGenerationPanel {...props} courses={generationCatalog.slice(1)} />))
  expect(document.activeElement?.getAttribute('aria-label')).toBe('Kohorte filtern')
  act(() => root.unmount())
})
