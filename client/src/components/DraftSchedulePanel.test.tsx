import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DraftSchedulePanel, GenerationConstraintEditor } from './DraftSchedulePanel'
import {
  draftScheduleFixture,
  emptyDraftScheduleFixture,
  generationConstraintsFixture,
  secondDraftScheduleFixture,
} from '../test/draftScheduleFixtures'
import type { GenerationConstraints } from '../api/draftSchedule'

function renderPanel({
  schedules = [draftScheduleFixture],
}: {
  schedules?: typeof draftScheduleFixture[]
} = {}): Root {
  const root = createRoot(document.body.appendChild(document.createElement('div')))

  act(() => {
    root.render(
      <DraftSchedulePanel
        schedules={schedules}
      />,
    )
  })

  return root
}

function renderConstraintEditor({
  constraints = generationConstraintsFixture,
  onConstraintsChange = vi.fn(),
  onClear = vi.fn(),
}: {
  constraints?: GenerationConstraints
  onConstraintsChange?: (constraints: GenerationConstraints) => void
  onClear?: () => void
} = {}): Root {
  const root = createRoot(document.body.appendChild(document.createElement('div')))

  act(() => {
    root.render(
      <GenerationConstraintEditor
        constraints={constraints}
        isLoading={false}
        onChange={onConstraintsChange}
        onClear={onClear}
      />,
    )
  })

  return root
}

afterEach(() => {
  document.body.innerHTML = ''
})

function setInputValue(input: HTMLInputElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

function setSelectValue(select: HTMLSelectElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(select, value)
  select.dispatchEvent(new Event('change', { bubbles: true }))
}

describe('DraftSchedulePanel', () => {
  it('renders generated sessions chronologically with planning context', () => {
    renderPanel()

    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]

    expect(document.body.textContent).toContain('Courses overview')
    expect(rows).toHaveLength(2)
    expect(rows[0].textContent).toContain('2026-09-07')
    expect(rows[1].textContent).toContain('2026-09-14')
    expect(document.body.textContent).toContain('Planning 101')
    expect(document.body.textContent).toContain('AI 1')
    expect(document.body.textContent).toContain('Ada Lovelace')
    expect(document.body.textContent).toContain('R1')
    expect(document.body.textContent).toContain('Full-time')
  })

  it('shows a no-schedule empty state', () => {
    renderPanel({ schedules: [] })

    expect(document.body.textContent).toContain('No generated draft schedules for this semester yet.')
  })

  it('shows a distinct empty state when a generated schedule has zero sessions', () => {
    renderPanel({ schedules: [emptyDraftScheduleFixture] })

    expect(document.body.textContent).toContain('No generated draft schedules for this semester yet.')
  })

  it('switches between list and weekly review modes', () => {
    renderPanel()

    expect(document.body.textContent).toContain('2026-09-07')

    const weeklyButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Weekly',
    )

    act(() => {
      weeklyButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('Week of 2026-09-07')
    expect(document.body.textContent).toContain('Week of 2026-09-14')

    const listButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'List',
    )

    act(() => {
      listButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector('.session-table')).not.toBeNull()
  })

  it('filters visible sessions and shows a no-results state', () => {
    renderPanel({
      schedules: [{
        ...draftScheduleFixture,
        sessions: [
          {
            ...draftScheduleFixture.sessions[0],
            cohortId: 99,
          },
        ],
      }],
    })

    const cohortFilter = document.querySelector<HTMLSelectElement>('select[name="cohortId"]')

    act(() => {
      if (cohortFilter) {
        cohortFilter.value = '1'
        cohortFilter.dispatchEvent(new Event('change', { bubbles: true }))
      }
    })

    expect(document.body.textContent).toContain('No sessions match the active filters.')

    const clearButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Clear filters',
    )

    act(() => {
      clearButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('2026-09-14')
  })

  it('builds compact overview filters from all generated plans', () => {
    renderPanel({ schedules: [draftScheduleFixture, secondDraftScheduleFixture] })

    const courseFilter = document.querySelector<HTMLSelectElement>('select[name="courseId"]')
    const cohortFilter = document.querySelector<HTMLSelectElement>('select[name="cohortId"]')

    expect(courseFilter?.textContent).toContain('Planning 101')
    expect(courseFilter?.textContent).toContain('Scheduling 201')
    expect(cohortFilter?.textContent).toContain('AI 1')
    expect(cohortFilter?.textContent).toContain('AI 2')

    act(() => {
      if (courseFilter) {
        setSelectValue(courseFilter, '2')
      }
    })

    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]
    expect(rows).toHaveLength(1)
    expect(rows[0].textContent).not.toContain('Planning 101')
    expect(rows[0].textContent).toContain('Scheduling 201')
    expect(rows[0].textContent).toContain('2026-09-21')
  })

  it('shows generation constraints separately from review filters', () => {
    renderConstraintEditor()
    renderPanel()

    const constraintSection = document.querySelector('.generation-constraints')
    const filterBar = document.querySelector('.filter-bar')

    expect(constraintSection?.textContent).toContain('Inputs for the next draft')
    expect(constraintSection?.textContent).toContain('Start date')
    expect(filterBar?.textContent).toContain('Course')
    expect(filterBar?.textContent).not.toContain('Start date')
  })

  it('emits planning period edits and generation action separately', () => {
    const onConstraintsChange = vi.fn()
    renderConstraintEditor({ onConstraintsChange })

    const startInput = document.querySelector<HTMLInputElement>('input[type="date"]')

    act(() => {
      if (startInput) {
        setInputValue(startInput, '2026-09-14')
      }
    })

    expect(onConstraintsChange).toHaveBeenCalledWith(
      expect.objectContaining({
        planningPeriod: expect.objectContaining({ startDate: '2026-09-14' }),
      }),
    )
  })

  it('adds, removes, and submits weekly teaching window edits', () => {
    const onConstraintsChange = vi.fn()
    renderConstraintEditor({ onConstraintsChange })

    const addButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Add window',
    )

    act(() => {
      addButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(onConstraintsChange).toHaveBeenLastCalledWith(
      expect.objectContaining({
        allowedTeachingWindows: expect.arrayContaining([
          expect.objectContaining({ weekday: 0, startTime: '08:00', endTime: '12:00' }),
        ]),
      }),
    )
    onConstraintsChange.mockClear()

    const weekdaySelect = document.querySelector<HTMLSelectElement>('.constraint-window-row select')

    act(() => {
      if (weekdaySelect) {
        setSelectValue(weekdaySelect, '3')
      }
    })

    expect(onConstraintsChange).toHaveBeenCalledWith(
      expect.objectContaining({
        allowedTeachingWindows: expect.arrayContaining([expect.objectContaining({ weekday: 3 })]),
      }),
    )
  })

  it('clears the full saved constraint set without changing existing draft sessions', () => {
    const onClear = vi.fn()
    renderConstraintEditor({
      constraints: {
        ...generationConstraintsFixture,
        isCustom: true,
      },
      onClear,
    })

    renderPanel()

    const clearButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Clear custom constraints',
    )

    act(() => {
      clearButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(onClear).toHaveBeenCalledOnce()
    expect(document.body.textContent).toContain('2026-09-07')
    expect(document.body.textContent).toContain('2026-09-14')
  })
})
