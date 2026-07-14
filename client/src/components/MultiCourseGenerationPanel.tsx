import type { CourseOption } from '../api/planningOptions'

type Props = {
  courses: CourseOption[]
  selectedCourseIds: number[]
  disabled?: boolean
  onChange: (courseIds: number[]) => void
  onGenerate: () => void
}

export function MultiCourseGenerationPanel({
  courses,
  selectedCourseIds,
  disabled = false,
  onChange,
  onGenerate,
}: Props) {
  const count = selectedCourseIds.length
  const valid = count >= 2 && count <= 50

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
        <h3 id="multi-course-title">Several courses</h3>
        <button type="button" className="secondary-button" onClick={() => onChange([])} disabled={disabled || count === 0}>
          Clear selection
        </button>
      </div>
      <p className="constraint-note">
        Each course uses its own saved generation constraints, or its semester and Study Type defaults.
      </p>
      <div className="course-picker" role="group" aria-label="Courses to generate">
        {courses.map((course) => (
          <label className="course-checkbox" key={course.id}>
            <input
              type="checkbox"
              checked={selectedCourseIds.includes(course.id)}
              onChange={() => toggle(course.id)}
              disabled={disabled || (!selectedCourseIds.includes(course.id) && count >= 50)}
            />
            <span>{course.name}</span>
          </label>
        ))}
      </div>
      <p className={valid ? 'selection-count' : 'selection-count selection-invalid'}>
        {count} selected {valid ? '' : '— select 2 to 50 courses'}
      </p>
      <button type="button" className="generate-button" onClick={onGenerate} disabled={disabled || !valid}>
        {disabled ? 'Generating several courses...' : 'Generate selected courses'}
      </button>
    </section>
  )
}
