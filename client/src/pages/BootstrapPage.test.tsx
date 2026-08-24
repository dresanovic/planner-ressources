import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { beforeEach, expect, it, vi } from 'vitest'

const bootstrap = vi.hoisted(() => vi.fn())
vi.mock('../api/authentication', async (original) => ({ ...(await original()), bootstrapAdministrator: bootstrap }))
import { BootstrapPage } from './BootstrapPage'

beforeEach(() => { bootstrap.mockReset() })

it('does not sign in automatically after bootstrap', async () => {
  bootstrap.mockResolvedValue(undefined); const complete = vi.fn(); const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<BootstrapPage onComplete={complete} />))
  const values = ['a'.repeat(64), 'admin', 'Administration', 'sicheres passwort', 'sicheres passwort']
  document.querySelectorAll('input').forEach((input, index) => { input.value = values[index]; input.dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(bootstrap).toHaveBeenCalledOnce(); expect(complete).toHaveBeenCalledOnce(); expect(document.cookie).toBe('')
  act(() => root.unmount())
})

it('clears every secret field and focuses the password after a confirmation mismatch', async () => {
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<BootstrapPage onComplete={vi.fn()} />))
  const fields = [...document.querySelectorAll<HTMLInputElement>('input')]
  const values = ['a'.repeat(64), 'admin', 'Administration', 'sicheres passwort', 'anderes passwort']
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  await act(async () => { fields.forEach((field, index) => { setValue.call(field, values[index]); field.dispatchEvent(new Event('input', { bubbles: true })) }) })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(fields[0].value).toBe('')
  expect(fields.slice(3).map((field) => field.value)).toEqual(['', ''])
  expect(document.activeElement).toBe(fields[3])
  expect(bootstrap).not.toHaveBeenCalled()
  act(() => root.unmount())
})
