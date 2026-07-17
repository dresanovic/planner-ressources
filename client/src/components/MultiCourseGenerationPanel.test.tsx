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
    expect(document.body.textContent).toContain('2 selected')
    expect(document.body.textContent).toContain('Maximize scheduled units')
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
    const clear = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Clear selection')
    act(() => clear?.click())
    expect(onChange).toHaveBeenCalledWith([])
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
})
