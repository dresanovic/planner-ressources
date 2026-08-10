import { useEffect, useMemo, useRef, useState } from 'react'

import type {
  AllowedTeachingWindow,
  DraftSession,
  DraftSchedule,
  GenerationConstraints,
  PlanningEntity,
  ReviewFilters,
  SessionEditFailure,
  ViewMode,
} from '../api/draftSchedule'
import type { PlanningOptions, RoomOption } from '../api/planningOptions'
import type { LecturerRecord } from '../api/resourceCatalog'
import type { ExamIssue, ExamSession } from '../api/examScheduling'
import type { WorkspaceListContext } from './CalendarPlanningWorkspace'
import { WEEKDAY_NAMES } from '../utils/weekdays'
import {
  groupSessionsByWeek,
  sortSessionsChronologically,
} from './scheduleReviewUtils'
import { TeachingSessionEditor } from './TeachingSessionEditor'
import { ScheduleOccurrenceRow } from './ScheduleOccurrenceList'
import {
  buildTeachingSessionEditModels,
  createTeachingSessionDraft,
  derivedLengthLabel,
  resourceLabel,
  type EditableDraftSessionRequest,
  type TeachingSessionEditModel,
} from './sessionEditModel'
import { formatCalendarDate, formatCalendarDateRange, isIsoCalendarDate } from '../utils/datePresentation'
import { ActionableProblemList } from './ActionableProblemList'
import { outsideRecommendedWindowProblem } from './calendarFindingLabel'
import { EuropeanDateField } from './EuropeanDateField'
import { safeReasonText, type UserProblem } from '../utils/userProblems'
import { label } from '../config/terminology'

const EMPTY_ROOMS: RoomOption[] = []
const EMPTY_LECTURERS: LecturerRecord[] = []
const EMPTY_COURSE_RESOURCES: PlanningOptions['courseResources'] = []
const EMPTY_EXAMS: ExamSession[] = []

