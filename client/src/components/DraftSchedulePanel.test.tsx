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
import type { ExamSession } from '../api/examScheduling'
import type { WorkspaceListContext } from './CalendarPlanningWorkspace'

function renderPanel({
  schedules = [draftScheduleFixture],
  onUpdateSession = vi.fn(),
  onDeleteSession = vi.fn(),
  courseResources = [],
  isBusy = false,
  exams = [],
  examCourseNames = {},
  readOnly = false,
  contextLabel,
  requestedEditSessionId,
  onRequestedEditHandled,
  workspaceListContext,
}: {
  schedules?: DraftSchedule[]
  onUpdateSession?: (sessionId: number, payload: Omit<UpdateDraftSessionRequest, 'scheduleRevisionId'>) => Promise<void>
  onDeleteSession?: (session: DraftSchedule['sessions'][number], schedule: DraftSchedule) => void
  courseResources?: PlanningOptions['courseResources']
  isBusy?: boolean
  exams?: ExamSession[]
  examCourseNames?: Record<number, string>
  readOnly?: boolean
  contextLabel?: string
  requestedEditSessionId?: number | null
  onRequestedEditHandled?: () => void
  workspaceListContext?: WorkspaceListContext | null
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
        exams={exams}
        examCourseNames={examCourseNames}
        readOnly={readOnly}
        contextLabel={contextLabel}
        requestedEditSessionId={requestedEditSessionId}
        onRequestedEditHandled={onRequestedEditHandled}
        workspaceListContext={workspaceListContext}
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
  it('opens the established inline editor when requested by the calendar', async () => {
    const onRequestedEditHandled = vi.fn()
    renderPanel({
      requestedEditSessionId: 2,
      onRequestedEditHandled,
    })

    await act(async () => {})
    expect(buttonByText('Speichern')).toBeDefined()
    expect(document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')?.value).toBe('14.09.2026')
    expect(onRequestedEditHandled).toHaveBeenCalledOnce()
  })

  it('renders immutable publication context without teaching mutation controls', () => {
    renderPanel({ readOnly: true, contextLabel: 'Current publication · Revision 1' })
    expect(document.body.textContent).toContain('Current publication · Revision 1')
    expect(buttonByText('Bearbeiten')).toBeUndefined()
    expect(buttonByText('Löschen')).toBeUndefined()
    expect(document.body.textContent).toContain('Planning 101')
  })

  it('shows retained recommendation and final-teaching context for exams', () => {
    renderPanel({ schedules: [], examCourseNames: { 1: 'Planning 101' }, exams: [{
      id: 1, revision: 1, courseId: 1, semesterId: 1, configurationIdentifier: 'Final', examType: 'Written', durationMinutes: 90, requiredCapacity: 30,
      recommendedStartDate: '2026-10-09', recommendedEndDate: '2026-10-16', recommendationWasOverridden: true, outsideRecommendedWindow: false,
      finalTeachingAnchor: { date: '2026-10-02', endTime: '12:00', teachingSessionId: 42 }, date: '2026-10-16', startTime: '09:00', endTime: '10:30',
      lecturer: { id: 1, name: 'Ada', referenceCode: 'L-1' }, cohort: { id: 1, name: 'C1', referenceCode: null }, room: { id: 1, name: 'R1', referenceCode: 'R-1', capacity: 40 },
      lifecycleStatus: 'active', source: 'manual', validityIssues: [], inputSnapshotToken: 'token',
    }] })
    expect(document.body.textContent).toContain('Empfohlener Zeitraum 09.10.2026–16.10.2026 (manuell festgelegt)')
    expect(document.body.textContent).toContain('Letzte Lehrveranstaltung 02.10.2026 um 12:00')
  })

  it('explains an outside-window exam with European dates and a truthful next action', () => {
    renderPanel({ schedules: [], examCourseNames: { 1: 'KI Grundlagen' }, exams: [{
      id: 7, revision: 1, courseId: 1, semesterId: 1, configurationIdentifier: 'Klausur', examType: 'Schriftlich', durationMinutes: 90, requiredCapacity: 30,
      recommendedStartDate: '2026-09-15', recommendedEndDate: '2026-09-30', recommendationWasOverridden: false, outsideRecommendedWindow: true,
      finalTeachingAnchor: { date: '2026-09-04', endTime: '12:00', teachingSessionId: 42 }, date: '2026-09-11', startTime: '18:00', endTime: '19:30',
      lecturer: { id: 1, name: 'Ada', referenceCode: 'L-1' }, cohort: { id: 1, name: 'C1', referenceCode: null }, room: { id: 1, name: 'R1', referenceCode: 'R-1', capacity: 40 },
      lifecycleStatus: 'active', source: 'manual', validityIssues: [
        { code: 'INSUFFICIENT_ROOM_CAPACITY', message: 'RAW CAPACITY FAILURE', relatedDate: '2026-09-11', relatedResource: { id: 1, name: 'R1', referenceCode: 'R-1' }, relatedSessionId: null, holidayName: null },
        { code: 'INSTITUTION_HOLIDAY', message: 'RAW HOLIDAY FAILURE', relatedDate: '2026-09-11', relatedResource: null, relatedSessionId: null, holidayName: 'Planungsfeiertag' },
      ], inputSnapshotToken: 'token',
    }] })

    const text = document.body.textContent ?? ''
    expect(text).toContain('Prüfung für „KI Grundlagen“')
    expect(text).toContain('11.09.2026')
    expect(text).toContain('15.09.2026–30.09.2026')
    expect(text).toContain('nicht blockierend')
    expect(text).toContain('bleibt gespeichert')
    expect(text).toContain('„Bearbeiten“')
    expect(text).toContain('bewusst beibehalten')
    expect(text).not.toContain('OUTSIDE_RECOMMENDED_WINDOW')
    expect(document.querySelectorAll('.actionable-problem')).toHaveLength(3)
    expect(text).toContain('R1“ hat 40 Plätze; benötigt werden 30')
    expect(text).toContain('Planungsfeiertag')
    expect(text).toContain('blockiert die Verwendung dieses Prüfungstermins')
    expect(text).not.toContain('RAW CAPACITY FAILURE')
    expect(text).not.toContain('INSUFFICIENT_ROOM_CAPACITY')
  })

  it('renders generated sessions chronologically with planning context', () => {
    renderPanel()

    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]

    expect(document.body.textContent).toContain('Lehrveranstaltungen')
    expect(rows).toHaveLength(2)
    expect(rows[0].textContent).toContain('07.09.2026')
    expect(rows[1].textContent).toContain('14.09.2026')
    expect(document.body.textContent).toContain('Planning 101')
    expect(document.body.textContent).toContain('AI 1')
    expect(document.body.textContent).toContain('Ada Lovelace')
    expect(document.body.textContent).toContain('R1')
    expect(document.body.textContent).toContain('Full-time')
  })

  it('uses the shared workspace projection and focuses an exact trace target', async () => {
    renderPanel({
      schedules: [draftScheduleFixture, secondDraftScheduleFixture],
      workspaceListContext: {
        courseIds: [2],
        teachingSessionIds: [3],
        examIds: [],
        activeFilterCount: 1,
        traceTarget: {
          reference: 'course:2',
          label: 'Scheduling 201 · 2 units remaining',
          courseIds: [2],
          teachingSessionIds: [3],
          examIds: [],
        },
      },
    })

    expect(document.body.textContent).toContain('Betroffener Datensatz')
    expect(document.body.textContent).toContain('Scheduling 201 · 2 units remaining')
    expect(document.body.textContent).not.toContain('Planning 101')
    expect(document.querySelector('[aria-label="Draft session filters"]')).toBeNull()
    await act(async () => {
      await Promise.resolve()
    })
    expect(document.activeElement).toBe(document.querySelector('[data-trace-reference="course:2"]'))
  })

  it('shows a no-schedule empty state', () => {
    renderPanel({ schedules: [] })

    expect(document.body.textContent).toContain('Für dieses Semester gibt es noch keine Planungsentwürfe.')
  })

  it('shows a distinct empty state when a generated schedule has zero sessions', () => {
    renderPanel({ schedules: [emptyDraftScheduleFixture] })

    expect(document.body.textContent).toContain('Für dieses Semester gibt es noch keine Planungsentwürfe.')
  })

  it('switches between list and weekly review modes', () => {
    renderPanel()

    expect(document.body.textContent).toContain('07.09.2026')

    const weeklyButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Woche',
    )

    act(() => {
      weeklyButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('Woche ab 07.09.2026')
    expect(document.body.textContent).toContain('Woche ab 14.09.2026')

    const listButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Liste',
    )

    act(() => {
      listButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector('.session-table')).not.toBeNull()
  })

  it('offers exact-session Delete actions in list and weekly modes', () => {
    const onDeleteSession = vi.fn()
    renderPanel({ onDeleteSession })
    const listDeletes = [...document.querySelectorAll('button')].filter((item) => item.textContent === 'Löschen')
    expect(listDeletes).toHaveLength(2)
    act(() => listDeletes[0].click())
    expect(onDeleteSession).toHaveBeenCalledWith(expect.objectContaining({ id: 1 }), expect.objectContaining({ draftScheduleId: 1 }))

    const weekly = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Woche')!
    act(() => weekly.click())
    const weeklyDeletes = [...document.querySelectorAll('button')].filter((item) => item.textContent === 'Löschen')
    expect(weeklyDeletes).toHaveLength(2)
  })

  it('disables edit entry and an already-open edit save while the overview is stale', () => {
    const onUpdateSession = vi.fn().mockResolvedValue(undefined)
    const root = renderPanel({ onUpdateSession })
    const edit = [...document.querySelectorAll<HTMLButtonElement>('button')].find((item) => item.textContent === 'Bearbeiten')!
    act(() => edit.click())
    expect((buttonByText('Speichern') as HTMLButtonElement).disabled).toBe(false)

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

    expect((buttonByText('Speichern') as HTMLButtonElement).disabled).toBe(true)
    const remainingEdits = [...document.querySelectorAll<HTMLButtonElement>('button')].filter((item) => item.textContent === 'Bearbeiten')
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

    expect(document.body.textContent).toContain('Keine Termine entsprechen den aktiven Filtern.')

    const clearButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Filter zurücksetzen',
    )

    act(() => {
      clearButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('14.09.2026')
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
    expect(rows[0].textContent).toContain('21.09.2026')
  })

  it('shows generation constraints separately from review filters', () => {
    renderConstraintEditor()
    renderPanel()

    const constraintSection = document.querySelector('.generation-constraints')
    const filterBar = document.querySelector('.filter-bar')

    expect(constraintSection?.textContent).toContain('Eingaben für den nächsten Entwurf')
    expect(constraintSection?.textContent).toContain('Beginn')
    expect(filterBar?.textContent).toContain('Lehrveranstaltung')
    expect(filterBar?.textContent).not.toContain('Beginn')
  })

  it('emits planning period edits and generation action separately', () => {
    const onConstraintsChange = vi.fn()
    renderConstraintEditor({ onConstraintsChange })

    const startInput = document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')

    act(() => {
      if (startInput) {
        setInputValue(startInput, '14.09.2026')
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
      (button) => button.textContent === 'Zeitfenster hinzufügen',
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
      (button) => button.textContent === 'Benutzerdefinierte Regeln zurücksetzen',
    )

    act(() => {
      clearButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(onClear).toHaveBeenCalledOnce()
    expect(document.body.textContent).toContain('07.09.2026')
    expect(document.body.textContent).toContain('14.09.2026')
  })

  it('opens manual edit controls and cancels without saving', () => {
    const onUpdateSession = vi.fn()
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Bearbeiten')

    act(() => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')?.value).toBe('07.09.2026')
    expect(document.body.textContent).toContain('3 h 30 min')

    const cancelButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Abbrechen')

    act(() => {
      cancelButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')).toBeNull()
    expect(onUpdateSession).not.toHaveBeenCalled()
  })

  it('submits date, start, end, and room edits', async () => {
    const onUpdateSession = vi.fn().mockResolvedValue(undefined)
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Bearbeiten')

    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const dateInput = document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')
    const timeInputs = [...document.querySelectorAll<HTMLInputElement>('input[type="time"]')]
    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')

    act(() => {
      if (dateInput) {
        setInputValue(dateInput, '14.12.2026')
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

    const saveButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Speichern')

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

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Bearbeiten')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')
    const optionLabels = [...(roomSelect?.options ?? [])].map((option) => option.textContent)

    expect(optionLabels).toContain('R1 (40 Plätze)')
    expect(optionLabels).toContain('Auditorium (80 Plätze)')
    expect(optionLabels).not.toContain('Tiny (20 Plätze)')
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

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Bearbeiten')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const roomSelect = document.querySelector<HTMLSelectElement>('.inline-edit-field select')
    const optionLabels = [...(roomSelect?.options ?? [])].map((option) => option.textContent)

    expect(roomSelect?.value).toBe('4')
    expect(optionLabels).toContain('Tiny (20 Plätze)')
    expect(optionLabels.some((label) => label?.includes('R1') && label.includes('ROOM-001') && label.includes('40 Plätze'))).toBe(true)
    expect(optionLabels).not.toContain('R2')
    expect(optionLabels).not.toContain('Auditorium')
  })

  it('shows edit failures without falsely saving', async () => {
    const onUpdateSession = vi.fn().mockRejectedValue([
      { code: 'INSUFFICIENT_ROOM_CAPACITY', message: 'Room capacity is too low.' },
    ])
    renderPanel({ onUpdateSession })

    const editButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Bearbeiten')
    await act(async () => {
      editButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    const saveButton = [...document.querySelectorAll('button')].find((button) => button.textContent === 'Speichern')
    await act(async () => {
      saveButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.body.textContent).toContain('Der Termin konnte nicht gespeichert werden')
    expect(document.querySelector<HTMLInputElement>('input[inputmode="numeric"]')).not.toBeNull()
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

    expect(document.body.textContent).toContain('07.09.2026')
  })

  it('shows list-mode alert reasons and related session details within two interactions', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    const alert = document.querySelector<HTMLDetailsElement>('.validation-alert')
    const summary = alert?.querySelector('summary')

    expect(summary?.textContent).toContain('zeitliche Überschneidung')
    expect(alert?.open).toBe(false)

    act(() => {
      summary?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(alert?.open).toBe(true)
    expect(alert?.textContent).toContain('Scheduling 201')
    expect(alert?.textContent).toContain('07.09.2026 09:00-12:30')
  })

  it('keeps overlap alerts visible when filters hide related sessions', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture, secondDraftScheduleFixture] })

    const courseFilter = document.querySelector<HTMLSelectElement>('select[name="courseId"]')
    act(() => {
      if (courseFilter) {
        setSelectValue(courseFilter, '1')
      }
    })

    expect(document.body.textContent).toContain('zeitliche Überschneidung')
    expect(document.body.textContent).toContain('Scheduling 201')
    const rows = [...document.querySelectorAll('.session-row:not(.session-header)')]
    expect(rows.every((row) => row.textContent?.includes('Planning 101'))).toBe(true)
  })

  it('shows multiple validation alert reasons on one session', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    expect(document.body.textContent).toContain('Kapazität reicht nicht aus')
    expect(document.body.textContent).toContain('genaue Ursache ist nicht verfügbar')
  })

  it('updates visible alert state after session update changes schedules', () => {
    const { rerender } = renderPanelWithRoot({ schedules: [draftScheduleFixture] })

    expect(document.body.textContent).not.toContain('zeitliche Überschneidung')

    act(() => {
      rerender([alertDraftScheduleFixture])
    })

    expect(document.body.textContent).toContain('zeitliche Überschneidung')

    act(() => {
      rerender([draftScheduleFixture])
    })

    expect(document.body.textContent).not.toContain('zeitliche Überschneidung')
  })

  it('shows validation alerts in weekly mode', () => {
    renderPanel({ schedules: [alertDraftScheduleFixture] })

    const weeklyButton = [...document.querySelectorAll('button')].find(
      (button) => button.textContent === 'Woche',
    )

    act(() => {
      weeklyButton?.dispatchEvent(new MouseEvent('click', { bubbles: true }))
    })

    expect(document.querySelector('.weekly-review')).not.toBeNull()
    expect(document.body.textContent).toContain('zeitliche Überschneidung')
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

    expect(document.body.textContent).toContain('Feiertag „Founders Day“ am 07.09.2026')
    expect(document.querySelectorAll('.validation-alert')).toHaveLength(1)
    expect(document.body.textContent).not.toContain('Holiday calendar entry')

    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Woche')?.click())
    expect(document.querySelector('.weekly-review')?.textContent).toContain('Feiertag „Founders Day“ am 07.09.2026')
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
    expect(document.body.textContent).toContain('zeitliche Überschneidung')
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
