import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  advancePlannerAuthGeneration,
  PLANNER_AUTH_INVALIDATED_EVENT,
  plannerFetch,
} from './plannerFetch'


describe('plannerFetch', () => {
  const fetchMock = vi.fn<typeof fetch>()

  beforeEach(() => {
    fetchMock.mockReset()
    vi.stubGlobal('fetch', fetchMock)
  })

  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('includes the browser session and marks only explicit user activity', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }))

    await plannerFetch('/api/planning-options', { activity: 'user' })
    await plannerFetch('/api/auth/session')

    expect(fetchMock).toHaveBeenNthCalledWith(
      1,
      '/api/planning-options',
      expect.objectContaining({
        credentials: 'include',
        headers: expect.any(Headers),
      }),
    )
    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('X-Planner-Activity')).toBe('user')
    expect(new Headers(fetchMock.mock.calls[1][1]?.headers).has('X-Planner-Activity')).toBe(false)
  })

  it.each(['POST', 'PUT', 'PATCH', 'DELETE'])('adds CSRF protection to unsafe %s requests', async (method) => {
    fetchMock.mockResolvedValue(new Response(null, { status: 204 }))

    await plannerFetch('/api/protected', { method })

    expect(new Headers(fetchMock.mock.calls[0][1]?.headers).get('X-CSRF-Protection')).toBe('1')
  })

  it('preserves caller headers without adding CSRF to safe requests', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 200 }))

    await plannerFetch('/api/protected', { headers: { Accept: 'application/json' } })

    const headers = new Headers(fetchMock.mock.calls[0][1]?.headers)
    expect(headers.get('Accept')).toBe('application/json')
    expect(headers.has('X-CSRF-Protection')).toBe(false)
  })

  it('emits exactly one invalidation signal for a 401 and never retries a mutation', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 401 }))
    const listener = vi.fn()
    globalThis.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)

    try {
      const response = await plannerFetch('/api/protected', {
        method: 'POST',
        body: JSON.stringify({ revision: 3 }),
        activity: 'user',
      })

      expect(response.status).toBe(401)
      expect(fetchMock).toHaveBeenCalledTimes(1)
      expect(listener).toHaveBeenCalledTimes(1)
    } finally {
      globalThis.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)
    }
  })

  it('does not invalidate planner authentication for an expected public 401', async () => {
    fetchMock.mockResolvedValue(new Response('{}', { status: 401 }))
    const listener = vi.fn()
    globalThis.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)

    try {
      const response = await plannerFetch('/api/auth/login', {
        method: 'POST',
        invalidateOn401: false,
      })

      expect(response.status).toBe(401)
      expect(listener).not.toHaveBeenCalled()
    } finally {
      globalThis.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)
    }
  })

  it('ignores a delayed 401 from an older authentication generation', async () => {
    let resolveResponse!: (response: Response) => void
    fetchMock.mockReturnValue(new Promise((resolve) => { resolveResponse = resolve }))
    const listener = vi.fn()
    globalThis.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)

    try {
      const oldRequest = plannerFetch('/api/protected')
      advancePlannerAuthGeneration()
      resolveResponse(new Response('{}', { status: 401 }))

      expect((await oldRequest).status).toBe(401)
      expect(listener).not.toHaveBeenCalled()
    } finally {
      globalThis.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT, listener)
    }
  })

  it('does not persist request, credential, or response material in browser storage', async () => {
    const localSet = vi.spyOn(Storage.prototype, 'setItem')
    fetchMock.mockResolvedValue(new Response('{"secret":"not-for-storage"}', { status: 200 }))

    await plannerFetch('/api/auth/login', {
      method: 'POST',
      body: '{"password":"not-for-storage"}',
    })

    expect(localSet).not.toHaveBeenCalled()
  })
})