function examValidityProblem(exam: ExamSession, issue: ExamIssue, courseName: string, index: number): UserProblem {
  const relatedDate = issue.relatedDate && isIsoCalendarDate(issue.relatedDate)
    ? formatCalendarDate(issue.relatedDate)
    : formatCalendarDate(exam.date)
  const relatedResource = issue.relatedResource?.name
  const finalTeaching = `${formatCalendarDate(exam.finalTeachingAnchor.date)} um ${exam.finalTeachingAnchor.endTime}`
  const explanations: Record<string, string> = {
    FINAL_TEACHING_SESSION_MISSING: 'Der für die Prüfung verwendete letzte Lehrtermin ist nicht mehr vorhanden.',
    INVALID_EXAM_INTERVAL: 'Der Prüfungszeitraum endet nicht gültig am selben Kalendertag.',
    OUTSIDE_SEMESTER: `Der Prüfungstermin am ${relatedDate} liegt außerhalb des Semesters.`,
    BEFORE_FINAL_TEACHING: `Die Prüfung beginnt vor dem Ende des letzten Lehrtermins am ${finalTeaching}.`,
    RESPONSIBLE_LECTURER_INELIGIBLE: `Die zugeordnete Lehrperson${relatedResource ? ` „${relatedResource}“` : ''} ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.`,
    ROOM_INELIGIBLE: `Der zugeordnete Raum${relatedResource ? ` „${relatedResource}“` : ''} ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.`,
    INSUFFICIENT_ROOM_CAPACITY: `Der Raum „${exam.room.name}“ hat ${exam.room.capacity} Plätze; benötigt werden ${exam.requiredCapacity}.`,
    LECTURER_UNAVAILABLE: `Die zugeordnete Lehrperson${relatedResource ? ` „${relatedResource}“` : ''} ist am ${relatedDate} während des Prüfungszeitraums nicht verfügbar.`,
    ROOM_UNAVAILABLE: `Der zugeordnete Raum${relatedResource ? ` „${relatedResource}“` : ''} ist am ${relatedDate} während des Prüfungszeitraums nicht verfügbar.`,
    INSTITUTION_HOLIDAY: `Der Prüfungstermin liegt am ${relatedDate}${issue.holidayName ? ` auf dem Hochschulfeiertag „${issue.holidayName}“` : ' auf einem Hochschulfeiertag'}.`,
    LECTURER_OCCUPIED: `Die zugeordnete Lehrperson${relatedResource ? ` „${relatedResource}“` : ''} ist am ${relatedDate} zeitgleich einem anderen Termin zugeordnet.`,
    ROOM_OCCUPIED: `Der zugeordnete Raum${relatedResource ? ` „${relatedResource}“` : ''} ist am ${relatedDate} zeitgleich einem anderen Termin zugeordnet.`,
    COHORT_OCCUPIED: `Die Kohorte ist am ${relatedDate} zeitgleich einem anderen Termin zugeordnet.`,
  }
  const guidance: Record<string, string> = {
    FINAL_TEACHING_SESSION_MISSING: 'Speichern Sie zuerst den vollständigen Lehrplan und planen Sie die Prüfung anschließend erneut.',
    INVALID_EXAM_INTERVAL: 'Bearbeiten Sie Startzeit oder Prüfungsanforderung so, dass die Prüfung am selben Kalendertag endet.',
    OUTSIDE_SEMESTER: 'Bearbeiten Sie die Prüfung und wählen Sie ein Datum innerhalb des Semesters.',
    BEFORE_FINAL_TEACHING: 'Bearbeiten Sie die Prüfung und wählen Sie einen Zeitpunkt nach dem letzten Lehrtermin.',
    RESPONSIBLE_LECTURER_INELIGIBLE: 'Wählen Sie beim Bearbeiten eine aktive, für die Lehrveranstaltung freigegebene Lehrperson.',
    ROOM_INELIGIBLE: 'Wählen Sie beim Bearbeiten einen aktiven, für die Lehrveranstaltung freigegebenen Raum.',
    INSUFFICIENT_ROOM_CAPACITY: 'Wählen Sie beim Bearbeiten einen Raum mit ausreichender Kapazität.',
    LECTURER_UNAVAILABLE: 'Ändern Sie beim Bearbeiten die Lehrperson oder den Prüfungszeitpunkt.',
    ROOM_UNAVAILABLE: 'Ändern Sie beim Bearbeiten den Raum oder den Prüfungszeitpunkt.',
    INSTITUTION_HOLIDAY: 'Prüfen Sie das Datum und ändern Sie den Termin, wenn die Prüfung nicht am Feiertag stattfinden soll.',
    LECTURER_OCCUPIED: 'Ändern Sie beim Bearbeiten die Lehrperson oder den Prüfungszeitpunkt.',
    ROOM_OCCUPIED: 'Ändern Sie beim Bearbeiten den Raum oder den Prüfungszeitpunkt.',
    COHORT_OCCUPIED: 'Ändern Sie beim Bearbeiten den Prüfungszeitpunkt.',
  }
  return {
    key: `exam-validity-${exam.id}-${issue.code}-${issue.relatedSessionId ?? index}`,
    tone: 'blocking',
    title: `Prüfung für „${courseName}“ kann nicht verwendet werden`,
    details: [
      `Betroffen ist der Prüfungstermin am ${formatCalendarDate(exam.date)} von ${exam.startTime} bis ${exam.endTime}.`,
      explanations[issue.code] ?? 'Eine bekannte Prüfungsregel ist nicht erfüllt; die genaue Ursache ist für diese Regel nicht verfügbar.',
      'Der Fehler blockiert die Verwendung dieses Prüfungstermins. Die gespeicherte Platzierung bleibt erhalten.',
      guidance[issue.code] ?? 'Öffnen Sie „Bearbeiten“, prüfen Sie die Prüfungsangaben und korrigieren Sie die markierten Werte.',
    ],
  }
}

