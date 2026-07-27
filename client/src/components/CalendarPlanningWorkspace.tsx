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
  { value: 'week', label: 'Week' },
  { value: 'day', label: 'Day' },
  { value: 'month', label: 'Month' },
  { value: 'list', label: 'List' },
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
          ? 'Calendar workspace recovered with current data.'
          : 'Calendar workspace refreshed with current data.',
      )
    }
    previousLoadState.current = { failed, refreshing }
  }, [props.error, props.loading, props.workspace])

  return (
    <>
      <CalendarPlanningWorkspaceContent
        key={props.workspace?.workspaceToken ?? 'no-workspace'}
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
  mode,
  anchor,
  setMode,
  setAnchor,
  resultsHeadingRef,
  onSelectionDisappeared,
}: WorkspaceContentProps) {
  const [filters, setFilters] = useState<WorkspaceFilters>({})
  const [selectedRef, setSelectedRef] = useState<string | null>(null)
  const [listTraceRef, setListTraceRef] = useState<string | null>(null)
  const [drilldown, setDrilldown] = useState<WorkspaceDrilldown | null>(null)
  const detailHeading = useRef<HTMLHeadingElement>(null)
  const drilldownHeading = useRef<HTMLHeadingElement>(null)
  const drilldownInitiator = useRef<HTMLButtonElement | null>(null)
  const priorTraceCourseId = useRef<number | null | undefined>(undefined)
  const selectedRefOnUnmount = useRef<string | null>(null)
  const selectionDisappearedHandler = useRef(onSelectionDisappeared)

  useEffect(() => {
    selectedRefOnUnmount.current = selectedRef
  }, [selectedRef])

  useEffect(() => {
    selectionDisappearedHandler.current = onSelectionDisappeared
  }, [onSelectionDisappeared])

  useEffect(() => {
    if (drilldown != null) drilldownHeading.current?.focus()
  }, [drilldown])

  useEffect(() => () => {
    if (selectedRefOnUnmount.current != null) {
      selectionDisappearedHandler.current(
        'The selected session is no longer available in the refreshed workspace.',
      )
    }
  }, [])

  if (loading && workspace == null) return <section className="calendar-workspace workspace-state" aria-busy="true" role="status">Loading {intendedContext ?? 'semester workspace'}…</section>
  if (error && workspace == null) return <section className="calendar-workspace workspace-state"><div role="alert"><h2>Calendar workspace unavailable</h2>{intendedContext && <p>{intendedContext}</p>}<p>{error}</p><button type="button" onClick={onRetry}>Retry</button></div><p>The established Courses overview remains available while the coherent workspace read is unavailable.</p><div className="workspace-list-mode">{renderListContent(listContent, null)}</div></section>
  if (workspace == null) return <section className="calendar-workspace workspace-state"><h2>No semester selected</h2><p>Select a semester to open its planning workspace.</p></section>
  if (workspace.workspaceState === 'no_revision') {
    return (
      <section className="calendar-workspace workspace-state" aria-labelledby="calendar-workspace-title" aria-busy={loading}>
        <p className="eyebrow">{workspace.semester.name}</p>
        <h2 id="calendar-workspace-title">Semester schedule</h2>
        <p>No schedule revision exists yet. Start a Draft to plan teaching and exams.</p>
        {error && <div className="refresh-error" role="alert"><span>Last known no-revision state shown. {error}</span><button type="button" onClick={onRetry}>Retry</button></div>}
        {onStartDraft && <button type="button" className="generate-button" onClick={onStartDraft}>Start Draft</button>}
      </section>
    )
  }
  const loadedWorkspace = workspace
  const impairedSections = Object.entries(workspace.sectionStatus).filter(
    ([, status]) => status.availability !== 'available',
  )

  const effectiveAnchor = anchor ?? currentPeriodDate(new Date().toISOString().slice(0, 10), workspace.semester.startDate, workspace.semester.endDate).date
  const range = visibleRange(mode, effectiveAnchor)
  const projection = projectWorkspace(workspace, filters)
  const visibleOccurrences = occurrencesInRange(projection.occurrences, range)
  const visibleHolidays = workspace.holidays.filter((holiday) => (
    range != null && holiday.date >= range.start && holiday.date <= range.end
  ))
  const selectedOccurrence = workspace.occurrences.find((item) => item.occurrenceRef === selectedRef) ?? null
  const activeFilterCount = Object.values(filters).filter(Boolean).length
  const summary = filteredSummary(workspace, projection.courses.map((item) => item.courseRef), projection.occurrences.map((item) => item.occurrenceRef), activeFilterCount > 0)
  const summaryScope = activeFilterCount > 0 ? 'Filtered subset' : 'Complete revision'
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
    setSelectedRef(reference)
    window.setTimeout(() => detailHeading.current?.focus(), 0)
  }

  function closeOccurrenceDetail() {
    const reference = selectedRef
    setSelectedRef(null)
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
    setFilters(nextFilters)
    if (
      selectedRef != null
      && !projectWorkspace(loadedWorkspace, nextFilters).occurrences.some(
        (item) => item.occurrenceRef === selectedRef,
      )
    ) {
      setSelectedRef(null)
      onSelectionDisappeared(
        'The selected session no longer matches the current result set.',
      )
    }
  }

  function goCurrent() {
    if (mode === 'list') return
    const current = currentPeriodDate(new Date().toISOString().slice(0, 10), loadedWorkspace.semester.startDate, loadedWorkspace.semester.endDate)
    setAnchor(current.date)
    if (current.substituted) {
      const boundary = current.date === loadedWorkspace.semester.startDate ? 'start' : 'end'
      announce(`Today is outside the semester. Showing the semester ${boundary}.`)
    } else announce('Showing the current period.')
  }

  return (
    <section className="calendar-workspace" aria-labelledby="calendar-workspace-title" aria-busy={loading}>
      <header className="calendar-context-header">
        <div>
          <p className="eyebrow">{workspace.semester.name} · {workspace.semester.startDate}–{workspace.semester.endDate}</p>
          <h2 id="calendar-workspace-title">Semester schedule</h2>
          <p>
            Revision {workspace.selectedRevision.revisionNumber} · {stateLabel(workspace.selectedRevision.lifecycleState)} ·{' '}
            {workspace.selectedRevision.designation === 'active_working' ? 'Active Working' : 'Current Published'}
          </p>
          {workspace.selectedRevision.readOnly && <p className="read-only-note">Published content is read-only. Warnings are recalculated from current planning data without changing the publication.</p>}
        </div>
        <div className="revision-context-switch" aria-label="Schedule revision context">
          {workspace.availableContexts.activeWorking && <button type="button" aria-pressed={workspace.selectedRevision.designation === 'active_working'} onClick={() => onSelectRevision?.(workspace.availableContexts.activeWorking!.revisionId)}>Working R{workspace.availableContexts.activeWorking.revisionNumber}</button>}
          {workspace.availableContexts.currentPublished && <button type="button" aria-pressed={workspace.selectedRevision.designation === 'current_published'} onClick={() => onSelectRevision?.(workspace.availableContexts.currentPublished!.revisionId)}>Published R{workspace.availableContexts.currentPublished.revisionNumber}</button>}
        </div>
      </header>

      {loading && <p className="active-filter-status" role="status">Refreshing workspace. Displayed values are last known until the refresh completes.</p>}
      {error && <div className="refresh-error" role="alert"><span>{lastKnown ? `Last known workspace shown. ${error}` : error}</span><button type="button" onClick={onRetry}>Retry</button></div>}
      {impairedSections.length > 0 && (
        <div className="partial-workspace-status" role="status">
          <strong>Some workspace information is incomplete.</strong>
          <ul>
            {impairedSections.map(([name, status]) => (
              <li key={name}>{name.replaceAll(/([A-Z])/g, ' $1')}: {status.availability}{status.reason ? ` · ${status.reason}` : ''}</li>
            ))}
          </ul>
        </div>
      )}

      <div className="workspace-summary-grid" aria-label={`${activeFilterCount ? 'Filtered' : 'Complete revision'} operational summary`}>
        <SummaryCard metricKey="unscheduledWork" label="Unscheduled work" metric={summary.unscheduledWork} value={formatUnscheduled(summary.unscheduledWork)} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="conflicts" label="Conflicts" metric={summary.conflicts} value={formatMetric(summary.conflicts, 'distinctFindingCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="capacityIssues" label="Capacity issues" metric={summary.capacityIssues} value={formatMetric(summary.capacityIssues, 'affectedOccurrenceCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="planningFailures" label="Planning failures" metric={summary.planningFailures} value={formatPlanningOutcomes(summary.planningFailures)} scopeLabel={summaryScope} onActivate={activateMetric} />
        <SummaryCard metricKey="needsReview" label="Needs review" metric={summary.needsReview} value={formatMetric(summary.needsReview, 'distinctCourseCount')} scopeLabel={summaryScope} onActivate={activateMetric} />
      </div>

      {drilldown && drilldownMetric && (
        <section className="workspace-drilldown" aria-labelledby="drilldown-title">
          <div><h3 id="drilldown-title" tabIndex={-1} ref={drilldownHeading} data-workspace-drilldown-heading>{drilldown.label} contributors</h3><p>{drilldownMetric.contributorRefs.length} affected record{drilldownMetric.contributorRefs.length === 1 ? '' : 's'} in the {activeFilterCount ? 'filtered subset' : 'complete revision'}.</p></div>
          <button type="button" onClick={clearDrilldown}>Clear drilldown</button>
          <ul>{drilldownMetric.contributorRefs.map((ref) => <li key={ref}><button type="button" onClick={() => navigateContributor(ref)}>{contributorLabel(workspace, ref)}</button></li>)}</ul>
        </section>
      )}

      <div className="calendar-toolbar">
        <div className="calendar-mode-switch" aria-label="Calendar mode">
          {MODES.map((item) => <button type="button" key={item.value} aria-pressed={mode === item.value} onClick={() => { setMode(item.value); if (item.value !== 'list') setListTraceRef(null) }}>{item.label}</button>)}
        </div>
        <div className="calendar-date-controls" aria-label="Calendar date">
          <button type="button" disabled={mode === 'list'} onClick={() => setAnchor(movePeriod(mode, effectiveAnchor, -1))} aria-label="Previous period">←</button>
          <button type="button" disabled={mode === 'list'} onClick={goCurrent}>{mode === 'list' ? 'Current period not applicable' : 'Current'}</button>
          <button type="button" disabled={mode === 'list'} onClick={() => setAnchor(movePeriod(mode, effectiveAnchor, 1))} aria-label="Next period">→</button>
          <input aria-label="Choose calendar date" type="date" value={effectiveAnchor} min={workspace.semester.startDate} max={workspace.semester.endDate} disabled={mode === 'list'} onChange={(event) => setAnchor(event.target.value)} />
          {range && <span className="visible-range">{range.start === range.end ? range.start : `${range.start} – ${range.end}`}</span>}
        </div>
      </div>

      <div className="workspace-filters" aria-label="Workspace filters">
        <FacetSelect label="Course" value={filters.course} values={workspace.filterFacets.courses} onChange={(value) => applyFilter('course', value)} />
        <FacetSelect label="Cohort" value={filters.cohort} values={workspace.filterFacets.cohorts} onChange={(value) => applyFilter('cohort', value)} />
        <FacetSelect label="Lecturer" value={filters.lecturer} values={workspace.filterFacets.lecturers} onChange={(value) => applyFilter('lecturer', value)} />
        <FacetSelect label="Room" value={filters.room} values={workspace.filterFacets.rooms} onChange={(value) => applyFilter('room', value)} />
        <FacetSelect label="Study type" value={filters.studyType} values={workspace.filterFacets.studyTypes} onChange={(value) => applyFilter('studyType', value)} />
        <FacetSelect label="Session type" value={filters.sessionType} values={workspace.filterFacets.sessionTypes} onChange={(value) => applyFilter('sessionType', value as WorkspaceFilters['sessionType'])} />
        <FacetSelect label="Lifecycle" value={filters.lifecycle} values={workspace.filterFacets.lifecycleContexts} onChange={(value) => applyFilter('lifecycle', value)} />
        <FacetSelect label="Validation" value={filters.validation} values={workspace.filterFacets.validationCategories} onChange={(value) => applyFilter('validation', value)} />
        <button type="button" disabled={activeFilterCount === 0 && drilldown == null} onClick={clearFiltersAndDrilldown}>Clear filters</button>
      </div>
      {activeFilterCount > 0 && <p className="active-filter-status" role="status">{activeFilterCount} active filter{activeFilterCount === 1 ? '' : 's'} · {projection.courses.length} courses · {projection.occurrences.length} occurrences</p>}

      <h3
        className="sr-only"
        tabIndex={-1}
        ref={resultsHeadingRef}
        data-workspace-results-heading
      >
        Calendar results
      </h3>
      <div
        className="workspace-list-mode"
        aria-label="List mode"
        hidden={mode !== 'list'}
      >
        {renderListContent(listContent, listContext)}
      </div>
      {mode !== 'list' && (
        visibleOccurrences.length === 0 && visibleHolidays.length === 0 ? (
          <p className="empty-state">{projection.occurrences.length === 0 && activeFilterCount > 0 ? 'No records match the active filters.' : 'No sessions occur in this period.'}</p>
        ) : (
          <>
            {visibleOccurrences.length === 0 && activeFilterCount > 0 && <p className="empty-state">No records match the active filters. Holiday date context remains visible.</p>}
            <CalendarSurface mode={mode} occurrences={visibleOccurrences} holidays={visibleHolidays} courses={workspace.courses} selectedRef={selectedRef} onSelect={chooseOccurrence} semesterStart={workspace.semester.startDate} semesterEnd={workspace.semester.endDate} />
          </>
        )
      )}

      {selectedOccurrence && (
        <OccurrenceDetail
          occurrence={selectedOccurrence}
          workspace={workspace}
          headingRef={detailHeading}
          onClose={closeOccurrenceDetail}
          onEditTeaching={(reference) => {
            setMode('list')
            setSelectedRef(null)
            onEditTeaching?.(reference)
          }}
          onDeleteTeaching={onDeleteTeaching}
          onEditExam={onEditExam}
          onDeleteExam={onDeleteExam}
        />
      )}
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
    setSelectedRef(null)
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
        <section className={`calendar-date-column ${date < semesterStart || date > semesterEnd ? 'outside-semester' : ''}`} key={date} role="row" aria-label={date}>
          <h3>{new Intl.DateTimeFormat(undefined, { weekday: 'short', month: 'short', day: 'numeric', timeZone: 'UTC' }).format(new Date(`${date}T12:00:00Z`))}</h3>
          {mode === 'month' && occurrences.filter((item) => item.date === date).length > 3 && (
            <p className="calendar-date-count">{occurrences.filter((item) => item.date === date).length} sessions</p>
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
                <span className="occurrence-kind">{item.kind === 'teaching' ? 'Teaching' : 'Exam'}</span>
                <strong>{courseByRef.get(item.courseRef)?.name ?? item.courseRef}</strong>
                <span>{item.startTime}–{item.endTime}</span>
                <span>{item.cohort}</span>
                {item.findingRefs.length > 0 && <span className="warning-label">⚠ {item.findingRefs.length} current warning{item.findingRefs.length === 1 ? '' : 's'}</span>}
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
                  ? 'Show fewer sessions'
                  : `Show all ${occurrences.filter((item) => item.date === date).length} sessions`}
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
      <div className="detail-heading"><h3 id="occurrence-detail-title" tabIndex={-1} ref={headingRef}>{occurrence.kind === 'teaching' ? 'Teaching session' : 'Exam session'} · {course?.name}</h3><button type="button" onClick={onClose} aria-label="Close session detail">×</button></div>
      <dl>
        <div><dt>Lifecycle</dt><dd>{stateLabel(workspace.selectedRevision.lifecycleState)}</dd></div>
        <div><dt>Revision</dt><dd>R{workspace.selectedRevision.revisionNumber} · {workspace.selectedRevision.designation === 'active_working' ? 'Working' : 'Current Published'}</dd></div>
        <div><dt>Course</dt><dd>{course?.name ?? occurrence.courseRef}</dd></div>
        <div><dt>Study type</dt><dd>{course?.studyType ?? 'Unavailable'}</dd></div>
        <div><dt>Date and time</dt><dd>{occurrence.date}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
        <div><dt>Cohort</dt><dd>{occurrence.cohort}</dd></div>
        <div><dt>Lecturer</dt><dd>{occurrence.lecturerRefs.join(', ')}</dd></div>
        <div><dt>Room</dt><dd>{occurrence.kind === 'exam' ? `${occurrence.assignedRoomName} (${occurrence.roomRef})` : occurrence.roomRef}</dd></div>
        {occurrence.kind === 'teaching' ? (
          <>
            <div><dt>Teaching units</dt><dd>{occurrence.teachingUnits}</dd></div>
            <div><dt>Source</dt><dd>{occurrence.source}</dd></div>
          </>
        ) : (
          <>
            <div><dt>Exam type</dt><dd>{occurrence.examType}</dd></div>
            <div><dt>Duration</dt><dd>{occurrence.durationMinutes} minutes</dd></div>
            <div><dt>Capacity</dt><dd>{occurrence.requiredCapacity} required; {occurrence.currentRoomCapacity == null ? 'current room capacity unavailable' : `${occurrence.currentRoomCapacity} current`}</dd></div>
            <div><dt>Configuration</dt><dd>{detailValue(occurrence.validityContext.configurationIdentifier)} · revision {detailValue(occurrence.validityContext.configurationRevision)}</dd></div>
            <div><dt>Final teaching</dt><dd>{detailValue(occurrence.validityContext.finalTeachingDate)} at {detailValue(occurrence.validityContext.finalTeachingEndTime)}</dd></div>
            <div><dt>Source</dt><dd>{detailValue(occurrence.validityContext.source)}</dd></div>
            {occurrence.recommendationContext && <div><dt>Recommended period</dt><dd>{detailValue(occurrence.recommendationContext.recommendedStartDate)}–{detailValue(occurrence.recommendationContext.recommendedEndDate)}{occurrence.recommendationContext.recommendationWasOverridden === true ? ' · planner override' : ''}</dd></div>}
          </>
        )}
      </dl>
      <section aria-labelledby="current-warnings-title"><h4 id="current-warnings-title">Current warnings</h4>{findings.length ? <ul>{findings.map((item) => <li key={item.findingRef}>{findingLabel(item)}</li>)}</ul> : <p>No current warnings.</p>}</section>
      {workspace.selectedRevision.readOnly ? <p className="read-only-note">Correction actions are unavailable for Current Published. Open the Working revision to make changes.</p> : (
        <div className="detail-actions">
          {occurrence.kind === 'teaching' ? <>{onEditTeaching && <button type="button" onClick={() => onEditTeaching(occurrence.occurrenceRef)}>Edit with existing editor</button>}{onDeleteTeaching && <button type="button" className="destructive-button" onClick={() => onDeleteTeaching(occurrence.occurrenceRef)}>Delete with confirmation</button>}</> : <>{onEditExam && <button type="button" onClick={() => onEditExam(occurrence.occurrenceRef)}>Edit with existing editor</button>}{onDeleteExam && <button type="button" className="destructive-button" onClick={() => onDeleteExam(occurrence.occurrenceRef)}>Delete with confirmation</button>}</>}
        </div>
      )}
    </aside>
  )
}

function SummaryCard({ metricKey, label, metric, value, scopeLabel, onActivate }: { metricKey: keyof LoadedCalendarWorkspace['summary']; label: string; metric: WorkspaceMetric; value: string; scopeLabel: string; onActivate: (metricKey: keyof LoadedCalendarWorkspace['summary'], label: string, metric: WorkspaceMetric, initiator: HTMLButtonElement) => void }) {
  const actionable = (metric.availability === 'available' || metric.availability === 'partial') && metric.contributorRefs.length > 0
  return <button type="button" className={`summary-card availability-${metric.availability}`} disabled={!actionable} onClick={(event) => onActivate(metricKey, label, metric, event.currentTarget)} aria-label={`${label}: ${value}. ${scopeLabel}. ${actionable ? 'Show contributing records.' : ''}`}><span>{label}</span><strong>{value}</strong><small>{metric.availability === 'partial' ? 'Known incomplete · ' : ''}{scopeLabel}</small></button>
}

function FacetSelect({ label, value, values, onChange }: { label: string; value?: string; values: { value: string; label: string }[]; onChange: (value: string | undefined) => void }) {
  if (values.length === 0) return null
  return <label><span>{label}</span><select value={value ?? ''} onChange={(event) => onChange(event.target.value || undefined)}><option value="">All</option>{values.map((item) => <option key={item.value} value={item.value}>{item.label}</option>)}</select></label>
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
    notApplicableReason: 'No scheduled occurrence matches the filters.',
    unavailableReason: 'Room capacity data is unavailable for every matching occurrence.',
  })
  const needsReviewMetric = coverageMetric({
    applicableCount: courses.length,
    unverifiedCount: validationUnverifiedCourseRefs.size,
    value: { distinctCourseCount: verifiedNeeds.length },
    contributorRefs: verifiedNeeds.map((item) => item.courseRef),
    notApplicableReason: 'No course-semester context matches the filters.',
    unavailableReason: 'Current validation data is unavailable for every matching course.',
  })
  return {
    unscheduledWork: workspace.summary.unscheduledWork.availability === 'unavailable' ? workspace.summary.unscheduledWork : courses.length ? { availability: 'available', scope: 'complete_revision', remainingTeachingUnits: courses.reduce((sum, item) => sum + item.remainingTeachingUnits, 0), remainingInstructionalMinutes: courses.reduce((sum, item) => sum + item.remainingInstructionalMinutes, 0), contributingCourseCount: remaining.length, contributorRefs: remaining.map((item) => item.courseRef) } : notApplicable('No course-semester context matches the filters.'),
    conflicts: workspace.summary.conflicts.availability === 'unavailable' ? workspace.summary.conflicts : occurrenceRefs.length ? { availability: 'available', scope: 'complete_revision', distinctFindingCount: conflicts.length, countByType: { lecturer: conflicts.filter((item) => item.category === 'lecturer_conflict').length, room: conflicts.filter((item) => item.category === 'room_conflict').length, cohort: conflicts.filter((item) => item.category === 'cohort_conflict').length }, contributorRefs: conflicts.map((item) => item.findingRef) } : notApplicable('No scheduled occurrence matches the filters.'),
    capacityIssues: capacityMetric,
    planningFailures: eligibleCourseRefs.size === 0 ? notApplicable('No eligible course-semester context matches the filters.') : outcomes.length === 0 ? { availability: 'unavailable', scope: 'complete_revision', coverage: { eligibleCourseCount: eligibleCourseRefs.size, coveredCourseCount: 0, coverageComplete: false }, contributorRefs: [], unavailableReason: workspace.summary.planningFailures.unavailableReason ?? 'No retained outcome covers the filtered courses.' } : { availability: new Set(outcomes.map((item) => item.courseRef)).size === eligibleCourseRefs.size ? 'available' : 'partial', scope: 'complete_revision', coverage: { eligibleCourseCount: eligibleCourseRefs.size, coveredCourseCount: new Set(outcomes.map((item) => item.courseRef)).size, coverageComplete: new Set(outcomes.map((item) => item.courseRef)).size === eligibleCourseRefs.size }, failedOutcomeCount: outcomes.filter((item) => item.classification === 'failed').length, staleOutcomeCount: outcomes.filter((item) => item.classification === 'stale').length, unchangedOutcomeCount: outcomes.filter((item) => item.classification === 'unchanged').length, contributorRefs: outcomes.filter((item) => ['failed', 'stale', 'unchanged'].includes(item.classification)).map((item) => item.outcomeRef) },
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
  if (metric.availability === 'unavailable') return 'Unavailable'
  if (metric.availability === 'not_applicable') return 'Not applicable'
  return String(metric[field] ?? 0)
}

function formatUnscheduled(metric: WorkspaceMetric) {
  if (metric.availability === 'unavailable') return 'Unavailable'
  if (metric.availability === 'not_applicable') return 'Not applicable'
  const minutes = metric.remainingInstructionalMinutes ?? 0
  return `${metric.remainingTeachingUnits ?? 0} units · ${Math.floor(minutes / 60)}h ${minutes % 60}m`
}

function formatPlanningOutcomes(metric: WorkspaceMetric) {
  if (metric.availability === 'unavailable') return 'Unavailable'
  if (metric.availability === 'not_applicable') return 'Not applicable'
  return `${metric.failedOutcomeCount ?? 0} failed · ${metric.staleOutcomeCount ?? 0} stale · ${metric.unchangedOutcomeCount ?? 0} unchanged`
}

function contributorLabel(workspace: LoadedCalendarWorkspace, ref: string) {
  const course = workspace.courses.find((item) => item.courseRef === ref)
  if (course) {
    const reasons = course.needsReviewReasonRefs.map((reasonRef) => {
      if (reasonRef.startsWith('remaining:')) return `${course.remainingTeachingUnits} units remaining`
      const finding = workspace.validationFindings.find((item) => item.findingRef === reasonRef)
      if (finding) return findingLabel(finding)
      const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === reasonRef)
      return outcome ? outcomeLabel(outcome) : reasonRef
    })
    return `${course.name}${reasons.length ? ` · ${reasons.join('; ')}` : ''}`
  }
  const occurrence = workspace.occurrences.find((item) => item.occurrenceRef === ref)
  if (occurrence) return `${occurrence.kind} · ${occurrence.date} ${occurrence.startTime}`
  const finding = workspace.validationFindings.find((item) => item.findingRef === ref)
  if (finding) return findingLabel(finding)
  const outcome = workspace.planningOutcomes.find((item) => item.outcomeRef === ref)
  if (outcome) return outcomeLabel(outcome)
  return ref
}

