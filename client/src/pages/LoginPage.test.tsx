import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'

const login = vi.hoisted(() => vi.fn())
vi.mock('../api/authentication', async (original) => ({ ...(await original()), login }))
import { LoginPage } from './LoginPage'

it('uses labelled German fields and clears only the password after generic failure', async () => {
  login.mockRejectedValue(new Error('secret backend reason'))
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => root.render(<LoginPage onAuthenticated={vi.fn()} />))
  const inputs = document.querySelectorAll('input'); const user = inputs[0]; const password = inputs[1]
  expect(password.minLength).toBe(-1)
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  await act(async () => { setValue.call(user, 'Planer'); user.dispatchEvent(new Event('input', { bubbles: true })); setValue.call(password, 'falsches passwort'); password.dispatchEvent(new Event('input', { bubbles: true })); await Promise.resolve() })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(document.querySelectorAll('input')[0].value).toBe('Planer'); expect(document.querySelectorAll('input')[1].value).toBe(''); expect(document.querySelector('[role="alert"]')?.textContent).toContain('Die Anmeldung war nicht möglich')
  act(() => root.unmount())
})
