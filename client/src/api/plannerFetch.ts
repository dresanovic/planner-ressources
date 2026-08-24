export const PLANNER_AUTH_INVALIDATED_EVENT = 'planner-auth-invalidated'

let authenticationGeneration = 0

export function advancePlannerAuthGeneration(): void {
  authenticationGeneration += 1
}

export type PlannerFetchOptions = RequestInit & {
  activity?: 'user'
  invalidateOn401?: boolean
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''
const SAFE_METHODS = new Set(['GET', 'HEAD', 'OPTIONS'])


export async function plannerFetch(
  path: RequestInfo | URL,
  options: PlannerFetchOptions = {},
): Promise<Response> {
  const requestGeneration = authenticationGeneration
  const { activity, invalidateOn401 = true, ...requestOptions } = options
  const method = (requestOptions.method ?? 'GET').toUpperCase()
  const headers = new Headers(requestOptions.headers)

  if (!SAFE_METHODS.has(method)) {
    headers.set('X-CSRF-Protection', '1')
    if (!headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  }
  if (activity === 'user') {
    headers.set('X-Planner-Activity', 'user')
  }

  const target = typeof path === 'string' && path.startsWith('/') ? `${API_BASE}${path}` : path
  const response = await fetch(target, {
    ...requestOptions,
    method,
    headers,
    credentials: 'include',
  })
  if (invalidateOn401 && response.status === 401 && requestGeneration === authenticationGeneration) {
    globalThis.dispatchEvent(new Event(PLANNER_AUTH_INVALIDATED_EVENT))
  }
  return response
}
