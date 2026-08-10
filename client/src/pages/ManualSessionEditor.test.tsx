import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'

import { ManualSessionEditor } from './CourseSchedulePage'

function change(input: HTMLInputElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

it('blocks an incomplete manual-session date before the mutation and focuses the field', async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ManualSessionEditor
    course={{
      id: 1, name: 'Algorithmen', totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4,
      lecturer: { id: 1, name: 'Ada' }, cohort: { id: 2, name: 'A1' }, cohortSize: 20,
      room: { id: 3, name: 'R1' }, studyType: { id: 4, name: 'Vollzeit' },
    }}
    semester={{ id: 1, name: 'Wintersemester', startDate: '2026-09-01', endDate: '2027-01-31' }}
    lecturers={[{ id: 1, name: 'Ada' }] as never}
    cohorts={[{ id: 2, name: 'A1', studentCount: 20 }]}
    rooms={[{ id: 3, name: 'R1', capacity: 30 }] as never}
    remainingUnits={4}
    isBusy={false}
    isSaving={false}
    requiresDraft={false}
    errors={[]}
    onSubmit={onSubmit}
  />))
  const date = document.querySelector<HTMLInputElement>('#manual-date')!

  await act(async () => change(date, '1.09.2026'))
  await act(async () => document.querySelector<HTMLButtonElement>('button[type="submit"]')?.click())

  expect(onSubmit).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(date)
  expect(date.getAttribute('aria-invalid')).toBe('true')
  expect(document.body.textContent).toContain('TT.MM.JJJJ')

  await act(async () => change(date, '02.09.2026'))
  await act(async () => document.querySelector<HTMLButtonElement>('button[type="submit"]')?.click())
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ date: '2026-09-02' }))
})
