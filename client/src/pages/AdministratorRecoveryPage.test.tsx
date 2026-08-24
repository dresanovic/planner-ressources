import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { beforeEach, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ recover: vi.fn() }))
vi.mock('../api/authentication', async (original) => ({ ...(await original()), recoverAdministrator: api.recover }))
import { AdministratorRecoveryPage } from './AdministratorRecoveryPage'

beforeEach(() => { api.recover.mockReset() })

it('uses no account selector, clears secrets, and requires normal login after recovery', async () => {
  api.recover.mockResolvedValue(undefined)
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  act(() => root.render(<AdministratorRecoveryPage />))
  expect(document.body.textContent).not.toContain('Benutzername')
  const fields = [...document.querySelectorAll<HTMLInputElement>('input')]
  expect(fields[0].type).toBe('password')
  act(() => { ['a'.repeat(64), 'neues passwort', 'neues passwort'].forEach((value, index) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(fields[index], value); fields[index].dispatchEvent(new Event('input', { bubbles: true })) }) })
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(api.recover).toHaveBeenCalledWith('a'.repeat(64), 'neues passwort')
  expect(document.body.textContent).toContain('Melden Sie sich jetzt an')
  expect(document.activeElement).toBe(document.querySelector('[role="status"]'))
  expect(document.querySelector('form')).toBeNull()
  expect(document.querySelector('a')?.getAttribute('href')).toBe('/login/')
  act(() => root.unmount())
})

it('clears the startup credential and passwords after a confirmation mismatch', async () => {
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  act(() => root.render(<AdministratorRecoveryPage />))
  const fields = [...document.querySelectorAll<HTMLInputElement>('input')]
  const values = ['a'.repeat(64), 'neues passwort', 'anderes passwort']
  const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  act(() => fields.forEach((field, index) => { setValue.call(field, values[index]); field.dispatchEvent(new Event('input', { bubbles: true })) }))
  await act(async () => { document.querySelector('form')!.dispatchEvent(new SubmitEvent('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(fields.map((field) => field.value)).toEqual(['', '', ''])
  expect(document.activeElement).toBe(fields[0])
  expect(api.recover).not.toHaveBeenCalled()
  act(() => root.unmount())
})
