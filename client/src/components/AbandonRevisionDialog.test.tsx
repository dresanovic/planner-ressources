import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { lifecycleOverviewFixture } from '../test/lifecycleFixtures'
import { AbandonRevisionDialog } from './AbandonRevisionDialog'

afterEach(() => { document.body.innerHTML = '' })
it('identifies the revision, preserves publication, traps focus, handles Escape, and returns focus', () => {
  const overview = lifecycleOverviewFixture()
  const cancel = vi.fn()
  const opener = document.body.appendChild(document.createElement('button'))
  opener.focus()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(<AbandonRevisionDialog semesterName={overview.semesterName} revision={overview.activeWorkingRevision!} currentPublication={null} busy={false} onCancel={cancel} onConfirm={vi.fn()} />))
  expect(document.body.textContent).toContain('Abandon revision 1?')
  expect(document.body.textContent).toContain('no current publication')
  const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
  const buttons = [...(dialog?.querySelectorAll<HTMLButtonElement>('button') ?? [])]
  expect(document.activeElement).toBe(buttons[0])
  buttons.at(-1)?.focus()
  act(() => buttons.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
  expect(document.activeElement).toBe(buttons[0])
  act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
  expect(cancel).toHaveBeenCalledOnce()
  act(() => root.unmount())
  expect(document.activeElement).toBe(opener)
})
