import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { ProtectedDeleteDialog } from './ProtectedDeleteDialog'

afterEach(() => { document.body.innerHTML = '' })

it('separates blockers and cancel does not delete', async () => {
  const onDelete = vi.fn()
  const onClose = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ProtectedDeleteDialog name="AI 1" usage={{ recordId: 1, revision: 2, canDelete: false, dependentRecords: [{ type: 'course', count: 1 }], savedSchedules: { type: 'draft_schedule', count: 2 }, blockers: [{ kind: 'dependent', type: 'course', count: 1, message: 'Used by a Course.' }, { kind: 'saved_schedule', type: 'draft_schedule', count: 2, message: 'Used in schedules.' }] }} onClose={onClose} onDelete={onDelete} onArchive={vi.fn()} />))
  expect(document.body.textContent).toContain('Dependent records')
  expect(document.body.textContent).toContain('Saved schedules')
  await act(async () => (Array.from(document.querySelectorAll('button')).find((button) => button.textContent === 'Cancel') as HTMLButtonElement).click())
  expect(onClose).toHaveBeenCalled()
  expect(onDelete).not.toHaveBeenCalled()
})

it('does not offer Archive for a record that is already inactive', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ProtectedDeleteDialog name="AI 1" usage={{ recordId: 1, revision: 2, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }} canArchive={false} onClose={vi.fn()} onDelete={vi.fn()} onArchive={vi.fn()} />))
  expect(Array.from(document.querySelectorAll('button')).some((button) => button.textContent === 'Archive')).toBe(false)
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
