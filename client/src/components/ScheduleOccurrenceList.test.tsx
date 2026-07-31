import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { publicLecturerReviewFixture } from '../test/lecturerReviewFixtures'
import { adaptLecturerReviewToWorkspace } from './calendarWorkspaceUtils'
import {
  ScheduleOccurrenceList,
  ScheduleOccurrenceRow,
} from './ScheduleOccurrenceList'

afterEach(() => {
  document.body.innerHTML = ''
})

it('renders selectable teaching and exam rows in chronological order', () => {
  const workspace = adaptLecturerReviewToWorkspace(
    publicLecturerReviewFixture(),
  )
  const select = vi.fn()
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)

  act(() =>
    root.render(
      <ScheduleOccurrenceList
        workspace={workspace}
        onSelectOccurrence={select}
      />,
    ),
  )

  const rows = host.querySelectorAll<HTMLButtonElement>(
    '[data-occurrence-ref]',
  )
  expect([...rows].map((row) => row.dataset.occurrenceRef)).toEqual([
    'teaching:101',
    'exam:202',
  ])
  act(() => rows[1].click())
  expect(select).toHaveBeenCalledWith('exam:202')
  expect(rows[1].textContent).toContain('Exam')
  const list = host.querySelector('[role="list"]')!
  const listItems = list.querySelectorAll(':scope > [role="listitem"]')
  expect(listItems).toHaveLength(2)
  expect(listItems[0].querySelector('button')).toBe(rows[0])
  expect(rows[0].getAttribute('role')).toBeNull()
})

it('keeps a passive occurrence row neutral outside a list', () => {
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)

  act(() => root.render(
    <ScheduleOccurrenceRow occurrenceRef="exam:202" kind="exam">
      <span>Written exam</span>
      <button type="button">Edit</button>
    </ScheduleOccurrenceRow>,
  ))

  const row = host.querySelector('[data-schedule-occurrence-ref="exam:202"]')!
  expect(row.getAttribute('role')).toBeNull()
  expect(row.querySelector('button')?.textContent).toBe('Edit')
})

it('keeps keyboard-native button semantics and filtered empty messaging', () => {
  const workspace = adaptLecturerReviewToWorkspace(
    publicLecturerReviewFixture(),
  )
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)

  act(() =>
    root.render(
      <ScheduleOccurrenceList
        workspace={workspace}
        occurrences={[]}
        onSelectOccurrence={vi.fn()}
        emptyMessage="No sessions match these filters."
      />,
    ),
  )

  expect(host.textContent).toContain('No sessions match these filters.')
  expect(host.querySelector('[data-occurrence-ref]')).toBeNull()
})
