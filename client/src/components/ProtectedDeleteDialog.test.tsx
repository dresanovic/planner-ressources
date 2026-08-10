import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { ProtectedDeleteDialog } from './ProtectedDeleteDialog'

afterEach(() => { document.body.innerHTML = '' })

it('separates contextual German blockers without rendering backend messages', async () => {
  const onDelete = vi.fn()
  const onClose = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ProtectedDeleteDialog name="AI 1" usage={{ recordId: 1, revision: 2, canDelete: false, dependentRecords: [{ type: 'course', count: 1 }], savedSchedules: { type: 'draft_schedule', count: 2 }, blockers: [{ kind: 'dependent', type: 'course', count: 1, message: 'Used by a Course.' }, { kind: 'saved_schedule', type: 'draft_schedule', count: 2, message: 'Used in schedules.' }] }} onClose={onClose} onDelete={onDelete} onArchive={vi.fn()} />))
  expect(document.body.textContent).toContain('Abhängige Datensätze')
  expect(document.body.textContent).toContain('Gespeicherte Planungen')
  expect(document.body.textContent).toContain('1 abhängiger Datensatz')
  expect(document.body.textContent).toContain('2 gespeicherten Planungen')
  expect(document.body.textContent).not.toContain('Used by a Course.')
  expect(document.body.textContent).not.toContain('Used in schedules.')
  await act(async () => (Array.from(document.querySelectorAll('button')).find((button) => button.textContent === 'Abbrechen') as HTMLButtonElement).click())
  expect(onClose).toHaveBeenCalled()
  expect(onDelete).not.toHaveBeenCalled()
})

it('does not offer Archive for a record that is already inactive', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ProtectedDeleteDialog name="AI 1" usage={{ recordId: 1, revision: 2, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }} canArchive={false} onClose={vi.fn()} onDelete={vi.fn()} onArchive={vi.fn()} />))
  expect(Array.from(document.querySelectorAll('button')).some((button) => button.textContent === 'Archivieren')).toBe(false)
})

it('focuses the dialog, traps Tab, and closes on Escape', async () => {
  const onClose = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ProtectedDeleteDialog name="AI 1" usage={{ recordId: 1, revision: 2, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }} onClose={onClose} onDelete={vi.fn()} onArchive={vi.fn()} />))
  const buttons = Array.from(document.querySelectorAll<HTMLButtonElement>('button'))
  expect(document.activeElement).toBe(buttons[0])
  buttons.at(-1)?.focus()
  buttons.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }))
  expect(document.activeElement).toBe(buttons[0])
  buttons[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
  expect(onClose).toHaveBeenCalledOnce()
})
