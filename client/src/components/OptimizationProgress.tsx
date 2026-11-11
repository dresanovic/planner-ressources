import { useOptimizationSession } from '../hooks/optimizationSession'
import { teachingAlgorithmLabel } from '../api/conflictAwareGeneration'

export function OptimizationProgress({ onOpen }: { onOpen: () => void }) {
  const { operation } = useOptimizationSession()
  const { status, selection, busy, unknown, action } = operation
  if (!status && !busy && !unknown) return null
  const scope = status ?? selection
  const message = unknown ? 'Optimierungsstatus unbestätigt. Verbindung wird geprüft.'
    : action === 'cancelling' ? 'Abbruch angefordert. Bestätigung wird abgewartet.'
    : action === 'saving' || status?.phase === 'saving' ? 'Optimierung wird gespeichert.'
    : status?.phase === 'awaiting_decision' ? 'Optimierung: Ergebnis zur Übernahme bereit.'
    : status?.phase === 'saved' ? 'Optimierung gespeichert.'
    : status && ['cancelled', 'failed', 'stale', 'interrupted', 'timeout_no_candidate'].includes(status.phase) ? 'Optimierung beendet. Ergebnis prüfen.'
    : 'Optimierung läuft. Sie können die Ansicht wechseln.'
  return <section className="optimization-progress" aria-label="Aktuelle Optimierung">
    <div>
      <p role="status" aria-live="polite">{message}</p>
      {scope && <p>Semester #{scope.semesterId} · Revision #{scope.scheduleRevisionId} · {scope.selectedCourseIds.length} Kurse{status ? ` · ${teachingAlgorithmLabel(status.algorithm)} · ${Math.floor(status.elapsedMilliseconds / 1000)} Sekunden` : ''}</p>}
    </div>
    <div className="optimization-progress-actions">
      <button type="button" className="secondary-button" onClick={onOpen}>Zum Optimierungslauf</button>
      {(busy || unknown || status?.canAccept) && <button type="button" className="secondary-button" disabled={action === 'cancelling'} onClick={() => void operation.cancel()}>Optimierung abbrechen</button>}
    </div>
  </section>
}
