import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ReplacementConfirmationDialog } from './ReplacementConfirmationDialog'
import { batchPreparationFixture } from '../test/draftScheduleFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('ReplacementConfirmationDialog', () => {
  it('identifies replacement courses, warns about manual edits, and supports cancellation', () => {
    const cancel = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ReplacementConfirmationDialog preparation={batchPreparationFixture} onConfirm={vi.fn()} onCancel={cancel} />))
    expect(document.body.textContent).toContain('Planning 101')
    expect(document.body.textContent).not.toContain('Scheduling 201')
    expect(document.body.textContent).toContain('all manual session edits')
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Cancel')
    act(() => button?.click())
    expect(cancel).toHaveBeenCalledOnce()
  })
})
