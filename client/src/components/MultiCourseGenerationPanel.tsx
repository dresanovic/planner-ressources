import type { CourseOption } from '../api/planningOptions'
import { label } from '../config/terminology'

type Props = {
  courses: CourseOption[]
  courseDraftStatuses?: Record<number, { hasDraft: boolean; scheduledUnits: number; totalUnits: number }>
  selectedCourseIds: number[]
  disabled?: boolean
  busy?: boolean
  disabledReason?: string
  unavailableDatesInput?: string
  unavailableDateErrors?: string[]
  onChange: (courseIds: number[]) => void
  onUnavailableDatesInputChange?: (value: string) => void
  onGenerate: () => void
}

export function MultiCourseGenerationPanel({
  courses,
  courseDraftStatuses,
  selectedCourseIds,
  disabled = false,
  busy = false,
  disabledReason,
  unavailableDatesInput = '',
  unavailableDateErrors = [],
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
        <h3 id="multi-course-title">Stundenpläne erzeugen</h3>
        <button type="button" className="secondary-button" onClick={() => onChange([])} disabled={disabled || count === 0}>
          Auswahl aufheben
        </button>
      </div>
      <p className="constraint-note">
        Maximiert die geplanten Lehreinheiten der Auswahl, ohne Überschneidungen bei {label('lecturer.plural')}, {label('room.plural')} oder {label('cohort.plural')} zu erzeugen.
      </p>
      <div className="course-picker" role="group" aria-label={`${label('course.plural')} für die Optimierung`}>
        {courses.map((course) => {
          const draftStatus = courseDraftStatuses?.[course.id]
          return (
            <label className="course-checkbox" key={course.id}>
              <input
                type="checkbox"
                checked={selectedCourseIds.includes(course.id)}
                onChange={() => toggle(course.id)}
                disabled={disabled || (!selectedCourseIds.includes(course.id) && count >= 20)}
              />
              <span className="course-checkbox-name">{course.name}</span>
              {draftStatus && (
                <span className={`course-draft-status ${draftStatus.hasDraft ? 'has-draft' : 'no-draft'}`}>
                  {draftStatus.hasDraft
                    ? `Entwurf · ${draftStatus.scheduledUnits}/${draftStatus.totalUnits} Lehreinheiten`
                    : 'Kein Entwurf'}
                </span>
              )}
            </label>
          )
        })}
      </div>
      <p className={valid ? 'selection-count' : 'selection-count selection-invalid'} aria-live="polite">
        {count} ausgewählt {valid ? `— ${count === 1 ? 'Einzelplanung' : 'gemeinsame Planung'}` : `— wählen Sie 1 bis 20 ${label('course.plural')}`}
      </p>
      {onUnavailableDatesInputChange && (
        <label className="constraint-field">
          <span>Zukünftige Abwesenheitstage (optional, durch Kommas getrennt)</span>
          <input
            type="text"
            value={unavailableDatesInput}
            placeholder="26.10.2026, 02.11.2026"
            aria-invalid={unavailableDateErrors.length > 0 || undefined}
            aria-describedby={unavailableDateErrors.length > 0 ? 'unavailable-date-errors' : undefined}
            onChange={(event) => onUnavailableDatesInputChange(event.target.value)}
            disabled={disabled}
          />
        </label>
      )}
      {unavailableDateErrors.length > 0 && <div id="unavailable-date-errors" className="field-error" role="alert">{unavailableDateErrors.map((value) => <p key={value}>„{value}“ ist ungültig. Verwenden Sie TT.MM.JJJJ.</p>)}</div>}
      {disabledReason && <p className="constraint-note" role="status">{disabledReason}</p>}
      <button type="button" className="generate-button" onClick={onGenerate} disabled={disabled || !valid || unavailableDateErrors.length > 0}>
        {busy ? `Ausgewählte ${label('course.plural')} werden optimiert…` : `Ausgewählte ${label('course.plural')} optimieren`}
      </button>
    </section>
  )
}
