import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ReplacementConfirmationDialog } from './ReplacementConfirmationDialog'
import { decisionRequiredGenerationFixture } from '../test/optimizationFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('ReplacementConfirmationDialog', () => {
  it('shows factual aggregate and per-course comparison with only the atomic actions', () => {
    const cancel = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={cancel}
      />,
    ))

    expect(document.body.textContent).toContain('Aktueller Stundenplan')
    expect(document.body.textContent).toContain('Neu erzeugter Stundenplan')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain('Databases')
    expect(document.body.textContent).toContain('16')
    expect(document.body.textContent).toContain('Aktuelle Regelverletzung: OUTSIDE_ALLOWED_WINDOW')
    expect(document.body.textContent).toContain('Geeignete Räume sind belegt.')
    expect(document.body.textContent).toContain('plannerseitig erstellter oder bearbeiteter Termine')
    expect(document.body.textContent).not.toContain('besser')
    expect(document.body.textContent).not.toContain('Optimierung bestätigen')
    const labels = [...document.querySelectorAll('button')].map((button) => button.textContent)
    expect(labels).toContain('Neu erzeugten Stundenplan übernehmen')
    expect(labels).toContain('Abbrechen')
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Abbrechen')?.click())
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('keeps a lower-unit partial candidate selectable', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={vi.fn()}
      />,
    ))
    const accept = [...document.querySelectorAll<HTMLButtonElement>('button')]
      .find((button) => button.textContent === 'Neu erzeugten Stundenplan übernehmen')
    expect(accept?.disabled).toBe(false)
  })

  it('moves focus into the modal, traps Tab, and supports Escape cancellation', () => {
    const cancel = vi.fn()
    const opener = document.body.appendChild(document.createElement('button'))
    opener.focus()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={cancel}
      />,
    ))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    const controls = [...(dialog?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(controls.at(-1))
    act(() => controls.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(controls[0])
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('keeps focus in the dialog and disables every action while acceptance is in flight', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        disabled
        onAccept={vi.fn()}
        onCancel={vi.fn()}
      />,
    ))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    expect([...document.querySelectorAll<HTMLButtonElement>('button')].every((button) => button.disabled)).toBe(true)
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(dialog)
  })
})
