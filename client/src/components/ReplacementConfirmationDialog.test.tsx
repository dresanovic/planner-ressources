import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ReplacementConfirmationDialog } from './ReplacementConfirmationDialog'
import { optimizationPreparationFixture } from '../test/optimizationFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('ReplacementConfirmationDialog', () => {
  it('identifies affected courses, explains protection, and supports cancellation', () => {
    const cancel = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ReplacementConfirmationDialog preparation={optimizationPreparationFixture} onConfirm={vi.fn()} onCancel={cancel} />))
    expect(document.body.textContent).toContain('Databases')
    expect(document.body.textContent).not.toContain('Algorithms')
    expect(document.body.textContent).toContain('manual session edits')
    expect(document.body.textContent).toContain('units do not decrease')
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Cancel')
    act(() => button?.click())
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('moves focus into the modal and supports Escape cancellation', () => {
    const cancel = vi.fn()
    const opener = document.body.appendChild(document.createElement('button'))
    opener.focus()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ReplacementConfirmationDialog preparation={optimizationPreparationFixture} onConfirm={vi.fn()} onCancel={cancel} />))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('contains reverse and forward tab navigation from the initial dialog focus', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ReplacementConfirmationDialog preparation={optimizationPreparationFixture} onConfirm={vi.fn()} onCancel={vi.fn()} />))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    const controls = [...(dialog?.querySelectorAll<HTMLButtonElement>('button') ?? [])]
    expect(document.activeElement).toBe(dialog)

    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(controls[1])

    act(() => controls[1]?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(controls[0])
  })

  it('keeps focus in the dialog while its controls are disabled', () => {
    const onConfirm = vi.fn()
    const onCancel = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preparation={optimizationPreparationFixture}
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    ))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    const confirmButton = [...document.querySelectorAll<HTMLButtonElement>('button')]
      .find((button) => button.textContent === 'Confirm optimization')
    act(() => confirmButton?.focus())
    expect(document.activeElement).toBe(confirmButton)

    act(() => root.render(
      <ReplacementConfirmationDialog
        preparation={optimizationPreparationFixture}
        disabled
        onConfirm={onConfirm}
        onCancel={onCancel}
      />,
    ))
    expect(document.activeElement).toBe(dialog)

    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(dialog)
  })
})
