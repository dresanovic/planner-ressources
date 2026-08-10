import type { UserProblem } from '../utils/userProblems'

type Props = {
  problems: UserProblem[]
  className?: string
}

function idPart(value: string): string {
  return value.replace(/[^A-Za-z0-9_-]+/g, '-')
}

function problemId(problem: UserProblem): string {
  return `${problem.fieldId ?? 'problem'}-problem-${idPart(problem.key)}`
}

// eslint-disable-next-line react-refresh/only-export-components
export function problemDescriptionIds(
  problems: UserProblem[],
  fieldId: string,
): string | undefined {
  const ids = problems
    .filter((problem) => problem.fieldId === fieldId)
    .map(problemId)
  return ids.length > 0 ? ids.join(' ') : undefined
}

function ProblemItems({ problems }: { problems: UserProblem[] }) {
  return (
    <ul className="actionable-problem-list">
      {problems.map((problem) => (
        <li className={`actionable-problem actionable-problem--${problem.tone}`} key={problem.key}>
          <div id={problemId(problem)}>
            <strong>{problem.title}</strong>
            {problem.details.map((detail, index) => <p key={`${problem.key}-detail-${index}`}>{detail}</p>)}
          </div>
          {problem.action?.href ? (
            <a className="secondary-button" href={problem.action.href}>{problem.action.label}</a>
          ) : problem.action?.onClick ? (
            <button className="secondary-button" type="button" onClick={problem.action.onClick}>
              {problem.action.label}
            </button>
          ) : null}
        </li>
      ))}
    </ul>
  )
}

export function ActionableProblemList({ problems, className }: Props) {
  const blocking = problems.filter((problem) => problem.tone === 'blocking')
  const warnings = problems.filter((problem) => problem.tone === 'warning')
  if (problems.length === 0) return null

  return (
    <div className={className ? `actionable-problems ${className}` : 'actionable-problems'}>
      {blocking.length > 0 && (
        <section role="alert" aria-label="Fehler">
          <ProblemItems problems={blocking} />
        </section>
      )}
      {warnings.length > 0 && (
        <section role="status" aria-live="polite" aria-label="Hinweise">
          <ProblemItems problems={warnings} />
        </section>
      )}
    </div>
  )
}
