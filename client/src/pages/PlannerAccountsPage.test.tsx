import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { beforeEach, expect, it, vi } from 'vitest'

const api = vi.hoisted(() => ({ list: vi.fn(), create: vi.fn(), disable: vi.fn(), inspect: vi.fn(), reactivate: vi.fn(), transfer: vi.fn() }))
vi.mock('../api/authentication', async (original) => ({ ...(await original()), listPlannerAccounts: api.list, createPlannerAccount: api.create, disablePlannerAccount: api.disable, inspectSession: api.inspect, issueReactivationAccess: api.reactivate, transferAdministration: api.transfer }))
import { AuthenticationApiError } from '../api/authentication'
import { PlannerAccountsPage } from './PlannerAccountsPage'

beforeEach(() => vi.clearAllMocks())

it('shows only the approved lifecycle projection and hides self-managed administrator actions', async () => {
  api.list.mockResolvedValue([{ id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 1, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null }]); const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: true }} />); await Promise.resolve() })
  expect(document.body.textContent).toContain('Planer-Konten'); expect(document.body.textContent).toContain('Systemadministration'); expect(document.body.textContent).toContain('Aktiv'); expect(document.body.textContent).not.toContain('Zugang zurücksetzen'); expect(document.body.textContent).not.toContain('Passwort-Hash'); expect(document.body.textContent).not.toContain('Sitzung')
  act(() => root.unmount())
})

it('transfers only to another active planner and immediately reports lost authority', async () => {
  api.list.mockResolvedValue([
    { id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 4, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null },
    { id: 2, loginName: 'planer', displayName: 'Planung', accessLevel: 'planner', state: 'active', revision: 7, createdAt: '2026-09-01T09:00:00Z', disabledAt: null, reactivatedAt: null },
    { id: 3, loginName: 'inaktiv', displayName: 'Inaktiv', accessLevel: 'planner', state: 'inactive', revision: 2, createdAt: '2026-09-01T10:00:00Z', disabledAt: '2026-09-02T10:00:00Z', reactivatedAt: null },
  ])
  const former = { id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: false }
  api.transfer.mockResolvedValue(former)
  const changed = vi.fn(); const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ ...former, isAdministrator: true }} onCurrentAccountChange={changed} />); await Promise.resolve() })
  const transferButtons = [...document.querySelectorAll('button')].filter((item) => item.textContent === 'Administration übertragen')
  expect(transferButtons).toHaveLength(1)
  act(() => transferButtons[0].dispatchEvent(new MouseEvent('click', { bubbles: true })))
  const dialog = document.querySelector('[role="dialog"]')!
  expect(dialog.textContent).toContain('Sie bleiben als Planer angemeldet')
  const confirm = [...dialog.querySelectorAll('button')].find((item) => item.textContent === 'Administration übertragen')!
  await act(async () => { confirm.dispatchEvent(new MouseEvent('click', { bubbles: true })); await Promise.resolve() })
  expect(api.transfer).toHaveBeenCalledWith(2, 7, 4)
  expect(changed).toHaveBeenCalledWith(former)
  act(() => root.unmount())
})

it('submits a confirmed account action only once while its request is pending', async () => {
  const accounts = [
    { id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 4, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null },
    { id: 2, loginName: 'planer', displayName: 'Planung', accessLevel: 'planner', state: 'inactive', revision: 7, createdAt: '2026-09-01T09:00:00Z', disabledAt: '2026-09-02T10:00:00Z', reactivatedAt: null },
  ] as const
  api.list.mockResolvedValue(accounts)
  let resolve!: (value: unknown) => void
  api.reactivate.mockReturnValue(new Promise((done) => { resolve = done }))
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: true }} />); await Promise.resolve() })
  const open = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Reaktivieren')!
  act(() => open.dispatchEvent(new MouseEvent('click', { bubbles: true })))
  const confirm = [...document.querySelectorAll('[role="dialog"] button')].find((item) => item.textContent === 'Reaktivieren')!
  act(() => {
    confirm.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    confirm.dispatchEvent(new MouseEvent('click', { bubbles: true }))
  })
  expect(api.reactivate).toHaveBeenCalledTimes(1)
  await act(async () => {
    resolve({ account: accounts[1], oneTimeAccess: { credential: 'x'.repeat(43), purpose: 'reactivation', expiresAt: '2026-09-03T10:00:00Z' } })
    await Promise.resolve()
  })
  act(() => root.unmount())
})

