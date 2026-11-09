import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

import type {
  BlockingReason,
  CoverageFacts,
  OptimizationDecisionRequiredResult,
} from '../api/conflictAwareGeneration'
import { label } from '../config/terminology'
import { OptimizationProofFacts, IntensiveArrangementFacts } from './OptimizationProofFacts'
import { formatCalendarDate } from '../utils/datePresentation'

type Props = {
  preview: OptimizationDecisionRequiredResult
  disabled?: boolean
  onAccept: () => void
  onCancel: () => void
  onRetry?: () => void
}

function remainingReasonText(reason: BlockingReason): string {
  if (reason.code === 'INSTITUTION_HOLIDAY' && reason.holidayDate) {
    return `Unterrichtsfreie Tage wurden als mögliche Lehrtermine ausgeschlossen. ${reason.holidayName ? `Feiertag „${reason.holidayName}“, ` : ''}betroffenes Datum: ${formatCalendarDate(reason.holidayDate)}. Dies beschreibt keinen gespeicherten Termin auf einem Feiertag.`
  }
  return reason.message
}

export function ReplacementConfirmationDialog({
  preview,
  disabled = false,
  onAccept,
  onCancel,
  onRetry,
}: Props) {
  const dialogRef = useRef<HTMLElement>(null)
  const [retryConfirmation,setRetryConfirmation]=useState(false)

  useEffect(()=>{
    if(retryConfirmation) dialogRef.current?.querySelector<HTMLButtonElement>('[data-retry-back]')?.focus()
    else dialogRef.current?.querySelector<HTMLButtonElement>('[data-retry-open]')?.focus()
  },[retryConfirmation])

  useEffect(() => {
    const returnFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null
    dialogRef.current?.focus()
    return () => returnFocus?.focus()
  }, [])

  useEffect(() => {
    if (disabled) dialogRef.current?.focus()
  }, [disabled])

  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !disabled) {
      event.preventDefault()
      if(retryConfirmation) {setRetryConfirmation(false);return}
      onCancel()
      return
    }
    if (event.key !== 'Tab') return
    const controls = [
      ...(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? []),
    ]
    if (controls.length === 0) {
      event.preventDefault()
      dialogRef.current?.focus()
      return
    }
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  return (
    <div className="dialog-backdrop" role="presentation">
      <section
        ref={dialogRef}
        className="replacement-dialog regeneration-comparison-dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="regeneration-comparison-title"
        aria-describedby="regeneration-comparison-description"
        tabIndex={-1}
        onKeyDown={handleKeyDown}
      >
        <button
          type="button"
          className="dialog-close-button"
          aria-label="Vergleich schließen"
          onClick={onCancel}
          disabled={disabled}
        >
          ×
        </button>
        <h2 id="regeneration-comparison-title">Stundenpläne vergleichen</h2>
        <p id="regeneration-comparison-description">
          Für die gesamte Auswahl ist eine gemeinsame Entscheidung erforderlich.
          {preview.hasSavedSessions === false ? ' Keine gespeicherten Lehrtermine in dieser Auswahl. Die Übernahme erstellt die erzeugten Stundenpläne.' : ' Beim Übernehmen werden alle ausgewählten gespeicherten Termine ersetzt, einschließlich plannerseitig erstellter oder bearbeiteter Termine.'}
        </p>
        {preview.proof && <><p role="status"><strong>Noch nicht gespeichert.</strong> Die gesamte Auswahl bleibt bis zur ausdrücklichen Übernahme vorläufig. Auch eine geringere Abdeckung darf übernommen werden.</p><OptimizationProofFacts proof={preview.proof}/></>}
        {preview.proof && preview.proof.candidateFingerprint === preview.candidateFingerprint
          && preview.comparison.current.intensiveFacts?.preparedSnapshotToken === preview.proof.preparedSnapshotToken
          && preview.comparison.current.intensiveFacts.totalUnits === preview.comparison.current.scheduledUnits
          && <IntensiveArrangementFacts facts={preview.comparison.current.intensiveFacts} label="Aktuelle intensive Planung" />}
        {preview.proof && preview.proof.candidateFingerprint === preview.candidateFingerprint
          && preview.comparison.generated.intensiveFacts?.preparedSnapshotToken === preview.proof.preparedSnapshotToken
          && preview.comparison.generated.intensiveFacts.candidateFingerprint === preview.candidateFingerprint
          && preview.comparison.generated.intensiveFacts.totalUnits === preview.comparison.generated.scheduledUnits
          && <IntensiveArrangementFacts facts={preview.comparison.generated.intensiveFacts} label="Erzeugte intensive Planung" />}

        <ComparisonPair
          current={preview.comparison.current}
          generated={preview.comparison.generated}
          heading="Gesamte Auswahl"
        />

        <div className="regeneration-course-list">
          {preview.comparison.courses.map((course) => (
            <section
              key={course.courseId}
              className="regeneration-course-comparison"
              aria-labelledby={`regeneration-course-${course.courseId}`}
            >
              <h3 id={`regeneration-course-${course.courseId}`}>
                {course.courseName ?? `${label('course.singular')} ${course.courseId}`}
              </h3>
              <ComparisonPair current={course.current} generated={course.generated} />
              {course.resolvedCurrentWarnings.length > 0 && (
                <div className="comparison-evidence current-evidence">
                  <h4>Im aktuellen Stundenplan erkannte Regelverletzungen</h4>
                  <ul>
                    {course.resolvedCurrentWarnings.map((warning) => (
                      <li key={warning.code}>
                        {warningLabel(warning.code)} ({warning.count})
                      </li>
                    ))}
                  </ul>
                </div>
              )}
              {course.remainingReasons.length > 0 && (
                <div className="comparison-evidence generated-evidence">
                  <h4>Gründe für verbleibende Lehreinheiten</h4>
                  <ul>
                    {course.remainingReasons.map((reason, index) => (
                      <li key={`${reason.code}-${index}`}>{remainingReasonText(reason)}</li>
                    ))}
                  </ul>
                </div>
              )}
              {course.generated.remainingUnits > 0 && course.remainingReasons.length === 0 && <p>Für die verbleibenden Lehreinheiten liegen keine belegten Gründe vor. Daraus folgt nicht, dass weitere Termine unmöglich sind.</p>}
              {preview.proof && !preview.proof.coverageProven && course.generated.remainingUnits > 0 && <p>Diese Angaben sind beobachtete Einschränkungen. Ein Nachweis, dass weitere Einheiten unmöglich sind, fehlt.</p>}
            </section>
          ))}
        </div>

        {retryConfirmation ? <section className="retry-confirmation" aria-label="Neuen Versuch bestätigen">
          <h3>Aktuellen Vorschlag verwerfen?</h3>
          <p>Der neue Versuch startet mit den aktuellen gespeicherten Eingaben und setzt diese Suche nicht fort. Er kann schlechter ausfallen oder kein Ergebnis liefern. Das aktuelle konfigurierte Zeitbudget wird vor dem neuen Start angezeigt. Für mehr Zeit kann die Installationsbetreuung die Konfiguration ändern; alternativ wählen Sie weniger Lehrveranstaltungen.</p>
          <div className="dialog-actions">
            <button type="button" data-retry-back onClick={()=>setRetryConfirmation(false)} disabled={disabled}>Zurück zum Vergleich</button>
            <button type="button" onClick={onRetry} disabled={disabled}>Verwerfen und neuen Versuch vorbereiten</button>
          </div>
        </section> : <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onCancel} disabled={disabled}>
            Abbrechen
          </button>
          <button type="button" onClick={onAccept} disabled={disabled}>
            {disabled ? 'Wird übernommen…' : 'Neu erzeugten Stundenplan übernehmen'}
          </button>
          {onRetry && <button type="button" data-retry-open className="secondary-button" disabled={disabled} onClick={()=>setRetryConfirmation(true)}>Erneut optimieren</button>}
        </div>}
      </section>
    </div>
  )
}

