import { useMemo, useState } from 'react'

import type {
  AllowedTeachingWindow,
  DraftScheduleContext,
  DraftSession,
  DraftSchedule,
  GenerationConstraints,
  PlanningEntity,
  ReviewFilters,
  SessionEditFailure,
  UpdateDraftSessionRequest,
  ViewMode,
} from '../api/draftSchedule'
import type { PlanningOptions, RoomOption } from '../api/planningOptions'
import type { LecturerRecord, ResourceCandidate } from '../api/resourceCatalog'
import { WEEKDAY_NAMES } from '../utils/weekdays'
import {
  groupSessionsByWeek,
  sortSessionsChronologically,
} from './scheduleReviewUtils'

type DraftSchedulePanelProps = {
  schedules: DraftSchedule[]
  rooms?: RoomOption[]
  lecturers?: LecturerRecord[]
  courseResources?: PlanningOptions['courseResources']
  onUpdateSession?: (sessionId: number, payload: UpdateDraftSessionRequest) => Promise<void>
  onDeleteSession?: (session: DraftSession, schedule: DraftSchedule) => void
  resetKey?: number
  isBusy?: boolean
}

export function DraftSchedulePanel(props: DraftSchedulePanelProps) {
  return <DraftSchedulePanelStateful key={props.resetKey ?? 0} {...props} />
}

