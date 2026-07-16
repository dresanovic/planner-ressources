import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { ScheduleDeletionDialog } from './ScheduleDeletionDialog'

afterEach(() => { document.body.innerHTML = '' })

function renderDialog(overrides: Partial<Parameters<typeof ScheduleDeletionDialog>[0]> = {}) {
  const trigger = document.body.appendChild(document.createElement('button'))
  trigger.textContent = 'Delete session'
  trigger.focus()
  const onCancel = vi.fn()
  const onConfirm = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(
    <ScheduleDeletionDialog
      scope={{
        kind: 'session', courseName: 'Planning 101', semesterName: 'Fall', date: '2026-09-07',
        startTime: '08:00', endTime: '09:45', unitsRemoved: 2, resultingRemainingUnits: 6, lastSession: false,
      }}
      isBusy={false}
      onCancel={onCancel}
      onConfirm={onConfirm}
      {...overrides}
    />,
  ))
  return { root, trigger, onCancel, onConfirm }
}

it('labels the modal and presents the exact single-session consequence', () => {
  renderDialog()
  const dialog = document.querySelector('[role="dialog"]')
  expect(dialog?.getAttribute('aria-modal')).toBe('true')
  expect(dialog?.getAttribute('aria-labelledby')).toBeTruthy()
  expect(dialog?.textContent).toContain('Planning 101')
  expect(dialog?.textContent).toContain('2026-09-07')
  expect(dialog?.textContent).toContain('2 units')
  expect(dialog?.textContent).toContain('6 units remaining')
})

it('moves focus inside, traps Tab, supports Escape, and restores focus', () => {
  const { root, trigger, onCancel } = renderDialog()
  const buttons = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
  expect(document.activeElement).toBe(buttons[0])
  buttons.at(-1)?.focus()
  buttons.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true, cancelable: true }))
  expect(document.activeElement).toBe(buttons[0])
  buttons[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
  expect(onCancel).toHaveBeenCalledOnce()
  act(() => root.unmount())
  expect(document.activeElement).toBe(trigger)
})

it('disables both controls while the destructive action is busy', () => {
  renderDialog({ isBusy: true })
  const buttons = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
  expect(buttons.every((button) => button.disabled)).toBe(true)
})

it('explains when deleting the selected session also removes the empty parent', () => {
  renderDialog({
    scope: {
      kind: 'session', courseName: 'Planning 101', semesterName: 'Fall', date: '2026-09-07',
      startTime: '08:00', endTime: '09:45', unitsRemoved: 2, resultingRemainingUnits: 8, lastSession: true,
    },
  })
  expect(document.body.textContent).toContain('last session')
  expect(document.body.textContent).toContain('empty Draft Schedule')
})

it('identifies complete course-draft scope and preserved records', () => {
  renderDialog({
    scope: {
      kind: 'courseDraft', courseName: 'Planning 101', semesterName: 'Fall',
      sessionCount: 3, unitsRemoved: 8, resultingRemainingUnits: 12,
    },
  })
  expect(document.body.textContent).toContain('Clear this course Draft Schedule?')
  expect(document.body.textContent).toContain('3 sessions')
  expect(document.body.textContent).toContain('8 scheduled units will be removed')
  expect(document.body.textContent).toContain('12 units remaining')
  expect(document.body.textContent).toContain('saved generation constraints will be preserved')
  expect(document.body.textContent).toContain('Clear course draft')
})
