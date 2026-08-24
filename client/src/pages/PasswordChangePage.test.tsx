import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ change: vi.fn() }))
vi.mock('../api/authentication', async (original) => ({ ...(await original()), changePassword: api.change }))
import { PasswordChangePage } from './PasswordChangePage'

it('clears all password fields after a failed current-password proof', async () => {
  api.change.mockRejectedValue(new Error('safe failure'))
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  act(() => root.render(<PasswordChangePage onCancel={vi.fn()} onComplete={vi.fn()} />))
  const fields = [...document.querySelectorAll<HTMLInputElement>('input')]
  act(() => { for (const [field, value] of fields.map((field, index) => [field, ['altes passwort', 'neues passwort', 'neues passwort'][index]] as const)) { const setter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!; setter.call(field, value); field.dispatchEvent(new Event('input', { bubbles: true })) } })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(api.change).toHaveBeenCalledWith('altes passwort', 'neues passwort')
  expect(fields.map((field) => field.value)).toEqual(['', '', ''])
  expect(fields[0].getAttribute('aria-describedby')).toBe('password-change-error')
  expect(document.activeElement).toBe(fields[0])
  act(() => root.unmount())
})
