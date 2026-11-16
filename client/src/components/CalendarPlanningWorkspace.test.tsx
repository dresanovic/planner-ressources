import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { describe, expect, it, vi } from 'vitest'

import type { CalendarWorkspace, LoadedCalendarWorkspace } from '../api/calendarWorkspace'
import {
  loadedCalendarWorkspaceFixture,
  noRevisionWorkspaceFixture,
  partialCalendarWorkspaceFixture,
  publishedCalendarWorkspaceFixture,
  timeGridWorkspaceFixture,
  multiCalendarTimeGridFixture,
} from '../test/calendarWorkspaceFixtures'
import {
  CalendarPlanningWorkspace,
  type WorkspaceListContext,
} from './CalendarPlanningWorkspace'


function renderWorkspace(workspace: CalendarWorkspace) {
  const host = document.createElement('div')
  document.body.append(host)
  const root = createRoot(host)
  act(() => root.render(
    <CalendarPlanningWorkspace
      workspace={workspace}
      loading={false}
      listContent={<div data-testid="existing-list">Existing Courses overview</div>}
      onRetry={vi.fn()}
      onStartDraft={vi.fn()}
    />,
  ))
  return host
}

function button(label: string) {
  return [...document.querySelectorAll<HTMLButtonElement>('button')].find((item) => item.textContent?.trim() === label)
}

