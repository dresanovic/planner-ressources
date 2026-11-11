import type { CourseOption } from '../api/planningOptions'
import { teachingAlgorithmLabel, type TeachingAlgorithm } from '../api/conflictAwareGeneration'
import { label } from '../config/terminology'
import { safeReasonText } from '../utils/userProblems'
import { useLayoutEffect, useRef } from 'react'

type Props = {
  algorithm?: TeachingAlgorithm
  courses: CourseOption[]
  cohorts?: { id: number; name: string }[]
  cohortId?: number | null
  onCohortChange?: (id: number | null) => void
  semesterName?: string
  freshness?: 'loading' | 'ready' | 'error'
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
  algorithm,
  courses,
  cohorts = [],
  cohortId = null,
  onCohortChange,
  semesterName = 'Aktuelles Semester',
  freshness = 'ready',
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
  const valid = count >= 1 && count <= 20 && new Set(selectedCourseIds).size === count
  const visibleCourses = courses.filter((course) => cohortId == null || course.cohort?.id === cohortId)
  const hiddenCount = selectedCourseIds.filter((id) => !visibleCourses.some((course) => course.id === id)).length
  const chosenCohort = cohorts.find((cohort) => cohort.id === cohortId)
  const filterRef = useRef<HTMLSelectElement>(null)
  const focusedResult = useRef<HTMLElement | null>(null)
  useLayoutEffect(() => {
    if (focusedResult.current && !focusedResult.current.isConnected && document.activeElement === document.body) {
      filterRef.current?.focus()
      focusedResult.current = null
    }
  })

  function toggle(courseId: number) {
    onChange(
      selectedCourseIds.includes(courseId)
        ? selectedCourseIds.filter((id) => id !== courseId)
        : [...selectedCourseIds, courseId],
    )
  }

  return (
    <section className="multi-course-panel" aria-labelledby="multi-course-title" onFocusCapture={(event) => { focusedResult.current = event.target.closest('.course-picker') ? event.target as HTMLElement : null }}>
      <div className="section-heading">
        <h3 id="multi-course-title">Stundenpläne erzeugen</h3>
        <button type="button" className="secondary-button" onClick={() => onChange([])} disabled={disabled || count === 0}>
          Auswahl aufheben
        </button>
      </div>
      {algorithm && <p role="status" aria-live="polite">Algorithmus: {teachingAlgorithmLabel(algorithm)}</p>}
      <p className="constraint-note">
        Maximiert die geplanten Lehreinheiten der Auswahl, ohne Überschneidungen bei {label('lecturer.plural')}, {label('room.plural')} oder {label('cohort.plural')} zu erzeugen.
      </p>
      {onCohortChange && <div className="course-list-filters">
        <label>Kohorte filtern<select ref={filterRef} aria-label="Kohorte filtern" value={cohortId ?? ''} onChange={(event) => onCohortChange(event.target.value === '' ? null : Number(event.target.value))}>
          <option value="">Alle Kohorten</option>
          {cohortId != null && !chosenCohort && <option value={cohortId}>Kohorte #{cohortId} — nicht verfügbar</option>}
          {cohorts.map((cohort) => <option key={cohort.id} value={cohort.id}>{cohort.name} · #{cohort.id}</option>)}
        </select></label>
        <button type="button" className="secondary-button" onClick={() => onCohortChange(null)}>Kohortenfilter zurücksetzen</button>
      </div>}
      <p role="status">{semesterName} · {cohortId == null ? 'Alle Kohorten' : chosenCohort?.name ?? `Kohorte #${cohortId} — nicht verfügbar`} · {freshness === 'loading' ? 'Planungsoptionen werden geladen…' : freshness === 'error' ? 'Planungsoptionen konnten nicht aktualisiert werden. Laden Sie die Seite erneut. Die Auswahl bleibt erhalten.' : `${visibleCourses.length} Treffer`}</p>
      {freshness === 'ready' && (courses.length === 0 ? <p>Keine Lehrveranstaltungen in diesem Semester.</p> : visibleCourses.length === 0 && <p>Keine Treffer. Setzen Sie den Kohortenfilter zurück.</p>)}
      <div className="course-picker" role="group" aria-label={`${label('course.plural')} für die Optimierung`}>
        {visibleCourses.map((course) => {
          const draftStatus = courseDraftStatuses?.[course.id]
          return (
            <label className="course-checkbox" key={course.id}>
              <input
                type="checkbox"
                checked={selectedCourseIds.includes(course.id)}
                onChange={() => toggle(course.id)}
                disabled={disabled || (!selectedCourseIds.includes(course.id) && (count >= 20 || course.availability?.available === false))}
              />
              <span className="course-checkbox-name">{course.name} · {course.cohort?.name ?? 'Keine Kohorte'} · #{course.id}{course.availability?.available === false && <span> — Nicht verfügbar: {course.availability.reasons.map((reason) => safeReasonText(reason, course.name)).join(' ')}</span>}</span>
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
      <p aria-live="polite">{hiddenCount} durch den Kohortenfilter verborgen{count >= 20 && ' · Maximal 20 Lehrveranstaltungen; heben Sie eine Auswahl auf, um weitere hinzuzufügen.'}</p>
      {count > 0 && <details className="course-selection-review"><summary>Gesamte Auswahl prüfen ({count})</summary><ul>{selectedCourseIds.map((id, index) => {
        const course = courses.find((item) => item.id === id)
        return <li key={`${id}-${index}`}>{course ? `${course.name} · ${course.cohort?.name ?? 'Keine Kohorte'} · #${id}${course.availability?.available === false ? ' — nicht verfügbar' : ''}` : `Lehrveranstaltung #${id} — nicht verfügbar`}</li>
      })}</ul></details>}
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
      <button type="button" className="generate-button" onClick={onGenerate} disabled={disabled || freshness !== 'ready' || !valid || unavailableDateErrors.length > 0}>
        {busy ? `Ausgewählte ${label('course.plural')} werden optimiert…` : `Ausgewählte ${label('course.plural')} optimieren`}
      </button>
    </section>
  )
}
