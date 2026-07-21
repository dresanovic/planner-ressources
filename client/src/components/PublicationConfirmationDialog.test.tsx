import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { publicationFixture } from '../test/lifecycleFixtures'
import { PublicationConfirmationDialog } from './PublicationConfirmationDialog'


afterEach(() => { document.body.innerHTML = '' })


describe('PublicationConfirmationDialog', () => {
  it('shows the first-publication consequence and every non-blocking condition', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy={false} onConfirm={vi.fn()} onCancel={vi.fn()} />))
    expect(document.body.textContent).toContain('Publish revision 1')
    expect(document.body.textContent).toContain('first publication')
    expect(document.body.textContent).toContain('2 units remain')
    expect(document.body.textContent).toContain('do not prevent publication')
  })

  it('supports cancellation, Escape, focus containment, focus return, and busy duplicate prevention', () => {
    const cancel = vi.fn()
    const confirm = vi.fn()
    const opener = document.body.appendChild(document.createElement('button'))
    opener.focus()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy={false} onConfirm={confirm} onCancel={cancel} />))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    expect(document.activeElement).toBe(dialog)
    const buttons = [...(dialog?.querySelectorAll<HTMLButtonElement>('button') ?? [])]
    buttons.at(-1)?.focus()
    act(() => buttons.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(buttons[0])
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(cancel).toHaveBeenCalledOnce()
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy onConfirm={confirm} onCancel={cancel} />))
    expect([...(dialog?.querySelectorAll('button') ?? [])].every((button) => button.disabled)).toBe(true)
    act(() => root.unmount())
    expect(document.activeElement).toBe(opener)
  })
})