function DraftSchedulePanelStateful({
  schedules,
  rooms = [],
  lecturers = [],
  courseResources = [],
  onUpdateSession,
  onDeleteSession,
  isBusy = false,
}: DraftSchedulePanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [filters, setFilters] = useState<ReviewFilters>({})
  const [editingSessionId, setEditingSessionId] = useState<number | null>(null)
  const [editDraft, setEditDraft] = useState<UpdateDraftSessionRequest | null>(null)
  const [editErrors, setEditErrors] = useState<SessionEditFailure[]>([])
  const [isSavingEdit, setIsSavingEdit] = useState(false)
  const overviewSessions = useMemo(
    () => flattenSchedules(schedules, rooms, lecturers, courseResources),
    [schedules, rooms, lecturers, courseResources],
  )
  const filterOptions = useMemo(() => buildFilterOptions(overviewSessions, schedules), [overviewSessions, schedules])
  const visibleSessions = sortSessionsChronologically(
    overviewSessions.filter((session) => matchesFilters(session, filters)),
  )
  const hasActiveFilters = Object.values(filters).some((value) => value !== undefined)

  return (
    <section className={`planner-panel ${isBusy ? 'overview-busy' : ''}`} aria-labelledby="courses-overview-title" aria-busy={isBusy}>
      <div className="panel-toolbar">
        <div>
          <p className="eyebrow">Draft plans</p>
          <h2 id="courses-overview-title">Courses overview</h2>
        </div>
      </div>

      {overviewSessions.length > 0 ? (
        <>
          <div className="filter-bar" aria-label="Draft session filters">
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
          </div>

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
            <p className="empty-state">No sessions match the active filters.</p>
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
                <span>Actions</span>
              </div>
              {visibleSessions.map((session) => (
                <div className="session-row" key={`${session.draftScheduleId}-${session.id}`}>
                  {editingSessionId === session.id && editDraft ? (
                    <SessionEditFields
                      session={session}
                      draft={editDraft}
                      isSaving={isSavingEdit}
                      isDisabled={isBusy}
                      errors={editErrors}
                      onChange={setEditDraft}
                      onCancel={closeEdit}
                      onSave={saveEdit}
                    />
                  ) : (
                    <>
                      <span>
                        {session.date}
                        <SessionAlerts alerts={session.validationAlerts} />
                      </span>
                      <span>
                        {session.startTime}-{session.endTime}
                      </span>
                      <span>{derivedLengthLabel(session.startTime, session.endTime)}</span>
                      <span>{session.context.course.name}</span>
                      <span>{session.context.cohort.name}</span>
                      <span>{resourceLabel(session.lecturer)}</span>
                      <span>{resourceLabel(session.room)}</span>
                      <span>{session.context.studyType.name}</span>
                      <span className="session-actions">
                        <button type="button" className="secondary-button compact-button" onClick={() => openEdit(session)} disabled={isBusy}>
                          Edit
                        </button>
                        <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>
                          Delete
                        </button>
                      </span>
                    </>
                  )}
                </div>
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
                            <button type="button" className="secondary-button compact-button" onClick={() => openEdit(session)} disabled={isBusy}>
                              Edit
                            </button>
                            <button type="button" className="destructive-button compact-button" onClick={() => requestDelete(session)} disabled={isBusy}>
                              Delete
                            </button>
                          </article>
                        ))}
                      </div>
                    ))}
                  </div>
                </section>
              ))}
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

  function openEdit(session: OverviewSession) {
    if (isBusy) return
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
  }

  function requestDelete(session: OverviewSession) {
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

type SessionEditFieldsProps = {
  session: OverviewSession
  draft: UpdateDraftSessionRequest
  isSaving: boolean
  isDisabled: boolean
  errors: SessionEditFailure[]
  onChange: (draft: UpdateDraftSessionRequest) => void
  onCancel: () => void
  onSave: () => void
}

function SessionEditFields({
  session,
  draft,
  isSaving,
  isDisabled,
  errors,
  onChange,
  onCancel,
  onSave,
}: SessionEditFieldsProps) {
  const availableLecturers = session.eligibleLecturers.length > 0
    ? session.eligibleLecturers
    : [session.lecturer]
  const availableRooms = session.eligibleRooms.length > 0
    ? session.eligibleRooms
    : [{ ...session.room, capacity: session.context.cohortSize }]

  return (
    <>
      <label className="inline-edit-field">
        <span>Date</span>
        <input
          type="date"
          value={draft.date}
          disabled={isDisabled}
          onChange={(event) => onChange({ ...draft, date: event.target.value })}
        />
      </label>
      <label className="inline-edit-field">
        <span>Start</span>
        <input
          type="time"
          value={draft.startTime}
          disabled={isDisabled}
          onChange={(event) => onChange({ ...draft, startTime: event.target.value })}
        />
      </label>
      <label className="inline-edit-field">
        <span>End</span>
        <input
          type="time"
          value={draft.endTime}
          disabled={isDisabled}
          onChange={(event) => onChange({ ...draft, endTime: event.target.value })}
        />
      </label>
      <span>{derivedLengthLabel(draft.startTime, draft.endTime)}</span>
      <span>{session.context.course.name}</span>
      <span>{session.context.cohort.name}</span>
      <label className="lecturer-edit-field">
        <span>Lecturer</span>
        <select
          value={draft.lecturerId}
          disabled={isDisabled}
          onChange={(event) => onChange({ ...draft, lecturerId: Number(event.target.value) })}
        >
          {availableLecturers.map((lecturer) => (
            <option value={lecturer.id} key={lecturer.id}>{resourceLabel(lecturer)}</option>
          ))}
        </select>
      </label>
      <label className="inline-edit-field">
        <span>Room</span>
        <select
          value={draft.roomId}
          disabled={isDisabled}
          onChange={(event) => onChange({ ...draft, roomId: Number(event.target.value) })}
        >
          {availableRooms.map((room) => (
            <option value={room.id} key={room.id}>
              {resourceLabel(room)}
              {room.capacity ? ` (${room.capacity} seats)` : ''}
            </option>
          ))}
        </select>
      </label>
      <div className="edit-actions">
        <button type="button" onClick={onSave} disabled={isSaving || isDisabled}>
          Save
        </button>
        <button type="button" className="secondary-button" onClick={onCancel} disabled={isSaving}>
          Cancel
        </button>
        {errors.length > 0 && (
          <div className="inline-error" role="alert">
            {errors.map((error) => (
              <span key={error.code}>{error.message}</span>
            ))}
          </div>
        )}
      </div>
    </>
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

type OverviewSession = DraftSession & {
  draftScheduleId: number
  context: DraftScheduleContext
  eligibleLecturers: EditableResource[]
  eligibleRooms: EditableResource[]
}

type EditableResource = { id: number; name: string; referenceCode?: string; capacity?: number | null }

type FilterOptions = {
  courses: PlanningEntity[]
  cohorts: PlanningEntity[]
  lecturers: PlanningEntity[]
  rooms: PlanningEntity[]
  studyTypes: PlanningEntity[]
}

function flattenSchedules(
  schedules: DraftSchedule[],
  rooms: RoomOption[],
  lecturers: LecturerRecord[],
  courseResources: PlanningOptions['courseResources'],
): OverviewSession[] {
  return schedules.flatMap((schedule) =>
    schedule.sessions.map((session) => {
      const configuration = courseResources.find((item) => item.courseId === schedule.courseId)
      const listedRoom = rooms.find((item) => item.id === session.roomId)
      const listedLecturer = lecturers.find((item) => item.id === session.lecturerId)
      const currentLecturer = listedLecturer
        ? { id: listedLecturer.id, name: listedLecturer.name, referenceCode: listedLecturer.referenceCode }
        : session.lecturer
      const currentRoom = listedRoom
        ? { id: listedRoom.id, name: listedRoom.name, referenceCode: 'referenceCode' in listedRoom ? String(listedRoom.referenceCode) : '', capacity: listedRoom.capacity }
        : session.room
      return {
        ...session,
        lecturer: currentLecturer,
        room: currentRoom,
        draftScheduleId: schedule.draftScheduleId,
        context: schedule.context,
        eligibleLecturers: configuration
          ? editableCandidates(configuration.eligibleLecturers, currentLecturer)
          : lecturers.filter((item) => item.isActive || item.id === session.lecturerId).map((item) => ({ ...item })),
        eligibleRooms: configuration
          ? editableCandidates(configuration.eligibleRooms, currentRoom)
          : rooms.filter((item) => item.capacity >= schedule.context.cohortSize || item.id === session.roomId).map((item) => ({
              ...item,
              referenceCode: 'referenceCode' in item ? String(item.referenceCode) : '',
            })),
      }
    }),
  )
}

function buildFilterOptions(sessions: OverviewSession[], schedules: DraftSchedule[]): FilterOptions {
  return {
    courses: uniqueEntities(schedules.map((schedule) => schedule.context.course)),
    cohorts: uniqueEntities(schedules.map((schedule) => schedule.context.cohort)),
    lecturers: uniqueEntities(sessions.map((session) => ({ id: session.lecturerId, name: resourceLabel(session.lecturer) }))),
    rooms: uniqueEntities(sessions.map((session) => ({ id: session.roomId, name: resourceLabel(session.room) }))),
    studyTypes: uniqueEntities(schedules.map((schedule) => schedule.context.studyType)),
  }
}

function editableCandidates(candidates: ResourceCandidate[], current: EditableResource): EditableResource[] {
  const options = candidates
    .filter((candidate) => candidate.id === current.id || (candidate.isEligible && candidate.isUsable))
    .map((candidate) => ({
      id: candidate.id,
      name: candidate.name,
      referenceCode: candidate.referenceCode,
      capacity: candidate.capacity,
    }))
  return options.some((option) => option.id === current.id) ? options : [current, ...options]
}

function resourceLabel(resource: { name: string; referenceCode?: string }): string {
  return resource.referenceCode ? `${resource.name} Â· ${resource.referenceCode}` : resource.name
}

function uniqueEntities(entities: PlanningEntity[]): PlanningEntity[] {
  return [...new Map(entities.map((entity) => [entity.id, entity])).values()].sort((a, b) =>
    a.name.localeCompare(b.name),
  )
}

function matchesFilters(session: OverviewSession, filters: ReviewFilters): boolean {
  return (
    (filters.courseId === undefined || session.courseId === filters.courseId) &&
    (filters.cohortId === undefined || session.cohortId === filters.cohortId) &&
    (filters.lecturerId === undefined || session.lecturerId === filters.lecturerId) &&
    (filters.roomId === undefined || session.roomId === filters.roomId) &&
    (filters.studyTypeId === undefined || session.studyTypeId === filters.studyTypeId)
  )
}

function derivedLengthLabel(startTime: string, endTime: string): string {
  const minutes = minutesBetween(startTime, endTime)
  if (minutes === null) {
    return 'Invalid'
  }
  if (minutes < 60) {
    return `${minutes} min`
  }
  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return remainder === 0 ? `${hours} h` : `${hours} h ${remainder} min`
}

function minutesBetween(startTime: string, endTime: string): number | null {
  const [startHour, startMinute] = startTime.split(':').map(Number)
  const [endHour, endMinute] = endTime.split(':').map(Number)
  if ([startHour, startMinute, endHour, endMinute].some((value) => Number.isNaN(value))) {
    return null
  }
  const minutes = endHour * 60 + endMinute - (startHour * 60 + startMinute)
  return minutes > 0 ? minutes : null
}
