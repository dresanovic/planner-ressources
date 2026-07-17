import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { BatchResultSummary } from './BatchResultSummary'
import { mixedOptimizationResultFixture } from '../test/optimizationFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('BatchResultSummary', () => {
  it('shows all outcome counts, progress, reasons, proof scope, and retry action', () => {
    const retry = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<BatchResultSummary result={mixedOptimizationResultFixture} onRetryFailed={retry} />))
    expect(document.body.textContent).toContain('1 complete · 1 improved partial · 1 unchanged · 1 failed · 1 stale')
    expect(document.body.textContent).toContain('ROOM OCCUPIED')
    expect(document.body.textContent).toContain('Eligible rooms are occupied.')
    expect(document.body.textContent).toContain('Proven optimal for the prepared snapshot')
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Retry failed or stale courses')
    act(() => button?.click())
    expect(retry).toHaveBeenCalledOnce()
  })

  it('does not claim optimality when preparation became stale before solving', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const result = {
      ...mixedOptimizationResultFixture,
      summary: { ...mixedOptimizationResultFixture.summary, optimalForPreparedSnapshot: false as const },
    }

    act(() => root.render(<BatchResultSummary result={result} onRetryFailed={() => undefined} />))

    expect(document.body.textContent).toContain('No optimality proof was produced')
    expect(document.body.textContent).not.toContain('Proven optimal for the prepared snapshot')
  })
})
