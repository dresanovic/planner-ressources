import { useCallback, useEffect, useMemo, useRef, useState } from 'react'

import {
  getPublicLecturerReview,
  LecturerReviewApiError,
  submitPublicLecturerFeedback,
  type LecturerReviewFeedbackInput,
  type PublicLecturerReview,
} from '../api/lecturerReview'
import { CalendarPlanningWorkspace } from '../components/CalendarPlanningWorkspace'
import { DiscardChangesDialog } from '../components/DiscardChangesDialog'
import { ScheduleOccurrenceList } from '../components/ScheduleOccurrenceList'
import { SessionPane } from '../components/SessionPane'
import { adaptLecturerReviewToWorkspace } from '../components/calendarWorkspaceUtils'
import '../App.css'


const UNAVAILABLE_MESSAGE =
  'This review is unavailable. Contact the planner for a new link.'

type LecturerReviewPageProps = {
  secret: string | null
}

type PendingSelection = {
  next: string | null
  restoreFocusTo: HTMLElement | null
  commitFilter?: () => void
}

export function LecturerReviewPage({ secret }: LecturerReviewPageProps) {
  const [review, setReview] = useState<PublicLecturerReview | null>(null)
  const [loading, setLoading] = useState(secret !== null)
  const [unavailable, setUnavailable] = useState(secret === null)
  const [temporaryError, setTemporaryError] = useState<string | null>(null)
  const [selectedRef, setSelectedRef] = useState<string | null>(null)
  const [pendingSelection, setPendingSelection] =
    useState<PendingSelection | null>(null)
  const [revisionComment, setRevisionComment] = useState('')
  const [sessionComments, setSessionComments] = useState<Record<string, string>>({})
  const [flagComments, setFlagComments] = useState<Record<string, string>>({})
  const [submissionIds, setSubmissionIds] = useState<Record<string, string>>({})
  const [pendingKey, setPendingKey] = useState<string | null>(null)
  const [feedbackStatus, setFeedbackStatus] = useState('')
  const [feedbackError, setFeedbackError] = useState('')
  const loadGeneration = useRef(0)
  const selectedRefValue = useRef<string | null>(null)

  useEffect(() => {
    selectedRefValue.current = selectedRef
  }, [selectedRef])

  const focusWorkspaceResults = useCallback(() => {
    const focus = () =>
      document
        .querySelector<HTMLElement>('[data-workspace-results-heading]')
        ?.focus()
    focus()
    window.setTimeout(focus, 0)
  }, [])

  const clearProtectedReview = useCallback(() => {
    setReview(null)
    setSelectedRef(null)
    setPendingSelection(null)
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
      const validSessionRefs = new Set(
        result.courses.flatMap((course) =>
          course.sessions.map((session) => session.sessionRef),
        ),
      )
      const removedSelected =
        selectedRefValue.current !== null &&
        !validSessionRefs.has(selectedRefValue.current)
      setReview(result)
      setSelectedRef((current) =>
        current !== null && validSessionRefs.has(current) ? current : null,
      )
      setSessionComments((current) =>
        retainSessionEntries(current, validSessionRefs),
      )
      setFlagComments((current) =>
        retainSessionEntries(current, validSessionRefs),
      )
      setSubmissionIds((current) =>
        Object.fromEntries(
          Object.entries(current).filter(
            ([key]) =>
              key === 'revision-comment' ||
              [...validSessionRefs].some((ref) => key.endsWith(`:${ref}`)),
          ),
        ),
      )
      setUnavailable(false)
      if (removedSelected) {
        setFeedbackStatus('')
        setFeedbackError(
          'The selected assignment is no longer in this review. Its unsent feedback was discarded.',
        )
        focusWorkspaceResults()
      }
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
  }, [clearProtectedReview, focusWorkspaceResults, secret])

  useEffect(() => {
    queueMicrotask(() => void load())
  }, [load])

  const workspace = useMemo(
    () => (review === null ? null : adaptLecturerReviewToWorkspace(review)),
    [review],
  )
  const publicSessions = useMemo(
    () =>
      new Map(
        (review?.courses ?? []).flatMap((course) =>
          course.sessions.map((session) => [session.sessionRef, session] as const),
        ),
      ),
    [review],
  )

  function hasSessionDraft(reference: string) {
    return Boolean(
      sessionComments[reference]?.trim() || flagComments[reference]?.trim(),
    )
  }

  function requestSelection(next: string | null) {
    if (
      selectedRef !== null &&
      next !== selectedRef &&
      hasSessionDraft(selectedRef)
    ) {
      setPendingSelection({
        next,
        restoreFocusTo:
          document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null,
      })
      return
    }
    setSelectedRef(next)
  }

  function requestTargetHidingFilter(commitFilter: () => void) {
    if (selectedRef !== null && hasSessionDraft(selectedRef)) {
      setPendingSelection({
        next: null,
        commitFilter,
        restoreFocusTo:
          document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null,
      })
      return
    }
    commitFilter()
    setSelectedRef(null)
  }

  function discardAndContinue() {
    const pending = pendingSelection
    if (selectedRef !== null) {
      setSessionComments((current) => ({ ...current, [selectedRef]: '' }))
      setFlagComments((current) => ({ ...current, [selectedRef]: '' }))
    }
    pending?.commitFilter?.()
    setSelectedRef(pending?.next ?? null)
    setPendingSelection(null)
  }

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
      const result = await submitPublicLecturerFeedback(secret, {
        ...input,
        clientSubmissionId,
      })
      clearDraft()
      setSubmissionIds((current) => {
        const next = { ...current }
        delete next[key]
        return next
      })
      setReview((current) =>
        current === null ||
        current.submittedFeedback.some((item) => item.id === result.item.id)
          ? current
          : {
              ...current,
              submittedFeedback: [...current.submittedFeedback, result.item],
            },
      )
      setFeedbackStatus(
        result.outcome === 'already_accepted'
          ? 'Feedback was already accepted.'
          : 'Feedback accepted.',
      )
    } catch (reason) {
      if (reason instanceof LecturerReviewApiError && reason.status === 409) {
        const staleSessionRef = input.sessionRef
        if (staleSessionRef !== undefined) {
          setSelectedRef((current) =>
            current === staleSessionRef ? null : current,
          )
          setSessionComments((current) => {
            const next = { ...current }
            delete next[staleSessionRef]
            return next
          })
          setFlagComments((current) => {
            const next = { ...current }
            delete next[staleSessionRef]
            return next
          })
          setSubmissionIds((current) =>
            Object.fromEntries(
              Object.entries(current).filter(
                ([submissionKey]) =>
                  !submissionKey.endsWith(`:${staleSessionRef}`),
              ),
            ),
          )
        } else {
          setSubmissionIds((current) => {
            const next = { ...current }
            delete next[key]
            return next
          })
        }
        setFeedbackStatus('')
        setFeedbackError(
          'The assignment changed. Reload the browser page or reopen the link before submitting feedback.',
        )
        focusWorkspaceResults()
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
        reason instanceof LecturerReviewApiError && reason.retryable
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

  if (loading || review === null || workspace === null) {
    return (
      <main className="lecturer-review-public" aria-busy="true">
        <section className="review-card" role="status">
          <h1>Loading schedule review</h1>
          <p>Please wait while the current schedule is checked.</p>
        </section>
      </main>
    )
  }

  const selectedSession =
    selectedRef === null ? undefined : publicSessions.get(selectedRef)
  const validationMessages =
    selectedSession?.validationFindingRefs
      .map((reference) =>
        review.validationFindings.find(
          (finding) => finding.findingRef === reference,
        )?.message,
      )
      .filter((message): message is string => message !== undefined) ?? []

  return (
    <main className="lecturer-review-public restricted-calendar-workspace">
      <header className="review-card review-header">
        <p className="eyebrow">Read-only schedule review</p>
        <h1>Review your teaching and exam assignments</h1>
        <p>{review.identityDisclaimer}</p>
        <p>
          Your comments are advisory. They do not approve, edit, or block
          publication of this schedule.
        </p>
        <dl className="review-metadata">
          <div>
            <dt>Revision</dt>
            <dd>{review.revision.semesterName} · {review.revision.label}</dd>
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
      </header>

      <CalendarPlanningWorkspace
        workspace={workspace}
        loading={false}
        onRetry={() => undefined}
        accessProfile="lecturer-review"
        fixedContext={(
          <div className="lecturer-fixed-context" aria-label="Lecturer context">
            <strong>Lecturer</strong>
            <span>{review.intendedLecturer}</span>
            <small>Fixed by this review link</small>
          </div>
        )}
        intendedContext={`${review.revision.semesterName} · ${review.revision.label}`}
        selectedOccurrenceRef={selectedRef}
        onSelectedOccurrenceChange={requestSelection}
        onRequestTargetHidingFilter={requestTargetHidingFilter}
        listContent={(context) => {
          const teachingIds = new Set(context?.teachingSessionIds ?? [])
          const examIds = new Set(context?.examIds ?? [])
          const occurrences =
            context === null
              ? workspace.occurrences
              : workspace.occurrences.filter((occurrence) => {
                  const id = Number(occurrence.occurrenceRef.split(':')[1])
                  return occurrence.kind === 'teaching'
                    ? teachingIds.has(id)
                    : examIds.has(id)
                })
          return (
            <ScheduleOccurrenceList
              workspace={workspace}
              occurrences={occurrences}
              selectedOccurrenceRef={selectedRef}
              onSelectOccurrence={requestSelection}
              emptyMessage={
                workspace.occurrences.length === 0
                  ? 'There are currently no teaching or exam assignments for this lecturer in this revision.'
                  : 'No sessions match the active filters.'
              }
            />
          )
        }}
        renderSessionPane={(occurrence, requestClose) => {
          const session = publicSessions.get(occurrence.occurrenceRef)
          return (
            <SessionPane
              occurrence={occurrence}
              workspace={workspace}
              mode="detail"
              busy={pendingKey !== null}
              error={feedbackError}
              status={feedbackStatus}
              decisionOpen={pendingSelection !== null}
              onRequestClose={() => {
                requestSelection(null)
                if (!hasSessionDraft(occurrence.occurrenceRef)) requestClose()
              }}
              restrictedReview={{
                lecturerName: review.intendedLecturer,
                revisionLabel: review.revision.label,
                lifecycleState: review.revision.state,
                roomName: session?.roomName ?? 'Unavailable',
                validationAvailability: review.validationAvailability,
                validationMessages,
                feedbackActions: (
                  <SessionFeedbackActions
                    occurrenceRef={occurrence.occurrenceRef}
                    sessionComment={
                      sessionComments[occurrence.occurrenceRef] ?? ''
                    }
                    flagComment={flagComments[occurrence.occurrenceRef] ?? ''}
                    pending={pendingKey !== null}
                    onSessionCommentChange={(value) =>
                      setSessionComments((current) => ({
                        ...current,
                        [occurrence.occurrenceRef]: value,
                      }))
                    }
                    onFlagCommentChange={(value) =>
                      setFlagComments((current) => ({
                        ...current,
                        [occurrence.occurrenceRef]: value,
                      }))
                    }
                    onSubmitComment={() => {
                      const comment =
                        sessionComments[occurrence.occurrenceRef]?.trim() ?? ''
                      void submitFeedback(
                        `session-comment:${occurrence.occurrenceRef}`,
                        {
                          kind: 'session_comment',
                          sessionRef: occurrence.occurrenceRef,
                          comment,
                        },
                        () =>
                          setSessionComments((current) => ({
                            ...current,
                            [occurrence.occurrenceRef]: '',
                          })),
                      )
                    }}
                    onSubmitFlag={() => {
                      const comment =
                        flagComments[occurrence.occurrenceRef]?.trim() ?? ''
                      void submitFeedback(
                        `flag:${occurrence.occurrenceRef}`,
                        {
                          kind: 'impossible_session',
                          sessionRef: occurrence.occurrenceRef,
                          ...(comment ? { comment } : {}),
                        },
                        () =>
                          setFlagComments((current) => ({
                            ...current,
                            [occurrence.occurrenceRef]: '',
                          })),
                      )
                    }}
                  />
                ),
              }}
            />
          )
        }}
      />

      <section className="review-card revision-feedback" aria-labelledby="revision-comment">
        <h2 id="revision-comment">Comment on the revision</h2>
        <label htmlFor="lecturer-review-revision-comment">Revision comment</label>
        <textarea
          id="lecturer-review-revision-comment"
          maxLength={2000}
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
          Submit revision comment
        </button>
        <h3>Feedback sent through this link</h3>
        {review.submittedFeedback.length === 0 ? (
          <p>No feedback has been sent through this link yet.</p>
        ) : (
          <ul className="review-feedback-list">
            {review.submittedFeedback.map((item) => (
              <li key={item.id}>
                <strong>{humanize(item.kind)}</strong>
                {item.sessionRef !== null && (
                  <p>{publicSessionLabel(review, item.sessionRef)}</p>
                )}
                {item.comment !== null && <p>{item.comment}</p>}
                <small>
                  {formatTimestamp(item.submittedAt, item.timeZone)} ({item.timeZone})
                </small>
              </li>
            ))}
          </ul>
        )}
      </section>

      <p className="sr-only" role="status" aria-live="polite">
        {feedbackStatus}
      </p>
      {feedbackError && selectedRef === null && (
        <p className="review-card" role="alert">{feedbackError}</p>
      )}
      {pendingSelection !== null && (
        <DiscardChangesDialog
          destinationLabel="the selected schedule context"
          title="Discard unsent feedback?"
          description="Your feedback has not been sent. Discard it to continue to the selected schedule context."
          keepLabel="Keep writing"
          discardLabel="Discard feedback"
          restoreFocusTo={pendingSelection.restoreFocusTo}
          onKeepEditing={() => setPendingSelection(null)}
          onDiscard={discardAndContinue}
        />
      )}
    </main>
  )
}

function retainSessionEntries(
  entries: Record<string, string>,
  validSessionRefs: ReadonlySet<string>,
) {
  return Object.fromEntries(
    Object.entries(entries).filter(([reference]) =>
      validSessionRefs.has(reference),
    ),
  )
}

function SessionFeedbackActions({
  occurrenceRef,
  sessionComment,
  flagComment,
  pending,
  onSessionCommentChange,
  onFlagCommentChange,
  onSubmitComment,
  onSubmitFlag,
}: {
  occurrenceRef: string
  sessionComment: string
  flagComment: string
  pending: boolean
  onSessionCommentChange: (value: string) => void
  onFlagCommentChange: (value: string) => void
  onSubmitComment: () => void
  onSubmitFlag: () => void
}) {
  const id = occurrenceRef.replace(':', '-')
  return (
    <>
      <label htmlFor={`session-comment-${id}`}>Session comment</label>
      <textarea
        id={`session-comment-${id}`}
        maxLength={2000}
        value={sessionComment}
        onInput={(event) => onSessionCommentChange(event.currentTarget.value)}
      />
      <span>{sessionComment.trim().length} / 2000</span>
      <button
        type="button"
        disabled={pending || !sessionComment.trim()}
        onClick={onSubmitComment}
      >
        Submit session comment
      </button>
      <label htmlFor={`flag-comment-${id}`}>
        Not possible explanation (optional)
      </label>
      <textarea
        id={`flag-comment-${id}`}
        maxLength={2000}
        value={flagComment}
        onInput={(event) => onFlagCommentChange(event.currentTarget.value)}
      />
      <span>{flagComment.trim().length} / 2000</span>
      <button type="button" disabled={pending} onClick={onSubmitFlag}>
        Flag as not possible
      </button>
    </>
  )
}

function humanize(value: string) {
  const words = value.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function publicSessionLabel(review: PublicLecturerReview, sessionRef: string) {
  for (const course of review.courses) {
    const session = course.sessions.find(
      (candidate) => candidate.sessionRef === sessionRef,
    )
    if (session) {
      return `Session: ${humanize(session.sessionKind)} · ${course.code} · ${course.title} · ${session.date}, ${session.startTime}–${session.endTime}`
    }
  }
  const [kind, sourceId] = sessionRef.split(':', 2)
  return `Session: ${humanize(kind)} session ${sourceId} · No longer in the current assignment projection`
}

function formatTimestamp(value: string, timeZone: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone,
  })
}
