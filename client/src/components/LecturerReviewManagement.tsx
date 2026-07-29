import { useEffect, useMemo, useRef, useState } from 'react'

import {
  buildLecturerReviewUrl,
  type IssueLecturerReviewInput,
  type IssuedLecturerReviewLink,
  type LecturerReviewOverview,
  type ReplaceLecturerReviewInput,
} from '../api/lecturerReview'


type LecturerReviewManagementProps = {
  overview: LecturerReviewOverview
  busy: boolean
  onIssue: (
    input: Required<IssueLecturerReviewInput>,
  ) => Promise<IssuedLecturerReviewLink>
  onRevoke?: (linkId: number) => Promise<LecturerReviewOverview>
  onReplace?: (
    linkId: number,
    input: Required<ReplaceLecturerReviewInput>,
  ) => Promise<IssuedLecturerReviewLink>
  onOpenCurrentSession?: (navigation: {
    revisionId: number
    occurrenceRef: string
  }) => void
}

export function LecturerReviewManagement({
  overview,
  busy,
  onIssue,
  onRevoke = () => Promise.reject(new Error('Revoke is unavailable.')),
  onReplace = () => Promise.reject(new Error('Replacement is unavailable.')),
  onOpenCurrentSession,
}: LecturerReviewManagementProps) {
  const [resultOverview, setResultOverview] =
    useState<LecturerReviewOverview | null>(null)
  const [lecturerId, setLecturerId] = useState('')
  const [durationDays, setDurationDays] = useState<1 | 2 | 3>(3)
  const [replacementDurationDays, setReplacementDurationDays] =
    useState<1 | 2 | 3>(3)
  const [issued, setIssued] = useState<IssuedLecturerReviewLink | null>(null)
  const [transientUrl, setTransientUrl] = useState<string | null>(null)
  const [uncertainLinkIds, setUncertainLinkIds] = useState<Set<number>>(
    () => new Set(),
  )
  const [notPossibleOnly, setNotPossibleOnly] = useState(false)
  const [status, setStatus] = useState('')
  const [error, setError] = useState('')
  const previousRevision = useRef(overview.revision.id)
  const feedbackHeadingRef = useRef<HTMLHeadingElement>(null)
  const currentOverview =
    resultOverview?.revision.id === overview.revision.id
      ? resultOverview
      : overview

  useEffect(() => {
    if (previousRevision.current !== overview.revision.id) {
      previousRevision.current = overview.revision.id
      setResultOverview(null)
      setIssued(null)
      setTransientUrl(null)
      setLecturerId('')
      setStatus('')
      setError('')
      setUncertainLinkIds(new Set())
      setNotPossibleOnly(false)
    }
  }, [overview])

  const selectedLecturer = useMemo(
    () =>
      currentOverview.lecturers.find(
        (lecturer) => lecturer.lecturerId === Number(lecturerId),
      ) ?? null,
    [lecturerId, currentOverview.lecturers],
  )
  const working = ['draft', 'ready_for_review'].includes(
    currentOverview.revision.state,
  )
  const canIssue =
    !busy &&
    working &&
    selectedLecturer !== null &&
    selectedLecturer.initialIssueAllowed
  const feedbackComplete =
    currentOverview.feedbackAvailability === 'complete'
  const visibleFeedbackGroups = notPossibleOnly
    ? currentOverview.feedbackGroups.filter(
        (group) =>
          group.level === 'session' && group.impossibleFlagCount > 0,
      )
    : currentOverview.feedbackGroups

  function toggleNotPossibleFilter() {
    if (!feedbackComplete) return
    const next = !notPossibleOnly
    setNotPossibleOnly(next)
    if (next) {
      queueMicrotask(() => feedbackHeadingRef.current?.focus())
    }
  }

  async function issue() {
    if (!canIssue || selectedLecturer === null) return
    setError('')
    setStatus('Issuing review link…')
    try {
      const result = await onIssue({
        lecturerId: selectedLecturer.lecturerId,
        durationDays,
      })
      setIssued(result)
      setResultOverview(result.overview)
      setTransientUrl(buildLecturerReviewUrl(result.secret))
      setStatus(
        'Review link issued. Copy it now; the secret is shown only in this result.',
      )
    } catch {
      setIssued(null)
      setTransientUrl(null)
      setStatus('')
      setError('The review link could not be issued.')
    }
  }

  async function revoke(linkId: number) {
    setError('')
    setStatus('Revoking review link…')
    try {
      const result = await onRevoke(linkId)
      setResultOverview(result)
      setIssued(null)
      setTransientUrl(null)
      setUncertainLinkIds((current) => {
        const next = new Set(current)
        next.delete(linkId)
        return next
      })
      setStatus('Link revoked.')
    } catch {
      setStatus('')
      setError(
        'The link could not be revoked. Refresh and review its current status.',
      )
    }
  }

  async function replace(linkId: number) {
    setError('')
    setStatus('Replacing review link…')
    setIssued(null)
    setTransientUrl(null)
    try {
      const result = await onReplace(linkId, {
        durationDays: replacementDurationDays,
      })
      setResultOverview(result.overview)
      setIssued(result)
      setTransientUrl(buildLecturerReviewUrl(result.secret))
      setUncertainLinkIds((current) => {
        const next = new Set(current)
        next.delete(linkId)
        return next
      })
      setStatus(
        'Replacement issued. Earlier access is no longer available; copy the new link now.',
      )
    } catch {
      setUncertainLinkIds((current) => new Set(current).add(linkId))
      setStatus('')
      setError(
        'The replacement result is unknown because the response was lost. Refresh to check the current status, then replace again to create a new replacement if needed.',
      )
    }
  }

  async function copy() {
    if (transientUrl === null) return
    try {
      await navigator.clipboard.writeText(transientUrl)
      setError('')
      setStatus('Link copied.')
    } catch {
      setStatus('')
      setError(
        'Could not copy the link. Select and copy the one-time URL manually.',
      )
    }
  }

  function dismiss() {
    setIssued(null)
    setTransientUrl(null)
    setStatus('One-time link details dismissed.')
    setError('')
  }

  const detailLecturer =
    issued?.overview.lecturers.find(
      (lecturer) => lecturer.lecturerId === issued.issuedLink.lecturerId,
    ) ?? selectedLecturer

  return (
    <section className="lecturer-review-management">
      <header>
        <p className="eyebrow">Accountless lecturer review</p>
        <h2>{currentOverview.revision.label}</h2>
        <p>
          {humanize(currentOverview.revision.state)}
          {currentOverview.revision.state === 'ready_for_review' &&
            ' · Recommended time to request feedback'}
        </p>
      </header>

      <section
        className="review-feedback-area"
        aria-labelledby="review-feedback-heading"
      >
        <button
          type="button"
          className="review-feedback-filter"
          aria-pressed={notPossibleOnly}
          disabled={!feedbackComplete}
          onClick={toggleNotPossibleFilter}
        >
          <span aria-hidden="true">!</span>{' '}
          {feedbackComplete
            ? `Not possible ${currentOverview.impossibleFlagCount}`
            : currentOverview.feedbackAvailability === 'partial'
              ? 'Not possible count incomplete'
              : 'Not possible count unavailable'}
        </button>
        {!feedbackComplete && (
          <p role="status">
            {currentOverview.feedbackAvailability === 'partial'
              ? 'Feedback is partial; the Not possible count is incomplete.'
              : 'Feedback is unavailable; no complete count can be shown.'}
          </p>
        )}
        <h3
          id="review-feedback-heading"
          ref={feedbackHeadingRef}
          tabIndex={-1}
        >
          {notPossibleOnly ? 'Not possible feedback' : 'Lecturer feedback'}
        </h3>
        <p className="review-feedback-announcement" aria-live="polite">
          {notPossibleOnly
            ? `${visibleFeedbackGroups.length} flagged session ${
                visibleFeedbackGroups.length === 1 ? 'group' : 'groups'
              } shown.`
            : `${visibleFeedbackGroups.length} feedback ${
                visibleFeedbackGroups.length === 1 ? 'group' : 'groups'
              } shown.`}
        </p>
        {notPossibleOnly && visibleFeedbackGroups.length === 0 ? (
          <p role="status">No sessions have Not possible feedback.</p>
        ) : visibleFeedbackGroups.length === 0 ? (
          <p>No feedback has been submitted for this revision.</p>
        ) : (
          <div className="review-feedback-groups">
            {visibleFeedbackGroups.map((group) => (
              <article className="review-feedback-group" key={group.groupRef}>
                <h4>
                  {group.level === 'revision'
                    ? 'Revision feedback'
                    : group.sessionContext?.courseTitle ??
                      'Historical session feedback'}
                </h4>
                {group.sessionContext !== null && (
                  <dl className="review-feedback-context">
                    <div>
                      <dt>Course</dt>
                      <dd>
                        {group.sessionContext.courseCode} ·{' '}
                        {group.sessionContext.courseTitle}
                      </dd>
                    </div>
                    <div>
                      <dt>Session</dt>
                      <dd>{group.sessionContext.sessionType}</dd>
                    </div>
                    <div>
                      <dt>Date and time</dt>
                      <dd>
                        {group.sessionContext.date},{' '}
                        {group.sessionContext.startTime}–
                        {group.sessionContext.endTime} (
                        {group.sessionContext.timeZone})
                      </dd>
                    </div>
                    <div>
                      <dt>Room</dt>
                      <dd>{group.sessionContext.roomName}</dd>
                    </div>
                    <div>
                      <dt>Cohort</dt>
                      <dd>{group.sessionContext.cohortName}</dd>
                    </div>
                    <div>
                      <dt>Not possible flags</dt>
                      <dd>{group.impossibleFlagCount}</dd>
                    </div>
                  </dl>
                )}
                <ul>
                  {group.items.map((item) => (
                    <li key={item.id}>
                      <strong>{feedbackKindLabel(item.kind)}</strong>
                      {item.comment !== null && <p>{item.comment}</p>}
                      <p>{item.attribution}</p>
                      <time dateTime={item.submittedAt}>
                        {formatTimestamp(item.submittedAt, item.timeZone)} ({item.timeZone})
                      </time>
                      {item.sessionContext != null && (
                        <p>
                          At submission: {item.sessionContext.date},{' '}
                          {item.sessionContext.startTime}–
                          {item.sessionContext.endTime};{' '}
                          {item.sessionContext.roomName};{' '}
                          {item.sessionContext.cohortName}.
                        </p>
                      )}
                    </li>
                  ))}
                </ul>
                {group.currentNavigation !== null ? (
                  <button
                    type="button"
                    onClick={() =>
                      onOpenCurrentSession?.(group.currentNavigation!)
                    }
                  >
                    Open current session
                  </button>
                ) : (
                  group.level === 'session' && (
                    <p>The current session workflow is unavailable.</p>
                  )
                )}
              </article>
            ))}
          </div>
        )}
      </section>

      <div className="review-issue-controls">
        <label htmlFor="lecturer-review-lecturer">Lecturer</label>
        <select
          id="lecturer-review-lecturer"
          value={lecturerId}
          onChange={(event) => setLecturerId(event.target.value)}
          disabled={!working || busy}
        >
          <option value="">Select lecturer</option>
          {currentOverview.lecturers.map((lecturer) => (
            <option
              value={lecturer.lecturerId}
              disabled={!lecturer.initialIssueAllowed}
              key={lecturer.lecturerId}
            >
              {lecturer.lecturerName}
            </option>
          ))}
        </select>

        <label htmlFor="lecturer-review-duration">Duration</label>
        <select
          id="lecturer-review-duration"
          value={durationDays}
          onChange={(event) =>
            setDurationDays(Number(event.target.value) as 1 | 2 | 3)
          }
          disabled={!working || busy}
        >
          <option value="1">1 day</option>
          <option value="2">2 days</option>
          <option value="3">3 days</option>
        </select>

        <button type="button" disabled={!canIssue} onClick={() => void issue()}>
          Issue review link
        </button>
      </div>

      {!working && (
        <p role="note">
          Initial links can be issued only from a Working Draft or Ready for
          review revision.
        </p>
      )}

      <aside className="review-warning">
        <strong>Manual delivery</strong>
        <p>
          Send the link yourself through a private channel. It is a bearer
          link: anyone with it can read this lecturer’s scoped schedule and
          submit advisory feedback until access ends.
        </p>
      </aside>

      {currentOverview.links.length > 0 && (
        <section
          className="review-link-history"
          aria-labelledby="review-link-history"
        >
          <h3 id="review-link-history">Link history</h3>
          <ul>
            {currentOverview.links.map((link) => {
              const uncertain = uncertainLinkIds.has(link.id)
              const active = link.status === 'active' && !uncertain
              return (
                <li key={link.id}>
                  <strong>{link.intendedLecturerName}</strong>
                  <span>
                    {uncertain ? 'Status unknown' : humanize(link.status)}
                  </span>
                  <span>
                    Issued {formatTimestamp(link.issuedAt, link.timeZone)} · expires{' '}
                    {formatTimestamp(link.expiresAt, link.timeZone)}
                  </span>
                  {link.endedAt !== null && (
                    <span>Ended {formatTimestamp(link.endedAt, link.timeZone)}</span>
                  )}
                  {active && (
                    <div className="review-link-actions">
                      <button
                        type="button"
                        disabled={busy}
                        onClick={() => void revoke(link.id)}
                      >
                        Revoke link
                      </button>
                      {link.replaceAllowed && (
                        <>
                          <label htmlFor={`replacement-duration-${link.id}`}>
                            Replacement duration
                          </label>
                          <select
                            id={`replacement-duration-${link.id}`}
                            value={replacementDurationDays}
                            disabled={busy}
                            onChange={(event) =>
                              setReplacementDurationDays(
                                Number(event.target.value) as 1 | 2 | 3,
                              )
                            }
                          >
                            <option value="1">1 day</option>
                            <option value="2">2 days</option>
                            <option value="3">3 days</option>
                          </select>
                          <button
                            type="button"
                            disabled={busy}
                            onClick={() => void replace(link.id)}
                          >
                            Replace link
                          </button>
                        </>
                      )}
                    </div>
                  )}
                </li>
              )
            })}
          </ul>
        </section>
      )}

      {issued !== null && transientUrl !== null && (
        <section className="review-one-time-result" aria-labelledby="review-url">
          <h3 id="review-url">One-time review URL</h3>
          <p className="review-secret-url">{transientUrl}</p>
          <dl className="review-metadata">
            <div>
              <dt>Lecturer</dt>
              <dd>{issued.issuedLink.intendedLecturerName}</dd>
            </div>
            <div>
              <dt>Revision</dt>
              <dd>{issued.overview.revision.label}</dd>
            </div>
            <div>
              <dt>Courses</dt>
              <dd>
                {detailLecturer?.courses
                  .map((course) => course.title)
                  .join(', ') || 'No assigned courses'}
              </dd>
            </div>
            <div>
              <dt>Issued</dt>
              <dd>{formatTimestamp(issued.issuedLink.issuedAt, issued.issuedLink.timeZone)}</dd>
            </div>
            <div>
              <dt>Access expires</dt>
              <dd>
                {formatTimestamp(issued.issuedLink.expiresAt, issued.issuedLink.timeZone)} (
                {issued.issuedLink.timeZone})
              </dd>
            </div>
            <div>
              <dt>Status</dt>
              <dd>{humanize(issued.issuedLink.status)}</dd>
            </div>
          </dl>
          <div className="review-result-actions">
            <button type="button" onClick={() => void copy()}>
              Copy link
            </button>
            <button type="button" onClick={dismiss}>
              Dismiss
            </button>
          </div>
        </section>
      )}

      {status && <p role="status">{status}</p>}
      {error && <p role="alert">{error}</p>}
    </section>
  )
}

function humanize(value: string) {
  const words = value.replaceAll('_', ' ')
  return words.charAt(0).toUpperCase() + words.slice(1)
}

function feedbackKindLabel(value: string) {
  if (value === 'impossible_session') return 'Not possible'
  if (value === 'session_comment') return 'Session comment'
  return 'Revision comment'
}

function formatTimestamp(value: string, timeZone: string) {
  return new Date(value).toLocaleString(undefined, {
    dateStyle: 'medium',
    timeStyle: 'short',
    timeZone,
  })
}
