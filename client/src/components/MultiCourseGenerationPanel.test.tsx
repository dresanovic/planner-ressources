import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MultiCourseGenerationPanel } from './MultiCourseGenerationPanel'
import type { CourseOption } from '../api/planningOptions'

const entity = (id: number, name: string) => ({ id, name })
const courses: CourseOption[] = [1, 2, 3].map((id) => ({
  id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
  lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
}))

afterEach(() => { document.body.innerHTML = '' })

describe('MultiCourseGenerationPanel', () => {
  it('shows the optimized selection limit, unavailable dates, selection, and clear behavior', () => {
    const onChange = vi.fn()
    const onDates = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<MultiCourseGenerationPanel courses={courses} selectedCourseIds={[1, 2]} unavailableDatesInput="" onUnavailableDatesInputChange={onDates} onChange={onChange} onGenerate={vi.fn()} />))
    expect(document.body.textContent).toContain('2 ausgewählt')
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
