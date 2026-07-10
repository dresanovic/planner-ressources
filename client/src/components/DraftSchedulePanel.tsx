import { useMemo, useState } from 'react'

import type {
  AllowedTeachingWindow,
  DraftScheduleContext,
  DraftSession,
  DraftSchedule,
  GenerationConstraints,
  PlanningEntity,
  ReviewFilters,
  ViewMode,
} from '../api/draftSchedule'
import {
  groupSessionsByWeek,
  sortSessionsChronologically,
} from './scheduleReviewUtils'

type DraftSchedulePanelProps = {
  schedules: DraftSchedule[]
}

export function DraftSchedulePanel({
  schedules,
}: DraftSchedulePanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [filters, setFilters] = useState<ReviewFilters>({})
  const overviewSessions = useMemo(() => flattenSchedules(schedules), [schedules])
  const filterOptions = useMemo(() => buildFilterOptions(schedules), [schedules])
  const visibleSessions = sortSessionsChronologically(
    overviewSessions.filter((session) => matchesFilters(session, filters)),
  )
  const hasActiveFilters = Object.values(filters).some((value) => value !== undefined)

  return (
    <section className="planner-panel" aria-labelledby="courses-overview-title">
      <div className="panel-toolbar">
        <div>
          <p className="eyebrow">Generated plans</p>
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
            <div className="session-table" aria-label="Generated draft sessions">
              <div className="session-row session-header">
                <span>Date</span>
                <span>Time</span>
                <span>Units</span>
                <span>Course</span>
                <span>Cohort</span>
                <span>Lecturer</span>
                <span>Room</span>
                <span>Study type</span>
              </div>
              {visibleSessions.map((session) => (
                <div className="session-row" key={`${session.draftScheduleId}-${session.id}`}>
                  <span>{session.date}</span>
                  <span>
                    {session.startTime}-{session.endTime}
                  </span>
                  <span>{session.units}</span>
                  <span>{session.context.course.name}</span>
                  <span>{session.context.cohort.name}</span>
                  <span>{session.context.lecturer.name}</span>
                  <span>{session.context.room.name}</span>
                  <span>{session.context.studyType.name}</span>
                </div>
              ))}
            </div>
          ) : (
            <div className="weekly-review" aria-label="Generated draft sessions by week">
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
                            <span>{session.units} units</span>
                            <span>{session.context.course.name}</span>
                            <span>{session.context.cohort.name}</span>
                            <span>{session.context.lecturer.name}</span>
                            <span>{session.context.room.name}</span>
                            <span>{session.context.studyType.name}</span>
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
        <p className="empty-state">No generated draft schedules for this semester yet.</p>
      )}
    </section>
  )

  function setFilter(name: keyof ReviewFilters, value?: number) {
    setFilters((current) => ({
      ...current,
      [name]: value,
    }))
  }
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

const WEEKDAY_OPTIONS = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
]

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
                {WEEKDAY_OPTIONS.map((label, weekday) => (
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
}

type FilterOptions = {
  courses: PlanningEntity[]
  cohorts: PlanningEntity[]
  lecturers: PlanningEntity[]
  rooms: PlanningEntity[]
  studyTypes: PlanningEntity[]
}

function flattenSchedules(schedules: DraftSchedule[]): OverviewSession[] {
  return schedules.flatMap((schedule) =>
    schedule.sessions.map((session) => ({
      ...session,
      draftScheduleId: schedule.draftScheduleId,
      context: schedule.context,
    })),
  )
}

function buildFilterOptions(schedules: DraftSchedule[]): FilterOptions {
  return {
    courses: uniqueEntities(schedules.map((schedule) => schedule.context.course)),
    cohorts: uniqueEntities(schedules.map((schedule) => schedule.context.cohort)),
    lecturers: uniqueEntities(schedules.map((schedule) => schedule.context.lecturer)),
    rooms: uniqueEntities(schedules.map((schedule) => schedule.context.room)),
    studyTypes: uniqueEntities(schedules.map((schedule) => schedule.context.studyType)),
  }
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