type DraftSchedulePanelProps = {
  schedules: DraftSchedule[]
  rooms?: RoomOption[]
  lecturers?: LecturerRecord[]
  courseResources?: PlanningOptions['courseResources']
  onUpdateSession?: (sessionId: number, payload: EditableDraftSessionRequest) => Promise<void>
  onDeleteSession?: (session: DraftSession, schedule: DraftSchedule) => void
  resetKey?: number
  isBusy?: boolean
  exams?: ExamSession[]
  onEditExam?: (exam: ExamSession) => void
  onDeleteExam?: (exam: ExamSession) => void
  examCourseNames?: Record<number, string>
  readOnly?: boolean
  contextLabel?: string
  requestedEditSessionId?: number | null
  onRequestedEditHandled?: () => void
  workspaceListContext?: WorkspaceListContext | null
}

export function DraftSchedulePanel(props: DraftSchedulePanelProps) {
  return <DraftSchedulePanelStateful key={props.resetKey ?? 0} {...props} />
}

function DraftSchedulePanelStateful({
  schedules,
  rooms = EMPTY_ROOMS,
  lecturers = EMPTY_LECTURERS,
  courseResources = EMPTY_COURSE_RESOURCES,
  onUpdateSession,
  onDeleteSession,
  isBusy = false,
  exams = EMPTY_EXAMS,
  onEditExam,
  onDeleteExam,
  examCourseNames = {},
  readOnly = false,
  contextLabel,
  requestedEditSessionId,
  onRequestedEditHandled,
  workspaceListContext,
}: DraftSchedulePanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [filters, setFilters] = useState<ReviewFilters>({})
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState<EditableDraftSessionRequest | null>(null)
  const [editErrors, setEditErrors] = useState<SessionEditFailure[]>([])
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const listTraceTargetRef = useRef<HTMLDivElement>(null)
  const listTraceReference = workspaceListContext?.traceTarget?.reference
  const overviewSessions = useMemo(
    () => buildTeachingSessionEditModels(schedules, rooms, lecturers, courseResources),
    [schedules, rooms, lecturers, courseResources],
  )
  const filterOptions = useMemo(() => buildFilterOptions(overviewSessions, schedules, exams, examCourseNames), [overviewSessions, schedules, exams, examCourseNames])
  const scopedSessions = scopeTeachingSessions(overviewSessions, workspaceListContext)
  const scopedExams = scopeExamSessions(exams, workspaceListContext)
  const visibleSessions = sortSessionsChronologically(
    scopedSessions.filter((session) => matchesFilters(session, filters)),
  )
  const hasActiveFilters = Object.values(filters).some((value) => value !== undefined)
  const visibleExams = scopedExams.filter((exam) => (
    (filters.courseId === undefined || exam.courseId === filters.courseId) &&
    (filters.cohortId === undefined || exam.cohort.id === filters.cohortId) &&
    (filters.lecturerId === undefined || exam.lecturer.id === filters.lecturerId) &&
    (filters.roomId === undefined || exam.room.id === filters.roomId)
  )).sort((left, right) => `${left.date}-${left.startTime}-${left.id}`.localeCompare(`${right.date}-${right.startTime}-${right.id}`))

  useEffect(() => {
    if (requestedEditSessionId == null || readOnly || isBusy) return
    const session = overviewSessions.find((item) => item.id === requestedEditSessionId)
    if (!session) return
    let cancelled = false
    queueMicrotask(() => {
      if (cancelled) return
      setViewMode('list')
      setEditingSessionId(session.id)
      setEditDraft({
        date: session.date,
        startTime: session.startTime,
        endTime: session.endTime,
        lecturerId: session.lecturerId,
        roomId: session.roomId,
      })
      setEditErrors([])
      onRequestedEditHandled?.()
    })
    return () => {
      cancelled = true
    }
  }, [
    requestedEditSessionId,
    readOnly,
    isBusy,
    overviewSessions,
    onRequestedEditHandled,
  ])

  useEffect(() => {
    if (listTraceReference == null) return
    let cancelled = false
    queueMicrotask(() => {
      if (cancelled) return
      setViewMode('list')
      listTraceTargetRef.current?.focus()
    })
    return () => {
      cancelled = true
    }
  }, [listTraceReference])

  return (
    <section className={`planner-panel ${isBusy ? 'overview-busy' : ''}`} aria-labelledby="courses-overview-title" aria-busy={isBusy}>
      <div className="panel-toolbar">
        <div>
          <p className="eyebrow">{contextLabel ?? 'Planungsentwürfe'}</p>
          <h2 id="courses-overview-title">{label('course.heading')}</h2>
        </div>
      </div>
      {workspaceListContext?.traceTarget && (
        <div
          className="workspace-list-trace"
          role="status"
          tabIndex={-1}
          ref={listTraceTargetRef}
          data-trace-reference={workspaceListContext.traceTarget.reference}
        >
          <strong>Betroffener Datensatz</strong>
          <span>{workspaceListContext.traceTarget.label}</span>
          {workspaceListContext.traceTarget.teachingSessionIds.length === 0
            && workspaceListContext.traceTarget.examIds.length === 0
            && <span>Kein geplanter Termin entspricht den aktiven Filtern. Verwenden Sie die vorhandenen Planungsfelder für diese {label('course.singular')}.</span>}
        </div>
      )}

      {overviewSessions.length > 0 || exams.length > 0 ? (
        <>
          {workspaceListContext == null && <div className="filter-bar" aria-label="Filter für Entwurfstermine">
            <FilterSelect
              label={label('course.fieldLabel')}
              name="courseId"
              value={filters.courseId}
              options={filterOptions.courses}
              onChange={setFilter}
            />
            <FilterSelect
              label={label('cohort.fieldLabel')}
              name="cohortId"
              value={filters.cohortId}
              options={filterOptions.cohorts}
              onChange={setFilter}
            />
            <FilterSelect
              label={label('lecturer.fieldLabel')}
              name="lecturerId"
              value={filters.lecturerId}
              options={filterOptions.lecturers}
              onChange={setFilter}
            />
            <FilterSelect
              label={label('room.fieldLabel')}
              name="roomId"
              value={filters.roomId}
              options={filterOptions.rooms}
              onChange={setFilter}
            />
            <FilterSelect
              label="Studienart"
              name="studyTypeId"
              value={filters.studyTypeId}
              options={filterOptions.studyTypes}
              onChange={setFilter}
            />
            <button type="button" onClick={() => setFilters({})} disabled={!hasActiveFilters}>
              Filter zurücksetzen
            </button>
          </div>}

          <div className="review-controls" aria-label="Ansichtsmodus">
            <button
              type="button"
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              Liste
            </button>
            <button
              type="button"
              className={viewMode === 'weekly' ? 'active' : ''}
              onClick={() => setViewMode('weekly')}
            >
              Woche
            </button>
          </div>

          {visibleSessions.length === 0 ? (
            visibleExams.length === 0 && <p className="empty-state">Keine Termine entsprechen den aktiven Filtern.</p>
          ) : viewMode === 'list' ? (
            <div className="session-table" aria-label="Entwurfstermine">
              <div className="session-row session-header">
                <span>Datum</span>
                <span>Zeit</span>
                <span>Dauer</span>
                <span>{label('course.tableHeading')}</span>
                <span>{label('cohort.tableHeading')}</span>
                <span>{label('lecturer.tableHeading')}</span>
                <span>{label('room.tableHeading')}</span>
                <span>Studienart</span>
                 {!readOnly && <span>Aktionen</span>}
              </div>
              {visibleSessions.map((session) => (
                editingSessionId === session.id && editDraft ? (
                <div className="session-row" key={`${session.draftScheduleId}-${session.id}`}>
                  <TeachingSessionEditor
                    session={session}
                    draft={editDraft}
                    isSaving={isSavingEdit}
                    isDisabled={isBusy}
                    errors={editErrors}
                    onChange={setEditDraft}
                    onCancel={closeEdit}
                    onSave={saveEdit}
                  />
                </div>
                ) : (
                  <ScheduleOccurrenceRow
                    className="session-row"
                    occurrenceRef={`teaching:${session.id}`}
                    kind="teaching"
                    key={`${session.draftScheduleId}-${session.id}`}
                  >
                    <span>
                      {formatCalendarDate(session.date)}
                      <SessionAlerts alerts={session.validationAlerts} />
                    </span>
                    <span>{session.startTime}-{session.endTime}</span>
                    <span>{derivedLengthLabel(session.startTime, session.endTime)}</span>
                    <span>{session.context.course.name}</span>
                    <span>{session.context.cohort.name}</span>
                    <span>{resourceLabel(session.lecturer)}</span>
                    <span>{resourceLabel(session.room)}</span>
                    <span>{session.context.studyType.name}</span>
                    {!readOnly && <span className="session-actions">
                      <button type="button" className="secondary-button compact-button" onClick={() => openEdit(session)} disabled={isBusy}>Bearbeiten</button>
                      <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>Löschen</button>
                    </span>}
                  </ScheduleOccurrenceRow>
                )
              ))}
            </div>
          ) : (
            <div className="weekly-review" aria-label="Entwurfstermine nach Woche">
              {groupSessionsByWeek(visibleSessions).map((week) => (
                <section className="week-group" key={week.weekStart}>
                  <h3>Woche ab {formatCalendarDate(week.weekStart)}</h3>
                  <div className="week-days">
                    {week.days.map((day) => (
                      <div className="week-day" key={day.date}>
                        <h4>{formatCalendarDate(day.date)}</h4>
                        {day.sessions.map((session) => (
                          <article className="week-session" key={`${session.draftScheduleId}-${session.id}`}>
                            <strong>
                              {session.startTime}-{session.endTime}
                            </strong>
                            <span>{derivedLengthLabel(session.startTime, session.endTime)}</span>
                            <span>{session.context.course.name}</span>
                            <span>{session.context.cohort.name}</span>
                            <span>{resourceLabel(session.lecturer)}</span>
                            <span>{resourceLabel(session.room)}</span>
                            <span>{session.context.studyType.name}</span>
                            <SessionAlerts alerts={session.validationAlerts} />
                            {!readOnly && <button type="button" className="secondary-button compact-button" onClick={() => openEdit(session)} disabled={isBusy}>
                              Bearbeiten
                            </button>}
                            {!readOnly && <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>
                              Löschen
                            </button>}
                          </article>
                        ))}
                      </div>
                    ))}
                  </div>
                </section>
              ))}
            </div>
          )}
          {visibleExams.length > 0 && (
            <div className="session-table exam-session-table" aria-label="Prüfungstermine">
              <div className="session-row exam-session-row session-header"><span>Art</span><span>Datum und Uhrzeit</span><span>Status</span><span>Prüfung</span><span>{label('course.tableHeading')}</span><span>{label('cohort.tableHeading')}</span><span>{label('lecturer.tableHeading')}</span><span>{label('room.tableHeading')}</span>{!readOnly && <span>Aktionen</span>}</div>
              {visibleExams.map((exam) => <ScheduleOccurrenceRow className="session-row exam-session-row" occurrenceRef={`exam:${exam.id}`} kind="exam" key={`exam-${exam.id}`}>
                <span><strong>Prüfung</strong>{exam.source === 'generated' ? ' · Erzeugt' : ' · Manuell'}</span>
                <span>{formatCalendarDate(exam.date)}<br/>{exam.startTime}-{exam.endTime} ({exam.durationMinutes} min)</span>
                <span className={`exam-lifecycle ${exam.lifecycleStatus}`}>{exam.lifecycleStatus === 'active' ? 'Aktiv' : 'Vergangen'}</span>
                <span>{exam.configurationIdentifier}<br/>{exam.examType}<small>Empfohlener Zeitraum {formatCalendarDateRange(exam.recommendedStartDate, exam.recommendedEndDate)}{exam.recommendationWasOverridden ? ' (manuell festgelegt)' : ''}</small><small>Letzte Lehrveranstaltung {formatCalendarDate(exam.finalTeachingAnchor.date)} um {exam.finalTeachingAnchor.endTime}</small><ActionableProblemList problems={[
                  ...(exam.outsideRecommendedWindow ? [outsideRecommendedWindowProblem({ exam, courseName: examCourseNames[exam.courseId] ?? `${label('course.singular')} ${exam.courseId}`, saved: true, editable: !readOnly })] : []),
                  ...exam.validityIssues.map((issue, index) => examValidityProblem(exam, issue, examCourseNames[exam.courseId] ?? `${label('course.singular')} ${exam.courseId}`, index)),
                ]} /></span>
                <span>{examCourseNames[exam.courseId] ?? `${label('course.singular')} #${exam.courseId}`}</span><span>{exam.cohort.name}</span><span>{resourceLabel(exam.lecturer)}</span><span>{resourceLabel(exam.room)} · Kapazität {exam.room.capacity}/{exam.requiredCapacity} erforderlich</span>
                {!readOnly && <span className="session-actions"><button type="button" className="secondary-button compact-button" disabled={isBusy} onClick={()=>onEditExam?.(exam)}>Bearbeiten</button><button type="button" className="destructive-button compact-button" disabled={isBusy} onClick={()=>onDeleteExam?.(exam)}>Löschen</button></span>}
              </ScheduleOccurrenceRow>)}
            </div>
          )}
        </>
      ) : (
        <p className="empty-state">Für dieses Semester gibt es noch keine Planungsentwürfe.</p>
      )}
    </section>
  )

  function setFilter(name: keyof ReviewFilters, value?: number) {
    setFilters((current) => ({
      ...current,
      [name]: value,
    }))
  }

  function openEdit(session: TeachingSessionEditModel) {
    if (isBusy || readOnly) return
    setViewMode('list')
    setEditingSessionId(session.id)
    setEditDraft(createTeachingSessionDraft(session))
    setEditErrors([])
  }

  function requestDelete(session: TeachingSessionEditModel) {
    const schedule = schedules.find((item) => item.draftScheduleId === session.draftScheduleId)
    if (schedule && onDeleteSession) onDeleteSession(session, schedule)
  }

  function closeEdit() {
    setEditingSessionId(null)
    setEditDraft(null)
    setEditErrors([])
    setIsSavingEdit(false)
  }

  async function saveEdit() {
    if (!editingSessionId || !editDraft || !onUpdateSession) {
      return
    }
    setIsSavingEdit(true)
    setEditErrors([])
    try {
      await onUpdateSession(editingSessionId, editDraft)
      closeEdit()
    } catch (error) {
      setEditErrors(Array.isArray(error) ? error : [{ code: 'REQUEST_FAILED', message: 'Der Termin konnte nicht gespeichert werden. Prüfen Sie die Eingaben und versuchen Sie es erneut.' }])
      setIsSavingEdit(false)
    }
  }
}

