import type { OptimizationGenerationResult } from '../api/conflictAwareGeneration'

type Props = {
  result: OptimizationGenerationResult
  retryDisabled?: boolean
  onRetryFailed: () => void
}

const statusLabels = {
  complete: 'Complete',
  improved_partial: 'Improved partial',
  unchanged: 'Unchanged',
  failed: 'Failed',
  stale: 'Stale',
}

export function BatchResultSummary({ result, retryDisabled = false, onRetryFailed }: Props) {
  const retryCount = result.summary.failed + result.summary.stale
  return (
    <section className="batch-result" aria-labelledby="batch-result-title" aria-live="polite">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Conflict-aware semester optimization</p>
          <h2 id="batch-result-title">Saved optimization result</h2>
        </div>
        {retryCount > 0 && (
          <button type="button" onClick={onRetryFailed} disabled={retryDisabled}>
            Retry failed or stale courses
          </button>
        )}
      </div>
      <p className="batch-counts">
        {result.summary.complete} complete · {result.summary.improvedPartial} improved partial · {result.summary.unchanged} unchanged · {result.summary.failed} failed · {result.summary.stale} stale
      </p>
      <p>{result.summary.scheduledUnits} units scheduled · {result.summary.remainingUnits} remaining · {(result.summary.elapsedMilliseconds / 1000).toFixed(1)} seconds</p>
      <p className="constraint-note">
        {result.summary.optimalForPreparedSnapshot
          ? 'Proven optimal for the prepared snapshot. Stale outcomes are preserved and do not claim that the refreshed semester is globally optimal.'
          : 'No optimality proof was produced because the prepared inputs could not be solved. Refresh stale inputs and try again.'}
      </p>
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status}`} key={outcome.courseId} aria-label={`${outcome.courseName ?? `Course ${outcome.courseId}`}: ${statusLabels[outcome.status]}`}>
            <div>
              <strong>{outcome.courseName ?? `Course ${outcome.courseId}`}</strong>
              <span>{statusLabels[outcome.status]}</span>
            </div>
            <p>{outcome.scheduledUnits} scheduled · {outcome.remainingUnits} remaining</p>
            {outcome.improvement && <p>+{outcome.improvement.addedUnits} units; {outcome.improvement.reducedConflicts} fewer conflicts; {outcome.improvement.reducedLecturerChanges} fewer lecturer changes; {outcome.improvement.reducedRoomChanges} fewer room changes</p>}
            {outcome.reasons.map((reason) => <p key={`${outcome.courseId}-${reason.code}-${reason.holidayDate ?? ''}`}><strong>{reason.code.replaceAll('_', ' ')}</strong>: {reason.message} ({reason.relatedCount})</p>)}
            {outcome.errors.map((error) => <p key={`${outcome.courseId}-${error.code}`}><strong>{error.code.replaceAll('_', ' ')}</strong>: {error.message}</p>)}
          </article>
        ))}
      </div>
    </section>
  )
}
