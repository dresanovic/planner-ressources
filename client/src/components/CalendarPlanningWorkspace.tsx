import { useCallback, useEffect, useRef, useState, type ReactNode, type RefObject } from 'react'

import type {
  CalendarMode,
  CalendarWorkspace,
  LoadedCalendarWorkspace,
  WorkspaceMetric,
  WorkspaceOccurrence,
} from '../api/calendarWorkspace'
import {
  currentPeriodDate,
  movePeriod,
  occurrencesInRange,
  projectWorkspace,
  visibleRange,
  type WorkspaceFilters,
} from './calendarWorkspaceUtils'
import { calendarFindingLabel } from './calendarFindingLabel'
import { EuropeanDateField } from './EuropeanDateField'
import { formatCalendarDate, formatCalendarDateRange, institutionLocalToday } from '../utils/datePresentation'
import { safeReasonText } from '../utils/userProblems'
import { label } from '../config/terminology'

type Props = {
  workspace: CalendarWorkspace | null
  loading: boolean
  error?: string
  lastKnown?: boolean
  intendedContext?: string
  listContent: ReactNode | ((context: WorkspaceListContext | null) => ReactNode)
  onRetry: () => void
  onStartDraft?: () => void
  onSelectRevision?: (revisionId: number) => void
  onEditTeaching?: (occurrenceRef: string) => void
  onDeleteTeaching?: (occurrenceRef: string) => void
  onEditExam?: (occurrenceRef: string) => void
  onDeleteExam?: (occurrenceRef: string) => void
  selectedCourseId?: number | null
  onTraceCourse?: (courseId: number | null) => void
  selectedOccurrenceRef?: string | null
  onSelectedOccurrenceChange?: (occurrenceRef: string | null) => void
  renderSessionPane?: (
    occurrence: WorkspaceOccurrence,
    requestClose: () => void,
  ) => ReactNode
  accessProfile?: 'planner' | 'lecturer-review'
  fixedContext?: ReactNode
  contextActions?: ReactNode
  onRequestTargetHidingFilter?: (commitFilter: () => void) => void
}

export type WorkspaceListTraceTarget = {
  reference: string
  label: string
  courseIds: number[]
  teachingSessionIds: number[]
  examIds: number[]
}

export type WorkspaceListContext = {
  courseIds: number[]
  teachingSessionIds: number[]
  examIds: number[]
  activeFilterCount: number
  traceTarget: WorkspaceListTraceTarget | null
}

const MODES: { value: CalendarMode; label: string }[] = [
  { value: 'week', label: 'Woche' },
  { value: 'day', label: 'Tag' },
  { value: 'month', label: 'Monat' },
  { value: 'list', label: 'Liste' },
]

type WorkspaceDrilldown = {
  label: string
  metricKey: keyof LoadedCalendarWorkspace['summary']
  priorMode: CalendarMode
  priorAnchor: string | null
}

type WorkspaceContentProps = Props & {
  mode: CalendarMode
  anchor: string | null
  setMode: (mode: CalendarMode) => void
  setAnchor: (anchor: string | null) => void
  resultsHeadingRef: RefObject<HTMLHeadingElement | null>
  onSelectionDisappeared: (message: string) => void
}

export function CalendarPlanningWorkspace(props: Props) {
  const [mode, setMode] = useState<CalendarMode>('week')
  const [anchor, setAnchor] = useState<string | null>(null)
  const [statusAnnouncement, setStatusAnnouncement] = useState('')
  const resultsHeadingRef = useRef<HTMLHeadingElement>(null)
  const previousLoadState = useRef({ failed: false, refreshing: false })
  const handleSelectionDisappeared = useCallback((message: string) => {
    setStatusAnnouncement(message)
    resultsHeadingRef.current?.focus()
    window.setTimeout(() => resultsHeadingRef.current?.focus(), 0)
  }, [])

  useEffect(() => {
    const failed = Boolean(props.error)
    const refreshing = props.loading && props.workspace != null
    if (
      props.workspace != null
      && !props.loading
      && !props.error
      && (previousLoadState.current.failed || previousLoadState.current.refreshing)
    ) {
      setStatusAnnouncement(
        previousLoadState.current.failed
          ? 'Der Kalender-Arbeitsbereich wurde mit aktuellen Daten wiederhergestellt.'
          : 'Der Kalender-Arbeitsbereich wurde mit aktuellen Daten aktualisiert.',
      )
    }
    previousLoadState.current = { failed, refreshing }
  }, [props.error, props.loading, props.workspace])

  return (
    <>
      <CalendarPlanningWorkspaceContent
        {...props}
        mode={mode}
        anchor={anchor}
        setMode={setMode}
        setAnchor={setAnchor}
        resultsHeadingRef={resultsHeadingRef}
        onSelectionDisappeared={handleSelectionDisappeared}
      />
      <p
        className="sr-only"
        role="status"
        aria-live="polite"
        data-workspace-recovery-announcement
      >
        {statusAnnouncement}
      </p>
    </>
  )
}

