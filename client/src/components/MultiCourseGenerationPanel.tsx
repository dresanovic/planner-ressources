import type { CourseOption } from '../api/planningOptions'

type Props = {
  courses: CourseOption[]
  selectedCourseIds: number[]
  disabled?: boolean
  unavailableDatesInput?: string
  onChange: (courseIds: number[]) => void
  onUnavailableDatesInputChange?: (value: string) => void
  onGenerate: () => void
}

export function MultiCourseGenerationPanel({
  courses,
  selectedCourseIds,
  disabled = false,
  unavailableDatesInput = '',
  onChange,
  onUnavailableDatesInputChange,
  onGenerate,
}: Props) {
  const count = selectedCourseIds.length
  const valid = count >= 1 && count <= 20

  function toggle(courseId: number) {
    onChange(
      selectedCourseIds.includes(courseId)
        ? selectedCourseIds.filter((id) => id !== courseId)
        : [...selectedCourseIds, courseId],
    )
  }

  return (
    <section className="multi-course-panel" aria-labelledby="multi-course-title">
      <div className="section-heading">
        <h3 id="multi-course-title">Conflict-aware semester optimization</h3>
        <button type="button" className="secondary-button" onClick={() => onChange([])} disabled={disabled || count === 0}>
          Clear selection
        </button>
      </div>
      <p className="constraint-note">
        Maximize scheduled units across the selection without creating lecturer, room, or cohort overlaps.
      </p>
      <div className="course-picker" role="group" aria-label="Courses to optimize">
        {courses.map((course) => (
          <label className="course-checkbox" key={course.id}>
            <input
              type="checkbox"
              checked={selectedCourseIds.includes(course.id)}
              onChange={() => toggle(course.id)}
              disabled={disabled || (!selectedCourseIds.includes(course.id) && count >= 20)}
            />
            <span>{course.name}</span>
          </label>
        ))}
      </div>
      <p className={valid ? 'selection-count' : 'selection-count selection-invalid'}>
        {count} selected {valid ? '' : '— select 1 to 20 courses'}
      </p>
      {onUnavailableDatesInputChange && (
        <label className="constraint-field">
          <span>Future unavailable dates (optional, comma-separated)</span>
          <input
            type="text"
            value={unavailableDatesInput}
            placeholder="2026-10-26, 2026-11-02"
            onChange={(event) => onUnavailableDatesInputChange(event.target.value)}
            disabled={disabled}
          />
        </label>
      )}
      <button type="button" className="generate-button" onClick={onGenerate} disabled={disabled || !valid}>
        {disabled ? 'Optimizing selected courses...' : 'Optimize selected courses'}
      </button>
    </section>
  )
}
