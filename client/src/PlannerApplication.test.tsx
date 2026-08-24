import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const auth = vi.hoisted(() => ({ inspectSession: vi.fn(), login: vi.fn(), logout: vi.fn() }))
vi.mock('./api/authentication', async (original) => ({ ...(await original()), inspectSession: auth.inspectSession, login: auth.login, logout: auth.logout }))
vi.mock('./App', () => ({ default: ({ currentAccount, onLogout }: { currentAccount: { displayName: string }; onLogout: () => void }) => <main data-testid="protected-shell">{currentAccount.displayName}<button type="button" onClick={onLogout}>Abmelden</button></main> }))

import PlannerApplication from './PlannerApplication'
import { PLANNER_AUTH_INVALIDATED_EVENT } from './api/plannerFetch'

describe('PlannerApplication authentication gate', () => {
  let host: HTMLDivElement; let root: Root
  beforeEach(() => { vi.clearAllMocks(); window.history.replaceState({}, '', '/'); host = document.createElement('div'); document.body.replaceChildren(host); root = createRoot(host) })
  afterEach(() => { act(() => root.unmount()) })

  it('does not mount protected planner content until session inspection succeeds', async () => {
    let resolve!: (value: unknown) => void
    auth.inspectSession.mockReturnValue(new Promise((done) => { resolve = done }))
    await act(async () => { root.render(<PlannerApplication />); await Promise.resolve() })
    expect(document.querySelector('[data-testid="protected-shell"]')).toBeNull()
    expect(document.body.textContent).toContain('Sitzung wird geprüft')
    await act(async () => { resolve({ id: 1, loginName: 'admin', displayName: 'Administration', isAdministrator: true }); await Promise.resolve() })
    expect(document.querySelector('[data-testid="protected-shell"]')?.textContent).toContain('Administration')
  })

  it('removes protected content immediately after a protected 401 signal', async () => {
    auth.inspectSession.mockResolvedValue({ id: 1, loginName: 'planner', displayName: 'Planung', isAdministrator: false })
    await act(async () => { root.render(<PlannerApplication />); await Promise.resolve() })
    expect(document.querySelector('[data-testid="protected-shell"]')).not.toBeNull()
    document.querySelector<HTMLButtonElement>('[data-testid="protected-shell"] button')!.focus()
    act(() => globalThis.dispatchEvent(new Event(PLANNER_AUTH_INVALIDATED_EVENT)))
    expect(document.querySelector('[data-testid="protected-shell"]')).toBeNull()
    expect(document.body.textContent).toContain('Ihre Sitzung ist beendet')
    expect(document.activeElement).toBe(document.querySelector('[role="alert"]'))
    expect(window.location.pathname).toBe('/login/')
  })

  it('renders exact standalone auth routes without inspecting a session', async () => {
    await act(async () => { root.render(<PlannerApplication initialPath="/bootstrap/" />); await Promise.resolve() })
    expect(document.body.textContent).toContain('Erste Systemadministration einrichten')
    expect(auth.inspectSession).not.toHaveBeenCalled()
  })

  it('removes protected data immediately but requires retry when logout is unconfirmed', async () => {
    auth.inspectSession.mockResolvedValue({ id: 1, loginName: 'planner', displayName: 'Planung', isAdministrator: false })
    let rejectLogout!: (reason: unknown) => void
    auth.logout.mockReturnValueOnce(new Promise((_resolve, reject) => { rejectLogout = reject }))
    await act(async () => { root.render(<PlannerApplication />); await Promise.resolve() })

    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Abmelden')!.dispatchEvent(new MouseEvent('click', { bubbles: true })))
    expect(document.querySelector('[data-testid="protected-shell"]')).toBeNull()
    expect(document.body.textContent).toContain('Abmeldung wird bestätigt')

    await act(async () => { rejectLogout(new TypeError('network unavailable')); await Promise.resolve() })
    expect(document.querySelector('[role="alert"]')?.textContent).toContain('konnte nicht bestätigt werden')
    auth.logout.mockResolvedValueOnce(undefined)
    await act(async () => { [...document.querySelectorAll('button')].find((item) => item.textContent === 'Abmeldung erneut versuchen')!.dispatchEvent(new MouseEvent('click', { bubbles: true })); await Promise.resolve() })
    expect(auth.logout).toHaveBeenCalledTimes(2)
    expect(document.body.textContent).toContain('Anmelden')
  })
})
