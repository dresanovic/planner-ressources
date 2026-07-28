import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { DiscardChangesDialog } from './DiscardChangesDialog'

afterEach(() => { document.body.innerHTML = ''; vi.useRealTimers() })

it('keeps editing by default, treats Escape as keep, and restores deterministic focus', () => {
  vi.useFakeTimers()
  const origin = document.body.appendChild(document.createElement('button'))
  origin.textContent = 'Origin'
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  const onKeepEditing = vi.fn()
  act(() => root.render(<DiscardChangesDialog destinationLabel="Academic Data" restoreFocusTo={origin} onKeepEditing={onKeepEditing} onDiscard={vi.fn()} />))
  expect((document.activeElement as HTMLElement)?.textContent).toBe('Keep editing')
  act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
  expect(onKeepEditing).toHaveBeenCalledOnce()
  expect(document.activeElement).not.toBe(origin)
  act(() => vi.runAllTimers())
  expect(document.activeElement).toBe(origin)
})

it('requires an explicit destructive discard action', () => {
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  const onDiscard = vi.fn()
  act(() => root.render(<DiscardChangesDialog destinationLabel="another session" onKeepEditing={vi.fn()} onDiscard={onDiscard} />))
  const discard = [...host.querySelectorAll('button')].find((button) => button.textContent === 'Discard changes')!
  act(() => discard.click())
  expect(onDiscard).toHaveBeenCalledOnce()
})

it('restores Keep editing focus only after the pane is no longer inert', () => {
  vi.useFakeTimers()
  function Harness() {
    const [decisionOpen, setDecisionOpen] = useState(true)
    const [paneFocusTarget, setPaneFocusTarget] = useState<HTMLButtonElement | null>(null)
    return (
      <>
        <button ref={setPaneFocusTarget} data-pane-focus inert={decisionOpen || undefined}>Pane field</button>
        {decisionOpen && paneFocusTarget && (
          <DiscardChangesDialog
            destinationLabel="the calendar"
            restoreFocusTo={paneFocusTarget}
            onKeepEditing={() => setDecisionOpen(false)}
            onDiscard={vi.fn()}
          />
        )}
      </>
    )
  }
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(<Harness />))
  const paneField = host.querySelector<HTMLButtonElement>('[data-pane-focus]')!

  act(() => [...host.querySelectorAll<HTMLButtonElement>('button')]
    .find((button) => button.textContent === 'Keep editing')?.click())

  expect(paneField.hasAttribute('inert')).toBe(false)
  expect(document.activeElement).not.toBe(paneField)
  act(() => vi.runAllTimers())
  expect(document.activeElement).toBe(paneField)
  vi.useRealTimers()
})
