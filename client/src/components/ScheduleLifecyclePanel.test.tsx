import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { lifecycleOverviewFixture } from '../test/lifecycleFixtures'
import { ScheduleLifecyclePanel } from './ScheduleLifecyclePanel'


afterEach(() => { document.body.innerHTML = '' })


describe('ScheduleLifecyclePanel', () => {
  it('offers an explicit Start Draft action when no lifecycle revision exists', () => {
    const startDraft = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const empty = { ...lifecycleOverviewFixture(), activeWorkingRevision: null, revisions: [], allowedActions: { createWorkingRevision: true } }
    act(() => root.render(<ScheduleLifecyclePanel overview={empty} selectedRevisionId={null} busy={false} onStartDraft={startDraft} onSelectRevision={vi.fn()} onPreparePublication={vi.fn()} onTransition={vi.fn()} onAbandon={vi.fn()} />))
    expect(document.querySelector('[aria-label="Schedule publication lifecycle"]')).not.toBeNull()
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Start Draft')
    act(() => button?.click())
    expect(startDraft).toHaveBeenCalledOnce()
    expect(document.body.textContent).not.toContain('Publish revision')
  })

  it('distinguishes active working from current publication using visible text', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const fixture = lifecycleOverviewFixture()
    const published = { ...fixture.activeWorkingRevision!, revisionId: 10, revisionNumber: 0, state: 'published' as const, isActiveWorking: false, isCurrentPublication: true, publishedAt: '2026-07-19T10:00:00Z', allowedActions: { markReady: false, returnToDraft: false, preparePublication: false, abandon: false, restore: false, editSchedule: false } }
    const overview = { ...fixture, currentPublication: published, revisions: [fixture.activeWorkingRevision!, published] }
    act(() => root.render(<ScheduleLifecyclePanel overview={overview} selectedRevisionId={11} busy={false} onStartDraft={vi.fn()} onSelectRevision={vi.fn()} onPreparePublication={vi.fn()} onTransition={vi.fn()} onAbandon={vi.fn()} />))
    expect(document.body.textContent).toContain('Active working revision')
    expect(document.body.textContent).toContain('Current publication')
    expect(document.body.textContent).toContain('Draft')
    expect(document.body.textContent).toContain('Published')
  })

  it('renders Ready and restore actions plus machine-readable Vienna history', () => {
    const fixture = lifecycleOverviewFixture()
    const transition = vi.fn()
    const ready = { ...fixture.activeWorkingRevision!, state: 'ready_for_review' as const, allowedActions: { ...fixture.activeWorkingRevision!.allowedActions, markReady: false, returnToDraft: true } }
    const overview = { ...fixture, activeWorkingRevision: ready, revisions: [ready] }
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<ScheduleLifecyclePanel overview={overview} selectedRevisionId={ready.revisionId} busy={false} onStartDraft={vi.fn()} onSelectRevision={vi.fn()} onPreparePublication={vi.fn()} onTransition={transition} onAbandon={vi.fn()} />))
    expect(document.body.textContent).toContain('Ready for review')
    expect(document.body.textContent).toContain('Return to Draft')
    const timestamp = document.querySelector('time')
    expect(timestamp?.dateTime).toBe('2026-07-20T10:00:00Z')
    expect(timestamp?.textContent).toContain('Europe/Vienna')
  })
})
