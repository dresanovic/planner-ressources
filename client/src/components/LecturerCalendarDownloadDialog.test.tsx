import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { LecturerCalendarDownloadDialog } from './LecturerCalendarDownloadDialog'

afterEach(() => {
  document.body.innerHTML = ''
})

function renderDialog({
  eventCount = 2,
  busy = false,
  error = null,
  onCancel = vi.fn(),
  onConfirm = vi.fn(),
}: {
  eventCount?: number
  busy?: boolean
  error?: string | null
  onCancel?: () => void
  onConfirm?: () => void
} = {}) {
  const opener = document.body.appendChild(document.createElement('button'))
  opener.textContent = 'Kalender herunterladen'
  opener.focus()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(
    <LecturerCalendarDownloadDialog
      eventCount={eventCount}
      busy={busy}
      error={error}
      restoreFocusTo={opener}
      onCancel={onCancel}
      onConfirm={onConfirm}
    />,
  ))
  return { root, opener, onCancel, onConfirm }
}

describe('LecturerCalendarDownloadDialog', () => {
  it.each([0, 2])('shows the complete opened count %s and re-evaluation notice', (eventCount) => {
    renderDialog({ eventCount })

    const dialog = document.querySelector('[role="dialog"]')
    expect(dialog?.getAttribute('aria-modal')).toBe('true')
    expect(dialog?.getAttribute('aria-labelledby')).toBeTruthy()
    expect(dialog?.getAttribute('aria-describedby')).toBeTruthy()
    expect(dialog?.textContent).toContain(`${eventCount}`)
    expect(dialog?.textContent).toMatch(/ungefilterten/i)
    expect(dialog?.textContent).toMatch(/erneut.*abweichen/i)
    expect(dialog?.textContent).toContain('Abbrechen')
    expect(dialog?.textContent).toContain('Download fortsetzen')
  })

  it('does not confirm on open, cancels safely, and disables duplicate confirmation while busy', () => {
    const cancel = vi.fn()
    const confirm = vi.fn()
    const first = renderDialog({ onCancel: cancel, onConfirm: confirm })

    expect(confirm).not.toHaveBeenCalled()
    expect(document.activeElement?.textContent).toBe('Abbrechen')
    act(() => {
      document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    })
    expect(cancel).toHaveBeenCalledOnce()
    act(() => first.root.unmount())
    expect(document.activeElement).toBe(first.opener)

    document.body.innerHTML = ''
    renderDialog({ busy: true, onCancel: cancel, onConfirm: confirm })
    const controls = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
    expect(controls.every((control) => control.disabled)).toBe(true)
    controls.at(-1)?.click()
    expect(confirm).not.toHaveBeenCalled()
  })

  it('states the complete static privacy and repeat-import boundary', () => {
    renderDialog()
    const text = document.querySelector('[role="dialog"]')?.textContent ?? ''

    expect(text).toMatch(/statische Momentaufnahme/i)
    expect(text).toMatch(/aktualisieren oder löschen.*nicht/i)
    expect(text).toMatch(/persönlichen Terminplan/i)
    expect(text).toMatch(/Kopieren oder teilen.*offengelegt/i)
    expect(text).toMatch(/Speichern und löschen/i)
    expect(text).toMatch(/wiederholter manueller Import.*doppelte Termine/i)
    expect(text).toMatch(/gleicht importierte Termine nicht ab/i)
    expect(text).toMatch(/entfernt sie nicht/i)
  })

  it('contains forward and reverse tab focus and never confirms from the backdrop', () => {
    const confirm = vi.fn()
    renderDialog({ onConfirm: confirm })
    const controls = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
    const first = controls[0]
    const last = controls.at(-1)!

    last.focus()
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(first)
    first.focus()
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(last)
    act(() => document.querySelector<HTMLElement>('.dialog-backdrop')?.click())
    expect(confirm).not.toHaveBeenCalled()
  })

  it('announces retryable errors and ignores Escape while busy', () => {
    const cancel = vi.fn()
    renderDialog({
      busy: true,
      error: 'Der Kalender konnte vorübergehend nicht erstellt werden.',
      onCancel: cancel,
    })

    expect(document.querySelector('[role="alert"]')?.textContent).toContain('vorübergehend')
    act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' })))
    expect(cancel).not.toHaveBeenCalled()
  })
})