function SessionAlerts({ alerts }: { alerts: DraftSession['validationAlerts'] }) {
  if (alerts.length === 0) {
    return null
  }
  return (
    <div className="validation-alerts">
      {alerts.map((alert) => (
        <details className="validation-alert" key={`${alert.code}-${alert.message}`}>
          <summary>
            <span className="validation-alert-code">Hinweis</span>
            <span>{safeReasonText(alert.code, 'Termin')}{alert.holidayDate ? ` Feiertag „${alert.holidayName ?? 'unbekannt'}“ am ${formatCalendarDate(alert.holidayDate)}.` : ''}</span>
          </summary>
          {alert.relatedSessions.length > 0 && (
            <ul>
              {alert.relatedSessions.map((related) => (
                <li key={related.sessionId}>
                  {related.courseName} | {formatCalendarDate(related.date)} {related.startTime}-{related.endTime} | {related.cohortName} | {related.lecturerName} | {related.roomName}
                </li>
              ))}
            </ul>
          )}
        </details>
      ))}
    </div>
  )
}

type FilterSelectProps = {
  label: string
  name: keyof ReviewFilters
  value?: number
  options: PlanningEntity[]
  onChange: (name: keyof ReviewFilters, value?: number) => void
}

function FilterSelect({ label, name, value, options, onChange }: FilterSelectProps) {
  return (
    <label className="filter-field">
      <span>{label}</span>
      <select
        name={name}
        value={value ?? ''}
        onChange={(event) =>
          onChange(name, event.target.value ? Number(event.target.value) : undefined)
        }
      >
        <option value="">Alle</option>
        {options.map((option) => (
          <option value={option.id} key={option.id}>
            {option.name}
          </option>
        ))}
      </select>
    </label>
  )
}

