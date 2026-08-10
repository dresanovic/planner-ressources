import { act } from 'react'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  LECTURER_REVIEW_SECRET_CANARY,
  lecturerReviewFeedbackResultFixture,
  publicLecturerReviewFixture,
} from './test/lecturerReviewFixtures'
import {
  getPublicLecturerReview,
  submitPublicLecturerFeedback,
} from './api/lecturerReview'
import { terminologyDefaults } from './test/terminologyDefaults'

const probes = vi.hoisted(() => ({
  plannerModuleLoads: 0,
  publicModuleLoads: 0,
}))

vi.mock('./App.tsx', () => {
  probes.plannerModuleLoads += 1
  return {
    default: function PlannerProbe() {
      return <div data-testid="planner-probe">Planner application</div>
    },
  }
})

vi.mock('./pages/LecturerReviewPage.tsx', () => {
  probes.publicModuleLoads += 1
  return {
    LecturerReviewPage: ({ secret }: { secret: string | null }) => (
      <main
        data-testid="public-review-probe"
        data-secret={secret ?? 'none'}
        data-hash-at-render={window.location.hash}
      >
        Public lecturer review
      </main>
    ),
  }
})

async function bootstrap(path: string) {
  vi.resetModules()
  window.history.replaceState({}, '', path)
  document.body.innerHTML = '<div id="root"></div>'
  const terminologyFetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
    new Response(JSON.stringify({ labels: terminologyDefaults }), { status: 200 }),
  )
  await act(async () => {
    await import('./main')
    await Promise.resolve()
  })
  return terminologyFetch
}