it('removes account authority after a 403 and refreshes safe session metadata', async () => {
  const accounts = [
    { id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 4, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null },
    { id: 2, loginName: 'planer', displayName: 'Planung', accessLevel: 'planner', state: 'inactive', revision: 7, createdAt: '2026-09-01T09:00:00Z', disabledAt: '2026-09-02T10:00:00Z', reactivatedAt: null },
  ] as const
  const former = { id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: false }
  api.list.mockResolvedValue(accounts)
  api.reactivate.mockRejectedValue(new AuthenticationApiError(403, 'administrator_required', 'Nur Administration'))
  api.inspect.mockResolvedValue(former)
  const changed = vi.fn(); const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ ...former, isAdministrator: true }} onCurrentAccountChange={changed} />); await Promise.resolve() })
  act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Reaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })))
  await act(async () => { [...document.querySelectorAll('[role="dialog"] button')].find((item) => item.textContent === 'Reaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })); await Promise.resolve() })
  expect(api.inspect).toHaveBeenCalledOnce()
  expect(changed).toHaveBeenCalledWith(former)
  expect(document.querySelector('.account-list')?.textContent).not.toContain('Planung')
  act(() => root.unmount())
})

it('refreshes the account list after a stale revision response', async () => {
  const administrator = { id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 4, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null } as const
  const inactive = { id: 2, loginName: 'planer', displayName: 'Planung', accessLevel: 'planner', state: 'inactive', revision: 7, createdAt: '2026-09-01T09:00:00Z', disabledAt: '2026-09-02T10:00:00Z', reactivatedAt: null } as const
  const active = { ...inactive, state: 'active' as const, revision: 8, reactivatedAt: '2026-09-03T10:00:00Z' }
  api.list.mockResolvedValueOnce([administrator, inactive]).mockResolvedValueOnce([administrator, active])
  api.reactivate.mockRejectedValue(new AuthenticationApiError(409, 'stale_account', 'Veraltet'))
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: true }} />); await Promise.resolve() })
  act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Reaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })))
  await act(async () => { [...document.querySelectorAll('[role="dialog"] button')].find((item) => item.textContent === 'Reaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })); await Promise.resolve(); await Promise.resolve() })
  expect(api.list).toHaveBeenCalledTimes(2)
  expect(document.querySelector('[role="alert"]')?.textContent).toContain('aktualisiert')
  expect([...document.querySelectorAll('button')].some((item) => item.textContent === 'Zugang zurücksetzen')).toBe(true)
  act(() => root.unmount())
})

it('clears a displayed one-time link when another account action begins', async () => {
  const administrator = { id: 1, loginName: 'admin', displayName: 'Administration', accessLevel: 'administrator', state: 'active', revision: 4, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null } as const
  const planner = { id: 2, loginName: 'planer', displayName: 'Planung', accessLevel: 'planner', state: 'active', revision: 7, createdAt: '2026-09-01T09:00:00Z', disabledAt: null, reactivatedAt: null } as const
  const access = { credential: 'x'.repeat(43), purpose: 'setup' as const, expiresAt: '2026-09-03T10:00:00Z' }
  api.list.mockResolvedValue([administrator, planner])
  api.create.mockResolvedValue({ account: planner, oneTimeAccess: access })
  let finishDisable!: () => void
  api.disable.mockReturnValue(new Promise((resolve) => { finishDisable = () => resolve(planner) }))
  const host = document.createElement('div'); document.body.replaceChildren(host); const root = createRoot(host)
  await act(async () => { root.render(<PlannerAccountsPage currentAccount={{ id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: true }} />); await Promise.resolve() })
  const fields = document.querySelectorAll('.account-create input'); const setValue = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!
  act(() => { setValue.call(fields[0], 'neu'); fields[0].dispatchEvent(new Event('input', { bubbles: true })); setValue.call(fields[1], 'Neue Planung'); fields[1].dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => { document.querySelector('.account-create')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })); await Promise.resolve() })
  expect(document.querySelector('.one-time-access input')).not.toBeNull()
  act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Deaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })))
  act(() => [...document.querySelectorAll('[role="dialog"] button')].find((item) => item.textContent === 'Deaktivieren')!.dispatchEvent(new MouseEvent('click', { bubbles: true })))
  expect(document.querySelector('.one-time-access')).toBeNull()
  await act(async () => { finishDisable(); await Promise.resolve() })
  act(() => root.unmount())
})
