import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { loadedCalendarWorkspaceFixture } from '../test/calendarWorkspaceFixtures'
import { SessionPane } from './SessionPane'

afterEach(() => { document.body.innerHTML = ''; Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true }) })

it('shows complete teaching detail and reaches editing in the second intentional action', () => {
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences.find((item) => item.kind === 'teaching')!
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  const onEdit = vi.fn()
  act(() => root.render(<SessionPane occurrence={occurrence} workspace={workspace} mode="detail" onRequestClose={vi.fn()} onRequestEdit={onEdit} />))
  expect(host.textContent).toContain('Teaching session')
  expect(host.textContent).toContain('Teaching units')
  const edit = [...host.querySelectorAll('button')].find((button) => button.textContent === 'Edit session')!
  act(() => edit.click())
  expect(onEdit).toHaveBeenCalledOnce()
})

it('keeps the actionable details for every warning kind', () => {
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences.find((item) => item.kind === 'teaching')!
  occurrence.findingRefs = ['finding:capacity:1'] as never
  workspace.validationFindings = [{
    findingRef: 'finding:capacity:1',
    category: 'room_capacity',
    validationBasis: 'current',
    affectedCourseRefs: [occurrence.courseRef],
    affectedOccurrenceRefs: [occurrence.occurrenceRef],
    details: {
      kind: 'capacity',
      occurrenceRef: occurrence.occurrenceRef,
      requiredCapacity: 30,
      roomRef: occurrence.roomRef,
      roomName: 'Room Alpha',
      currentCapacity: 20,
    },
  }] as never
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(
    <SessionPane
      occurrence={occurrence}
      workspace={workspace}
      mode="detail"
      onRequestClose={vi.fn()}
    />,
  ))
  expect(host.textContent).toContain('Room Alpha capacity 20; 30 required')
})

it('uses the restricted safe-field branch with feedback actions only', () => {
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences.find(
    (item) => item.kind === 'exam',
  )!
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)

  act(() =>
    root.render(
      <SessionPane
        occurrence={occurrence}
        workspace={workspace}
        mode="detail"
        onRequestClose={vi.fn()}
        onRequestEdit={vi.fn()}
        onRequestDelete={vi.fn()}
        restrictedReview={{
          lecturerName: 'Dr Ada Lecturer',
          revisionLabel: 'Working R2',
          lifecycleState: 'ready_for_review',
          roomName: 'Auditorium B',
          validationAvailability: 'complete',
          validationMessages: ['This exam needs review.'],
          feedbackActions: <button type="button">Send feedback</button>,
        }}
      />,
    ),
  )

  expect(host.textContent).toContain('Dr Ada Lecturer')
  expect(host.textContent).toContain('Working R2')
  expect(host.textContent).toContain('Ready for review')
  expect(host.textContent).toContain('C-001')
  expect(host.textContent).toContain('Auditorium B')
  expect(host.textContent).toContain('This exam needs review.')
  expect(host.textContent).toContain('Send feedback')
  expect(host.textContent).not.toContain('Edit session')
  expect(host.textContent).not.toContain('Delete')
  expect(host.textContent).not.toContain('Configuration')
  expect(host.textContent).not.toContain('Capacity')
})

it.each([
  ['partial' as const, 'Validation is incomplete; a complete no-issue result is not available.'],
  ['unavailable' as const, 'Current validation is unavailable.'],
])('does not describe empty %s validation as warning-free', (validationAvailability, message) => {
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences[0]
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)

  act(() => root.render(
    <SessionPane
      occurrence={occurrence}
      workspace={workspace}
      mode="detail"
      onRequestClose={vi.fn()}
      restrictedReview={{
        lecturerName: 'Dr Ada Lecturer',
        revisionLabel: 'Working R2',
        lifecycleState: 'ready_for_review',
        roomName: 'Room A-101',
        validationAvailability,
        validationMessages: [],
        feedbackActions: null,
      }}
    />,
  ))

  expect(host.textContent).toContain(message)
  expect(host.textContent).not.toContain('No current warnings.')
})

it('composes either domain editor, reports status, and closes cleanly with Escape', () => {
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences.find((item) => item.kind === 'exam')!
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  const onClose = vi.fn()
  act(() => root.render(<SessionPane occurrence={occurrence} workspace={workspace} mode="editing" editor={<label>Exam correction<input /></label>} status="Placement saved." error="Refresh failed." onRequestClose={onClose} />))
  expect(host.textContent).toContain('Exam correction')
  expect(host.querySelector('[role=status]')?.textContent).toContain('Placement saved.')
  expect(host.querySelector('[role=alert]')?.textContent).toContain('Refresh failed.')
  act(() => document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
  expect(onClose).toHaveBeenCalledOnce()
})

it('becomes a focus-contained full-screen dialog at 820px or below', () => {
  Object.defineProperty(window, 'innerWidth', { value: 820, configurable: true })
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences[0]
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(<><button data-background-control>Background</button><SessionPane occurrence={occurrence} workspace={workspace} mode="detail" onRequestClose={vi.fn()} /></>))
  const pane = host.querySelector('[role=dialog]')
  expect(pane?.getAttribute('aria-modal')).toBe('true')
  expect(host.querySelector<HTMLElement>('[data-background-control]')?.inert).toBe(true)
  const buttons = pane!.querySelectorAll('button')
  act(() => { buttons[buttons.length - 1].focus(); document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })) })
  expect(pane?.contains(document.activeElement)).toBe(true)
})

it('exposes only the discard decision as modal and keeps it operable across a narrow resize', () => {
  Object.defineProperty(window, 'innerWidth', { value: 1024, configurable: true })
  const workspace = loadedCalendarWorkspaceFixture()
  const occurrence = workspace.occurrences[0]
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(
    <>
      <SessionPane occurrence={occurrence} workspace={workspace} mode="editing" decisionOpen editor={<input />} onRequestClose={vi.fn()} />
      <div className="dialog-backdrop">
        <div className="discard-changes-dialog" role="dialog" aria-modal="true">
          <button type="button">Keep editing</button>
          <button type="button">Discard changes</button>
        </div>
      </div>
    </>,
  ))

  act(() => {
    Object.defineProperty(window, 'innerWidth', { value: 820, configurable: true })
    window.dispatchEvent(new Event('resize'))
  })

  const pane = host.querySelector<HTMLElement>('.session-pane')!
  const decision = host.querySelector<HTMLElement>('.discard-changes-dialog')!
  expect(pane.hasAttribute('inert')).toBe(true)
  expect(pane.getAttribute('aria-hidden')).toBe('true')
  expect(pane.getAttribute('aria-modal')).toBeNull()
  expect(decision.closest<HTMLElement>('.dialog-backdrop')?.hasAttribute('inert')).toBe(false)
  expect(document.querySelectorAll('[aria-modal="true"]')).toHaveLength(1)
  expect(decision.querySelector<HTMLButtonElement>('button')?.disabled).toBe(false)
})
