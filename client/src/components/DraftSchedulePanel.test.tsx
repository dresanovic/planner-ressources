import { act } from 'react'
import { createRoot, type Root } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { DraftSchedulePanel, GenerationConstraintEditor } from './DraftSchedulePanel'
import {
  alertDraftScheduleFixture,
  draftScheduleFixture,
  emptyDraftScheduleFixture,
  generationConstraintsFixture,
  roomOptionsFixture,
  secondDraftScheduleFixture,
} from '../test/draftScheduleFixtures'
import type { DraftSchedule, GenerationConstraints, UpdateDraftSessionRequest } from '../api/draftSchedule'
import type { PlanningOptions } from '../api/planningOptions'

function renderPanel({
  schedules = [draftScheduleFixture],
  onUpdateSession = vi.fn(),
  onDeleteSession = vi.fn(),
  courseResources = [],
  isBusy = false,
}: {
  schedules?: DraftSchedule[]
  onUpdateSession?: (sessionId: number, payload: UpdateDraftSessionRequest) => Promise<void>
  onDeleteSession?: (session: DraftSchedule['sessions'][number], schedule: DraftSchedule) => void
  courseResources?: PlanningOptions['courseResources']
  isBusy?: boolean
} = {}): Root {
  const root = createRoot(document.body.appendChild(document.createElement('div')))

  act(() => {
    root.render(
      <DraftSchedulePanel
        schedules={schedules}
        rooms={roomOptionsFixture}
        courseResources={courseResources}
        onUpdateSession={onUpdateSession}
        onDeleteSession={onDeleteSession}
        isBusy={isBusy}
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

function buttonByText(label: string) {
  return [...document.querySelectorAll('button')].find((button) => button.textContent === label)
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

    expect(document.body.textContent).toContain('No Draft Schedules for this semester yet.')
  })

  it('shows a distinct empty state when a generated schedule has zero sessions', () => {
    renderPanel({ schedules: [emptyDraftScheduleFixture] })

    expect(document.body.textContent).toContain('No Draft Schedules for this semester yet.')
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

  it('offers exact-session Delete actions in list and weekly modes', () => {
    const onDeleteSession = vi.fn()
    renderPanel({ onDeleteSession })
    const listDeletes = [...document.querySelectorAll('button')].filter((item) => item.textContent === 'Delete')
    expect(listDeletes).toHaveLength(2)
    act(() => listDeletes[0].click())
    expect(onDeleteSession).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), expect.objectContaining({ draftScheduleId: 1 }))

    const weekly = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Weekly')!
    act(() => weekly.click())
    const weeklyDeletes = [...document.querySelectorAll('button')].filter((item) => item.textContent === 'Delete')
    expect(weeklyDeletes).toHaveLength(2)
  })

  it('disables edit entry and an already-open edit save while the overview is stale', () => {
    const onUpdateSession = vi.fn().mockResolvedValue(undefined)
    const root = renderPanel({ onUpdateSession })
    const edit = [...document.querySelectorAll<HTMLButtonElement>('button')].find((item) => item.textContent === 'Edit')!
    act(() => edit.click())
    expect((buttonByText('Save') as HTMLButtonElement).disabled).toBe(false)

    act(() => {
      root.render(
        <DraftSchedulePanel
          schedules={[draftScheduleFixture]}
          rooms={roomOptionsFixture}
          onUpdateSession={onUpdateSession}
          isBusy
        />,
      )
    })

    expect((buttonByText('Save') as HTMLButtonElement).disabled).toBe(true)
    const remainingEdits = [...document.querySelectorAll<HTMLButtonElement>('button')].filter((item) => item.textContent === 'Edit')
    expect(remainingEdits.every((item) => item.disabled)).toBe(true)
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

  it('opens manual edit controls and cancels without saving', () => {
    const onUpdateSession = vi.fn()
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Edit')

    act(() => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector<HTMLInputElement>('input[type="date"]')?.value).toBe('2026-09-07')
    expect(document.body.textContent).toContain('3 h 30 min')

    const cancelButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Cancel')

    act(() => {
      cancelButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector<HTMLInputElement>('input[type="date"]')).toBeNull()
    expect(onUpdateSession).not.toHaveBeenCalled()
  })

  it('submits date, start, end, and room edits', async () => {
    const onUpdateSession = vi.fn().mockResolvedValue(undefined)
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Edit')

    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const dateInput = document.querySelector<HTMLInputElement>('input[type="date"]')
    const timeInputs = [...document.querySelectorAll<HTMLInputElement>('input[type="time"]')]
    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')

    act(() => {
      if (dateInput) {
        setInputValue(dateInput, '2026-12-14')
      }
      if (timeInputs[0]) {
        setInputValue(timeInputs[0], '09:00')
      }
      if (timeInputs[1]) {
        setInputValue(timeInputs[1], '10:30')
      }
      if (roomSelect) {
        setSelectValue(roomSelect, '3')
      }
    })

    const saveButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Save')

    await act(async () => {
      saveButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(onUpdateSession).toHaveBeenCalledWith(1, {
      date: '2026-12-14',
      startTime: '09:00',
      endTime: '10:30',
      lecturerId: 1,
      roomId: 3,
    })
  })

  it('limits room choices to rooms with enough capacity', async () => {
    renderPanel()

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Edit')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')
    const optionLabels = [...(roomSelect?.options ?? [])].map((option) => option.textContent)

    expect(optionLabels).toContain('R1 (40 seats)')
    expect(optionLabels).toContain('Auditorium (80 seats)')
    expect(optionLabels).not.toContain('Tiny (20 seats)')
  })

  it('keeps the current ineligible room selected while offering eligible alternatives', async () => {
    const currentSession = {
      ...draftScheduleFixture.sessions[1],
      roomId: 4,
      roomName: 'Tiny',
      roomReferenceCode: 'ROOM-004',
      room: { id: 4, name: 'Tiny', referenceCode: 'ROOM-004' },
      validationAlerts: [{ code: 'ROOM_INELIGIBLE' as const, message: 'Assigned Room is outside the current eligibility set.', relatedSessions: [] }],
    }
    renderPanel({
      schedules: [{ ...draftScheduleFixture, sessions: [currentSession] }],
      courseResources: [{
        courseId: 1,
        eligibleLecturers: [],
        eligibleRooms: [{ id: 1, name: 'R1', referenceCode: 'ROOM-001', kind: 'room', capacity: 40, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
      }],
    })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Edit')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')
    const optionLabels = [...(roomSelect?.options ?? [])].map((option) => option.textContent)

    expect(roomSelect?.value).toBe('4')
    expect(optionLabels).toContain('Tiny (20 seats)')
    expect(optionLabels.some((label) => label?.includes('R1') && label.includes('ROOM-001') && label.includes('40 seats'))).toBe(true)
    expect(optionLabels).not.toContain('R2')
    expect(optionLabels).not.toContain('Auditorium')
  })

  it('shows edit failures without falsely saving', async () => {
    const onUpdateSession = vi.fn().mockRejectedValue([
      { code: 'INSUFFICIENT_ROOM_CAPACITY', message: 'Room capacity is too low.' },
    ])
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Edit')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const saveButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Save')
    await act(async () => {
      saveButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('Room capacity is too low.')
    expect(document.querySelector<HTMLInputElement>('input[type="date"]')).not.toBeNull()
  })

  it('uses edited room values for display and filters', () => {
    renderPanel({
      schedules: [
        {
          ...draftScheduleFixture,
          sessions: [
            {
              ...draftScheduleFixture.sessions[1],
              roomId: 3,
            },
          ],
        },
      ],
    })

    expect(document.body.textContent).toContain('Auditorium')

    const roomFilter = document.querySelector<HTMLSelectElement>('select[name="roomId"]')
    expect(roomFilter?.textContent).toContain('Auditorium')

    act(() => {
      if (roomFilter) {
        setSelectValue(roomFilter, '3')
      }
    })

    expect(document.body.textContent).toContain('2026-09-07')
  })

  it('shows list-mode alert reasons and related session details within two interactions', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    const alert = document.querySelector<HTMLDetailsElement>('.validation-alert')
    const summary = alert?.querySelector('summary')

    expect(summary?.textContent).toContain('LECTURER OVERLAP')
    expect(summary?.textContent).toContain('Lecturer overlaps with 1 session.')
    expect(alert?.open).toBe(false)

    act(() => {
      summary?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(alert?.open).toBe(true)
    expect(alert?.textContent).toContain('Scheduling 201')
    expect(alert?.textContent).toContain('2026-09-07 09:00-12:30')
  })

  it('keeps overlap alerts visible when filters hide related sessions', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture, secondDraftScheduleFixture] })

    const courseFilter = document.querySelector<HTMLSelectElement>('select[name="courseId"]')
    act(() => {
      if (courseFilter) {
        setSelectValue(courseFilter, '1')
      }
    })

    expect(document.body.textContent).toContain('LECTURER OVERLAP')
    expect(document.body.textContent).toContain('Scheduling 201')
    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]
    expect(rows.every((row) => row.textContent?.includes('Planning 101'))).toBe(true)
  })

  it('shows multiple validation alert reasons on one session', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    expect(document.body.textContent).toContain('ROOM CAPACITY')
    expect(document.body.textContent).toContain('STUDY TYPE WINDOW VIOLATION')
  })

  it('updates visible alert state after session update changes schedules', () => {
    const { rerender } = renderPanelWithRoot({ schedules: [draftScheduleFixture] })

    expect(document.body.textContent).not.toContain('LECTURER OVERLAP')

    act(() => {
      rerender([alertDraftScheduleFixture])
    })

    expect(document.body.textContent).toContain('LECTURER OVERLAP')

    act(() => {
      rerender([draftScheduleFixture])
    })

    expect(document.body.textContent).not.toContain('LECTURER OVERLAP')
  })

  it('shows validation alerts in weekly mode', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    const weeklyButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Weekly',
    )

    act(() => {
      weeklyButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector('.weekly-review')).not.toBeNull()
    expect(document.body.textContent).toContain('LECTURER OVERLAP')
  })

  it('renders a non-blocking named holiday alert only inside the affected session', () => {
    const holidaySchedule = {
      ...draftScheduleFixture,
      sessions: draftScheduleFixture.sessions.map((session, index) => index === 0 ? {
        ...session,
        validationAlerts: [{
          code: 'INSTITUTION_HOLIDAY' as const,
          message: 'Founders Day on 2026-09-07 is an institution holiday.',
          relatedSessions: [],
          holidayDate: '2026-09-07',
          holidayName: 'Founders Day',
        }],
      } : session),
    }
    renderPanel({ schedules: [holidaySchedule] })

    expect(document.body.textContent).toContain('Founders Day on 2026-09-07')
    expect(document.querySelectorAll('.validation-alert')).toHaveLength(1)
    expect(document.body.textContent).not.toContain('Holiday calendar entry')

    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Weekly')?.click())
    expect(document.querySelector('.weekly-review')?.textContent).toContain('Founders Day on 2026-09-07')
  })

  it('externally resets active overview filters while preserving schedules and alerts', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <DraftSchedulePanel resetKey={0} schedules={[alertDraftScheduleFixture, secondDraftScheduleFixture]} rooms={roomOptionsFixture} />,
    ))
    const courseFilter = document.querySelector<HTMLSelectElement>('select[name="courseId"]')
    act(() => { if (courseFilter) setSelectValue(courseFilter, '1') })
    expect(document.querySelectorAll('.session-row:not(.session-header)')).toHaveLength(2)

    act(() => root.render(
      <DraftSchedulePanel resetKey={1} schedules={[alertDraftScheduleFixture, secondDraftScheduleFixture]} rooms={roomOptionsFixture} />,
    ))
    expect(document.querySelectorAll('.session-row:not(.session-header)')).toHaveLength(3)
    expect(document.body.textContent).toContain('LECTURER OVERLAP')
  })
})

function renderPanelWithRoot({ schedules }: { schedules: DraftSchedule[] }) {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onUpdateSession = vi.fn()

  function rerender(nextSchedules: DraftSchedule[]) {
    root.render(
      <DraftSchedulePanel
        schedules={nextSchedules}
        rooms={roomOptionsFixture}
        onUpdateSession={onUpdateSession}
      />,
    )
  }

  act(() => {
    rerender(schedules)
  })

  return { root, rerender }
}
