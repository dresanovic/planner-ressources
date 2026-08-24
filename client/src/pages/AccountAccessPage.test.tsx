import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { beforeEach, expect, it, vi } from 'vitest'

const redeem = vi.hoisted(() => vi.fn())
vi.mock('../api/authentication', async (original) => ({ ...(await original()), redeemAccountAccess: redeem }))
import { AccountAccessPage } from './AccountAccessPage'

beforeEach(() => { redeem.mockReset() })

it('clears password fields, never auto-signs in, and uses the generic unusable-access outcome', async () => {
  window.history.replaceState({}, '', '/account-access/'); redeem.mockRejectedValue(new Error('expired')); const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<AccountAccessPage accessCredential={'a'.repeat(43)} />))
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  const inputs = document.querySelectorAll('input')
  await act(async () => { setValue.call(inputs[0], 'sicheres passwort'); inputs[0].dispatchEvent(new Event('input', { bubbles: true })); setValue.call(inputs[1], 'sicheres passwort'); inputs[1].dispatchEvent(new Event('input', { bubbles: true })); await Promise.resolve() })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(redeem).toHaveBeenCalledOnce(); expect([...document.querySelectorAll('input')].every((input) => input.value === '')).toBe(true); expect(document.querySelector('[role="alert"]')?.textContent).toContain('Der Zugang ist nicht verfügbar'); expect(window.location.pathname).not.toBe('/')
  act(() => root.unmount())
})

it('focuses the successful redemption result', async () => {
  redeem.mockResolvedValue(undefined)
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<AccountAccessPage accessCredential={'c'.repeat(43)} onCredentialConsumed={vi.fn()} />))
  const inputs = document.querySelectorAll('input')
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  await act(async () => { for (const input of inputs) { setValue.call(input, 'sicheres passwort'); input.dispatchEvent(new Event('input', { bubbles: true })) } })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(document.activeElement).toBe(document.querySelector('[role="status"]'))
  act(() => root.unmount())
})

it('focuses the password after a confirmation mismatch', async () => {
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<AccountAccessPage accessCredential={'d'.repeat(43)} />))
  const inputs = document.querySelectorAll('input')
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  await act(async () => { setValue.call(inputs[0], 'sicheres passwort'); inputs[0].dispatchEvent(new Event('input', { bubbles: true })); setValue.call(inputs[1], 'anderes passwort'); inputs[1].dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(document.activeElement).toBe(inputs[0])
  expect(redeem).not.toHaveBeenCalled()
  act(() => root.unmount())
})

it('disposes the credential before the first redemption settles and cannot resubmit it', async () => {
  redeem.mockRejectedValue(new Error('expired'))
  const secret = 'b'.repeat(43)
  function Harness() {
    const [credential, setCredential] = useState<string | null>(secret)
    return <><output data-testid="credential-state">{credential ?? 'cleared'}</output><AccountAccessPage accessCredential={credential} onCredentialConsumed={() => setCredential(null)} /></>
  }
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<Harness />))
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  let inputs = document.querySelectorAll('input')
  await act(async () => { for (const input of inputs) { setValue.call(input, 'sicheres passwort'); input.dispatchEvent(new Event('input', { bubbles: true })) } })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(redeem).toHaveBeenCalledOnce()
  expect(document.querySelector('[data-testid="credential-state"]')?.textContent).toBe('cleared')

  inputs = document.querySelectorAll('input')
  await act(async () => { for (const input of inputs) { setValue.call(input, 'sicheres passwort'); input.dispatchEvent(new Event('input', { bubbles: true })) } })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(redeem).toHaveBeenCalledOnce()
  act(() => root.unmount())
})
