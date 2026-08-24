import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'
import { OneTimeAccessResult } from './OneTimeAccessResult'

it('keeps the one-time secret in transient component state and announces copy without reading it', async () => {
  const writeText = vi.fn().mockResolvedValue(undefined); Object.defineProperty(navigator, 'clipboard', { configurable: true, value: { writeText } })
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host); const close = vi.fn(); const secret = 'z'.repeat(43)
  await act(async () => root.render(<OneTimeAccessResult access={{ credential: secret, purpose: 'setup', expiresAt: '2026-09-02T08:00:00Z' }} onClose={close} />))
  expect((document.querySelector('input') as HTMLInputElement).value).toContain(`#/${secret}`)
  await act(async () => { [...document.querySelectorAll('button')].find((button) => button.textContent === 'Link kopieren')!.click(); await Promise.resolve() })
  expect(writeText).toHaveBeenCalledOnce(); expect(document.querySelector('[role="status"]')?.textContent).not.toContain(secret)
  act(() => [...document.querySelectorAll('button')].find((button) => button.textContent === 'Schließen')!.click()); expect(close).toHaveBeenCalledOnce(); act(() => root.unmount())
})
