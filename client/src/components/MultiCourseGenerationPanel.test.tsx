import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { MultiCourseGenerationPanel } from './MultiCourseGenerationPanel'
import type { CourseOption } from '../api/planningOptions'

const entity = (id: number, name: string) => ({ id, name })
const courses: CourseOption[] = [1, 2, 3].map((id) => ({
  id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4,
  lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
}))

afterEach(() => { document.body.innerHTML = '' })

describe('MultiCourseGenerationPanel', () => {
  it('shows count, constraint isolation, selection, and clear behavior', () => {
    const onChange = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<MultiCourseGenerationPanel courses={courses} selectedCourseIds={[1, 2]} onChange={onChange} onGenerate={vi.fn()} />))
    expect(document.body.textContent).toContain('2 selected')
    expect(document.body.textContent).toContain('Each course uses its own saved generation constraints')
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => boxes[2].click())
    expect(onChange).toHaveBeenCalledWith([1, 2, 3])
    const clear = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Clear selection')
    act(() => clear?.click())
    expect(onChange).toHaveBeenCalledWith([])
  })
})
