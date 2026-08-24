import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'
import { AccountActionDialog } from './AccountActionDialog'

it('starts on cancel, traps focus, supports Escape, and restores the opener', async () => {
  const opener = document.createElement('button'); opener.textContent = 'open'; document.body.replaceChildren(opener, document.createElement('div')); opener.focus(); const host = document.body.lastElementChild as HTMLDivElement; const root = createRoot(host); const cancel = vi.fn()
  await act(async () => root.render(<AccountActionDialog title="Planung deaktivieren" confirmLabel="Deaktivieren" onCancel={cancel} onConfirm={vi.fn()}><p>Folge</p></AccountActionDialog>))
  const buttons = document.querySelectorAll('.account-action-dialog button'); expect(document.activeElement).toBe(buttons[0]); act(() => buttons[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true }))); expect(document.activeElement).toBe(buttons[1]); act(() => buttons[1].dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))); expect(cancel).toHaveBeenCalledOnce(); act(() => root.unmount()); expect(document.activeElement).toBe(opener)
})

it('moves focus to a trapped close action when confirmation becomes busy', async () => {
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host); const cancel = vi.fn(); const confirm = vi.fn()
  await act(async () => root.render(<AccountActionDialog title="Planung reaktivieren" confirmLabel="Reaktivieren" onCancel={cancel} onConfirm={confirm}><p>Folge</p></AccountActionDialog>))
  const initialButtons = document.querySelectorAll('.account-action-dialog button')
  ;(initialButtons[1] as HTMLButtonElement).focus()
  expect(document.activeElement).toBe(initialButtons[1])
  await act(async () => root.render(<AccountActionDialog title="Planung reaktivieren" confirmLabel="Reaktivieren" busy onCancel={cancel} onConfirm={confirm}><p>Folge</p></AccountActionDialog>))
  const dialog = document.querySelector('[role="dialog"]')!; const buttons = dialog.querySelectorAll('button')
  expect(dialog.getAttribute('aria-busy')).toBe('true'); expect(buttons[0].textContent).toBe('Dialog schließen'); expect(buttons[0].disabled).toBe(false); expect(buttons[1].disabled).toBe(true)
  expect(document.activeElement).toBe(buttons[0]); act(() => buttons[0].dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))); expect(document.activeElement).toBe(buttons[0])
  act(() => buttons[1].dispatchEvent(new MouseEvent('click', { bubbles: true })))
  expect(confirm).not.toHaveBeenCalled(); act(() => dialog.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))); expect(cancel).toHaveBeenCalledOnce(); act(() => root.unmount())
})