function ComparisonPair({
  current,
  generated,
  heading,
}: {
  current: CoverageFacts
  generated: CoverageFacts
  heading?: string
}) {
  return (
    <section className="comparison-pair" aria-label={heading}>
      {heading && <h3>{heading}</h3>}
      <div className="comparison-columns">
        <CoverageBlock heading="Aktueller Stundenplan" facts={current} />
        <CoverageBlock heading="Neu erzeugter Stundenplan" facts={generated} />
      </div>
    </section>
  )
}

function CoverageBlock({ heading, facts }: { heading: string; facts: CoverageFacts }) {
  return (
    <section className="comparison-side" aria-label={heading}>
      <h4>{heading}</h4>
      <dl>
        <div><dt>Erforderlich</dt><dd>{facts.requiredUnits} LE</dd></div>
        <div><dt>Geplant</dt><dd>{facts.scheduledUnits} LE</dd></div>
        <div><dt>Verbleibend</dt><dd>{facts.remainingUnits} LE</dd></div>
        <div><dt>Status</dt><dd>{facts.status === 'complete' ? 'Vollständig' : 'Teilplan'}</dd></div>
      </dl>
    </section>
  )
}

function warningLabel(code: string) {
  const labels: Record<string, string> = {
    GENERATION_CONSTRAINT_VIOLATION: 'Termin liegt außerhalb der aktiven Datums- oder Zeitgrenzen',
    STUDY_TYPE_WINDOW_VIOLATION: 'Termin liegt außerhalb des aktiven Studienzeitfensters',
    LECTURER_OVERLAP: 'Lehrendenüberschneidung',
    ROOM_OVERLAP: 'Raumüberschneidung',
    COHORT_OVERLAP: 'Kohortenüberschneidung',
    ROOM_CAPACITY: 'Raumkapazität unterschritten',
    LECTURER_UNAVAILABLE: 'Lehrperson nicht verfügbar',
    ROOM_UNAVAILABLE: 'Raum nicht verfügbar',
    LECTURER_INELIGIBLE: 'Lehrperson nicht zulässig',
    ROOM_INELIGIBLE: 'Raum nicht zulässig',
    INSTITUTION_HOLIDAY: 'Termin liegt an einem Hochschulfeiertag',
  }
  return labels[code] ?? `Aktuelle Regelverletzung: ${code}`
}
