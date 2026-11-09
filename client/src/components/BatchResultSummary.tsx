import type { BlockingReason, OptimizationGenerationResult } from '../api/conflictAwareGeneration'
import { formatCalendarDate } from '../utils/datePresentation'
import { safeReasonText } from '../utils/userProblems'
import { label } from '../config/terminology'
import { OptimizationProofFacts, IntensiveArrangementFacts } from './OptimizationProofFacts'

type Props = {
  result: OptimizationGenerationResult
  retryDisabled?: boolean
  onRetryFailed: () => void
}

const statusLabels = {
  complete: 'Vollständig',
  improved_partial: 'Unvollständig',
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
      case 'INSTITUTION_HOLIDAY':
        return `${courseName}: Unterrichtsfreie Tage wurden als mögliche Lehrtermine ausgeschlossen. Der Hinweis bezeichnet keinen gespeicherten Termin auf einem Feiertag.`
      case 'SELECTED_COURSE_COMPETITION':
        return `${courseName}: Die ausgewählten Lehrveranstaltungen konkurrieren um gemeinsame Zeitfenster oder Ressourcen. Eine andere Verteilung kann zulasten anderer Lehrveranstaltungen gehen.`
      case 'STUDY_TYPE_WINDOW_UNAVAILABLE':
        return `${courseName}: Kein aktives Studienzeitfenster ist lang genug für die minimale Termingröße. Prüfen Sie die Zeitfenster des Studientyps.`
      case 'LECTURER_UNAVAILABLE':
        return `${courseName}: Zulässige Lehrpersonen sind in ansonsten erlaubten Zeitfenstern nicht verfügbar. Prüfen Sie die Verfügbarkeiten und Zuordnungen.`
      case 'ROOM_UNAVAILABLE':
        return `${courseName}: Zulässige Räume sind in ansonsten erlaubten Zeitfenstern nicht verfügbar. Prüfen Sie die Raumverfügbarkeiten.`
      case 'NO_ELIGIBLE_LECTURER':
        return `${courseName}: Keine aktive zulässige Lehrperson ist zugeordnet. Prüfen Sie die Lehrpersonenzuordnung.`
      case 'NO_ELIGIBLE_ROOM':
        return `${courseName}: Kein aktiver zulässiger Raum ist zugeordnet. Prüfen Sie die Raumzuordnung.`
      case 'INSUFFICIENT_ROOM_CAPACITY':
        return `${courseName}: Kein aktiver zulässiger Raum bietet genügend Plätze für die Kohorte. Prüfen Sie Raumkapazität und Zuordnung.`
      case 'UNAVAILABLE_DATE':
        return `${courseName}: Ausgeschlossene Tage schränken die möglichen Lehrtermine ein. Prüfen Sie die eingegebenen Abwesenheitstage.`
      case 'NO_ALLOWED_DATE_OR_WINDOW':
        return `${courseName}: Es wurde kein zulässiger Tag mit passendem Zeitfenster gefunden. Prüfen Sie Planungszeitraum und Studienzeitfenster.`
      case 'COURSE_CONSTRAINT':
        return `${courseName}: Die aktiven Datums-, Zeitfenster- oder Termingrößenvorgaben schränken die Platzierung ein. Prüfen Sie diese Planungsgrenzen.`
      case 'INVALID_PLANNING_INPUT':
        return `${courseName}: Die Planungsdaten sind ungültig oder unvollständig. Prüfen Sie die Eingaben.`
      case 'STALE_PLANNING_INPUT':
        return safeReasonText(reason.code, courseName)
      default:
        return `${courseName}: Für diese Planungseinschränkung liegen keine näheren Angaben vor.`
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
        {result.summary.complete} vollständig · {result.summary.improvedPartial} unvollständig · {result.summary.unchanged} unverändert · {result.summary.failed} fehlgeschlagen · {result.summary.stale} veraltet
      </p>
      <p>{result.summary.scheduledUnits} Lehreinheiten geplant · {result.summary.remainingUnits} offen · {(result.summary.elapsedMilliseconds / 1000).toFixed(1)} Sekunden</p>
      <p className="constraint-note">
        {result.proof && !result.summary.optimalForPreparedSnapshot
          ? 'Gespeichert nach ausdrücklicher Übernahme. Der gültige Stundenplan bleibt ohne vollständigen Optimalitätsnachweis; dies ist kein fehlgeschlagener Speichervorgang.'
          : result.summary.optimalForPreparedSnapshot
          ? 'Für den vorbereiteten Datenstand als optimal nachgewiesen. Der Nachweis gilt ausschließlich für die vorbereitete Auswahl und feste Belegung.'
          : 'Es wurde kein Optimalitätsnachweis erzeugt, weil die vorbereiteten Eingaben nicht gelöst werden konnten. Aktualisieren Sie veraltete Eingaben und versuchen Sie es erneut.'}
      </p>
      {result.proof && <OptimizationProofFacts proof={result.proof}/>}
      {result.intensiveFacts && result.intensiveFacts.totalUnits === result.summary.scheduledUnits
        && (!result.proof || (result.proof.preparedSnapshotToken === result.intensiveFacts.preparedSnapshotToken && result.proof.candidateFingerprint === result.intensiveFacts.candidateFingerprint))
        && <IntensiveArrangementFacts facts={result.intensiveFacts} label="Gespeicherte intensive Planung" />}
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status}`} key={outcome.courseId} aria-label={`${outcome.courseName ?? `${label('course.singular')} ${outcome.courseId}`}: ${statusLabels[outcome.status]}`}>
            <div>
              <strong>{outcome.courseName ?? `${label('course.singular')} ${outcome.courseId}`}</strong>
              <span>{statusLabels[outcome.status]}</span>
            </div>
            <p>{outcome.scheduledUnits} geplant · {outcome.remainingUnits} offen</p>
            {outcome.remainingUnits > 0 && outcome.reasons.length === 0 && <p>Für die verbleibenden Lehreinheiten liegen keine belegten Gründe vor.</p>}
            {outcome.improvement && <p>+{outcome.improvement.addedUnits} Lehreinheiten; {outcome.improvement.reducedConflicts} Konflikte weniger; {outcome.improvement.reducedLecturerChanges} Wechsel der Lehrperson weniger; {outcome.improvement.reducedRoomChanges} Raumwechsel weniger</p>}
            {outcome.reasons.map((reason) => <p key={`${outcome.courseId}-${reason.code}-${reason.holidayDate ?? ''}-${reason.sourceKind ?? ''}-${reason.sourceId ?? ''}`}><strong>Hinweis</strong>: {blockerText(reason, outcome.courseName ?? `Lehrveranstaltung ${outcome.courseId}`)}{reason.holidayDate ? ` ${reason.holidayName ? `Feiertag „${reason.holidayName}“, ` : ''}betroffenes Datum: ${formatCalendarDate(reason.holidayDate)}.` : ''} ({reason.relatedCount} betroffen)</p>)}
            {outcome.errors.map((error) => <p key={`${outcome.courseId}-${error.code}`}><strong>Fehler</strong>: {safeReasonText(error.code, outcome.courseName ?? `Lehrveranstaltung ${outcome.courseId}`)}</p>)}
          </article>
        ))}
      </div>
    </section>
  )
}
