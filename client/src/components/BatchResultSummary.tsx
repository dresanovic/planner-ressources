import type { BatchGenerationResult } from '../api/multiCourseDraftGeneration'

type Props = {
  result: BatchGenerationResult
  retryDisabled?: boolean
  onRetryFailed: () => void
}

export function BatchResultSummary({ result, retryDisabled = false, onRetryFailed }: Props) {
  return (
    <section className="batch-result" aria-labelledby="batch-result-title">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Multi-course generation</p>
          <h2 id="batch-result-title">Generation result</h2>
        </div>
        {result.summary.failed > 0 && (
          <button type="button" onClick={onRetryFailed} disabled={retryDisabled}>
            Retry failed courses
          </button>
        )}
      </div>
      <p className="batch-counts">
        {result.summary.succeeded} succeeded · {result.summary.failed} failed · {result.summary.total} total
      </p>
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status}`} key={outcome.courseId}>
            <div>
              <strong>{outcome.courseName ?? `Course ${outcome.courseId}`}</strong>
              <span>{outcome.status}</span>
            </div>
            {outcome.errors.map((error) => (
              <p key={`${outcome.courseId}-${error.code}`}>
                <strong>{error.code.replaceAll('_', ' ')}</strong>: {error.message}
              </p>
            ))}
          </article>
        ))}
      </div>
    </section>
  )
}