describe('client bootstrap lecturer-review boundary', () => {
  beforeEach(() => {
    vi.restoreAllMocks()
    localStorage.clear()
    sessionStorage.clear()
  })

  it('removes the secret from every address and persistence surface while preserving the exact public path', async () => {
    const localWrite = vi.spyOn(Storage.prototype, 'setItem')
    const replaceState = vi.spyOn(window.history, 'replaceState')
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {})

    const terminologyFetch = await bootstrap(
      `/lecturer-review/?language=en#/${LECTURER_REVIEW_SECRET_CANARY}`,
    )

    const publicPage = document.querySelector<HTMLElement>(
      '[data-testid="public-review-probe"]',
    )
    expect(publicPage?.dataset.secret).toBe(LECTURER_REVIEW_SECRET_CANARY)
    expect(publicPage?.dataset.hashAtRender).toBe('')
    expect(window.location.pathname).toBe('/lecturer-review/')
    expect(window.location.search).toBe('?language=en')
    expect(window.location.hash).toBe('')
    expect(window.location.href).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(replaceState).toHaveBeenLastCalledWith(
      window.history.state,
      '',
      '/lecturer-review/?language=en',
    )
    expect(JSON.stringify(window.history.state)).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(probes.publicModuleLoads).toBe(1)
    expect(probes.plannerModuleLoads).toBe(0)
    expect(document.querySelector('[data-testid="planner-probe"]')).toBeNull()
    expect(localWrite).not.toHaveBeenCalled()
    expect(localStorage.length).toBe(0)
    expect(sessionStorage.length).toBe(0)
    expect(JSON.stringify(consoleError.mock.calls)).not.toContain(
      LECTURER_REVIEW_SECRET_CANARY,
    )
    expect(terminologyFetch).toHaveBeenCalledOnce()
    expect(terminologyFetch.mock.calls[0][0]).toBe('/api/public/ui-terminology')
    expect(terminologyFetch.mock.calls[0][1]).toEqual(expect.objectContaining({ credentials: 'omit' }))
    expect(replaceState.mock.invocationCallOrder[0]).toBeLessThan(terminologyFetch.mock.invocationCallOrder[0])
  })

  it('keeps malformed credentials on the isolated safe public surface', async () => {
    await bootstrap('/lecturer-review/#/too-short')

    expect(
      document.querySelector<HTMLElement>(
        '[data-testid="public-review-probe"]',
      )?.dataset.secret,
    ).toBe('none')
    expect(window.location.pathname).toBe('/lecturer-review/')
    expect(window.location.hash).toBe('')
    expect(probes.publicModuleLoads).toBe(1)
    expect(probes.plannerModuleLoads).toBe(0)
  })

  it('does not treat a similar planner path as the public entry point', async () => {
    const publicLoadsBefore = probes.publicModuleLoads
    await bootstrap(
      `/lecturer-reviewing/#/${LECTURER_REVIEW_SECRET_CANARY}`,
    )

    expect(document.querySelector('[data-testid="planner-probe"]')).not.toBeNull()
    expect(document.querySelector('[data-testid="public-review-probe"]')).toBeNull()
    expect(probes.plannerModuleLoads).toBe(1)
    expect(probes.publicModuleLoads).toBe(publicLoadsBefore)
  })

  it('renders fixed German bootstrap failure copy and retries only the safe catalog read', async () => {
    vi.resetModules()
    window.history.replaceState({}, '', '/')
    document.body.innerHTML = '<div id="root"></div>'
    const fetchMock = vi.spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(new Response('unavailable', { status: 503 }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ labels: terminologyDefaults }), { status: 200 }))

    await act(async () => {
      await import('./main')
      await Promise.resolve()
    })
    expect(document.body.textContent).toContain('Bezeichnungen konnten nicht geladen werden')
    expect(document.querySelector('[data-testid="planner-probe"]')).toBeNull()
    expect(fetchMock).toHaveBeenCalledOnce()

    const retry = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Erneut versuchen')!
    await act(async () => {
      retry.click()
      await Promise.resolve()
      await Promise.resolve()
    })
    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(document.querySelector('[data-testid="planner-probe"]')).not.toBeNull()
  })

  it('retries a transient application chunk failure without reinitializing the catalog', async () => {
    const { renderApplication } = await import('./main')
    document.body.innerHTML = '<div id="recovery-root"></div>'
    const root = (await import('react-dom/client')).createRoot(document.getElementById('recovery-root')!)
    const loadPlanner = vi.fn()
      .mockRejectedValueOnce(new Error('transient chunk failure'))
      .mockResolvedValueOnce({ default: () => <div data-testid="recovered-planner">Recovered</div> })
    await act(async () => { await renderApplication(root, false, null, { loadPlanner, loadLecturerReview: vi.fn() }) })
    expect(document.getElementById('recovery-root')?.textContent).toContain('Anwendung konnte nicht geladen werden')
    await act(async () => {
      ;[...document.querySelectorAll('button')].find((button) => button.textContent === 'Anwendung erneut laden')?.click()
      await Promise.resolve(); await Promise.resolve()
    })
    expect(loadPlanner).toHaveBeenCalledTimes(2)
    expect(document.querySelector('[data-testid="recovered-planner"]')).not.toBeNull()
  })

  it('uses only the two fixed relative public APIs with omitted browser credentials', async () => {
    const review = publicLecturerReviewFixture()
    const result = lecturerReviewFeedbackResultFixture()
    const fetchMock = vi
      .spyOn(globalThis, 'fetch')
      .mockResolvedValueOnce(
        new Response(JSON.stringify(review), { status: 200 }),
      )
      .mockResolvedValueOnce(
        new Response(JSON.stringify(result), { status: 201 }),
      )

    await getPublicLecturerReview(LECTURER_REVIEW_SECRET_CANARY)
    await submitPublicLecturerFeedback(
      LECTURER_REVIEW_SECRET_CANARY,
      {
        clientSubmissionId: '11111111-1111-4111-8111-111111111111',
        kind: 'revision_comment',
        comment: 'Tuesday afternoon is preferable.',
      },
    )

    expect(fetchMock).toHaveBeenCalledTimes(2)
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual([
      '/api/public/lecturer-review',
      '/api/public/lecturer-review/feedback',
    ])
    for (const [path, request] of fetchMock.mock.calls) {
      expect(path).toMatch(/^\/api\/public\/lecturer-review(?:\/feedback)?$/)
      expect(path).not.toContain(LECTURER_REVIEW_SECRET_CANARY)
      expect(path).not.toMatch(/^https?:\/\//)
      expect(request?.credentials).toBe('omit')
      expect(request?.headers).toEqual(
        expect.objectContaining({
          Authorization: `Bearer ${LECTURER_REVIEW_SECRET_CANARY}`,
        }),
      )
    }
  })
})
