import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { ScheduleContextHeader } from './ScheduleContextHeader'

afterEach(() => { document.body.innerHTML = '' })

it('always shows semester and only destination-meaningful revision/course controls', () => {
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  const props = { semesterId: 1, semesters: [{ id: 1, label: 'Fall' }], revisionId: 2, revisions: [{ id: 2, label: 'Working R2' }], courseId: 3, courses: [{ id: 3, label: 'Algorithms' }], onSemesterChange: vi.fn(), onRevisionChange: vi.fn(), onCourseChange: vi.fn() }
  act(() => root.render(<ScheduleContextHeader destination="calendar" {...props} />))
  expect([...host.querySelectorAll('label span')].map((item) => item.textContent)).toEqual(['Semester', 'Revision', 'Course'])
  act(() => root.render(<ScheduleContextHeader destination="versions" {...props} />))
  expect([...host.querySelectorAll('label span')].map((item) => item.textContent)).toEqual(['Semester', 'Revision'])
  act(() => root.render(<ScheduleContextHeader destination="exams" {...props} />))
  expect([...host.querySelectorAll('label span')].map((item) => item.textContent)).toEqual(['Semester', 'Course'])
  act(() => root.render(<ScheduleContextHeader destination="reviews" {...props} />))
  expect(host.querySelector('h2')?.textContent).toBe('Lecturer coordination')
  expect([...host.querySelectorAll('label span')].map((item) => item.textContent)).toEqual(['Semester', 'Revision'])
})

it('makes unavailable context explicit without color-only meaning', () => {
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(<ScheduleContextHeader destination="calendar" semesterId={9} semesters={[{ id: 1, label: 'Fall' }]} revisionId={null} revisions={[]} courseId={null} courses={[]} onSemesterChange={vi.fn()} onRevisionChange={vi.fn()} onCourseChange={vi.fn()} />))
  expect(host.textContent).toContain('Unavailable')
  expect(host.textContent).toContain('No revision available')
  expect(host.textContent).toContain('No course available')
})
