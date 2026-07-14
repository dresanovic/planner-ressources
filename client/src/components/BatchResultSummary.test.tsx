import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { BatchResultSummary } from './BatchResultSummary'
import { batchResultFixture } from '../test/draftScheduleFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('BatchResultSummary', () => {
  it('shows aggregate counts, every failure reason, and failed-only retry action', () => {
    const retry = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<BatchResultSummary result={batchResultFixture} onRetryFailed={retry} />))
    expect(document.body.textContent).toContain('1 succeeded · 1 failed · 2 total')
    expect(document.body.textContent).toContain('INSUFFICIENT ROOM CAPACITY')
    expect(document.body.textContent).toContain('Room is too small.')
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Retry failed courses')
    act(() => button?.click())
    expect(retry).toHaveBeenCalledOnce()
  })
})
