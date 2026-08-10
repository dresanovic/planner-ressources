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
import { formatCalendarDate, formatViennaDateTime } from '../utils/datePresentation'
import { label } from '../config/terminology'


const UNAVAILABLE_MESSAGE =
  'Diese Prüfung ist nicht verfügbar. Fordern Sie bei der planenden Person einen neuen Link an.'

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
          'Der ausgewählte Termin ist in dieser Prüfung nicht mehr enthalten. Die noch nicht gesendete Rückmeldung zu diesem Termin wurde verworfen.',
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
            ? 'Die Terminprüfung ist vorübergehend nicht verfügbar. Warten Sie kurz und laden Sie sie erneut.'
            : 'Die Terminprüfung konnte nicht erreicht werden. Prüfen Sie die Verbindung und laden Sie sie erneut.',
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
    setFeedbackStatus('Die Rückmeldung wird gesendet.')
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
          ? 'Diese Rückmeldung wurde bereits angenommen.'
          : 'Die Rückmeldung wurde angenommen.',
      )
    } catch (reason) {
      if (reason instanceof LecturerReviewApiError && reason.status === 409) {
        const staleSessionRef = input.sessionRef
        if (staleSessionRef !== undefined) {
          setSelectedRef((current) =>
            current === staleSessionRef ? null : current,
          )
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
        setFeedbackError(staleSessionRef !== undefined
          ? 'Die Terminzuordnung wurde zwischenzeitlich geändert. Ihre noch nicht gesendete Rückmeldung bleibt auf dieser Seite erhalten. Öffnen Sie den Termin erneut, um den Text bei Bedarf zu kopieren, bevor Sie die Browserseite neu laden oder den Link erneut öffnen. Prüfen Sie anschließend den aktuellen Stand.'
          : 'Der Revisionsstand wurde zwischenzeitlich geändert. Ihr noch nicht gesendeter Revisionskommentar bleibt im Eingabefeld erhalten. Kopieren Sie den Text bei Bedarf, bevor Sie die Browserseite neu laden oder den Link erneut öffnen, und prüfen Sie anschließend den aktuellen Stand.')
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
      setFeedbackError(retryable
        ? 'Die Rückmeldung konnte wegen einer Verbindungsstörung nicht bestätigt werden. Verwenden Sie „Erneut versuchen“ für dieselbe Rückmeldung; sie wird nicht absichtlich doppelt angelegt.'
        : 'Die Rückmeldung wurde nicht angenommen. Prüfen Sie den aktuellen Termin und Ihre Eingabe; die genaue technische Ursache wird nicht angezeigt.')
    } finally {
      setPendingKey(null)
    }
  }

  if (unavailable) {
    return (
      <main className="lecturer-review-public lecturer-review-safe-state">
        <section className="review-card" role="alert">
          <h1>Terminprüfung nicht verfügbar</h1>
          <p>{UNAVAILABLE_MESSAGE}</p>
        </section>
      </main>
    )
  }

  if (temporaryError !== null) {
    return (
      <main className="lecturer-review-public lecturer-review-safe-state">
        <section className="review-card" role="alert">
          <h1>Terminprüfung vorübergehend nicht verfügbar</h1>
          <p>{temporaryError}</p>
          <button type="button" onClick={() => void load()}>
            Erneut laden
          </button>
        </section>
      </main>
    )
  }

  if (loading || review === null || workspace === null) {
    return (
      <main className="lecturer-review-public" aria-busy="true">
        <section className="review-card" role="status">
          <h1>Terminprüfung wird geladen</h1>
          <p>Bitte warten Sie, während die aktuelle Planung geladen wird.</p>
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
        <p className="eyebrow">Schreibgeschützte Terminprüfung</p>
        <h1>Lehr- und Prüfungszuordnungen prüfen</h1>
        <p>{review.identityDisclaimer}</p>
        <p>
          Ihre Rückmeldungen sind Hinweise. Sie genehmigen, bearbeiten oder blockieren die Veröffentlichung dieser Planung nicht.
        </p>
        <dl className="review-metadata">
          <div>
            <dt>Revision</dt>
            <dd>{review.revision.semesterName} · {review.revision.label}</dd>
          </div>
          <div>
            <dt>Status</dt>
            <dd>{humanize(review.revision.state)}</dd>
          </div>
          <div>
            <dt>Zugriff gültig bis</dt>
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
          <div className="lecturer-fixed-context" aria-label={`${label('lecturer.singular')}-Kontext`}>
            <strong>{label('lecturer.singular')}</strong>
            <span>{review.intendedLecturer}</span>
            <small>Durch diesen Prüfungslink festgelegt</small>
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
                  ? `In dieser Revision gibt es derzeit keine Lehr- oder Prüfungstermine für diese ${label('lecturer.singular')}.`
                  : 'Kein Termin entspricht den aktiven Filtern.'
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
                roomName: session?.roomName ?? 'Nicht verfügbar',
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
        <h2 id="revision-comment">Rückmeldung zur Revision</h2>
        <label htmlFor="lecturer-review-revision-comment">Revisionskommentar</label>
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
          Revisionskommentar senden
        </button>
        <h3>Über diesen Link gesendete Rückmeldungen</h3>
        {review.submittedFeedback.length === 0 ? (
          <p>Über diesen Link wurde noch keine Rückmeldung gesendet.</p>
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
          destinationLabel="dem ausgewählten Planungskontext"
          title="Nicht gesendete Rückmeldung verwerfen?"
          description="Ihre Rückmeldung wurde noch nicht gesendet. Verwerfen Sie sie, um mit dem ausgewählten Planungskontext fortzufahren."
          keepLabel="Weiter schreiben"
          discardLabel="Rückmeldung verwerfen"
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
      <label htmlFor={`session-comment-${id}`}>Terminkommentar</label>
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
        Terminkommentar senden
      </button>
      <label htmlFor={`flag-comment-${id}`}>
        Begründung für „Nicht möglich“ (optional)
      </label>
      <textarea
        id={`flag-comment-${id}`}
        maxLength={2000}
        value={flagComment}
        onInput={(event) => onFlagCommentChange(event.currentTarget.value)}
      />
      <span>{flagComment.trim().length} / 2000</span>
      <button type="button" disabled={pending} onClick={onSubmitFlag}>
        Als nicht möglich kennzeichnen
      </button>
    </>
  )
}

function humanize(value: string) {
  return ({
    draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung', published: 'Veröffentlicht',
    revision_comment: 'Revisionskommentar', session_comment: 'Terminkommentar', impossible_session: 'Nicht möglich',
    teaching: 'Lehrtermin', exam: 'Prüfungstermin',
  } as Record<string, string>)[value] ?? 'Unbekannter Status'
}

function publicSessionLabel(review: PublicLecturerReview, sessionRef: string) {
  for (const course of review.courses) {
    const session = course.sessions.find(
      (candidate) => candidate.sessionRef === sessionRef,
    )
    if (session) {
      return `Termin: ${humanize(session.sessionKind)} · ${course.code} · ${course.title} · ${formatCalendarDate(session.date)}, ${session.startTime}–${session.endTime}`
    }
  }
  const [kind, sourceId] = sessionRef.split(':', 2)
  return `Termin: ${humanize(kind)} ${sourceId} · Nicht mehr in der aktuellen Zuordnung enthalten`
}

function formatTimestamp(value: string, _timeZone: string) {
  void _timeZone
  return formatViennaDateTime(value)
}
