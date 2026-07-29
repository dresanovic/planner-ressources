import { useCallback, useEffect, useRef, useState } from 'react'

import {
  getPublicLecturerReview,
  LecturerReviewApiError,
  submitPublicLecturerFeedback,
  type LecturerReviewFeedbackInput,
  type PublicLecturerReview,
} from '../api/lecturerReview'
import '../App.css'


const UNAVAILABLE_MESSAGE =
  'This review is unavailable. Contact the planner for a new link.'

type LecturerReviewPageProps = {
  secret: string | null
}

export function LecturerReviewPage({ secret }: LecturerReviewPageProps) {
  const [review, setReview] = useState<PublicLecturerReview | null>(null)
  const [loading, setLoading] = useState(secret !== null)
  const [unavailable, setUnavailable] = useState(secret === null)
  const [temporaryError, setTemporaryError] = useState<string | null>(null)
  const [revisionComment, setRevisionComment] = useState('')
  const [sessionComments, setSessionComments] = useState<Record<string, string>>({})
  const [flagComments, setFlagComments] = useState<Record<string, string>>({})
  const [submissionIds, setSubmissionIds] = useState<Record<string, string>>({})
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const [feedbackStatus, setFeedbackStatus] = useState('')
  const [feedbackError, setFeedbackError] = useState('')
  const loadGeneration = useRef(0)

  const clearProtectedReview = useCallback(() => {
    setReview(null)
    setRevisionComment('')
    setSessionComments({})
    setFlagComments({})
    setSubmissionIds({})
    setPendingKey(null)
    setFeedbackStatus('')
    setFeedbackError('')
  }, [])

  const load = useCallback(async () => {
    const generation = ++loadGeneration.current
    if (secret === null) {
      clearProtectedReview()
      setTemporaryError(null)
      setUnavailable(true)
      setLoading(false)
      return
    }
    setLoading(true)
    setTemporaryError(null)
    try {
      const result = await getPublicLecturerReview(secret)
      if (generation !== loadGeneration.current) return
      setReview(result)
      setUnavailable(false)
    } catch (reason) {
      if (generation !== loadGeneration.current) return
      clearProtectedReview()
      const terminal =
        (reason instanceof LecturerReviewApiError && reason.status === 404) ||
        (typeof reason === 'object' &&
          reason !== null &&
          'code' in reason &&
          reason.code === 'REVIEW_UNAVAILABLE')
      if (terminal) {
        setTemporaryError(null)
        setUnavailable(true)
      } else {
        setUnavailable(false)
        setTemporaryError(
          reason instanceof LecturerReviewApiError && reason.status === 429
            ? 'The review is temporarily unavailable. Please retry shortly.'
            : 'The review could not be reached. Check your connection and retry.',
        )
      }
    } finally {
      if (generation === loadGeneration.current) setLoading(false)
    }
  }, [clearProtectedReview, secret])

  useEffect(() => {
    queueMicrotask(() => void load())
  }, [load])

  async function submitFeedback(
    key: string,
    input: Omit<LecturerReviewFeedbackInput, 'clientSubmissionId'>,
    clearDraft: () => void,
  ) {
    if (secret === null || pendingKey !== null) return
    const clientSubmissionId =
      submissionIds[key] ?? globalThis.crypto.randomUUID()
    if (submissionIds[key] == null) {
      setSubmissionIds((current) => ({ ...current, [key]: clientSubmissionId }))
    }
    setPendingKey(key)
    setFeedbackStatus('Feedback submission pending.')
    setFeedbackError('')
    try {
      await submitPublicLecturerFeedback(secret, {
        ...input,
        clientSubmissionId,
      })
      clearDraft()
      setSubmissionIds((current) => {
        const next = { ...current }
        delete next[key]
        return next
      })
      setFeedbackStatus('Feedback accepted.')
      await load()
    } catch (reason) {
      if (reason instanceof LecturerReviewApiError && reason.status === 409) {
        clearProtectedReview()
        setTemporaryError(null)
        setUnavailable(false)
        await load()
        return
      }
      if (reason instanceof LecturerReviewApiError && reason.status === 404) {
        loadGeneration.current += 1
        clearProtectedReview()
        setTemporaryError(null)
        setUnavailable(true)
        return
      }
      setFeedbackStatus('')
      const retryable =
        reason instanceof Error &&
        'retryable' in reason &&
        reason.retryable === true
      if (!retryable) {
        setSubmissionIds((current) => {
          const next = { ...current }
          delete next[key]
          return next
        })
      }
      setFeedbackError(
        reason instanceof Error
          ? reason.message
          : typeof reason === 'object' &&
              reason !== null &&
              'message' in reason &&
              typeof reason.message === 'string'
            ? reason.message
            : 'Feedback was not accepted. Retry this same submission.',
      )
    } finally {
      setPendingKey(null)
    }
  }

  if (unavailable) {
    return (
      <main className="lecturer-review-public lecturer-review-safe-state">
        <section className="review-card" role="alert">
          <h1>Schedule review unavailable</h1>
          <p>{UNAVAILABLE_MESSAGE}</p>
        </section>
      </main>
    )
  }

  if (temporaryError !== null) {
    return (
      <main className="lecturer-review-public lecturer-review-safe-state">
        <section className="review-card" role="alert">
          <h1>Schedule review temporarily unavailable</h1>
          <p>{temporaryError}</p>
          <button type="button" onClick={() => void load()}>
            Retry review
          </button>
        </section>
      </main>
    )
  }

  if (loading || review === null) {
    return (
      <main className="lecturer-review-public" aria-busy="true">
        <section className="review-card" role="status">
          <h1>Loading schedule review</h1>
          <p>Please wait while the current schedule is checked.</p>
        </section>
      </main>
    )
  }

  return (
    <main className="lecturer-review-public">
      <header className="review-card review-header">
        <p className="eyebrow">Read-only schedule review</p>
        <h1>{review.intendedLecturer}</h1>
        <p>{review.identityDisclaimer}</p>
        <dl className="review-metadata">
          <div>
            <dt>Revision</dt>
            <dd>
              {review.revision.semesterName} · {review.revision.label}
            </dd>
          </div>
          <div>
            <dt>State</dt>
            <dd>{humanize(review.revision.state)}</dd>
          </div>
          <div>
            <dt>Access expires</dt>
            <dd>
              {formatTimestamp(review.accessExpiresAt, review.timeZone)} ({review.timeZone})
            </dd>
          </div>
        </dl>
        <p>
          Your comments are advisory. They do not approve, edit, or block
          publication of this schedule.
        </p>
        <button type="button" onClick={() => void load()}>
          Refresh schedule
        </button>
      </header>

      <section className="review-card" aria-labelledby="assigned-schedule">
        <h2 id="assigned-schedule">Assigned schedule</h2>
        {review.courses.length === 0 ? (
          <p>The assigned schedule is empty. You can still leave a revision comment.</p>
        ) : (
          <div className="review-course-list">
            {review.courses.map((course) => (
              <article className="review-course" key={course.sourceCourseId}>
                <header>
                  <p className="eyebrow">{course.code}</p>
                  <h3>{course.title}</h3>
                </header>
                <ul className="review-session-list">
                  {course.sessions.map((session) => (
                    <li key={session.sessionRef}>
                      <strong>{session.sessionType}</strong>
                      <span>
                        {session.date}, {session.startTime}–{session.endTime}
                      </span>
                      <span>
                        {session.roomName} · {session.cohortName}
                      </span>
                      <p>Session comment and Not possible feedback are advisory.</p>
                      <label htmlFor={`session-comment-${session.sessionKind}-${session.sourceSessionId}`}>
                        Session comment
                      </label>
                      <textarea
                        id={`session-comment-${session.sessionKind}-${session.sourceSessionId}`}
                        value={sessionComments[session.sessionRef] ?? ''}
                        onInput={(event) => {
                          const value = event.currentTarget.value
                          setSessionComments((current) => ({
                            ...current,
                            [session.sessionRef]: value,
                          }))
                        }}
                      />
                      <span>
                        {(sessionComments[session.sessionRef] ?? '').trim().length} / 2000
                      </span>
                      <button
                        type="button"
                        disabled={
                          pendingKey !== null ||
                          !(sessionComments[session.sessionRef] ?? '').trim() ||
                          (sessionComments[session.sessionRef] ?? '').trim()
                            .length > 2000
                        }
                        onClick={() =>
                          void submitFeedback(
                            `session-comment:${session.sessionRef}`,
                            {
                              kind: 'session_comment',
                              sessionRef: session.sessionRef,
                              comment: (
                                sessionComments[session.sessionRef] ?? ''
                              ).trim(),
                            },
                            () =>
                              setSessionComments((current) => ({
                                ...current,
                                [session.sessionRef]: '',
                              })),
                          )
                        }
                      >
                        Submit session comment
                      </button>
                      <label htmlFor={`flag-comment-${session.sessionKind}-${session.sourceSessionId}`}>
                        Not possible explanation (optional recommendation)
                      </label>
                      <textarea
                        id={`flag-comment-${session.sessionKind}-${session.sourceSessionId}`}
                        value={flagComments[session.sessionRef] ?? ''}
                        onInput={(event) => {
                          const value = event.currentTarget.value
                          setFlagComments((current) => ({
                            ...current,
                            [session.sessionRef]: value,
                          }))
                        }}
                      />
                      <span>
                        {(flagComments[session.sessionRef] ?? '').trim().length} / 2000
                      </span>
                      <button
                        type="button"
                        disabled={
                          pendingKey !== null ||
                          (flagComments[session.sessionRef] ?? '').trim()
                            .length > 2000
                        }
                        onClick={() => {
                          const comment = (
                            flagComments[session.sessionRef] ?? ''
                          ).trim()
                          void submitFeedback(
                            `flag:${session.sessionRef}`,
                            {
                              kind: 'impossible_session',
                              sessionRef: session.sessionRef,
                              ...(comment ? { comment } : {}),
                            },
                            () =>
                              setFlagComments((current) => ({
                                ...current,
                                [session.sessionRef]: '',
                              })),
                          )
                        }}
                      >
                        Not possible
                      </button>
                    </li>
                  ))}
                </ul>
              </article>
            ))}
          </div>
        )}
      </section>

      <section className="review-card" aria-labelledby="revision-comment">
        <h2 id="revision-comment">Revision comment</h2>
        <label htmlFor="lecturer-review-revision-comment">Revision comment</label>
        <textarea
          id="lecturer-review-revision-comment"
          value={revisionComment}
          onInput={(event) => setRevisionComment(event.currentTarget.value)}
        />
        <span>{revisionComment.trim().length} / 2000</span>
        <button
          type="button"
          disabled={
            pendingKey !== null ||
            !revisionComment.trim() ||
            revisionComment.trim().length > 2000
          }
          onClick={() =>
            void submitFeedback(
              'revision-comment',
              {
                kind: 'revision_comment',
                comment: revisionComment.trim(),
              },
              () => setRevisionComment(''),
            )
          }
        >
          {submissionIds['revision-comment']
            ? 'Retry revision comment'
            : 'Submit revision comment'}
        </button>
        {pendingKey !== null && <p role="status">Submitting feedback…</p>}
        {feedbackStatus && pendingKey === null && (
          <p role="status">{feedbackStatus}</p>
        )}
        {feedbackError && <p role="alert">{feedbackError}</p>}
        <h3>Feedback history</h3>
        {review.submittedFeedback.length > 0 && (
          <ul className="review-feedback-list">
            {review.submittedFeedback.map((item) => (
              <li key={item.id}>
                <strong>{humanize(item.kind)}</strong>
                {item.comment !== null && <p>{item.comment}</p>}
                <small>
                  {formatTimestamp(item.submittedAt, item.timeZone)} ({item.timeZone})
                </small>
              </li>
            ))}
          </ul>
        )}
      </section>
    </main>
  )
}

function humanize(value: string) {
  const words = value.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function formatTimestamp(value: string, timeZone: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone,
  })
}