type GenerationConstraintEditorProps = {
  constraints: GenerationConstraints
  isLoading: boolean
  onChange: (constraints: GenerationConstraints) => void
  onClear: () => void
}

export function GenerationConstraintEditor({
  constraints,
  isLoading,
  onChange,
  onClear,
}: GenerationConstraintEditorProps) {
  return (
    <section className="generation-constraints" aria-labelledby="generation-constraints-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Erzeugungsregeln</p>
          <h3 id="generation-constraints-title">Eingaben für den nächsten Entwurf</h3>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={onClear}
          disabled={isLoading || !constraints.isCustom}
        >
          Benutzerdefinierte Regeln zurücksetzen
        </button>
      </div>

      <div className="constraint-grid">
        <EuropeanDateField id="generation-start-date" label="Beginn" value={constraints.planningPeriod.startDate} onChange={(value) => onChange({ ...constraints, planningPeriod: { ...constraints.planningPeriod, startDate: value ?? '' } })} required />
        <EuropeanDateField id="generation-end-date" label="Ende" value={constraints.planningPeriod.endDate} min={constraints.planningPeriod.startDate} onChange={(value) => onChange({ ...constraints, planningPeriod: { ...constraints.planningPeriod, endDate: value ?? '' } })} required />
      </div>

      <div className="constraint-window-list" aria-label="Erlaubte wöchentliche Lehrzeitfenster">
        {constraints.allowedTeachingWindows.map((window, index) => (
          <div className="constraint-window-row" key={`${window.weekday}-${index}`}>
            <label className="constraint-field">
              <span>Wochentag</span>
              <select
                value={window.weekday}
                onChange={(event) =>
                  onChange(updateWindow(constraints, index, { weekday: Number(event.target.value) }))
                }
              >
                {WEEKDAY_NAMES.map((label, weekday) => (
                  <option value={weekday} key={label}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
            <label className="constraint-field">
              <span>Beginn</span>
              <input
                type="time"
                value={window.startTime}
                onChange={(event) =>
                  onChange(updateWindow(constraints, index, { startTime: event.target.value }))
                }
              />
            </label>
            <label className="constraint-field">
              <span>Ende</span>
              <input
                type="time"
                value={window.endTime}
                onChange={(event) =>
                  onChange(updateWindow(constraints, index, { endTime: event.target.value }))
                }
              />
            </label>
            <button
              type="button"
              className="secondary-button"
              onClick={() => onChange(removeWindow(constraints, index))}
              disabled={constraints.allowedTeachingWindows.length <= 1}
            >
              Entfernen
            </button>
          </div>
        ))}
      </div>

      <button
        type="button"
        className="secondary-button"
        onClick={() =>
          onChange({
            ...constraints,
            allowedTeachingWindows: [
              ...constraints.allowedTeachingWindows,
              { weekday: 0, startTime: '08:00', endTime: '12:00' },
            ],
          })
        }
      >
        Zeitfenster hinzufügen
      </button>
    </section>
  )
}

function updateWindow(
  constraints: GenerationConstraints,
  index: number,
  patch: Partial<AllowedTeachingWindow>,
): GenerationConstraints {
  return {
    ...constraints,
    allowedTeachingWindows: constraints.allowedTeachingWindows.map((window, currentIndex) =>
      currentIndex === index
        ? {
            ...window,
            ...patch,
            sourceTimeWindowId: patch.weekday === undefined ? window.sourceTimeWindowId : null,
          }
        : window,
    ),
  }
}

function removeWindow(constraints: GenerationConstraints, index: number): GenerationConstraints {
  return {
    ...constraints,
    allowedTeachingWindows: constraints.allowedTeachingWindows.filter((_, currentIndex) => currentIndex !== index),
  }
}

type FilterOptions = {
  courses: PlanningEntity[]
  cohorts: PlanningEntity[]
  lecturers: PlanningEntity[]
  rooms: PlanningEntity[]
  studyTypes: PlanningEntity[]
}

function buildFilterOptions(sessions: TeachingSessionEditModel[], schedules: DraftSchedule[], exams: ExamSession[] = [], examCourseNames: Record<number, string> = {}): FilterOptions {
  return {
    courses: uniqueEntities([...schedules.map((schedule) => schedule.context.course), ...exams.map((exam) => ({ id: exam.courseId, name: examCourseNames[exam.courseId] ?? `${label('course.singular')} #${exam.courseId}` }))]),
    cohorts: uniqueEntities([...schedules.map((schedule) => schedule.context.cohort), ...exams.map((exam) => ({ id: exam.cohort.id, name: exam.cohort.name }))]),
    lecturers: uniqueEntities([...sessions.map((session) => ({ id: session.lecturerId, name: resourceLabel(session.lecturer) })), ...exams.map((exam) => ({ id: exam.lecturer.id, name: resourceLabel(exam.lecturer) }))]),
    rooms: uniqueEntities([...sessions.map((session) => ({ id: session.roomId, name: resourceLabel(session.room) })), ...exams.map((exam) => ({ id: exam.room.id, name: resourceLabel(exam.room) }))]),
    studyTypes: uniqueEntities(schedules.map((schedule) => schedule.context.studyType)),
  }
}

function uniqueEntities(entities: PlanningEntity[]): PlanningEntity[] {
  return [...new Map(entities.map((entity) => [entity.id, entity])).values()].sort((a, b) =>
    a.name.localeCompare(b.name),
  )
}

function scopeTeachingSessions(
  sessions: TeachingSessionEditModel[],
  context?: WorkspaceListContext | null,
) {
  if (context == null) return sessions
  const trace = context.traceTarget
  if (trace != null) {
    const sessionIds = new Set(trace.teachingSessionIds)
    return sessions.filter((session) => sessionIds.has(session.id))
  }
  const sessionIds = new Set(context.teachingSessionIds)
  return sessions.filter((session) => sessionIds.has(session.id))
}

function scopeExamSessions(
  exams: ExamSession[],
  context?: WorkspaceListContext | null,
) {
  if (context == null) return exams
  const trace = context.traceTarget
  if (trace != null) {
    const examIds = new Set(trace.examIds)
    return exams.filter((exam) => examIds.has(exam.id))
  }
  const examIds = new Set(context.examIds)
  return exams.filter((exam) => examIds.has(exam.id))
}

function matchesFilters(session: TeachingSessionEditModel, filters: ReviewFilters): boolean {
  return (
    (filters.courseId === undefined || session.courseId === filters.courseId) &&
    (filters.cohortId === undefined || session.cohortId === filters.cohortId) &&
    (filters.lecturerId === undefined || session.lecturerId === filters.lecturerId) &&
    (filters.roomId === undefined || session.roomId === filters.roomId) &&
    (filters.studyTypeId === undefined || session.studyTypeId === filters.studyTypeId)
  )
}