function findingLabel(finding: LoadedCalendarWorkspace['validationFindings'][number]) {
  const details = finding.details
  if (details.kind === 'conflict') return `${details.conflictType} conflict · ${details.occurrenceRefs.join(', ')}`
  if (details.kind === 'capacity') return `${details.roomName} capacity ${details.currentCapacity}; ${details.requiredCapacity} required`
  if (details.kind === 'holiday') return `${details.holidayName} · ${details.holidayDate}`
  return details.issueCode.replaceAll('_', ' ')
}

function detailValue(value: unknown) {
  return typeof value === 'string' || typeof value === 'number' ? String(value) : 'Unavailable'
}

function outcomeLabel(outcome: LoadedCalendarWorkspace['planningOutcomes'][number]) {
  const reasons = outcome.reasons.map((reason) => (
    typeof reason.message === 'string'
      ? reason.message
      : typeof reason.code === 'string'
        ? reason.code.replaceAll('_', ' ')
        : JSON.stringify(reason)
  ))
  return `${outcome.operationKind.replaceAll('_', ' ')} · ${outcome.classification}${reasons.length ? ` · ${reasons.join('; ')}` : ''}`
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
  return value === 'ready_for_review' ? 'Ready for review (not approved)' : value.charAt(0).toUpperCase() + value.slice(1)
}

function announce(message: string) {
  const target = document.getElementById('calendar-workspace-announcer')
  if (target) target.textContent = message
}
