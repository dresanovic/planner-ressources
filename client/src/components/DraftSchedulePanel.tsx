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
import type { ExamSession } from '../api/examScheduling'
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

const EMPTY_ROOMS: RoomOption[] = []
const EMPTY_LECTURERS: LecturerRecord[] = []
const EMPTY_COURSE_RESOURCES: PlanningOptions['courseResources'] = []
const EMPTY_EXAMS: ExamSession[] = []

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
          <p className="eyebrow">{contextLabel ?? 'Draft plans'}</p>
          <h2 id="courses-overview-title">Courses overview</h2>
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
          <strong>Affected record</strong>
          <span>{workspaceListContext.traceTarget.label}</span>
          {workspaceListContext.traceTarget.teachingSessionIds.length === 0
            && workspaceListContext.traceTarget.examIds.length === 0
            && <span>No scheduled session matches the active filters; use the existing course planning controls for this course.</span>}
        </div>
      )}

      {overviewSessions.length > 0 || exams.length > 0 ? (
        <>
          {workspaceListContext == null && <div className="filter-bar" aria-label="Draft session filters">
            <FilterSelect
              label="Course"
              name="courseId"
              value={filters.courseId}
              options={filterOptions.courses}
              onChange={setFilter}
            />
            <FilterSelect
              label="Cohort"
              name="cohortId"
              value={filters.cohortId}
              options={filterOptions.cohorts}
              onChange={setFilter}
            />
            <FilterSelect
              label="Lecturer"
              name="lecturerId"
              value={filters.lecturerId}
              options={filterOptions.lecturers}
              onChange={setFilter}
            />
            <FilterSelect
              label="Room"
              name="roomId"
              value={filters.roomId}
              options={filterOptions.rooms}
              onChange={setFilter}
            />
            <FilterSelect
              label="Study type"
              name="studyTypeId"
              value={filters.studyTypeId}
              options={filterOptions.studyTypes}
              onChange={setFilter}
            />
            <button type="button" onClick={() => setFilters({})} disabled={!hasActiveFilters}>
              Clear filters
            </button>
          </div>}

          <div className="review-controls" aria-label="Review view mode">
            <button
              type="button"
              className={viewMode === 'list' ? 'active' : ''}
              onClick={() => setViewMode('list')}
            >
              List
            </button>
            <button
              type="button"
              className={viewMode === 'weekly' ? 'active' : ''}
              onClick={() => setViewMode('weekly')}
            >
              Weekly
            </button>
          </div>

          {visibleSessions.length === 0 ? (
            visibleExams.length === 0 && <p className="empty-state">No sessions match the active filters.</p>
          ) : viewMode === 'list' ? (
            <div className="session-table" aria-label="Draft sessions">
              <div className="session-row session-header">
                <span>Date</span>
                <span>Time</span>
                <span>Length</span>
                <span>Course</span>
                <span>Cohort</span>
                <span>Lecturer</span>
                <span>Room</span>
                <span>Study type</span>
                 {!readOnly && <span>Actions</span>}
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
                      {session.date}
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
                      <button type="button" className="secondary-button compact-button" onClick={() => openEdit(session)} disabled={isBusy}>Edit</button>
                      <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>Delete</button>
                    </span>}
                  </ScheduleOccurrenceRow>
                )
              ))}
            </div>
          ) : (
            <div className="weekly-review" aria-label="Draft sessions by week">
              {groupSessionsByWeek(visibleSessions).map((week) => (
                <section className="week-group" key={week.weekStart}>
                  <h3>Week of {week.weekStart}</h3>
                  <div className="week-days">
                    {week.days.map((day) => (
                      <div className="week-day" key={day.date}>
                        <h4>{day.date}</h4>
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
                              Edit
                            </button>}
                            {!readOnly && <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>
                              Delete
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
            <div className="session-table exam-session-table" aria-label="Exam sessions">
              <div className="session-row exam-session-row session-header"><span>Kind</span><span>Date and time</span><span>Lifecycle</span><span>Exam</span><span>Course</span><span>Cohort</span><span>Lecturer</span><span>Room</span>{!readOnly && <span>Actions</span>}</div>
              {visibleExams.map((exam) => <ScheduleOccurrenceRow className="session-row exam-session-row" occurrenceRef={`exam:${exam.id}`} kind="exam" key={`exam-${exam.id}`}>
                <span><strong>Exam</strong>{exam.source === 'generated' ? ' · Generated' : ' · Manual'}</span>
                <span>{exam.date}<br/>{exam.startTime}-{exam.endTime} ({exam.durationMinutes} min)</span>
                <span className={`exam-lifecycle ${exam.lifecycleStatus}`}>{exam.lifecycleStatus === 'active' ? 'Active' : 'Past'}</span>
                <span>{exam.configurationIdentifier}<br/>{exam.examType}<small>Recommended {exam.recommendedStartDate}–{exam.recommendedEndDate}{exam.recommendationWasOverridden ? ' (planner override)' : ''}</small><small>Final teaching {exam.finalTeachingAnchor.date} at {exam.finalTeachingAnchor.endTime}</small>{exam.outsideRecommendedWindow && <small className="soft-notice"> Outside recommended window</small>}{exam.validityIssues.map((issue, index) => <small className="validation-alert" key={`${issue.code}-${index}`}>{issue.code.replaceAll('_', ' ')}: {issue.message}</small>)}</span>
                <span>{examCourseNames[exam.courseId] ?? `Course #${exam.courseId}`}</span><span>{exam.cohort.name}</span><span>{resourceLabel(exam.lecturer)}</span><span>{resourceLabel(exam.room)} · capacity {exam.room.capacity}/{exam.requiredCapacity} required</span>
                {!readOnly && <span className="session-actions"><button type="button" className="secondary-button compact-button" disabled={isBusy} onClick={()=>onEditExam?.(exam)}>Edit</button><button type="button" className="destructive-button compact-button" disabled={isBusy} onClick={()=>onDeleteExam?.(exam)}>Delete</button></span>}
              </ScheduleOccurrenceRow>)}
            </div>
          )}
        </>
      ) : (
        <p className="empty-state">No Draft Schedules for this semester yet.</p>
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
      setEditErrors(Array.isArray(error) ? error : [{ code: 'REQUEST_FAILED', message: 'Could not save edit.' }])
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
            <span className="validation-alert-code">{alert.code.replaceAll('_', ' ')}</span>
            <span>{alert.message}</span>
          </summary>
          {alert.relatedSessions.length > 0 && (
            <ul>
              {alert.relatedSessions.map((related) => (
                <li key={related.sessionId}>
                  {related.courseName} | {related.date} {related.startTime}-{related.endTime} | {related.cohortName} | {related.lecturerName} | {related.roomName}
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
        <option value="">All</option>
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
          <p className="eyebrow">Generation constraints</p>
          <h3 id="generation-constraints-title">Inputs for the next draft</h3>
        </div>
        <button
          type="button"
          className="secondary-button"
          onClick={onClear}
          disabled={isLoading || !constraints.isCustom}
        >
          Clear custom constraints
        </button>
      </div>

      <div className="constraint-grid">
        <label className="constraint-field">
          <span>Start date</span>
          <input
            type="date"
            value={constraints.planningPeriod.startDate}
            onChange={(event) =>
              onChange({
                ...constraints,
                planningPeriod: {
                  ...constraints.planningPeriod,
                  startDate: event.target.value,
                },
              })
            }
          />
        </label>
        <label className="constraint-field">
          <span>End date</span>
          <input
            type="date"
            value={constraints.planningPeriod.endDate}
            onChange={(event) =>
              onChange({
                ...constraints,
                planningPeriod: {
                  ...constraints.planningPeriod,
                  endDate: event.target.value,
                },
              })
            }
          />
        </label>
      </div>

      <div className="constraint-window-list" aria-label="Allowed weekly teaching windows">
        {constraints.allowedTeachingWindows.map((window, index) => (
          <div className="constraint-window-row" key={`${window.weekday}-${index}`}>
            <label className="constraint-field">
              <span>Weekday</span>
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
              <span>Start</span>
              <input
                type="time"
                value={window.startTime}
                onChange={(event) =>
                  onChange(updateWindow(constraints, index, { startTime: event.target.value }))
                }
              />
            </label>
            <label className="constraint-field">
              <span>End</span>
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
              Remove
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
        Add window
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
    courses: uniqueEntities([...schedules.map((schedule) => schedule.context.course), ...exams.map((exam) => ({ id: exam.courseId, name: examCourseNames[exam.courseId] ?? `Course #${exam.courseId}` }))]),
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