function CalendarPlanningWorkspaceContent({
  workspace,
  loading,
  error,
  lastKnown = false,
  intendedContext,
  listContent,
  onRetry,
  onStartDraft,
  onSelectRevision,
  onEditTeaching,
  onDeleteTeaching,
  onEditExam,
  onDeleteExam,
  selectedCourseId,
  onTraceCourse,
  selectedOccurrenceRef,
  onSelectedOccurrenceChange,
  renderSessionPane,
  accessProfile = 'planner',
  fixedContext,
  contextActions,
  onRequestTargetHidingFilter,
  mode,
  anchor,
  setMode,
  setAnchor,
  resultsHeadingRef,
  onSelectionDisappeared,
}: WorkspaceContentProps) {
  const restricted = accessProfile === 'lecturer-review'
  const [filters, setFilters] = useState<WorkspaceFilters>({})
  const [internalSelectedRef, setInternalSelectedRef] = useState<string | null>(null)
  const selectedRef = selectedOccurrenceRef === undefined ? internalSelectedRef : selectedOccurrenceRef
  const updateSelection = useCallback((reference: string | null) => {
    if (selectedOccurrenceRef === undefined) setInternalSelectedRef(reference)
    onSelectedOccurrenceChange?.(reference)
  }, [onSelectedOccurrenceChange, selectedOccurrenceRef])
  const [listTraceRef, setListTraceRef] = useState<string | null>(null)
  const [drilldown, setDrilldown] = useState<WorkspaceDrilldown | null>(null)
  const detailHeading = useRef<HTMLHeadingElement>(null)
  const drilldownHeading = useRef<HTMLHeadingElement>(null)
  const drilldownInitiator = useRef<HTMLButtonElement | null>(null)
  const priorTraceCourseId = useRef<number | null | undefined>(undefined)
  const workspaceIdentity = useRef<string | null>(null)

  useEffect(() => {
    if (workspace?.workspaceState !== 'loaded') {
      workspaceIdentity.current = null
      return
    }
    const nextIdentity = [
      workspace.semester.semesterId,
      workspace.selectedRevision.revisionId,
      workspace.selectedRevision.designation,
    ].join(':')
    const identityChanged = (
      workspaceIdentity.current != null
      && workspaceIdentity.current !== nextIdentity
    )
    workspaceIdentity.current = nextIdentity

    if (identityChanged) {
      const hadSelection = selectedRef != null
      setFilters({})
      queueMicrotask(() => updateSelection(null))
      setListTraceRef(null)
      setDrilldown(null)
      if (hadSelection) {
        onSelectionDisappeared(
          'Der ausgewählte Termin ist in der ausgewählten Revision nicht mehr verfügbar.',
        )
      }
      return
    }

    setFilters((current) => reconcileFilters(current, workspace))
    if (
      selectedRef != null
      && !workspace.occurrences.some((item) => item.occurrenceRef === selectedRef)
    ) {
      queueMicrotask(() => updateSelection(null))
      onSelectionDisappeared(
        'Der ausgewählte Termin ist im aktualisierten Arbeitsbereich nicht mehr verfügbar.',
      )
    }
    if (
      drilldown != null
      && workspace.summary[drilldown.metricKey].contributorRefs.length === 0
    ) {
      queueMicrotask(() => setDrilldown(null))
    }
  }, [drilldown, onSelectionDisappeared, selectedRef, updateSelection, workspace])

  useEffect(() => {
    if (drilldown != null) drilldownHeading.current?.focus()
  }, [drilldown])

  useEffect(() => {
    if (
      workspace?.workspaceState !== 'loaded' ||
      selectedRef === null ||
      mode === 'list'
    ) {
      return
    }
    const occurrence = workspace.occurrences.find(
      (item) => item.occurrenceRef === selectedRef,
    )
    if (occurrence === undefined) return
    const effective = anchor ?? currentPeriodDate(
      institutionLocalToday(),
      workspace.semester.startDate,
      workspace.semester.endDate,
    ).date
    const selectedRange = visibleRange(mode, effective)
    if (
      selectedRange !== null &&
      (occurrence.date < selectedRange.start ||
        occurrence.date > selectedRange.end)
    ) {
      queueMicrotask(() => setAnchor(occurrence.date))
    }
  }, [anchor, mode, selectedRef, setAnchor, workspace])

  if (loading && workspace == null) return <section className="calendar-workspace workspace-state" aria-busy="true" role="status">{intendedContext ?? 'Semester-Arbeitsbereich'} wird geladen…</section>
  if (error && workspace == null) return <section className="calendar-workspace workspace-state"><div role="alert"><h2>Kalender-Arbeitsbereich nicht verfügbar</h2>{intendedContext && <p>{intendedContext}</p>}<p>{error}</p><button type="button" onClick={onRetry}>Erneut laden</button></div>{!restricted && <p>Die vorhandene Übersicht der {label('course.plural')} bleibt verfügbar, während der zusammenhängende Arbeitsbereich nicht geladen werden kann.</p>}<div className="workspace-list-mode">{renderListContent(listContent, null)}</div></section>
  if (workspace == null) return <section className="calendar-workspace workspace-state"><h2>Kein Semester ausgewählt</h2><p>Wählen Sie ein Semester, um den Planungsbereich zu öffnen.</p></section>
  if (workspace.workspaceState === 'no_revision') {
    return (
      <section className="calendar-workspace workspace-state" aria-labelledby="calendar-workspace-title" aria-busy={loading}>
        <p className="eyebrow">{workspace.semester.name}</p>
        <h2 id="calendar-workspace-title">Semesterplanung</h2>
        <p>Es gibt noch keine Planungsrevision. Starten Sie einen Entwurf, um Lehr- und Prüfungstermine zu planen.</p>
        {error && <div className="refresh-error" role="alert"><span>Der zuletzt bekannte Stand ohne Revision wird angezeigt. {error}</span><button type="button" onClick={onRetry}>Erneut laden</button></div>}
        {onStartDraft && <button type="button" className="generate-button" onClick={onStartDraft}>Entwurf starten</button>}
      </section>
    )
  }
  const loadedWorkspace = workspace
  const impairedSections = Object.entries(workspace.sectionStatus).filter(
    ([name, status]) => status.availability !== 'available'
      && (!restricted || name === 'validationFindings'),
  )

  const effectiveAnchor = anchor ?? currentPeriodDate(institutionLocalToday(), workspace.semester.startDate, workspace.semester.endDate).date
  const range = visibleRange(mode, effectiveAnchor)
  const projection = projectWorkspace(workspace, filters)
  const visibleOccurrences = occurrencesInRange(projection.occurrences, range)
  const visibleHolidays = workspace.holidays.filter((holiday) => (
    range != null && holiday.date >= range.start && holiday.date <= range.end
  ))
  const selectedOccurrence = workspace.occurrences.find((item) => item.occurrenceRef === selectedRef) ?? null
  const activeFilterCount = Object.values(filters).filter(Boolean).length
  const summary = filteredSummary(workspace, projection.courses.map((item) => item.courseRef), projection.occurrences.map((item) => item.occurrenceRef), activeFilterCount > 0)
  const summaryScope = activeFilterCount > 0 ? 'Gefilterte Teilmenge' : 'Vollständige Revision'
  const drilldownMetric = drilldown == null ? null : summary[drilldown.metricKey]
  const listContext = workspaceListContext(
    workspace,
    projection.courses.map((item) => item.courseId),
    projection.occurrences,
    activeFilterCount,
    listTraceRef,
  )

  function chooseOccurrence(reference: string) {
    setListTraceRef(null)
    updateSelection(reference)
    if (!renderSessionPane) window.setTimeout(() => detailHeading.current?.focus({ preventScroll: true }), 0)
  }

  function closeOccurrenceDetail() {
    const reference = selectedRef
    updateSelection(null)
    window.setTimeout(() => {
      const target = [...document.querySelectorAll<HTMLButtonElement>('[data-occurrence-ref]')]
        .find((item) => item.dataset.occurrenceRef === reference)
      target?.focus()
    }, 0)
  }

  function applyFilter<Key extends keyof WorkspaceFilters>(
    key: Key,
    value: WorkspaceFilters[Key],
  ) {
    const nextFilters = { ...filters, [key]: value }
    const hidesSelected = (
      selectedRef != null
      && !projectWorkspace(loadedWorkspace, nextFilters).occurrences.some(
        (item) => item.occurrenceRef === selectedRef,
      )
    )
    const commitFilter = () => {
      setFilters(nextFilters)
      if (hidesSelected) {
        onSelectionDisappeared(
          'Der ausgewählte Termin entspricht nicht mehr der aktuellen Ergebnismenge.',
        )
      }
    }
    if (hidesSelected && onRequestTargetHidingFilter) {
      onRequestTargetHidingFilter(commitFilter)
      return
    }
    commitFilter()
    if (hidesSelected) updateSelection(null)
  }

  function goCurrent() {
    if (mode === 'list') return
    const current = currentPeriodDate(institutionLocalToday(), loadedWorkspace.semester.startDate, loadedWorkspace.semester.endDate)
    setAnchor(current.date)
    if (current.substituted) {
      const boundary = current.date === loadedWorkspace.semester.startDate ? 'start' : 'end'
      announce(`Der heutige Tag liegt außerhalb des Semesters. Die ${boundary === 'start' ? 'erste' : 'letzte'} Semesterperiode wird angezeigt.`)
    } else announce('Die aktuelle Periode wird angezeigt.')
  }

  return (
    <section className="calendar-workspace" aria-labelledby="calendar-workspace-title" aria-busy={loading}>
      <header className="calendar-context-header">
        <div>
          <p className="eyebrow">{workspace.semester.name} · {formatCalendarDateRange(workspace.semester.startDate, workspace.semester.endDate)}</p>
          <h2 id="calendar-workspace-title">{restricted ? 'Ihre zugeordnete Planung' : 'Semesterplanung'}</h2>
          <p>
            {revisionLabel(workspace.selectedRevision)} · {stateLabel(workspace.selectedRevision.lifecycleState)} ·{' '}
            {workspace.selectedRevision.designation === 'active_working' ? 'Aktive Arbeitsrevision' : 'Aktuelle Veröffentlichung'}
          </p>
          {!restricted && workspace.selectedRevision.readOnly && <p className="read-only-note">Veröffentlichte Inhalte sind schreibgeschützt. Hinweise werden anhand der aktuellen Planungsdaten neu berechnet, ohne die Veröffentlichung zu ändern.</p>}
          {restricted && fixedContext}
        </div>
        {restricted && contextActions && (
          <div className="calendar-context-actions">{contextActions}</div>
        )}
        {!restricted && <div className="revision-context-switch" aria-label="Planungsrevision">
          {workspace.availableContexts.activeWorking && <button type="button" aria-pressed={workspace.selectedRevision.designation === 'active_working'} onClick={() => onSelectRevision?.(workspace.availableContexts.activeWorking!.revisionId)}>Arbeitsrevision R{workspace.availableContexts.activeWorking.revisionNumber}</button>}
          {workspace.availableContexts.currentPublished && <button type="button" aria-pressed={workspace.selectedRevision.designation === 'current_published'} onClick={() => onSelectRevision?.(workspace.availableContexts.currentPublished!.revisionId)}>Veröffentlichung R{workspace.availableContexts.currentPublished.revisionNumber}</button>}
        </div>}
      </header>

      {loading && <p className="active-filter-status" role="status">Der Arbeitsbereich wird aktualisiert. Bis zum Abschluss werden die zuletzt bekannten Werte angezeigt.</p>}
      {error && <div className="refresh-error" role="alert"><span>{lastKnown ? `Der zuletzt bekannte Arbeitsbereich wird angezeigt. ${error}` : error}</span><button type="button" onClick={onRetry}>Erneut laden</button></div>}
      {impairedSections.length > 0 && (
        <div className="partial-workspace-status" role="status">
          <strong>Einige Informationen im Arbeitsbereich sind unvollständig.</strong>
          <ul>
            {impairedSections.map(([name, status]) => (
              <li key={name}>{workspaceSectionLabel(name)}: {availabilityLabel(status.availability)}{status.reason ? ` · ${safeWorkspaceReason()}` : ''}</li>
            ))}
          </ul>
        </div>
      )}

      {!restricted && <div className="workspace-summary-grid" aria-label={`${activeFilterCount ? 'Gefilterte' : 'Vollständige'} operative Revisionsübersicht`}>
        <SummaryCard metricKey="unscheduledWork" label="Offener Planungsumfang" metric={summary.unscheduledWork} value={formatUnscheduled(summary.unscheduledWork)} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="conflicts" label="Konflikte" metric={summary.conflicts} value={formatMetric(summary.conflicts, 'distinctFindingCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="capacityIssues" label="Kapazitätsprobleme" metric={summary.capacityIssues} value={formatMetric(summary.capacityIssues, 'affectedOccurrenceCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="planningFailures" label="Planungsfehler" metric={summary.planningFailures} value={formatPlanningOutcomes(summary.planningFailures)} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="needsReview" label="Prüfung erforderlich" metric={summary.needsReview} value={formatMetric(summary.needsReview, 'distinctCourseCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
      </div>}

      {!restricted && drilldown && drilldownMetric && (
        <section className="workspace-drilldown" aria-labelledby="drilldown-title">
          <div><h3 id="drilldown-title" tabIndex={-1} ref={drilldownHeading} data-workspace-drilldown-heading>Datensätze für „{drilldown.label}“</h3><p>{drilldownMetric.contributorRefs.length} {drilldownMetric.contributorRefs.length === 1 ? 'betroffener Datensatz' : 'betroffene Datensätze'} in der {activeFilterCount ? 'gefilterten Teilmenge' : 'vollständigen Revision'}.</p></div>
          <button type="button" onClick={clearDrilldown}>Detailauswahl aufheben</button>
          <ul>{drilldownMetric.contributorRefs.map((ref) => {
            const problems = contributorProblems(workspace, ref)
            return <li key={ref}>
              <button type="button" onClick={() => navigateContributor(ref)}>{contributorLabel(workspace, ref)}</button>
              {problems.length > 0 && <ul className="workspace-contributor-problems">{problems.map((problem, index) => <li key={`${ref}-problem-${index}`}>{problem}</li>)}</ul>}
            </li>
          })}</ul>
        </section>
      )}

      <div className="calendar-toolbar">
        <div className="calendar-mode-switch" aria-label="Kalenderansicht">
          {MODES.map((item) => <button type="button" key={item.value} aria-pressed={mode === item.value} onClick={() => { setMode(item.value); if (item.value !== 'list') setListTraceRef(null) }}>{item.label}</button>)}
        </div>
        <div className="calendar-date-controls" aria-label="Kalenderdatum">
          <button type="button" disabled={mode === 'list'} onClick={() => setAnchor(movePeriod(mode, effectiveAnchor, -1))} aria-label="Vorherige Periode">←</button>
          <button type="button" disabled={mode === 'list'} onClick={goCurrent}>{mode === 'list' ? 'Aktuelle Periode nicht anwendbar' : 'Aktuell'}</button>
          <button type="button" disabled={mode === 'list'} onClick={() => setAnchor(movePeriod(mode, effectiveAnchor, 1))} aria-label="Nächste Periode">→</button>
          <EuropeanDateField id="calendar-anchor-date" className="constraint-field calendar-anchor-field" label="Kalenderdatum" value={effectiveAnchor} min={workspace.semester.startDate} max={workspace.semester.endDate} disabled={mode === 'list'} onChange={(value) => { if (value) setAnchor(value) }} required />
          {range && <span className="visible-range-group">
            <span className="visible-range-label">Angezeigter Zeitraum</span>
            <span className="visible-range">{range.start === range.end ? formatCalendarDate(range.start) : formatCalendarDateRange(range.start, range.end)}</span>
          </span>}
        </div>
      </div>

      <div className="workspace-filters" aria-label="Filter des Arbeitsbereichs">
        <FacetSelect label={label('course.fieldLabel')} value={filters.course} values={workspace.filterFacets.courses} onChange={(value) => applyFilter('course', value)} />
        <FacetSelect label={label('cohort.fieldLabel')} value={filters.cohort} values={workspace.filterFacets.cohorts} onChange={(value) => applyFilter('cohort', value)} />
        {!restricted && <FacetSelect label={label('lecturer.fieldLabel')} value={filters.lecturer} values={workspace.filterFacets.lecturers} onChange={(value) => applyFilter('lecturer', value)} />}
        <FacetSelect label={label('room.fieldLabel')} value={filters.room} values={workspace.filterFacets.rooms} onChange={(value) => applyFilter('room', value)} />
        <FacetSelect label="Studienart" value={filters.studyType} values={workspace.filterFacets.studyTypes} onChange={(value) => applyFilter('studyType', value)} />
        <FacetSelect label="Terminart" value={filters.sessionType} values={workspace.filterFacets.sessionTypes} onChange={(value) => applyFilter('sessionType', value as WorkspaceFilters['sessionType'])} />
        <FacetSelect label="Revisionsstatus" value={filters.lifecycle} values={workspace.filterFacets.lifecycleContexts} onChange={(value) => applyFilter('lifecycle', value)} />
        <FacetSelect label="Prüfstatus" value={filters.validation} values={workspace.filterFacets.validationCategories} onChange={(value) => applyFilter('validation', value)} />
        <button type="button" disabled={activeFilterCount === 0 && drilldown == null} onClick={clearFiltersAndDrilldown}>Filter zurücksetzen</button>
      </div>
      {activeFilterCount > 0 && <p className="active-filter-status" role="status">{activeFilterCount} aktive {activeFilterCount === 1 ? 'Filterbedingung' : 'Filterbedingungen'} · {projection.courses.length} {label('course.plural')} · {projection.occurrences.length} Termine</p>}

      <div className={`calendar-pane-layout${selectedOccurrence ? ' has-session-pane' : ''}`}>
        <div className="calendar-projection">
          <h3
            className="sr-only"
            tabIndex={-1}
            ref={resultsHeadingRef}
            data-workspace-results-heading
          >
            Kalenderergebnisse
          </h3>
          <div
            className="workspace-list-mode"
            aria-label="Listenansicht"
            hidden={mode !== 'list'}
          >
            {renderListContent(listContent, listContext)}
          </div>
          {mode !== 'list' && (
            visibleOccurrences.length === 0 && visibleHolidays.length === 0 ? (
              <p className="empty-state">{projection.occurrences.length === 0 && activeFilterCount > 0 ? 'Keine Datensätze entsprechen den aktiven Filtern.' : restricted && workspace.occurrences.length === 0 ? `In dieser Revision gibt es derzeit keine Lehr- oder Prüfungszuordnungen für diese ${label('lecturer.singular')}.` : 'In dieser Periode finden keine Termine statt.'}</p>
            ) : (
              <>
                {visibleOccurrences.length === 0 && activeFilterCount > 0 && <p className="empty-state">Keine Datensätze entsprechen den aktiven Filtern. Feiertage bleiben zur Einordnung sichtbar.</p>}
                <CalendarSurface mode={mode} occurrences={visibleOccurrences} holidays={visibleHolidays} courses={workspace.courses} selectedRef={selectedRef} onSelect={chooseOccurrence} semesterStart={workspace.semester.startDate} semesterEnd={workspace.semester.endDate} />
              </>
            )
          )}
        </div>
        {selectedOccurrence && renderSessionPane?.(selectedOccurrence, closeOccurrenceDetail)}
        {selectedOccurrence && !renderSessionPane && (
          <OccurrenceDetail
            occurrence={selectedOccurrence}
            workspace={workspace}
            headingRef={detailHeading}
            onClose={closeOccurrenceDetail}
            onEditTeaching={onEditTeaching}
            onDeleteTeaching={onDeleteTeaching}
            onEditExam={onEditExam}
            onDeleteExam={onDeleteExam}
          />
        )}
      </div>
      <p className="sr-only" id="calendar-workspace-announcer" aria-live="polite" />
    </section>
  )

  function activateMetric(
    metricKey: keyof LoadedCalendarWorkspace['summary'],
    label: string,
    metric: WorkspaceMetric,
    initiator: HTMLButtonElement,
  ) {
    if (metric.availability === 'available' || metric.availability === 'partial') {
      drilldownInitiator.current = initiator
      setDrilldown({
        label,
        metricKey,
        priorMode: mode,
        priorAnchor: anchor,
      })
    }
  }

  function clearDrilldown() {
    const focusTarget = drilldownInitiator.current
    if (drilldown) {
      setMode(drilldown.priorMode)
      setAnchor(drilldown.priorAnchor)
    }
    updateSelection(null)
    setDrilldown(null)
    setListTraceRef(null)
    if (priorTraceCourseId.current !== undefined) {
      onTraceCourse?.(priorTraceCourseId.current)
      priorTraceCourseId.current = undefined
    }
    window.setTimeout(() => {
      if (focusTarget?.isConnected && !focusTarget.disabled) {
        focusTarget.focus()
        if (document.activeElement === focusTarget) return
      }
      resultsHeadingRef.current?.focus()
    }, 0)
  }

  function clearFiltersAndDrilldown() {
    setFilters({})
    if (drilldown) {
      clearDrilldown()
      return
    }
    setListTraceRef(null)
  }

  function navigateContributor(ref: string) {
    if (ref.startsWith('teaching:') || ref.startsWith('exam:')) {
      const occurrence = loadedWorkspace.occurrences.find((item) => item.occurrenceRef === ref)
      if (occurrence) {
        setMode('day')
        setAnchor(occurrence.date)
        chooseOccurrence(ref)
      }
      return
    }
    const traceTarget = resolveListTraceTarget(
      loadedWorkspace,
      ref,
      new Set(projection.occurrences.map((item) => item.occurrenceRef)),
    )
    if (traceTarget.courseIds[0] != null) {
      if (priorTraceCourseId.current === undefined) {
        priorTraceCourseId.current = selectedCourseId
      }
      onTraceCourse?.(traceTarget.courseIds[0])
    }
    setListTraceRef(ref)
    setMode('list')
  }
}

function CalendarSurface({ mode, occurrences, holidays, courses, selectedRef, onSelect, semesterStart, semesterEnd }: { mode: Exclude<CalendarMode, 'list'>; occurrences: WorkspaceOccurrence[]; holidays: LoadedCalendarWorkspace['holidays']; courses: LoadedCalendarWorkspace['courses']; selectedRef: string | null; onSelect: (ref: string) => void; semesterStart: string; semesterEnd: string }) {
  const courseByRef = new Map(courses.map((item) => [item.courseRef, item]))
  const dates = [...new Set([...occurrences.map((item) => item.date), ...holidays.map((item) => item.date)])].sort()
  const [expandedDates, setExpandedDates] = useState<Set<string>>(() => new Set())
  return (
    <div className={`calendar-surface calendar-${mode}`} role="grid" aria-label={`${mode} calendar`}>
      {dates.map((date) => (
        <section className={`calendar-date-column ${date < semesterStart || date > semesterEnd ? 'outside-semester' : ''}`} key={date} role="row" aria-label={formatCalendarDate(date)}>
          <h3>{new Intl.DateTimeFormat('de-AT', { weekday: 'short', timeZone: 'UTC' }).format(new Date(`${date}T12:00:00Z`))}, {formatCalendarDate(date)}</h3>
          {mode === 'month' && occurrences.filter((item) => item.date === date).length > 3 && (
            <p className="calendar-date-count">{occurrences.filter((item) => item.date === date).length} Termine</p>
          )}
          {holidays.filter((item) => item.date === date).map((holiday) => (
            <p className="calendar-holiday" key={holiday.holidayRef}><span aria-hidden="true">◆</span> Holiday: {holiday.name}</p>
          ))}
          <div className="calendar-date-items" role="gridcell">
            {(mode === 'month' && occurrences.filter((item) => item.date === date).length > 3 && !expandedDates.has(date)
              ? occurrences.filter((item) => item.date === date).slice(0, 3)
              : occurrences.filter((item) => item.date === date)
            ).map((item) => (
              <button type="button" key={item.occurrenceRef} data-occurrence-ref={item.occurrenceRef} className={`calendar-occurrence ${item.kind} ${item.findingRefs.length ? 'has-warning' : ''}`} aria-pressed={selectedRef === item.occurrenceRef} onClick={() => onSelect(item.occurrenceRef)}>
                <span className="occurrence-kind">{item.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'}</span>
                <strong>{courseByRef.get(item.courseRef)?.name ?? item.courseRef}</strong>
                <span>{item.startTime}–{item.endTime}</span>
                <span>{item.cohort}</span>
                {item.findingRefs.length > 0 && <span className="warning-label">⚠ {item.findingRefs.length} {item.findingRefs.length === 1 ? 'aktueller Hinweis' : 'aktuelle Hinweise'}</span>}
              </button>
            ))}
            {mode === 'month' && occurrences.filter((item) => item.date === date).length > 3 && (
              <button
                type="button"
                className="calendar-date-continuation"
                aria-expanded={expandedDates.has(date)}
                onClick={() => setExpandedDates((current) => {
                  const next = new Set(current)
                  if (next.has(date)) next.delete(date)
                  else next.add(date)
                  return next
                })}
              >
                {expandedDates.has(date)
                  ? 'Weniger Termine anzeigen'
                  : `Alle ${occurrences.filter((item) => item.date === date).length} Termine anzeigen`}
              </button>
            )}
          </div>
        </section>
      ))}
    </div>
  )
}

function OccurrenceDetail({ occurrence, workspace, headingRef, onClose, onEditTeaching, onDeleteTeaching, onEditExam, onDeleteExam }: { occurrence: WorkspaceOccurrence; workspace: LoadedCalendarWorkspace; headingRef: RefObject<HTMLHeadingElement | null>; onClose: () => void; onEditTeaching?: (ref: string) => void; onDeleteTeaching?: (ref: string) => void; onEditExam?: (ref: string) => void; onDeleteExam?: (ref: string) => void }) {
  const course = workspace.courses.find((item) => item.courseRef === occurrence.courseRef)
  const findings = workspace.validationFindings.filter((item) => occurrence.findingRefs.includes(item.findingRef))
  return (
    <aside className="occurrence-detail" aria-labelledby="occurrence-detail-title">
      <div className="detail-heading"><h3 id="occurrence-detail-title" tabIndex={-1} ref={headingRef}>{occurrence.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'} · {course?.name}</h3><button type="button" onClick={onClose} aria-label="Termindetails schließen">×</button></div>
      <dl>
        <div><dt>Status</dt><dd>{stateLabel(workspace.selectedRevision.lifecycleState)}</dd></div>
        <div><dt>Revision</dt><dd>{revisionLabel(workspace.selectedRevision)} · {workspace.selectedRevision.designation === 'active_working' ? 'Arbeitsrevision' : 'Aktuelle Veröffentlichung'}</dd></div>
        <div><dt>{label('course.fieldLabel')}</dt><dd>{course?.name ?? occurrence.courseRef}</dd></div>
        <div><dt>Studienart</dt><dd>{course?.studyType ?? 'Nicht verfügbar'}</dd></div>
        <div><dt>Datum und Uhrzeit</dt><dd>{formatCalendarDate(occurrence.date)}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
        <div><dt>{label('cohort.fieldLabel')}</dt><dd>{occurrence.cohort}</dd></div>
        <div><dt>{label('lecturer.fieldLabel')}</dt><dd>{occurrence.lecturerRefs.join(', ')}</dd></div>
        <div><dt>{label('room.fieldLabel')}</dt><dd>{occurrence.kind === 'exam' ? `${occurrence.assignedRoomName} (${occurrence.roomRef})` : occurrence.roomRef}</dd></div>
        {occurrence.kind === 'teaching' ? (
          <>
            <div><dt>Lehreinheiten</dt><dd>{occurrence.teachingUnits}</dd></div>
            {occurrence.source !== undefined && <div><dt>Herkunft</dt><dd>{occurrence.source}</dd></div>}
          </>
        ) : (
          <>
            <div><dt>Prüfungsart</dt><dd>{occurrence.examType}</dd></div>
            <div><dt>Dauer</dt><dd>{occurrence.durationMinutes} Minuten</dd></div>
            {occurrence.requiredCapacity !== undefined && <div><dt>Kapazität</dt><dd>{occurrence.requiredCapacity} erforderlich; {occurrence.currentRoomCapacity == null ? 'aktuelle Raumkapazität nicht verfügbar' : `${occurrence.currentRoomCapacity} aktuell`}</dd></div>}
            {occurrence.validityContext && <>
              <div><dt>Konfiguration</dt><dd>{detailValue(occurrence.validityContext.configurationIdentifier)} · Revision {detailValue(occurrence.validityContext.configurationRevision)}</dd></div>
              <div><dt>Letzte Lehrveranstaltung</dt><dd>{formatCalendarDate(occurrence.validityContext.finalTeachingDate)} um {detailValue(occurrence.validityContext.finalTeachingEndTime)}</dd></div>
              <div><dt>Herkunft</dt><dd>{detailValue(occurrence.validityContext.source)}</dd></div>
            </>}
            {occurrence.recommendationContext && <div><dt>Empfohlener Zeitraum</dt><dd>{formatCalendarDateRange(occurrence.recommendationContext.recommendedStartDate, occurrence.recommendationContext.recommendedEndDate)}{occurrence.recommendationContext.recommendationWasOverridden === true ? ' · manuell festgelegt' : ''}</dd></div>}
          </>
        )}
      </dl>
      <section aria-labelledby="current-warnings-title"><h4 id="current-warnings-title">Aktuelle Hinweise</h4>{findings.length ? <ul>{findings.map((item) => <li key={item.findingRef}>{calendarFindingLabel(item)}</li>)}</ul> : <p>Keine aktuellen Hinweise.</p>}</section>
      {workspace.selectedRevision.readOnly ? <p className="read-only-note">In der aktuellen Veröffentlichung sind keine Korrekturen möglich. Öffnen Sie die Arbeitsrevision, um Änderungen vorzunehmen.</p> : (
        <div className="detail-actions">
          {occurrence.kind === 'teaching' ? <>{onEditTeaching && <button type="button" onClick={() => onEditTeaching(occurrence.occurrenceRef)}>Im vorhandenen Editor bearbeiten</button>}{onDeleteTeaching && <button type="button" className="destructive-button" onClick={() => onDeleteTeaching(occurrence.occurrenceRef)}>Mit Bestätigung löschen</button>}</> : <>{onEditExam && <button type="button" onClick={() => onEditExam(occurrence.occurrenceRef)}>Im vorhandenen Editor bearbeiten</button>}{onDeleteExam && <button type="button" className="destructive-button" onClick={() => onDeleteExam(occurrence.occurrenceRef)}>Mit Bestätigung löschen</button>}</>}
        </div>
      )}
    </aside>
  )
}

function SummaryCard({ metricKey, label, metric, value, scopeLabel, onActivate }: { metricKey: keyof LoadedCalendarWorkspace['summary']; label: string; metric: WorkspaceMetric; value: string; scopeLabel: string; onActivate: (metricKey: keyof LoadedCalendarWorkspace['summary'], label: string, metric: WorkspaceMetric, initiator: HTMLButtonElement) => void }) {
  const actionable = (metric.availability === 'available' || metric.availability === 'partial') && metric.contributorRefs.length > 0
  return <button type="button" className={`summary-card availability-${metric.availability}`} disabled={!actionable} onClick={(event) => onActivate(metricKey, label, metric, event.currentTarget)} aria-label={`${label}: ${value}. ${scopeLabel}. ${actionable ? 'Beitragende Datensätze anzeigen.' : ''}`}><span>{label}</span><strong>{value}</strong><small>{metric.availability === 'partial' ? 'Bekannt unvollständig · ' : ''}{scopeLabel}</small></button>
}

function reconcileFilters(
  filters: WorkspaceFilters,
  workspace: LoadedCalendarWorkspace,
): WorkspaceFilters {
  const facets: Record<keyof WorkspaceFilters, { value: string }[]> = {
    course: workspace.filterFacets.courses,
    cohort: workspace.filterFacets.cohorts,
    lecturer: workspace.filterFacets.lecturers,
    room: workspace.filterFacets.rooms,
    studyType: workspace.filterFacets.studyTypes,
    sessionType: workspace.filterFacets.sessionTypes,
    lifecycle: workspace.filterFacets.lifecycleContexts,
    validation: workspace.filterFacets.validationCategories,
  }
  let changed = false
  const next = { ...filters }
  for (const key of Object.keys(facets) as (keyof WorkspaceFilters)[]) {
    const value = filters[key]
    if (value != null && !facets[key].some((facet) => facet.value === value)) {
      delete next[key]
      changed = true
    }
  }
  return changed ? next : filters
}

function FacetSelect({ label, value, values, onChange }: { label: string; value?: string; values: { value: string; label: string }[]; onChange: (value: string | undefined) => void }) {
  if (values.length === 0) return null
  return <label><span>{label}</span><select value={value ?? ''} onChange={(event) => onChange(event.target.value || undefined)}><option value="">Alle</option>{values.map((item) => <option key={item.value} value={item.value}>{facetOptionLabel(item.value, item.label)}</option>)}</select></label>
}

function facetOptionLabel(value: string, fallback: string): string {
  return ({
    teaching: 'Lehrtermin', exam: 'Prüfungstermin',
    active_working: 'Arbeitsrevision', current_published: 'Aktuelle Veröffentlichung',
    working: 'Arbeitsrevision', published: 'Veröffentlicht', draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung',
  } as Record<string, string>)[value.toLowerCase()] ?? fallback
}

function filteredSummary(workspace: LoadedCalendarWorkspace, courseRefs: string[], occurrenceRefs: string[], filtered: boolean): LoadedCalendarWorkspace['summary'] {
  if (!filtered) return workspace.summary
  const courseSet = new Set(courseRefs)
  const occurrenceSet = new Set(occurrenceRefs)
  const courses = workspace.courses.filter((item) => courseSet.has(item.courseRef))
  const findings = workspace.validationFindings.filter((item) => item.affectedOccurrenceRefs.some((ref) => occurrenceSet.has(ref)))
  const eligibleCourseRefs = new Set(
    courses
      .filter((item) => item.planningEligible)
      .map((item) => item.courseRef),
  )
  const outcomes = workspace.planningOutcomes.filter(
    (item) => eligibleCourseRefs.has(item.courseRef),
  )
  const remaining = courses.filter((item) => item.remainingTeachingUnits > 0)
  const conflicts = findings.filter((item) => item.category.endsWith('_conflict'))
  const capacity = findings.filter((item) => item.category === 'room_capacity')
  const capacityUnverifiedRefs = new Set(findings.flatMap((item) => (
    item.details.kind === 'other'
    && item.details.issueCode === 'VALIDATION_DATA_MISSING'
    && item.details.roomRef != null
      ? item.affectedOccurrenceRefs
      : []
  )))
  const validationUnverifiedCourseRefs = new Set(findings.flatMap((item) => (
    item.details.kind === 'other'
    && ['VALIDATION_DATA_MISSING', 'HOLIDAY_DATA_MISSING'].includes(item.details.issueCode)
      ? item.affectedCourseRefs
      : []
  )))
  const verifiedNeeds = courses.filter((item) => (
    item.needsReviewReasonRefs.length > 0
    && !validationUnverifiedCourseRefs.has(item.courseRef)
  ))
  const capacityMetric = coverageMetric({
    applicableCount: occurrenceSet.size,
    unverifiedCount: capacityUnverifiedRefs.size,
    value: {
      affectedOccurrenceCount: new Set(
        capacity.flatMap((item) => item.affectedOccurrenceRefs)
          .filter((ref) => occurrenceSet.has(ref)),
      ).size,
    },
    contributorRefs: [
      ...new Set(
        capacity.flatMap((item) => item.affectedOccurrenceRefs)
          .filter((ref) => occurrenceSet.has(ref)),
      ),
    ],
    notApplicableReason: 'Kein geplanter Termin entspricht den Filtern.',
    unavailableReason: `Für alle passenden Termine fehlen Kapazitätsdaten der ${label('room.plural')}.`,
  })
  const needsReviewMetric = coverageMetric({
    applicableCount: courses.length,
    unverifiedCount: validationUnverifiedCourseRefs.size,
    value: { distinctCourseCount: verifiedNeeds.length },
    contributorRefs: verifiedNeeds.map((item) => item.courseRef),
    notApplicableReason: `Kein Semesterkontext einer ${label('course.singular')} entspricht den Filtern.`,
    unavailableReason: `Für alle passenden ${label('course.plural')} fehlen aktuelle Prüfdaten.`,
  })
  return {
    unscheduledWork: workspace.summary.unscheduledWork.availability === 'unavailable' ? workspace.summary.unscheduledWork : courses.length ? { availability: 'available', scope: 'complete_revision', remainingTeachingUnits: courses.reduce((sum, item) => sum + item.remainingTeachingUnits, 0), remainingInstructionalMinutes: courses.reduce((sum, item) => sum + item.remainingInstructionalMinutes, 0), contributingCourseCount: remaining.length, contributorRefs: remaining.map((item) => item.courseRef) } : notApplicable(`Kein Semesterkontext einer ${label('course.singular')} entspricht den Filtern.`),
    conflicts: workspace.summary.conflicts.availability === 'unavailable' ? workspace.summary.conflicts : occurrenceRefs.length ? { availability: 'available', scope: 'complete_revision', distinctFindingCount: conflicts.length, countByType: { lecturer: conflicts.filter((item) => item.category === 'lecturer_conflict').length, room: conflicts.filter((item) => item.category === 'room_conflict').length, cohort: conflicts.filter((item) => item.category === 'cohort_conflict').length }, contributorRefs: conflicts.map((item) => item.findingRef) } : notApplicable('Kein geplanter Termin entspricht den Filtern.'),
    capacityIssues: capacityMetric,
    planningFailures: eligibleCourseRefs.size === 0 ? notApplicable(`Kein planbarer Semesterkontext einer ${label('course.singular')} entspricht den Filtern.`) : outcomes.length === 0 ? { availability: 'unavailable', scope: 'complete_revision', coverage: { eligibleCourseCount: eligibleCourseRefs.size, coveredCourseCount: 0, coverageComplete: false }, contributorRefs: [], unavailableReason: 'Für die gefilterten Lehrveranstaltungen liegt kein gespeichertes Planungsergebnis vor.' } : { availability: new Set(outcomes.map((item) => item.courseRef)).size === eligibleCourseRefs.size ? 'available' : 'partial', scope: 'complete_revision', coverage: { eligibleCourseCount: eligibleCourseRefs.size, coveredCourseCount: new Set(outcomes.map((item) => item.courseRef)).size, coverageComplete: new Set(outcomes.map((item) => item.courseRef)).size === eligibleCourseRefs.size }, failedOutcomeCount: outcomes.filter((item) => item.classification === 'failed').length, staleOutcomeCount: outcomes.filter((item) => item.classification === 'stale').length, unchangedOutcomeCount: outcomes.filter((item) => item.classification === 'unchanged').length, contributorRefs: outcomes.filter((item) => ['failed', 'stale', 'unchanged'].includes(item.classification)).map((item) => item.outcomeRef) },
    needsReview: needsReviewMetric,
  }
}

function coverageMetric({
  applicableCount,
  unverifiedCount,
  value,
  contributorRefs,
  notApplicableReason,
  unavailableReason,
}: {
  applicableCount: number
  unverifiedCount: number
  value: Partial<WorkspaceMetric>
  contributorRefs: string[]
  notApplicableReason: string
  unavailableReason: string
}): WorkspaceMetric {
  if (applicableCount === 0) return notApplicable(notApplicableReason)
  if (unverifiedCount >= applicableCount) {
    return {
      availability: 'unavailable',
      scope: 'complete_revision',
      contributorRefs: [],
      unavailableReason,
    }
  }
  return {
    availability: unverifiedCount > 0 ? 'partial' : 'available',
    scope: 'complete_revision',
    contributorRefs,
    ...value,
  }
}

function notApplicable(reason: string): WorkspaceMetric {
  return { availability: 'not_applicable', scope: 'complete_revision', contributorRefs: [], notApplicableReason: reason }
}

function formatMetric(metric: WorkspaceMetric, field: 'distinctFindingCount' | 'affectedOccurrenceCount' | 'failedOutcomeCount' | 'distinctCourseCount') {
  if (metric.availability === 'unavailable') return 'Nicht verfügbar'
  if (metric.availability === 'not_applicable') return 'Nicht anwendbar'
  return String(metric[field] ?? 0)
}

function formatUnscheduled(metric: WorkspaceMetric) {
  if (metric.availability === 'unavailable') return 'Nicht verfügbar'
  if (metric.availability === 'not_applicable') return 'Nicht anwendbar'
  const minutes = metric.remainingInstructionalMinutes ?? 0
  return `${metric.remainingTeachingUnits ?? 0} Lehreinheiten · ${Math.floor(minutes / 60)} Std. ${minutes % 60} Min.`
}

function formatPlanningOutcomes(metric: WorkspaceMetric) {
  if (metric.availability === 'unavailable') return 'Nicht verfügbar'
  if (metric.availability === 'not_applicable') return 'Nicht anwendbar'
  return `${metric.failedOutcomeCount ?? 0} fehlgeschlagen · ${metric.staleOutcomeCount ?? 0} veraltet · ${metric.unchangedOutcomeCount ?? 0} unverändert`
}

function contributorLabel(workspace: LoadedCalendarWorkspace, ref: string) {
  const course = workspace.courses.find((item) => item.courseRef === ref)
  if (course) return course.name
  const occurrence = workspace.occurrences.find((item) => item.occurrenceRef === ref)
  if (occurrence) return `${occurrence.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'} · ${formatCalendarDate(occurrence.date)} ${occurrence.startTime}`
  const finding = workspace.validationFindings.find((item) => item.findingRef === ref)
  if (finding) return calendarFindingLabel(finding)
  const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === ref)
  if (outcome) return outcomeLabel(outcome)
  return ref
}

function detailValue(value: unknown) {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : 'Nicht verfügbar'
}

function revisionLabel(revision: LoadedCalendarWorkspace['selectedRevision']) {
  return revision.revisionLabel ?? `Revision ${revision.revisionNumber}`
}

function outcomeLabel(outcome: LoadedCalendarWorkspace['planningOutcomes'][number]) {
  const operation = ({ single_generation: 'Einzelerzeugung', batch_generation: 'Mehrfacherzeugung', semester_optimization: 'Semesteroptimierung', manual_creation: 'Manuelle Erstellung' } as Record<string, string>)[outcome.operationKind] ?? 'Planungsaktion'
  const classification = ({ failed: 'fehlgeschlagen', stale: 'veraltet', unchanged: 'unverändert', succeeded: 'erfolgreich' } as Record<string, string>)[outcome.classification] ?? 'unbekanntes Ergebnis'
  return `${operation} · ${classification}`
}

function contributorProblems(workspace: LoadedCalendarWorkspace, ref: string): string[] {
  const course = workspace.courses.find((item) => item.courseRef === ref)
  if (course) {
    return course.needsReviewReasonRefs.map((reasonRef) => {
      if (reasonRef.startsWith('remaining:')) return `${course.remainingTeachingUnits} Lehreinheiten sind noch offen. Vervollständigen Sie die Planung oder prüfen Sie den verbleibenden Umfang.`
      const finding = workspace.validationFindings.find((item) => item.findingRef === reasonRef)
      if (finding) return calendarFindingLabel(finding)
      const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === reasonRef)
      if (outcome) return `${outcomeLabel(outcome)}. Prüfen Sie das Planungsergebnis vor einem weiteren Versuch.`
      return 'Ein zugehöriger Prüfgrund ist nicht mehr verfügbar. Laden Sie den Arbeitsbereich erneut und prüfen Sie den aktuellen Stand.'
    })
  }
  const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === ref)
  if (outcome) {
    const reasons = outcome.reasons.map((reason) => safeReasonText(typeof reason.code === 'string' ? reason.code : 'UNKNOWN', 'Planungsergebnis'))
    return reasons.length > 0
      ? reasons
      : [`${outcomeLabel(outcome)}. Die genaue Ursache ist nicht verfügbar; laden Sie den aktuellen Stand und prüfen Sie das Ergebnis vor einem weiteren Versuch.`]
  }
  return []
}

function workspaceSectionLabel(name: string): string {
  return ({ occurrences: 'Termine', validationFindings: 'Prüfhinweise', planningOutcomes: 'Planungsergebnisse', summary: 'Übersicht', filterFacets: 'Filterwerte' } as Record<string, string>)[name] ?? 'Arbeitsbereichsdaten'
}

function availabilityLabel(value: string): string {
  return ({ available: 'verfügbar', partial: 'teilweise verfügbar', unavailable: 'nicht verfügbar', not_applicable: 'nicht anwendbar' } as Record<string, string>)[value] ?? 'Status unbekannt'
}

function safeWorkspaceReason(): string {
  return 'Die genaue Ursache ist nicht verfügbar. Laden Sie den Arbeitsbereich erneut und prüfen Sie den aktuellen Stand.'
}

function renderListContent(
  content: Props['listContent'],
  context: WorkspaceListContext | null,
) {
  return typeof content === 'function' ? content(context) : content
}

function workspaceListContext(
  workspace: LoadedCalendarWorkspace,
  courseIds: number[],
  occurrences: WorkspaceOccurrence[],
  activeFilterCount: number,
  traceReference: string | null,
): WorkspaceListContext {
  const traceTarget = traceReference == null
    ? null
    : resolveListTraceTarget(
        workspace,
        traceReference,
        new Set(occurrences.map((item) => item.occurrenceRef)),
      )
  return {
    courseIds,
    teachingSessionIds: occurrenceIds(occurrences, 'teaching'),
    examIds: occurrenceIds(occurrences, 'exam'),
    activeFilterCount,
    traceTarget,
  }
}

function resolveListTraceTarget(
  workspace: LoadedCalendarWorkspace,
  reference: string,
  visibleOccurrenceRefs: Set<string>,
): WorkspaceListTraceTarget {
  const course = workspace.courses.find((item) => item.courseRef === reference)
  const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === reference)
  const finding = workspace.validationFindings.find((item) => item.findingRef === reference)
  const courseRefs = course
    ? [course.courseRef]
    : outcome
      ? [outcome.courseRef]
      : finding?.affectedCourseRefs ?? []
  const occurrenceRefs = course
    ? course.occurrenceRefs.filter((ref) => visibleOccurrenceRefs.has(ref))
    : outcome
      ? workspace.courses
          .find((item) => item.courseRef === outcome.courseRef)
          ?.occurrenceRefs.filter((ref) => visibleOccurrenceRefs.has(ref)) ?? []
      : finding?.affectedOccurrenceRefs ?? []
  const targetOccurrences = workspace.occurrences.filter((item) => occurrenceRefs.includes(item.occurrenceRef))
  return {
    reference,
    label: contributorLabel(workspace, reference),
    courseIds: workspace.courses
      .filter((item) => courseRefs.includes(item.courseRef))
      .map((item) => item.courseId),
    teachingSessionIds: occurrenceIds(targetOccurrences, 'teaching'),
    examIds: occurrenceIds(targetOccurrences, 'exam'),
  }
}

function occurrenceIds(
  occurrences: WorkspaceOccurrence[],
  kind: WorkspaceOccurrence['kind'],
) {
  return occurrences
    .filter((item) => item.kind === kind)
    .map((item) => Number(item.occurrenceRef.split(':')[1]))
    .filter(Number.isFinite)
}

function stateLabel(value: string) {
  return ({ draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung (nicht freigegeben)', published: 'Veröffentlicht', superseded: 'Ersetzt', abandoned: 'Verworfen' } as Record<string, string>)[value] ?? 'Unbekannter Status'
}

function announce(message: string) {
  const target = document.getElementById('calendar-workspace-announcer')
  if (target) target.textContent = message
}
