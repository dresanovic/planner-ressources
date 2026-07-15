import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'

import { AcademicRecordEditor } from './AcademicRecordEditor'
import { AcademicCatalogApiError } from '../api/academicCatalog'

it('retains controlled values and renders required course relationships', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockRejectedValue(new Error('invalid'))
  await act(async () => root.render(<AcademicRecordEditor category="courses" options={{ semesters: [{ id: 1, name: 'Fall' }], cohorts: [{ id: 2, name: 'AI 1' }], studyTypes: [{ id: 3, name: 'Full-time' }], lecturers: [{ id: 4, name: 'Ada' }], rooms: [{ id: 5, name: 'R1' }] }} onSubmit={onSubmit} />))
  const name = document.querySelector<HTMLInputElement>('input[name="name"]')!
  act(() => { name.value = 'Scheduling 101'; name.dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(name.value).toBe('Scheduling 101')
  expect(document.body.textContent).toContain('Semester')
  expect(document.body.textContent).toContain('Lecturer')
  expect(document.body.textContent).toContain('Room')
})

it('blocks Course creation with actionable feedback when read-only resources are unavailable', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<AcademicRecordEditor category="courses" options={{ semesters: [{ id: 1, name: 'Fall' }], cohorts: [{ id: 2, name: 'AI 1' }], studyTypes: [{ id: 3, name: 'Full-time' }], lecturers: [], rooms: [] }} onSubmit={vi.fn()} />))
  expect(document.body.textContent).toContain('No Lecturer records are available')
  expect(document.body.textContent).toContain('No Room records are available')
  expect(document.querySelector<HTMLButtonElement>('button[type="submit"]')?.disabled).toBe(true)
})

it('shows every structured correction returned by catalog validation', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockRejectedValue(new AcademicCatalogApiError(422, [
    { code: 'VALIDATION_ERROR', message: 'Total units must be positive.', field: 'totalUnits' },
    { code: 'REQUIRED_RELATIONSHIP_INVALID', message: 'Semester does not exist.', field: 'semesterId' },
  ]))
  await act(async () => root.render(<AcademicRecordEditor category="semesters" onSubmit={onSubmit} />))
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(document.body.textContent).toContain('Total units must be positive.')
  expect(document.body.textContent).toContain('Semester does not exist.')
})

it('uses weekday names and derives chronological order without exposing Sort order', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  await act(async () => root.render(<AcademicRecordEditor
    category="time-windows"
    options={{ studyTypes: [{ id: 3, name: 'Part-time' }] }}
    initialValues={{ studyTypeId: 3, weekday: 4, startTime: '18:00', endTime: '22:00', sortOrder: 99 }}
    onSubmit={onSubmit}
  />))

  const weekday = document.querySelector<HTMLSelectElement>('select[name="weekday"]')!
  expect(Array.from(weekday.options).map((option) => option.textContent)).toEqual([
    'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday',
  ])
  expect(weekday.value).toBe('4')
  expect(document.querySelector('[name="sortOrder"]')).toBeNull()

  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ weekday: 4, sortOrder: 6840 }))
})