describe('CalendarPlanningWorkspace', () => {
  it.each(['none', 'selected', 'guarded'] as const)('moves focus to Day results after Month navigation with %s selection', async selection => {
    const host = document.body.appendChild(document.createElement('div'))
    const root = createRoot(host)
    let pendingCommit: (() => void) | undefined
    function Harness() {
      const [selectedRef, setSelectedRef] = useState<string | null>(null)
      return <CalendarPlanningWorkspace
        workspace={timeGridWorkspaceFixture()} loading={false} listContent={<p>List</p>} onRetry={vi.fn()}
        selectedOccurrenceRef={selectedRef} onSelectedOccurrenceChange={setSelectedRef}
        onRequestTargetHidingFilter={selection === 'guarded' ? commit => {
          pendingCommit = () => { setSelectedRef(null); commit() }
        } : undefined}
      />
    }
    act(() => root.render(<Harness />))
    try {
      act(() => [...host.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === 'Monat')!.click())
      if (selection !== 'none') act(() => host.querySelector<HTMLButtonElement>('[data-occurrence-ref]')!.click())
      const dateButton = host.querySelector<HTMLButtonElement>('[data-month-date="2027-06-25"] .month-date-button')!
      dateButton.focus()
      act(() => dateButton.click())
      if (selection === 'guarded') {
        expect(pendingCommit).toBeDefined()
        expect(document.activeElement).toBe(dateButton)
        expect(host.querySelector('.month-calendar')).not.toBeNull()
        act(() => pendingCommit!())
      }
      await act(async () => { await new Promise(resolve => window.setTimeout(resolve, 0)) })
      expect(host.querySelector('.month-calendar')).toBeNull()
      expect(host.querySelector('.hourly-calendar')).not.toBeNull()
      expect(host.querySelector<HTMLInputElement>('#calendar-anchor-date')?.value).toBe('25.06.2027')
      expect(document.activeElement).toBe(host.querySelector('[data-workspace-results-heading]'))
      expect(host.querySelector('[data-workspace-recovery-announcement]')?.textContent).toContain('25.06.2027')
    } finally {
      act(() => root.unmount())
      host.remove()
    }
  })
  it('compares a checkbox cohort subset with a lecturer across modes and reconciles refresh/reset', () => {
    const workspace: LoadedCalendarWorkspace = multiCalendarTimeGridFixture()
    workspace.courses[0].cohort = workspace.occurrences[0].cohort = 'BA Business Analytics & AI'
    workspace.courses[1].cohort = workspace.occurrences[1].cohort = 'MA IT & Wirtschaftsinformatik'
    workspace.courses.push({ ...workspace.courses[0], courseRef: 'course:3', courseId: 3, cohort: 'Other' })
    workspace.occurrences.push({ ...workspace.occurrences[0], occurrenceRef: 'teaching:3', courseRef: 'course:3', cohort: 'Other' })
    workspace.filterFacets.cohorts = workspace.courses.map(c => ({ value: c.cohort, label: c.cohort }))
    workspace.filterFacets.lecturers = [{ value: 'lecturer:1', label: 'Shared lecturer' }]
    workspace.occurrences.forEach(o => { o.lecturerRefs = ['lecturer:1'] })
    const host = document.body.appendChild(document.createElement('div')), root = createRoot(host)
    const listContent = vi.fn((context: WorkspaceListContext | null) => <p>List {context?.teachingSessionIds.length}</p>)
    const render = () => act(() => root.render(<CalendarPlanningWorkspace workspace={workspace} loading={false} listContent={listContent} onRetry={vi.fn()} />))
    render()
    const date = host.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(date, '26.06.2027')
      date.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const checkbox = (name: string) => [...host.querySelectorAll<HTMLInputElement>('.cohort-filter input')].find(i => i.parentElement?.textContent === name)!
    act(() => host.querySelector<HTMLElement>('.cohort-filter summary')!.click())
    act(() => checkbox('BA Business Analytics & AI').click())
    expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(1)
    act(() => checkbox('MA IT & Wirtschaftsinformatik').click())
    const lecturer = [...host.querySelectorAll('select')].find(i => i.previousElementSibling?.textContent === 'Lehrende Person')!
    act(() => { lecturer.value = 'lecturer:1'; lecturer.dispatchEvent(new Event('change', { bubbles: true })) })
    for (const mode of ['Woche', 'Tag', 'Monat', 'Liste']) {
      act(() => [...host.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === mode)!.click())
      if (mode !== 'Liste') expect([...host.querySelectorAll('[data-occurrence-ref]')].map(e => e.getAttribute('data-occurrence-ref'))).toEqual(['teaching:1', 'teaching:2'])
      expect(listContent.mock.calls.at(-1)![0]?.teachingSessionIds).toEqual([1, 2])
      if (mode === 'Woche') expect(host.querySelectorAll('.time-grid-column')).toHaveLength(8)
      if (mode === 'Monat') expect([...host.querySelectorAll('.month-cohort-label')].map(e => e.textContent)).toEqual(['BA BA & AI', 'MA IT & W'])
    }
    expect(host.querySelector('.active-filter-status')?.textContent).toContain('2 aktive Filterbedingungen')
    workspace.filterFacets.cohorts = workspace.filterFacets.cohorts.filter(c => c.value !== 'BA Business Analytics & AI')
    act(() => root.render(<CalendarPlanningWorkspace workspace={{ ...workspace, workspaceToken: 'refreshed' }} loading={false} listContent={listContent} onRetry={vi.fn()} />))
    expect(host.querySelector('.cohort-filter summary')?.textContent).toContain('1 ausgewählt')
    act(() => checkbox('Alle').click())
    expect(host.querySelector('.cohort-filter summary')?.textContent).toBe('Alle')
    act(() => checkbox('Other').click())
    act(() => checkbox('Other').click())
    expect(host.querySelector('.cohort-filter summary')?.textContent).toBe('Alle')
    act(() => checkbox('Other').click())
    const details = host.querySelector<HTMLDetailsElement>('.cohort-filter details')!
    act(() => details.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(details.open).toBe(false)
    expect(document.activeElement).toBe(details.querySelector('summary'))
    act(() => [...host.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === 'Filter zurücksetzen')!.click())
    expect(host.querySelector('.cohort-filter summary')?.textContent).toBe('Alle')
    expect(host.querySelector('.active-filter-status')).toBeNull()
    act(() => root.unmount())
    host.remove()
  })
  describe.each(['Tag', 'Woche', 'Monat'])('selected calendar windows in %s', mode => {
    it.each([
      ['Raum', 'room:2'],
      ['Terminart', 'exam'],
      ['Prüfstatus', 'none'],
    ])('hides empty calendar profiles when %s filtering removes every session', (filterLabel, filterValue) => {
      const workspace: LoadedCalendarWorkspace = multiCalendarTimeGridFixture()
      workspace.occurrences[1].roomRef = 'room:2'
      workspace.filterFacets.rooms = [{ value: 'room:1', label: 'Room A' }, { value: 'room:2', label: 'Room B' }]
      workspace.filterFacets.cohortCalendars = [{ value: 'Calendar A', label: 'Calendar A' }, { value: 'Calendar B', label: 'Calendar B' }]
      workspace.filterFacets.validationCategories = [{ value: 'none', label: 'No current issue' }]
      workspace.courses.push({ ...workspace.courses[0], courseRef: 'course:3', courseId: 3, name: 'Empty A profile',
        occurrenceRefs: [], findingRefs: [], remainingTeachingUnits: 0, remainingInstructionalMinutes: 0 })
      const context = structuredClone(workspace.teachingWindowContexts![0])
      workspace.teachingWindowContexts!.push({ ...context, courseRef: 'course:3', isCustom: true, sourceRevision: 2,
        windows: [{ ...context.windows[0], startTime: '09:00', endTime: '15:00' }] })
      const host = document.body.appendChild(document.createElement('div'))
      const root = createRoot(host)
      const listContent = vi.fn((context: WorkspaceListContext | null) => <p>Retained List · {context?.teachingSessionIds.length ?? 0} teaching sessions</p>)
      act(() => root.render(<CalendarPlanningWorkspace workspace={workspace} loading={false} listContent={listContent} onRetry={vi.fn()} />))
      const selectFilter = (label: string, value: string) => {
        const select = [...host.querySelectorAll<HTMLLabelElement>('.workspace-filters label')]
          .find(item => item.querySelector('span')?.textContent === label)!.querySelector('select')!
        act(() => { select.value = value; select.dispatchEvent(new Event('change', { bubbles: true })) })
      }
      const date = host.querySelector<HTMLInputElement>('#calendar-anchor-date')!
      act(() => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(date, '26.06.2027')
        date.dispatchEvent(new Event('change', { bubbles: true }))
      })
      act(() => [...host.querySelectorAll<HTMLButtonElement>('button')].find(item => item.textContent === mode)!.click())
      selectFilter('Kohortenkalender', 'Calendar A')
      selectFilter(filterLabel, filterValue)

      expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(0)
      const listContext = listContent.mock.calls.at(-1)![0]!
      expect(listContext.teachingSessionIds).toEqual([])
      expect(listContext.examIds).toEqual([])
      expect(listContext.courseIds).toEqual([])
      const surface = host.querySelector(mode === 'Monat' ? '.month-calendar' : '.hourly-calendar')!
      expect(surface.textContent).not.toContain('08:00–16:00')
      expect(surface.querySelector('details')).toBeNull()
      if (mode === 'Monat') expect(surface.querySelectorAll('[data-month-date]')).toHaveLength(35)
      else expect(surface.querySelectorAll('.time-grid-column')).toHaveLength(mode === 'Woche' ? 7 : 1)
      selectFilter('Kohortenkalender', '')
      expect(host.querySelectorAll('[data-occurrence-ref]')).toHaveLength(filterValue === 'exam' ? 0 : 1)
      if (mode !== 'Monat' && filterValue !== 'exam') expect(surface.textContent).toContain('10:00–18:00')
      act(() => root.unmount())
      host.remove()
    })
  })
  it('opens a different Month date without snapping back to the selected session', () => {
    const host = renderWorkspace(timeGridWorkspaceFixture())
    const find = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === text)!
    act(() => find('Monat').click())
    act(() => host.querySelector<HTMLButtonElement>('[data-occurrence-ref]')!.click())
    act(() => host.querySelector<HTMLButtonElement>('[data-month-date="2027-06-25"] .month-date-button')!.click())
    expect(find('Tag').getAttribute('aria-pressed')).toBe('true')
    expect(host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')?.value).toBe('25.06.2027')
    expect(host.querySelector('.occurrence-detail')).toBeNull()
  })
  it('opens a Month date in Day and keeps selected source facts alongside custom detail', () => {
    const workspace = timeGridWorkspaceFixture()
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(<CalendarPlanningWorkspace workspace={workspace} loading={false} listContent={<p>List</p>} onRetry={vi.fn()} renderSessionPane={(_, close) => <aside><h3>Custom pane</h3><button onClick={close}>Custom close</button></aside>} />))
    const findButton = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('button')].find(b => b.textContent === text)!
    act(() => findButton('Monat').click())
    const dateButton = host.querySelector<HTMLButtonElement>('[data-month-date="2027-06-26"] .month-date-button')!
    act(() => dateButton.click())
    expect(findButton('Tag').getAttribute('aria-pressed')).toBe('true')
    act(() => host.querySelector<HTMLButtonElement>('[data-occurrence-ref]')!.click())
    expect(host.textContent).toContain('Custom pane')
    expect(host.querySelector('.selected-window-context')?.textContent).toContain('08:00–16:00')
    act(() => root.unmount())
  })
  it('keeps empty dates without windows for an explicitly selected empty calendar', () => {
    const workspace: LoadedCalendarWorkspace = timeGridWorkspaceFixture()
    workspace.filterFacets.cohortCalendars = [{ value: 'Calendar A', label: 'Calendar A' }]
    workspace.occurrences = []
    const host = renderWorkspace(workspace)
    const select = [...host.querySelectorAll('select')].find(s => s.parentElement?.textContent?.startsWith('Kohortenkalender'))!
    act(() => { select.value = 'Calendar A'; select.dispatchEvent(new Event('change', { bubbles: true })) })
    expect(host.querySelectorAll('.time-grid-column')).toHaveLength(7)
    expect(host.textContent).not.toContain('Erlaubte Lehrstunden 08:00–16:00')
    expect(host.querySelector('.hourly-calendar details')).toBeNull()
  })
  it('shows lecturer names and room reference codes in occurrence details', () => {
    const workspace: LoadedCalendarWorkspace = loadedCalendarWorkspaceFixture()
    workspace.filterFacets = { ...workspace.filterFacets,
      lecturers: [{ value: 'lecturer:1', label: 'Ada Lovelace' }],
      rooms: [{ value: 'room:1', label: 'CAMPUS-055' }],
    }
    const host = renderWorkspace(workspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    for (const [kind, date] of [['Lehrtermin', '05.10.2026'], ['Prüfungstermin', '10.12.2026']]) {
      act(() => {
        Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, date)
        dateInput.dispatchEvent(new Event('change', { bubbles: true }))
      })
      const occurrence = [...host.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes(kind))!
      expect(occurrence.textContent).toContain('Raum: CAMPUS-055')
      act(() => occurrence.click())
      const details = host.querySelector('.occurrence-detail')!
      const valueFor = (label: string) => [...details.querySelectorAll('dt')]
        .find((item) => item.textContent === label)?.nextElementSibling?.textContent
      expect(valueFor('Lehrende Person')).toBe('Ada Lovelace')
      expect(valueFor('Raum')).toBe('CAMPUS-055')
    }
  })

  it('shows revision identity, five truthful summaries, and teaching/exam distinction', () => {
    renderWorkspace(loadedCalendarWorkspaceFixture() as CalendarWorkspace)

    expect(document.body.textContent).toContain('Revision 1')
    expect(document.body.textContent).toContain('Aktive Arbeitsrevision')
    expect(document.querySelectorAll('.summary-card')).toHaveLength(5)
    expect(document.body.textContent).toContain('Lehrtermin')
    expect(document.querySelector<HTMLElement>('[aria-label="Listenansicht"]')?.hidden).toBe(true)
    expect(button('Woche')?.getAttribute('aria-pressed')).toBe('true')
  })

  it('uses the established Courses overview as its only List mode', () => {
    renderWorkspace(loadedCalendarWorkspaceFixture() as CalendarWorkspace)
    act(() => button('Liste')?.click())

    expect(document.querySelectorAll('[data-testid="existing-list"]')).toHaveLength(1)
    expect(button('Aktuelle Periode nicht anwendbar')?.disabled).toBe(true)
  })

  it('keeps the existing List workflow mounted when another calendar mode is shown', () => {
    function StatefulList() {
      const [value, setValue] = useState('')
      return <label>Unsaved correction<input aria-label="Unsaved correction" value={value} onChange={(event) => setValue(event.target.value)} /></label>
    }
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        listContent={<StatefulList />}
        onRetry={vi.fn()}
      />,
    ))
    const modeButton = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === label)!
    act(() => modeButton('Liste').click())
    const input = host.querySelector<HTMLInputElement>('input[aria-label="Unsaved correction"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, 'keep me')
      input.dispatchEvent(new Event('input', { bubbles: true }))
      input.dispatchEvent(new Event('change', { bubbles: true }))
    })
    act(() => modeButton('Woche').click())
    expect(host.querySelector('[aria-label="Listenansicht"]')?.hasAttribute('hidden')).toBe(true)
    act(() => modeButton('Liste').click())
    expect(host.querySelector<HTMLInputElement>('input[aria-label="Unsaved correction"]')?.value).toBe('keep me')
  })

  it('passes the unified filtered projection and exact undated trace target to List', () => {
    const contexts: unknown[] = []
    const onTraceCourse = vi.fn()
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        listContent={(context) => {
          contexts.push(context)
          return <div data-testid="existing-list">Existing Courses overview</div>
        }}
        onRetry={vi.fn()}
        onTraceCourse={onTraceCourse}
      />,
    ))

    const sessionType = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'teaching')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const listMode = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Liste')!
    act(() => listMode.click())

    expect(contexts.at(-1)).toMatchObject({
      teachingSessionIds: [1],
      examIds: [],
      activeFilterCount: 1,
    })
    const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Prüfung erforderlich'))!
    act(() => needsReview.click())
    const contributor = [...host.querySelectorAll<HTMLButtonElement>('.workspace-drilldown button')]
      .find((item) => item.textContent?.includes('Algorithms'))!
    act(() => contributor.click())

    expect(contexts.at(-1)).toMatchObject({
      traceTarget: {
        reference: 'course:1',
        courseIds: [1],
        teachingSessionIds: [1],
        examIds: [],
        teachingCoverage: [{ courseId: 1, requiredUnits: 4, plannedUnits: 2, remainingUnits: 2 }],
      },
    })
    expect(onTraceCourse).toHaveBeenCalledWith(1)
    expect(host.textContent).toContain('Gefilterte Teilmenge')
  })

  it.each([true, false])('keeps the warning course across calendar modes with scheduled appointments=%s', hasAppointments => {
    const workspace: LoadedCalendarWorkspace = loadedCalendarWorkspaceFixture()
    workspace.courses.push({
      ...workspace.courses[0], courseId: 2, courseRef: 'course:2', name: 'Unrelated course',
      occurrenceRefs: ['teaching:2'], needsReviewReasonRefs: [],
    })
    workspace.occurrences.push({
      ...workspace.occurrences[0], occurrenceRef: 'teaching:2', courseRef: 'course:2',
    })
    if (!hasAppointments) {
      workspace.occurrences = workspace.occurrences.filter(item => item.courseRef !== 'course:1')
      workspace.courses[0].occurrenceRefs = []
    }
    const contexts: (WorkspaceListContext | null)[] = []
    const host = document.body.appendChild(document.createElement('div'))
    const root = createRoot(host)
    act(() => root.render(<CalendarPlanningWorkspace
      workspace={workspace} loading={false} onRetry={vi.fn()}
      listContent={context => { contexts.push(context); return <p>List</p> }}
    />))
    const mode = (name: string) => [...host.querySelectorAll<HTMLButtonElement>('.calendar-mode-switch button')]
      .find(item => item.textContent === name)!
    try {
      act(() => host.querySelector<HTMLButtonElement>('.summary-card:last-child')!.click())
      act(() => [...host.querySelectorAll<HTMLButtonElement>('.workspace-drilldown button')]
        .find(item => item.textContent === 'Algorithms')!.click())
      const courseFilter = [...host.querySelectorAll<HTMLSelectElement>('.workspace-filters select')]
        .find(item => item.previousElementSibling?.textContent === 'Lehrveranstaltung')!
      expect(courseFilter.value).toBe('course:1')
      for (const name of ['Tag', 'Woche', 'Monat']) {
        act(() => mode(name).click())
        expect(courseFilter.value).toBe('course:1')
        expect(host.querySelector('[aria-label="Ausgewählter Datensatz"]')?.textContent).toContain('Algorithms')
        const cards = [...host.querySelectorAll<HTMLElement>('[data-occurrence-ref]')]
        expect(cards.some(item => item.dataset.occurrenceRef === 'teaching:2')).toBe(false)
        expect(cards.some(item => item.dataset.occurrenceRef === 'teaching:1')).toBe(hasAppointments)
        if (!hasAppointments) expect(host.textContent).toContain('Für diesen Datensatz entspricht kein geplanter Termin den aktiven Filtern.')
        act(() => mode('Liste').click())
        expect(contexts.at(-1)?.traceTarget?.reference).toBe('course:1')
      }
      act(() => [...host.querySelectorAll<HTMLButtonElement>('button')]
        .find(item => item.textContent === 'Detailauswahl aufheben')!.click())
      expect(contexts.at(-1)?.traceTarget).toBeNull()
      expect(courseFilter.value).toBe('')
      expect(host.querySelector('[aria-label="Ausgewählter Datensatz"]')).toBeNull()
    } finally {
      act(() => root.unmount())
      host.remove()
    }
  })

  it('reconciles open drilldown contributors when filters change', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses.push({
      ...workspace.courses[0],
      courseRef: 'course:2',
      courseId: 2,
      code: 'C-002',
      name: 'Databases',
      lecturerRefs: ['lecturer:2'],
      occurrenceRefs: ['teaching:2'],
      needsReviewReasonRefs: ['remaining:course:2'],
    })
    workspace.occurrences.push({
      ...workspace.occurrences[0],
      occurrenceRef: 'teaching:2',
      courseRef: 'course:2',
      lecturerRefs: ['lecturer:2'],
    })
    workspace.summary.needsReview = {
      availability: 'available',
      scope: 'complete_revision',
      distinctCourseCount: 2,
      contributorRefs: ['course:1', 'course:2'],
    }
    workspace.filterFacets.courses = [
      { value: 'course:1', label: 'Algorithms' },
      { value: 'course:2', label: 'Databases' },
    ]
    const host = renderWorkspace(workspace)
    const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Prüfung erforderlich'))!

    act(() => needsReview.click())
    expect(host.querySelector('.workspace-drilldown')?.textContent).toContain('Algorithms')
    expect(host.querySelector('.workspace-drilldown')?.textContent).toContain('Databases')

    const courseFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Lehrveranstaltung')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(
        courseFilter,
        'course:2',
      )
      courseFilter.dispatchEvent(new Event('change', { bubbles: true }))
    })

    expect(host.querySelector('.workspace-drilldown')?.textContent).toContain(
      '1 betroffener Datensatz in der gefilterten Teilmenge',
    )
    expect(host.querySelector('.workspace-drilldown')?.textContent).not.toContain(
      'Algorithms',
    )
    expect(host.querySelector('.workspace-drilldown')?.textContent).toContain('Databases')
  })

  it('uses a predictable focus fallback when filtering disables the drilldown initiator', async () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses.push({
      ...workspace.courses[0],
      courseRef: 'course:2',
      courseId: 2,
      code: 'C-002',
      name: 'Databases',
      occurrenceRefs: ['teaching:2'],
      remainingTeachingUnits: 0,
      remainingInstructionalMinutes: 0,
      needsReviewReasonRefs: [],
    })
    workspace.occurrences.push({
      ...workspace.occurrences[0],
      occurrenceRef: 'teaching:2',
      courseRef: 'course:2',
    })
    workspace.filterFacets.courses = [
      { value: 'course:1', label: 'Algorithms' },
      { value: 'course:2', label: 'Databases' },
    ]
    const host = renderWorkspace(workspace)
    const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Prüfung erforderlich'))!
    const courseFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Lehrveranstaltung')!
    const selectCleanCourse = () => {
      act(() => {
        Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(
          courseFilter,
          'course:2',
        )
        courseFilter.dispatchEvent(new Event('change', { bubbles: true }))
      })
      expect(needsReview.disabled).toBe(true)
    }
    const waitForFocusRestore = async () => {
      await act(async () => {
        await new Promise((resolve) => window.setTimeout(resolve, 0))
      })
    }

    act(() => needsReview.click())
    selectCleanCourse()
    act(() => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Detailauswahl aufheben')!.click())
    await waitForFocusRestore()
    expect(document.activeElement).toBe(
      host.querySelector('[data-workspace-results-heading]'),
    )

    act(() => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Filter zurücksetzen')!.click())
    act(() => needsReview.click())
    selectCleanCourse()
    act(() => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Filter zurücksetzen')!.click())
    await waitForFocusRestore()
    expect(needsReview.disabled).toBe(false)
    expect(document.activeElement).toBe(needsReview)
  })

  it('restores the prior course after an undated trace through either clear path', () => {
    const onTraceCourse = vi.fn()
    function Harness() {
      const [selectedCourseId, setSelectedCourseId] = useState<number | null>(99)
      return (
        <>
          <output data-testid="selected-course">{selectedCourseId ?? 'none'}</output>
          <CalendarPlanningWorkspace
            workspace={loadedCalendarWorkspaceFixture()}
            loading={false}
            listContent={<div data-testid="existing-list">Existing Courses overview</div>}
            onRetry={vi.fn()}
            selectedCourseId={selectedCourseId}
            onTraceCourse={(courseId) => {
              onTraceCourse(courseId)
              setSelectedCourseId(courseId)
            }}
          />
        </>
      )
    }
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(<Harness />))
    const clearButton = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === label)!
    const traceCourse = () => {
      const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
        .find((item) => item.textContent?.includes('Prüfung erforderlich'))!
      act(() => needsReview.click())
      const contributor = [...host.querySelectorAll<HTMLButtonElement>('.workspace-drilldown button')]
        .find((item) => item.textContent?.includes('Algorithms'))!
      act(() => contributor.click())
      expect(host.querySelector('[data-testid="selected-course"]')?.textContent).toBe('1')
    }

    traceCourse()
    act(() => clearButton('Detailauswahl aufheben').click())
    expect(onTraceCourse.mock.calls).toEqual([[1], [99]])
    expect(host.querySelector('[data-testid="selected-course"]')?.textContent).toBe('99')

    traceCourse()
    act(() => clearButton('Filter zurücksetzen').click())
    expect(onTraceCourse.mock.calls).toEqual([[1], [99], [1], [99]])
    expect(host.querySelector('[data-testid="selected-course"]')?.textContent).toBe('99')
  })

  it('restores calendar context and focus through either drilldown clear path', async () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.summary.capacityIssues = {
      availability: 'available',
      scope: 'complete_revision',
      affectedOccurrenceCount: 1,
      contributorRefs: ['exam:1'],
    }
    const host = renderWorkspace(workspace)
    const inHostButton = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === label)!
    const capacityIssues = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Kapazitätsprobleme'))!
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(
        dateInput,
        '05.10.2026',
      )
      dateInput.dispatchEvent(new Event('input', { bubbles: true }))
    })
    const openDatedContributor = () => {
      act(() => capacityIssues.click())
      expect(document.activeElement).toBe(
        host.querySelector('[data-workspace-drilldown-heading]'),
      )
      const contributor = [...host.querySelectorAll<HTMLButtonElement>('.workspace-drilldown button')]
        .find((item) => item.textContent?.includes('10.12.2026'))!
      act(() => contributor.click())
    }

    expect(inHostButton('Woche').getAttribute('aria-pressed')).toBe('true')
    openDatedContributor()

    expect(inHostButton('Tag').getAttribute('aria-pressed')).toBe('true')
    expect(host.querySelector('.visible-range')?.textContent).toBe('10.12.2026')
    expect(host.textContent).toContain('Prüfungstermin')
    expect(host.textContent).toContain('Revision 1')
    expect(host.textContent).toContain('Aktive Arbeitsrevision')

    act(() => inHostButton('Filter zurücksetzen').click())
    await act(async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 0))
    })
    expect(inHostButton('Woche').getAttribute('aria-pressed')).toBe('true')
    expect(host.querySelector('.visible-range')?.textContent).toContain('05.10.2026')
    expect(host.querySelector('.occurrence-detail')).toBeNull()
    expect(host.querySelector('.workspace-drilldown')).toBeNull()
    expect(document.activeElement).toBe(capacityIssues)

    openDatedContributor()
    act(() => inHostButton('Detailauswahl aufheben').click())
    await act(async () => {
      await new Promise((resolve) => window.setTimeout(resolve, 0))
    })
    expect(inHostButton('Woche').getAttribute('aria-pressed')).toBe('true')
    expect(host.querySelector('.visible-range')?.textContent).toContain('05.10.2026')
    expect(document.activeElement).toBe(capacityIssues)
  })

  it('routes undated outcomes and findings to exact List targets with related conflict linkage', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.planningOutcomes = [{
      outcomeRef: 'outcome:1',
      revisionId: 11,
      courseRef: 'course:1',
      operationKind: 'semester_optimization',
      classification: 'failed',
      sourceStatus: 'failed',
      reasons: [{ code: 'NO_FEASIBLE_SLOT' }, { code: 'ROOM_CAPACITY' }],
      completedAt: '2026-09-01T10:00:00Z',
    }]
    workspace.validationFindings = [{
      findingRef: 'finding:conflict:room:teaching:1:exam:1',
      category: 'room_conflict',
      validationBasis: 'current',
      affectedOccurrenceRefs: ['teaching:1', 'exam:1'],
      affectedCourseRefs: ['course:1'],
      details: {
        kind: 'conflict',
        conflictType: 'room',
        occurrenceRefs: ['teaching:1', 'exam:1'],
        subjectRef: 'room:1',
      },
    }]
    workspace.courses[0].outcomeRefs = ['outcome:1']
    workspace.courses[0].findingRefs = ['finding:conflict:room:teaching:1:exam:1']
    workspace.occurrences[0].findingRefs = ['finding:conflict:room:teaching:1:exam:1']
    workspace.occurrences[1].findingRefs = ['finding:conflict:room:teaching:1:exam:1']
    workspace.summary.planningFailures = {
      availability: 'available',
      scope: 'complete_revision',
      coverage: {
        eligibleCourseCount: 1,
        coveredCourseCount: 1,
        coverageComplete: true,
      },
      failedOutcomeCount: 1,
      staleOutcomeCount: 0,
      unchangedOutcomeCount: 0,
      contributorRefs: ['outcome:1'],
    }
    workspace.summary.conflicts = {
      availability: 'available',
      scope: 'complete_revision',
      distinctFindingCount: 1,
      countByType: { lecturer: 0, room: 1, cohort: 0 },
      contributorRefs: ['finding:conflict:room:teaching:1:exam:1'],
    }
    const contexts: (WorkspaceListContext | null)[] = []
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={workspace}
        loading={false}
        listContent={(context) => {
          contexts.push(context)
          return <div data-testid="existing-list">Existing Courses overview</div>
        }}
        onRetry={vi.fn()}
      />,
    ))
    const summary = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes(label))!
    const drilldownContributor = (text: string) => [...host.querySelectorAll<HTMLButtonElement>('.workspace-drilldown button')]
      .find((item) => item.textContent?.toLowerCase().includes(text))!

    act(() => summary('Planungsfehler').click())
    const outcomeProblems = host.querySelectorAll('.workspace-contributor-problems > li')
    expect(outcomeProblems).toHaveLength(2)
    expect(outcomeProblems[0].textContent).toContain('genaue Ursache ist nicht verfügbar')
    expect(outcomeProblems[1].textContent).toContain('Kapazität reicht nicht aus')
    expect(drilldownContributor('semesteroptimierung').textContent).not.toContain('Kapazität')
    act(() => drilldownContributor('semesteroptimierung').click())
    expect(contexts.at(-1)).toMatchObject({
      courseIds: [1],
      teachingSessionIds: [1],
      examIds: [1],
      traceTarget: {
        reference: 'outcome:1',
        courseIds: [1],
        teachingSessionIds: [1],
        examIds: [1],
      },
    })

    const clear = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Detailauswahl aufheben')!
    act(() => clear.click())
    act(() => summary('Konflikte').click())
    act(() => drilldownContributor('mehreren terminen').click())
    expect(contexts.at(-1)).toMatchObject({
      traceTarget: {
        reference: 'finding:conflict:room:teaching:1:exam:1',
        courseIds: [1],
        teachingSessionIds: [1],
        examIds: [1],
      },
    })
    expect(host.textContent).toContain('Revision 1')
    expect(host.textContent).toContain('Aktive Arbeitsrevision')
  })

  it('renders named holiday date context even when no session occurs that day', () => {
    const host = renderWorkspace(loadedCalendarWorkspaceFixture() as CalendarWorkspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(
        dateInput,
        '26.10.2026',
      )
      dateInput.dispatchEvent(new Event('input', { bubbles: true }))
    })

    expect(host.textContent).toContain('Holiday: National Holiday')
  })

  it('navigates Day, Week, Month, and List while preserving active filters', () => {
    const host = renderWorkspace(loadedCalendarWorkspaceFixture() as CalendarWorkspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const inHostButton = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === label)!
    const sessionType = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'teaching')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
    })

    act(() => inHostButton('Tag').click())
    expect(host.querySelector('.visible-range')?.textContent).toBe('05.10.2026')
    act(() => host.querySelector<HTMLButtonElement>('[aria-label="Vorherige Periode"]')!.click())
    expect(host.querySelector('.visible-range')?.textContent).toBe('04.10.2026')
    act(() => inHostButton('Monat').click())
    expect(host.querySelector('.visible-range')?.textContent).toContain('01.10.2026')
    act(() => inHostButton('Liste').click())
    expect(sessionType.value).toBe('teaching')
    expect(inHostButton('Aktuelle Periode nicht anwendbar').disabled).toBe(true)
    expect(host.querySelector<HTMLElement>('[aria-label="Listenansicht"]')?.hidden).toBe(false)
  })

  it('excludes same-course findings whose occurrences are outside a resource filter', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.occurrences.push(
      {
        ...workspace.occurrences[0],
        occurrenceRef: 'teaching:2',
        roomRef: 'room:2',
      },
      {
        ...workspace.occurrences[0],
        occurrenceRef: 'teaching:3',
        roomRef: 'room:2',
      },
    )
    workspace.courses[0].occurrenceRefs.push('teaching:2', 'teaching:3')
    workspace.validationFindings.push({
      findingRef: 'finding:conflict:room:teaching:2:teaching:3',
      category: 'room_conflict',
      validationBasis: 'current',
      affectedCourseRefs: ['course:1'],
      affectedOccurrenceRefs: ['teaching:2', 'teaching:3'],
      details: {
        kind: 'conflict',
        conflictType: 'room',
        occurrenceRefs: ['teaching:2', 'teaching:3'],
        subjectRef: 'room:2',
      },
    })
    workspace.summary.conflicts = {
      availability: 'available',
      scope: 'complete_revision',
      distinctFindingCount: 1,
      countByType: { lecturer: 0, room: 1, cohort: 0 },
      contributorRefs: ['finding:conflict:room:teaching:2:teaching:3'],
    }
    workspace.filterFacets.rooms = [
      { value: 'room:1', label: 'Room 1' },
      { value: 'room:2', label: 'Room 2' },
    ]
    const host = renderWorkspace(workspace as CalendarWorkspace)
    const roomFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Raum')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(roomFilter, 'room:1')
      roomFilter.dispatchEvent(new Event('change', { bubbles: true }))
    })

    const conflict = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Konflikte'))!
    expect(conflict.querySelector('strong')?.textContent).toBe('0')
    expect(conflict.textContent).toContain('Gefilterte Teilmenge')
  })

  it('hands a teaching edit to the established List editor', () => {
    const onEditTeaching = vi.fn()
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        listContent={<div data-testid="existing-list">Existing Courses overview</div>}
        onRetry={vi.fn()}
        onEditTeaching={onEditTeaching}
      />,
    ))
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(
        dateInput,
        '05.10.2026',
      )
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })

    const teaching = [...host.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
      .find((item) => item.textContent?.includes('Lehrtermin'))
    act(() => teaching?.click())
    const edit = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Im vorhandenen Editor bearbeiten')
    act(() => edit?.click())

    expect(onEditTeaching).toHaveBeenCalledWith('teaching:1')
    expect(host.querySelector('[data-testid="existing-list"]')).not.toBeNull()
  })

  it('shows complete exam capacity, lifecycle, recommendation, and validity detail', () => {
    const host = renderWorkspace(loadedCalendarWorkspaceFixture() as CalendarWorkspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '10.12.2026')
      dateInput.dispatchEvent(new Event('input', { bubbles: true }))
    })
    const exam = [...host.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
      .find((item) => item.textContent?.includes('Prüfungstermin'))!
    act(() => exam.click())

    expect(host.textContent).toContain('30 erforderlich')
    expect(host.textContent).toContain('Auditorium 1')
    expect(host.textContent).toContain('40 aktuell')
    expect(host.textContent).toContain('Entwurf')
    expect(host.textContent).toContain('FINAL')
    expect(host.textContent).toContain('manuell festgelegt')
  })

  it('exposes a count and keyboard-operable continuation for a dense Month date', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.occurrences = Array.from({ length: 6 }, (_, index) => ({
      ...workspace.occurrences[0],
      occurrenceRef: `teaching:${index + 1}`,
      startTime: `${String(8 + index).padStart(2, '0')}:00`,
      endTime: `${String(9 + index).padStart(2, '0')}:00`,
    }))
    workspace.courses[0].occurrenceRefs = workspace.occurrences.map((item) => item.occurrenceRef)
    const host = renderWorkspace(workspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const month = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Monat')!
    act(() => month.click())

    expect(host.textContent).toContain('6 Termine')
    expect(host.querySelectorAll('.calendar-occurrence')).toHaveLength(3)
    const showAll = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.includes('Alle 6 Termine anzeigen'))!
    act(() => showAll.click())
    expect(host.querySelectorAll('.calendar-occurrence')).toHaveLength(6)
    expect(host.textContent).toContain('Weniger Termine anzeigen')
  })

  it('moves focus and explains when the selected result stops matching filters', async () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.filterFacets.sessionTypes = [
      { value: 'teaching', label: 'Teaching' },
      { value: 'exam', label: 'Exam' },
    ]
    const host = renderWorkspace(workspace)
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    act(() => host.querySelector<HTMLButtonElement>('.calendar-occurrence')!.click())
    const sessionType = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'exam')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
      await Promise.resolve()
    })

    expect(host.querySelector('.occurrence-detail')).toBeNull()
    expect(document.activeElement).toBe(host.querySelector('[data-workspace-results-heading]'))
    expect(host.textContent).toContain('Der ausgewählte Termin entspricht nicht mehr der aktuellen Ergebnismenge.')
  })

  it('announces successful recovery after a failed workspace load', async () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    const props = {
      loading: false,
      listContent: <div>Existing Courses overview</div>,
      onRetry: vi.fn(),
    }
    act(() => root.render(
      <CalendarPlanningWorkspace
        {...props}
        workspace={null}
        error="Network unavailable."
        intendedContext="Fall 2026 · Working"
      />,
    ))
    await act(async () => {
      root.render(
        <CalendarPlanningWorkspace
          {...props}
          workspace={loadedCalendarWorkspaceFixture()}
        />,
      )
      await Promise.resolve()
    })

    expect(host.querySelector('[data-workspace-recovery-announcement]')?.textContent)
      .toContain('Kalender-Arbeitsbereich wurde mit aktuellen Daten wiederhergestellt')
  })

  it('shows a no-revision action and a Published read-only explanation', () => {
    const noRevision = renderWorkspace(noRevisionWorkspaceFixture() as CalendarWorkspace)
    expect(noRevision.textContent).toContain('Entwurf starten')
    act(() => noRevision.remove())

    renderWorkspace(publishedCalendarWorkspaceFixture() as CalendarWorkspace)
    expect(document.body.textContent).toContain('Aktuelle Veröffentlichung')
    expect(document.body.textContent).toContain('Veröffentlichte Inhalte sind schreibgeschützt')
  })

  it('preserves valid filters, drilldown, and selection across a same-revision refresh', () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    const working = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={working}
        loading={false}
        listContent={<div>Existing Courses overview</div>}
        onRetry={vi.fn()}
      />,
    ))
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const teaching = [...host.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
      .find((item) => item.textContent?.includes('Lehrtermin'))!
    act(() => teaching.click())
    const sessionType = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'teaching')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Prüfung erforderlich'))!
    act(() => needsReview.click())
    const listMode = [...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Liste')!
    act(() => listMode.click())

    expect(host.querySelector('.occurrence-detail')).not.toBeNull()
    expect(host.querySelector('.workspace-drilldown')).not.toBeNull()
    expect(host.querySelector('.active-filter-status')).not.toBeNull()

    const refreshed = {
      ...working,
      workspaceToken: 'same-revision-refreshed',
      selectedRevision: { ...working.selectedRevision },
      occurrences: working.occurrences.map((occurrence) => ({ ...occurrence })),
      filterFacets: {
        ...working.filterFacets,
        sessionTypes: working.filterFacets.sessionTypes.map((facet) => ({ ...facet })),
      },
    }
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={refreshed}
        loading={false}
        listContent={<div>Existing Courses overview</div>}
        onRetry={vi.fn()}
      />,
    ))

    expect([...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent?.trim() === 'Liste')
      ?.getAttribute('aria-pressed')).toBe('true')
    expect(host.querySelector('.occurrence-detail')).not.toBeNull()
    expect(host.querySelector('.workspace-drilldown')).not.toBeNull()
    expect(host.querySelector('.active-filter-status')).not.toBeNull()
  })

  it('clears only unavailable filters, drilldown, and selection after refresh', async () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    const working = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={working}
        loading={false}
        listContent={<div>Existing Courses overview</div>}
        onRetry={vi.fn()}
      />,
    ))
    const dateInput = host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    act(() => host.querySelector<HTMLButtonElement>('.calendar-occurrence')?.click())
    const sessionType = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'teaching')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const needsReview = [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Prüfung erforderlich'))!
    act(() => needsReview.click())

    const refreshed = {
      ...working,
      workspaceToken: 'same-revision-with-removed-records',
      occurrences: working.occurrences.filter((item) => item.kind === 'exam'),
      courses: working.courses.map((course) => ({
        ...course,
        occurrenceRefs: course.occurrenceRefs.filter((reference) => reference.startsWith('exam:')),
      })),
      filterFacets: {
        ...working.filterFacets,
        sessionTypes: [{ value: 'exam', label: 'Exam' }],
      },
      summary: {
        ...working.summary,
        needsReview: {
          ...working.summary.needsReview,
          contributorRefs: [],
        },
      },
    } satisfies LoadedCalendarWorkspace
    await act(async () => {
      root.render(
        <CalendarPlanningWorkspace
          workspace={refreshed}
          loading={false}
          listContent={<div>Existing Courses overview</div>}
          onRetry={vi.fn()}
        />,
      )
      await Promise.resolve()
    })

    expect(host.querySelector('.occurrence-detail')).toBeNull()
    expect(host.querySelector('.workspace-drilldown')).toBeNull()
    expect(host.querySelector('.active-filter-status')).toBeNull()
    expect(host.querySelector('[data-workspace-recovery-announcement]')?.textContent)
      .toContain('ausgewählte Termin ist im aktualisierten Arbeitsbereich nicht mehr verfügbar')
  })

  it('recomputes partial metric coverage within verified, unverified, and mixed filters', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    const missingFindingRef = 'finding:other:teaching:2:VALIDATION_DATA_MISSING'
    workspace.courses.push({
      ...workspace.courses[0],
      courseRef: 'course:2',
      courseId: 2,
      code: 'C-002',
      name: 'Databases',
      remainingTeachingUnits: 0,
      remainingInstructionalMinutes: 0,
      occurrenceRefs: ['teaching:2'],
      findingRefs: [missingFindingRef],
      needsReviewReasonRefs: [missingFindingRef],
    })
    workspace.occurrences.push({
      ...workspace.occurrences[0],
      occurrenceRef: 'teaching:2',
      courseRef: 'course:2',
      roomRef: 'room:missing',
      findingRefs: [missingFindingRef],
    })
    workspace.validationFindings.push({
      findingRef: missingFindingRef,
      category: 'other',
      validationBasis: 'current',
      affectedCourseRefs: ['course:2'],
      affectedOccurrenceRefs: ['teaching:2'],
      details: {
        kind: 'other',
        issueCode: 'VALIDATION_DATA_MISSING',
        occurrenceRefs: ['teaching:2'],
        roomRef: 'room:missing',
      },
    })
    workspace.summary.capacityIssues = {
      availability: 'partial',
      scope: 'complete_revision',
      affectedOccurrenceCount: 0,
      contributorRefs: [],
    }
    workspace.summary.needsReview = {
      availability: 'partial',
      scope: 'complete_revision',
      distinctCourseCount: 1,
      contributorRefs: ['course:1'],
    }
    workspace.filterFacets.courses = [
      { value: 'course:1', label: 'Algorithms' },
      { value: 'course:2', label: 'Databases' },
    ]
    workspace.filterFacets.cohortCalendars = [{ value: 'Full-time', label: 'Full-time' }]
    const host = renderWorkspace(workspace)
    const courseFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Lehrveranstaltung')!
    const cohortCalendarFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Kohortenkalender')!
    const summary = (label: string) => [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes(label))!
    const select = (element: HTMLSelectElement, value: string) => act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(element, value)
      element.dispatchEvent(new Event('change', { bubbles: true }))
    })

    select(courseFilter, 'course:1')
    expect(summary('Kapazitätsprobleme').querySelector('strong')?.textContent).toBe('0')
    expect(summary('Kapazitätsprobleme').textContent).not.toContain('Bekannt unvollständig')
    expect(summary('Prüfung erforderlich').querySelector('strong')?.textContent).toBe('1')
    expect(summary('Prüfung erforderlich').textContent).not.toContain('Bekannt unvollständig')

    select(courseFilter, 'course:2')
    expect(summary('Kapazitätsprobleme').querySelector('strong')?.textContent).toBe('Nicht verfügbar')
    expect(summary('Prüfung erforderlich').querySelector('strong')?.textContent).toBe('Nicht verfügbar')

    select(courseFilter, '')
    select(cohortCalendarFilter, 'Full-time')
    expect(summary('Kapazitätsprobleme').textContent).toContain('Bekannt unvollständig')
    expect(summary('Prüfung erforderlich').textContent).toContain('Bekannt unvollständig')
  })

  it('uses only planning-eligible courses for filtered outcome coverage', () => {
    const workspace = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    workspace.courses.push({
      ...workspace.courses[0],
      courseRef: 'course:2',
      courseId: 2,
      code: 'C-002',
      name: 'Archived course',
      planningEligible: false,
      remainingTeachingUnits: 0,
      remainingInstructionalMinutes: 0,
      occurrenceRefs: ['teaching:2'],
      outcomeRefs: ['outcome:2'],
      needsReviewReasonRefs: [],
    })
    workspace.occurrences.push({
      ...workspace.occurrences[0],
      occurrenceRef: 'teaching:2',
      courseRef: 'course:2',
    })
    workspace.planningOutcomes.push(
      {
        outcomeRef: 'outcome:1',
        revisionId: 11,
        courseRef: 'course:1',
        operationKind: 'single_course_generation',
        classification: 'successful',
        sourceStatus: 'complete',
        reasons: [],
        completedAt: '2026-09-01T10:00:00Z',
      },
      {
        outcomeRef: 'outcome:2',
        revisionId: 11,
        courseRef: 'course:2',
        operationKind: 'single_course_generation',
        classification: 'failed',
        sourceStatus: 'failed',
        reasons: [{ code: 'RECORD_INACTIVE' }],
        completedAt: '2026-09-01T11:00:00Z',
      },
    )
    workspace.courses[0].outcomeRefs = ['outcome:1']
    workspace.filterFacets.courses = [
      { value: 'course:1', label: 'Algorithms' },
      { value: 'course:2', label: 'Archived course' },
    ]
    const host = renderWorkspace(workspace)
    const courseFilter = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Lehrveranstaltung')!
    const planningFailures = () => [...host.querySelectorAll<HTMLButtonElement>('.summary-card')]
      .find((item) => item.textContent?.includes('Planungsfehler'))!
    const selectCourse = (value: string) => act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(courseFilter, value)
      courseFilter.dispatchEvent(new Event('change', { bubbles: true }))
    })

    selectCourse('course:1')
    expect(planningFailures().textContent).toContain('0 fehlgeschlagen')
    expect(planningFailures().textContent).not.toContain('Bekannt unvollständig')

    selectCourse('course:2')
    expect(planningFailures().querySelector('strong')?.textContent).toBe('Nicht anwendbar')
  })

  it('identifies partial sections and initial failure without false current values', () => {
    const partial = renderWorkspace(partialCalendarWorkspaceFixture() as CalendarWorkspace)
    expect(partial.textContent).toContain('Einige Informationen im Arbeitsbereich sind unvollständig.')
    expect(partial.textContent).toContain('Die genaue Ursache ist nicht verfügbar.')
    act(() => partial.remove())

    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={null}
        loading={false}
        error="Network unavailable."
        intendedContext="Fall 2026 · Revision 2 · Aktuelle Veröffentlichung"
        listContent={<div>Existing Courses overview</div>}
        onRetry={vi.fn()}
      />,
    ))

    expect(host.textContent).toContain('Fall 2026 · Revision 2 · Aktuelle Veröffentlichung')
    expect(host.textContent).toContain('Network unavailable.')
    expect(host.querySelector('.summary-card')).toBeNull()
  })

  it('distinguishes loading, no-semester, no-session, no-match, and last-known refresh states', () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    const common = {
      listContent: <div>Existing Courses overview</div>,
      onRetry: vi.fn(),
    }
    act(() => root.render(<CalendarPlanningWorkspace {...common} workspace={null} loading />))
    expect(host.textContent).toContain('Semester-Arbeitsbereich wird geladen')
    act(() => root.render(<CalendarPlanningWorkspace {...common} workspace={null} loading={false} />))
    expect(host.textContent).toContain('Kein Semester ausgewählt')

    const empty = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    empty.occurrences = []
    empty.holidays = []
    empty.courses[0].occurrenceRefs = []
    empty.workspaceToken = 'empty-schedule'
    act(() => root.render(<CalendarPlanningWorkspace {...common} workspace={empty} loading={false} />))
    expect(host.textContent).toContain('In dieser Periode finden keine Termine statt.')

    const filtered = loadedCalendarWorkspaceFixture() as LoadedCalendarWorkspace
    filtered.workspaceToken = 'no-match'
    filtered.filterFacets.rooms = [{ value: 'room:missing', label: 'Missing room' }]
    act(() => root.render(<CalendarPlanningWorkspace {...common} workspace={filtered} loading={false} />))
    const room = [...host.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Raum')!
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(room, 'room:missing')
      room.dispatchEvent(new Event('change', { bubbles: true }))
    })
    expect(host.textContent).toContain('Keine Datensätze entsprechen den aktiven Filtern.')
    expect([...host.querySelectorAll<HTMLButtonElement>('button')]
      .find((item) => item.textContent === 'Filter zurücksetzen')?.disabled).toBe(false)

    act(() => root.render(
      <CalendarPlanningWorkspace
        {...common}
        workspace={filtered}
        loading={false}
        error="Refresh failed."
        lastKnown
      />,
    ))
    expect(host.textContent).toContain('Der zuletzt bekannte Arbeitsbereich wird angezeigt. Refresh failed.')
  })

  it('applies the lecturer-review access profile without planner controls', () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        accessProfile="lecturer-review"
        fixedContext={<p>Lecturer Dr Ada · fixed by link</p>}
        listContent={<div>Shared occurrence list</div>}
        onRetry={vi.fn()}
      />,
    ))

    expect(host.textContent).toContain('Ihre zugeordnete Planung')
    expect(host.textContent).toContain('Lecturer Dr Ada · fixed by link')
    expect(host.querySelector('.workspace-summary-grid')).toBeNull()
    expect(host.querySelector('.revision-context-switch')).toBeNull()
    expect(
      [...host.querySelectorAll('label')].some(
        (label) => label.textContent?.trim() === 'Lecturer',
      ),
    ).toBe(false)
    expect(host.textContent).not.toContain('Entwurf starten')
  })

  it('renders a neutral restricted context action outside date and filter controls', () => {
    const host = document.createElement('div')
    document.body.append(host)
    const root = createRoot(host)
    act(() => root.render(
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        accessProfile="lecturer-review"
        fixedContext={<p>Lecturer Dr Ada Â· fixed by link</p>}
        contextActions={<button type="button">Kalender herunterladen</button>}
        listContent={<div>Shared occurrence list</div>}
        onRetry={vi.fn()}
      />,
    ))

    const action = button('Kalender herunterladen')!
    expect(action.closest('.calendar-context-header')).not.toBeNull()
    expect(action.closest('.calendar-toolbar')).toBeNull()
    expect(action.closest('.workspace-filters')).toBeNull()
  })
})
