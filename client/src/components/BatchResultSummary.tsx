import type { BlockingReason, OptimizationGenerationResult } from '../api/conflictAwareGeneration'
import { formatCalendarDate } from '../utils/datePresentation'
import { safeReasonText } from '../utils/userProblems'
import { label } from '../config/terminology'

type Props = {
  result: OptimizationGenerationResult
  retryDisabled?: boolean
  onRetryFailed: () => void
}

const statusLabels = {
  complete: 'Vollständig',
  improved_partial: 'Teilweise verbessert',
  unchanged: 'Unverändert',
  failed: 'Fehlgeschlagen',
  stale: 'Veraltet',
}

function blockerText(reason: BlockingReason, courseName: string): string {
  const prefix = (() => {
    switch (reason.code) {
      case 'LECTURER_OCCUPIED':
        return `Lehrpersonenkonflikt: Für ${courseName} ist keine geeignete Lehrperson im betroffenen Zeitraum frei.`
      case 'ROOM_OCCUPIED':
        return `Raumkonflikt: Für ${courseName} ist kein geeigneter Raum im betroffenen Zeitraum frei.`
      case 'COHORT_OCCUPIED':
        return `Kohortenkonflikt: Die Kohorte von ${courseName} hat im betroffenen Zeitraum bereits einen Termin.`
      case 'ACTIVE_EXAM_BOUNDARY':
        return `Prüfungsgrenze: Die Lehrtermine von ${courseName} müssen spätestens mit Beginn der aktiven Prüfung enden.`
      default:
        return safeReasonText(reason.code, courseName)
    }
  })()
  if (reason.sourceKind === 'teaching_session' && reason.sourceId != null) {
    return `${prefix} Blockierender Lehrtermin #${reason.sourceId}.`
  }
  if (reason.sourceKind === 'active_exam' && reason.sourceId != null) {
    return `${prefix} Blockierende aktive Prüfung #${reason.sourceId}.`
  }
  return prefix
}

export function BatchResultSummary({ result, retryDisabled = false, onRetryFailed }: Props) {
  const retryCount = result.summary.failed + result.summary.stale
  return (
    <section className="batch-result" aria-labelledby="batch-result-title" aria-live="polite">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Konfliktfreie Semesteroptimierung</p>
          <h2 id="batch-result-title">Gespeichertes Optimierungsergebnis</h2>
        </div>
        {retryCount > 0 && (
          <button type="button" onClick={onRetryFailed} disabled={retryDisabled}>
            Fehlgeschlagene oder veraltete {label('course.plural')} erneut versuchen
          </button>
        )}
      </div>
      <p className="batch-counts">
        {result.summary.complete} vollständig · {result.summary.improvedPartial} teilweise verbessert · {result.summary.unchanged} unverändert · {result.summary.failed} fehlgeschlagen · {result.summary.stale} veraltet
      </p>
      <p>{result.summary.scheduledUnits} Lehreinheiten geplant · {result.summary.remainingUnits} offen · {(result.summary.elapsedMilliseconds / 1000).toFixed(1)} Sekunden</p>
      <p className="constraint-note">
        {result.summary.optimalForPreparedSnapshot
          ? 'Für den vorbereiteten Datenstand als optimal nachgewiesen. Veraltete Ergebnisse bleiben erhalten und behaupten nicht, dass das aktualisierte Semester global optimal ist.'
          : 'Es wurde kein Optimalitätsnachweis erzeugt, weil die vorbereiteten Eingaben nicht gelöst werden konnten. Aktualisieren Sie veraltete Eingaben und versuchen Sie es erneut.'}
      </p>
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status}`} key={outcome.courseId} aria-label={`${outcome.courseName ?? `${label('course.singular')} ${outcome.courseId}`}: ${statusLabels[outcome.status]}`}>
            <div>
              <strong>{outcome.courseName ?? `${label('course.singular')} ${outcome.courseId}`}</strong>
              <span>{statusLabels[outcome.status]}</span>
            </div>
            <p>{outcome.scheduledUnits} geplant · {outcome.remainingUnits} offen</p>
            {outcome.improvement && <p>+{outcome.improvement.addedUnits} Lehreinheiten; {outcome.improvement.reducedConflicts} Konflikte weniger; {outcome.improvement.reducedLecturerChanges} Wechsel der Lehrperson weniger; {outcome.improvement.reducedRoomChanges} Raumwechsel weniger</p>}
            {outcome.reasons.map((reason) => <p key={`${outcome.courseId}-${reason.code}-${reason.holidayDate ?? ''}-${reason.sourceKind ?? ''}-${reason.sourceId ?? ''}`}><strong>Hinweis</strong>: {blockerText(reason, outcome.courseName ?? `Lehrveranstaltung ${outcome.courseId}`)}{reason.holidayDate ? ` ${reason.holidayName ? `Feiertag „${reason.holidayName}“, ` : ''}betroffenes Datum: ${formatCalendarDate(reason.holidayDate)}.` : ''} ({reason.relatedCount} betroffen)</p>)}
            {outcome.errors.map((error) => <p key={`${outcome.courseId}-${error.code}`}><strong>Fehler</strong>: {safeReasonText(error.code, outcome.courseName ?? `Lehrveranstaltung ${outcome.courseId}`)}</p>)}
          </article>
        ))}
      </div>
    </section>
  )
}
