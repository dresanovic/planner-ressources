import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  AuthenticationApiError,
  bootstrapAdministrator,
  inspectSession,
  login,
  listPlannerAccounts,
} from './authentication'
import { PLANNER_AUTH_INVALIDATED_EVENT } from './plannerFetch'

describe('authentication transport', () => {
  const fetchMock = vi.fn<typeof fetch>()
  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })
  afterEach(() => vi.unstubAllGlobals())

  it('uses a non-activity credentialed session inspection and strict current account projection', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ id: 1, loginName: 'admin', displayName: 'Admin', isAdministrator: true }), { status: 200 }))
    await expect(inspectSession()).resolves.toEqual({ id: 1, loginName: 'admin', displayName: 'Admin', isAdministrator: true })
    const init = fetchMock.mock.calls[0][1]
    expect(init?.credentials).toBe('include')
    expect(new Headers(init?.headers).has('X-Planner-Activity')).toBe(false)
  })

  it('sends secrets only in JSON bodies and never persists them', async () => {
    const storage = vi.spyOn(Storage.prototype, 'setItem')
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))
    await bootstrapAdministrator('a'.repeat(64), 'admin', 'Admin', 'sicheres passwort')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/auth/bootstrap')
    expect(fetchMock.mock.calls[0][1]?.body).toContain('sicheres passwort')
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('X-CSRF-Protection')).toBe('1')
    expect(storage).not.toHaveBeenCalled()
  })

  it('accepts only exact safe success and error keys', async () => {
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ id: 1, loginName: 'admin', displayName: 'Admin', isAdministrator: true, passwordHash: 'leak' }), { status: 200 }))
    await expect(login('admin', 'sicheres passwort')).rejects.toThrow('invalid response')
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ code: 'login_failed', message: 'Sicher', detail: 'leak' }), { status: 401 }))
    await expect(login('admin', 'falsch passwort')).rejects.toThrow('invalid response')
    fetchMock.mockResolvedValueOnce(new Response(JSON.stringify({ code: 'login_failed', message: 'Sicher' }), { status: 401 }))
    const invalidated = vi.fn()
    globalThis.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT, invalidated)
    try {
      await expect(login('admin', 'falsch passwort')).rejects.toEqual(expect.objectContaining<Partial<AuthenticationApiError>>({ status: 401, code: 'login_failed' }))
      expect(invalidated).not.toHaveBeenCalled()
    } finally {
      globalThis.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT, invalidated)
    }
  })

  it('validates the minimal account listing and marks it as deliberate activity', async () => {
    fetchMock.mockResolvedValue(new Response(JSON.stringify({ accounts: [{ id: 1, loginName: 'admin', displayName: 'Admin', accessLevel: 'administrator', state: 'active', revision: 1, createdAt: '2026-09-01T08:00:00Z', disabledAt: null, reactivatedAt: null }] }), { status: 200 }))
    await expect(listPlannerAccounts()).resolves.toHaveLength(1)
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('X-Planner-Activity')).toBe('user')
  })
})
