import { useState } from 'react'

import type {
  AllowedTeachingWindow,
  DraftSchedule,
  GenerationConstraints,
  GenerationFailure,
  ReviewFilters,
  ViewMode,
} from '../api/draftSchedule'
import {
  filterSessions,
  groupSessionsByWeek,
  sortSessionsChronologically,
} from './scheduleReviewUtils'

type DraftSchedulePanelProps = {
  schedule: DraftSchedule | null
  generationConstraints: GenerationConstraints | null
  errors: GenerationFailure[]
  isLoading: boolean
  onGenerationConstraintsChange: (constraints: GenerationConstraints) => void
  onClearGenerationConstraints: () => void
  onGenerate: () => void
}

export function DraftSchedulePanel({
  schedule,
  generationConstraints,
  errors,
  isLoading,
  onGenerationConstraintsChange,
  onClearGenerationConstraints,
  onGenerate,
}: DraftSchedulePanelProps) {
  const [viewMode, setViewMode] = useState<ViewMode>('list')
  const [filters, setFilters] = useState<ReviewFilters>({})
  const visibleSessions = schedule
    ? sortSessionsChronologically(filterSessions(schedule.sessions, filters))
    : []
  const hasActiveFilters = Object.values(filters).some((value) => value !== undefined)

  return (
    <section className="planner-panel" aria-labelledby="draft-schedule-title">
      <div className="panel-toolbar">
        <div>
          <p className="eyebrow">Draft generation</p>
          <h2 id="draft-schedule-title">Single-course schedule</h2>
        </div>
        <button type="button" onClick={onGenerate} disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate'}
        </button>
      </div>

      {generationConstraints && (
        <GenerationConstraintEditor
          constraints={generationConstraints}
          isLoading={isLoading}
          onChange={onGenerationConstraintsChange}
          onClear={onClearGenerationConstraints}
        />
      )}

      {errors.length > 0 && (
        <div className="alert-list" role="alert">
          {errors.map((error) => (
            <div className="alert-item" key={error.code}>
              <strong>{error.code.replaceAll('_', ' ')}</strong>
              <span>{error.message}</span>
            </div>
          ))}
        </div>
      )}

      {schedule && schedule.sessions.length > 0 ? (
        <>
          <div className="filter-bar" aria-label="Draft session filters">
            <FilterSelect
              label="Course"
              name="courseId"
              value={filters.courseId}
              option={schedule.context.course}
              onChange={setFilter}
            />
            <FilterSelect
              label="Cohort"
              name="cohortId"
              value={filters.cohortId}
              option={schedule.context.cohort}
              onChange={setFilter}
            />
            <FilterSelect
              label="Lecturer"
              name="lecturerId"
              value={filters.lecturerId}
              option={schedule.context.lecturer}
              onChange={setFilter}
            />
            <FilterSelect
              label="Room"
              name="roomId"
              value={filters.roomId}
              option={schedule.context.room}
              onChange={setFilter}
            />
            <FilterSelect
              label="Study type"
              name="studyTypeId"
              value={filters.studyTypeId}
              option={schedule.context.studyType}
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
                <div className="session-row" key={session.id}>
                  <span>{session.date}</span>
                  <span>
                    {session.startTime}-{session.endTime}
                  </span>
                  <span>{session.units}</span>
                  <span>{schedule.context.course.name}</span>
                  <span>{schedule.context.cohort.name}</span>
                  <span>{schedule.context.lecturer.name}</span>
                  <span>{schedule.context.room.name}</span>
                  <span>{schedule.context.studyType.name}</span>
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
                          <article className="week-session" key={session.id}>
                            <strong>
                              {session.startTime}-{session.endTime}
                            </strong>
                            <span>{session.units} units</span>
                            <span>{schedule.context.course.name}</span>
                            <span>{schedule.context.cohort.name}</span>
                            <span>{schedule.context.lecturer.name}</span>
                            <span>{schedule.context.room.name}</span>
                            <span>{schedule.context.studyType.name}</span>
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
      ) : schedule ? (
        <p className="empty-state">Generated draft schedule has no sessions.</p>
      ) : (
        <p className="empty-state">No generated draft schedule yet.</p>
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
  option: { id: number; name: string }
  onChange: (name: keyof ReviewFilters, value?: number) => void
}

function FilterSelect({ label, name, value, option, onChange }: FilterSelectProps) {
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
        <option value={option.id}>{option.name}</option>
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

function GenerationConstraintEditor({
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
