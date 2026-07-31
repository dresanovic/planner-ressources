import type { RefObject } from 'react'
import type { ScheduleDestination } from './ApplicationNavigation'

type Option = {
  id: number
  label: string
  unavailable?: boolean
  statusLabel?: string
}

type Props = {
  destination: ScheduleDestination
  semesterId: number | null
  semesters: Option[]
  revisionId: number | null
  revisions: Option[]
  courseId: number | null
  courses: Option[]
  headingRef?: RefObject<HTMLHeadingElement | null>
  onSemesterChange: (id: number) => void
  onRevisionChange: (id: number) => void
  onCourseChange: (id: number) => void
}

export function ScheduleContextHeader({
  destination,
  semesterId,
  semesters,
  revisionId,
  revisions,
  courseId,
  courses,
  headingRef,
  onSemesterChange,
  onRevisionChange,
  onCourseChange,
}: Props) {
  return (
    <section className="schedule-context-surface" aria-label="Schedule context">
      <div>
        <p className="eyebrow">Schedule workspace</p>
        <h2 ref={headingRef} tabIndex={-1}>{destinationLabel(destination)}</h2>
      </div>
      <div className="schedule-context-controls">
        <ContextSelect label="Semester" value={semesterId} options={semesters} onChange={onSemesterChange} />
        {destination !== 'exams' && <ContextSelect label="Revision" value={revisionId} options={revisions} onChange={onRevisionChange} emptyLabel="No revision available" />}
        {destination !== 'versions' && destination !== 'reviews' && <ContextSelect label="Course" value={courseId} options={courses} onChange={onCourseChange} emptyLabel="No course available" />}
      </div>
    </section>
  )
}

function ContextSelect({
  label,
  value,
  options,
  onChange,
  emptyLabel = 'Unavailable',
}: {
  label: string
  value: number | null
  options: Option[]
  onChange: (id: number) => void
  emptyLabel?: string
}) {
  const valueAvailable = value != null && options.some((item) => item.id === value)
  return (
    <label className="schedule-context-field">
      <span>{label}</span>
      <select value={valueAvailable ? value : ''} disabled={options.length === 0} onChange={(event) => onChange(Number(event.target.value))}>
        {!valueAvailable && <option value="">{emptyLabel}</option>}
        {options.map((option) => (
          <option key={option.id} value={option.id}>
            {option.label}{option.statusLabel ? ` — ${option.statusLabel}` : option.unavailable ? ' — unavailable' : ''}
          </option>
        ))}
      </select>
    </label>
  )
}

function destinationLabel(destination: ScheduleDestination) {
  if (destination === 'versions') return 'Versions'
  if (destination === 'exams') return 'Exams'
  if (destination === 'reviews') return 'Lecturer coordination'
  return 'Calendar'
}
