import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { describe, expect, it, vi } from 'vitest'

import { DraftSchedulePanel } from './DraftSchedulePanel'
import {
  draftScheduleFixture,
  emptyDraftScheduleFixture,
} from '../test/draftScheduleFixtures'

function renderPanel(schedule: typeof draftScheduleFixture | null = draftScheduleFixture): Root {
  const root = createRoot(document.body.appendChild(document.createElement('div')))

  act(() => {
    root.render(
      <DraftSchedulePanel
        schedule={schedule}
        errors={[]}
        isLoading={false}
        onGenerate={vi.fn()}
      />,
    )
  })

  return root
}

describe('DraftSchedulePanel', () => {
  it('renders generated sessions chronologically with planning context', () => {
    renderPanel()

    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]

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
    renderPanel(null)

    expect(document.body.textContent).toContain('No generated draft schedule yet.')
  })

  it('shows a distinct empty state when a generated schedule has zero sessions', () => {
    renderPanel(emptyDraftScheduleFixture)

    expect(document.body.textContent).toContain('Generated draft schedule has no sessions.')
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
      ...draftScheduleFixture,
      sessions: [
        {
          ...draftScheduleFixture.sessions[0],
          cohortId: 99,
        },
      ],
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
})
