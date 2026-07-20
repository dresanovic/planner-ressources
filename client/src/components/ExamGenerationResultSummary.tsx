import type { ExamGenerationResult } from '../api/examScheduling'

export function ExamGenerationResultSummary({ result }: { result: ExamGenerationResult }) {
  return (
    <section className="exam-generation-result" aria-labelledby="exam-generation-result-title">
      <h2 id="exam-generation-result-title">Exam generation result</h2>
      <p>{result.summary.scheduled} scheduled · {result.summary.failed} failed · {result.summary.stale} stale · {result.summary.skippedActive} already active · {result.summary.skippedDisabled} disabled</p>
      <div className="batch-outcomes">
        {result.outcomes.map((outcome) => (
          <article className={`batch-outcome ${outcome.status === 'scheduled' ? '' : 'failed'}`} key={outcome.courseId}>
            <div><strong>{outcome.courseName}</strong><span>{outcome.status.replace('_', ' ')}</span></div>
            {outcome.reasons.map((reason, index) => <p key={`${reason.code}-${index}`}><strong>{reason.code.replaceAll('_', ' ')}:</strong> {reason.message}</p>)}
          </article>
        ))}
      </div>
    </section>
  )
}
