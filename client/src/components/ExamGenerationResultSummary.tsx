import type { ExamGenerationResult } from '../api/examScheduling'
import { safeReasonText } from '../utils/userProblems'

export function ExamGenerationResultSummary({ result }: { result: ExamGenerationResult }) {
  return (
    <section className="exam-generation-result" aria-labelledby="exam-generation-result-title">
      <h2 id="exam-generation-result-title">Ergebnis der Prüfungserzeugung</h2>
      <p>{result.summary.scheduled} geplant · {result.summary.failed} fehlgeschlagen · {result.summary.stale} veraltet · {result.summary.skippedActive} bereits aktiv · {result.summary.skippedDisabled} deaktiviert</p>
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status === 'scheduled' ? '' : 'failed'}`} key={outcome.courseId}>
            <div><strong>{outcome.courseName}</strong><span>{({ scheduled: 'Geplant', failed: 'Fehlgeschlagen', stale: 'Veraltet', skipped_active: 'Bereits aktiv', skipped_disabled: 'Deaktiviert' } as Record<string, string>)[outcome.status] ?? 'Unbekannt'}</span></div>
            {outcome.reasons.map((reason, index) => <p key={`${reason.code}-${index}`}><strong>Hinweis:</strong> {safeReasonText(reason.code, outcome.courseName)}</p>)}
          </article>
        ))}
      </div>
    </section>
  )
}
