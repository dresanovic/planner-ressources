import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { LoadedCalendarWorkspace, WorkspaceOccurrence } from '../api/calendarWorkspace'
import { calendarFindingLabel } from './calendarFindingLabel'

type Props = {
  occurrence: WorkspaceOccurrence
  workspace: LoadedCalendarWorkspace
  mode: 'detail' | 'editing'
  editor?: ReactNode
  busy?: boolean
  status?: string
  error?: string
  decisionOpen?: boolean
  actionUnavailableReason?: string
  onRequestClose: () => void
  onRequestEdit?: () => void
  onRequestDelete?: () => void
  restrictedReview?: {
    lecturerName: string
    revisionLabel: string
    lifecycleState: string
    roomName: string
    validationAvailability: 'complete' | 'partial' | 'unavailable'
    validationMessages: string[]
    feedbackActions: ReactNode
  }
}

export function SessionPane({
  occurrence,
  workspace,
  mode,
  editor,
  busy = false,
  status,
  error,
  decisionOpen = false,
  actionUnavailableReason,
  onRequestClose,
  onRequestEdit,
  onRequestDelete,
  restrictedReview,
}: Props) {
  const [narrow, setNarrow] = useState(() => window.innerWidth <= 820)
  const paneRef = useRef<HTMLElement>(null)
  const headingRef = useRef<HTMLHeadingElement>(null)
  const course = workspace.courses.find((item) => item.courseRef === occurrence.courseRef)
  const findings = workspace.validationFindings.filter((item) => occurrence.findingRefs.includes(item.findingRef))

  useEffect(() => {
    function resize() { setNarrow(window.innerWidth <= 820) }
    window.addEventListener('resize', resize)
    return () => window.removeEventListener('resize', resize)
  }, [])

  useEffect(() => {
    headingRef.current?.focus({ preventScroll: true })
  }, [mode, occurrence.occurrenceRef])

  useEffect(() => {
    if (!narrow || !paneRef.current) return
    const changed: { element: HTMLElement; inert: boolean; ariaHidden: string | null }[] = []
    let branch: HTMLElement | null = paneRef.current
    while (branch?.parentElement) {
      const parent: HTMLElement = branch.parentElement
      for (const sibling of parent.children) {
        if (sibling === branch || !(sibling instanceof HTMLElement)) continue
        if (
          decisionOpen
          && sibling.matches('.dialog-backdrop')
          && sibling.querySelector('.discard-changes-dialog')
        ) {
          continue
        }
        changed.push({
          element: sibling,
          inert: sibling.inert,
          ariaHidden: sibling.getAttribute('aria-hidden'),
        })
        sibling.inert = true
        sibling.setAttribute('aria-hidden', 'true')
      }
      branch = parent
      if (parent.matches('main')) break
    }
    const opener = document.querySelector<HTMLElement>('.navigation-opener')
    if (opener) {
      changed.push({ element: opener, inert: opener.inert, ariaHidden: opener.getAttribute('aria-hidden') })
      opener.inert = true
      opener.setAttribute('aria-hidden', 'true')
    }
    return () => {
      for (const item of changed) {
        item.element.inert = item.inert
        if (item.ariaHidden == null) item.element.removeAttribute('aria-hidden')
        else item.element.setAttribute('aria-hidden', item.ariaHidden)
      }
    }
  }, [decisionOpen, narrow])

  useEffect(() => {
    function keydown(event: KeyboardEvent) {
      if (decisionOpen) return
      if (event.key === 'Escape' && !busy) {
        event.preventDefault()
        onRequestClose()
      } else if (narrow && event.key === 'Tab') {
        trapFocus(event, paneRef.current)
      }
    }
    document.addEventListener('keydown', keydown)
    return () => document.removeEventListener('keydown', keydown)
  }, [busy, decisionOpen, narrow, onRequestClose])

  return (
    <aside
      ref={paneRef}
      className={`session-pane session-pane-${mode}${narrow ? ' session-pane-fullscreen' : ''}`}
      aria-labelledby="session-pane-title"
      role={narrow ? 'dialog' : undefined}
      aria-modal={narrow && !decisionOpen ? 'true' : undefined}
      aria-hidden={decisionOpen || undefined}
      inert={decisionOpen || undefined}
      aria-busy={busy || undefined}
    >
      <div className="session-pane-heading">
        <div>
          <p className="eyebrow">{mode === 'editing' ? 'Editing session' : 'Session detail'}</p>
          <h2 id="session-pane-title" ref={headingRef} tabIndex={-1}>
            {occurrence.kind === 'teaching' ? 'Teaching session' : 'Exam session'} · {course?.name ?? occurrence.courseRef}
          </h2>
        </div>
        <button type="button" className="session-pane-close" onClick={onRequestClose} disabled={busy} aria-label="Close session pane">×</button>
      </div>

      {status && <p className="mutation-feedback" role="status" aria-live="polite">{status}</p>}
      {error && <div className="refresh-error" role="alert">{error}</div>}

      {restrictedReview ? (
        <>
          <dl className="session-pane-details restricted-session-details">
            <div><dt>Revision</dt><dd>{restrictedReview.revisionLabel}</dd></div>
            <div><dt>Lifecycle</dt><dd>{stateLabel(restrictedReview.lifecycleState)}</dd></div>
            <div><dt>Course</dt><dd>{course ? `${course.code} · ${course.name}` : occurrence.courseRef}</dd></div>
            <div><dt>Study type</dt><dd>{course?.studyType ?? 'Unavailable'}</dd></div>
            <div><dt>Date and time</dt><dd>{occurrence.date}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
            <div><dt>Cohort</dt><dd>{occurrence.cohort}</dd></div>
            <div><dt>Lecturer</dt><dd>{restrictedReview.lecturerName}</dd></div>
            <div><dt>Room</dt><dd>{restrictedReview.roomName}</dd></div>
            {occurrence.kind === 'teaching' ? (
              <div><dt>Teaching units</dt><dd>{occurrence.teachingUnits}</dd></div>
            ) : (
              <>
                <div><dt>Exam type</dt><dd>{occurrence.examType}</dd></div>
                <div><dt>Duration</dt><dd>{occurrence.durationMinutes} minutes</dd></div>
              </>
            )}
          </dl>
          <section aria-labelledby="session-pane-warnings">
            <h3 id="session-pane-warnings">Current warnings</h3>
            {restrictedReview.validationMessages.length > 0 ? (
              <ul>
                {restrictedReview.validationMessages.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
            ) : (
              <p>
                {restrictedReview.validationAvailability === 'complete'
                  ? 'No current warnings.'
                  : restrictedReview.validationAvailability === 'partial'
                    ? 'Validation is incomplete; a complete no-issue result is not available.'
                    : 'Current validation is unavailable.'}
              </p>
            )}
          </section>
          <div className="session-pane-actions lecturer-feedback-actions">
            {restrictedReview.feedbackActions}
          </div>
        </>
      ) : mode === 'editing' ? editor : (
        <>
          <dl className="session-pane-details">
            <div><dt>Lifecycle</dt><dd>{stateLabel(workspace.selectedRevision.lifecycleState)}</dd></div>
            <div><dt>Revision</dt><dd>R{workspace.selectedRevision.revisionNumber} · {workspace.selectedRevision.designation === 'active_working' ? 'Working' : 'Current Published'}</dd></div>
            <div><dt>Course</dt><dd>{course?.name ?? occurrence.courseRef}</dd></div>
            <div><dt>Study type</dt><dd>{course?.studyType ?? 'Unavailable'}</dd></div>
            <div><dt>Date and time</dt><dd>{occurrence.date}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
            <div><dt>Cohort</dt><dd>{occurrence.cohort}</dd></div>
            <div><dt>Lecturer</dt><dd>{occurrence.lecturerRefs.join(', ')}</dd></div>
            <div><dt>Room</dt><dd>{occurrence.kind === 'exam' ? `${occurrence.assignedRoomName} (${occurrence.roomRef})` : occurrence.roomRef}</dd></div>
            {occurrence.kind === 'teaching' ? (
              <>
                <div><dt>Teaching units</dt><dd>{occurrence.teachingUnits}</dd></div>
                {occurrence.source !== undefined && <div><dt>Source</dt><dd>{occurrence.source}</dd></div>}
              </>
            ) : (
              <>
                <div><dt>Exam type</dt><dd>{occurrence.examType}</dd></div>
                <div><dt>Duration</dt><dd>{occurrence.durationMinutes} minutes</dd></div>
                {occurrence.requiredCapacity !== undefined && <div><dt>Capacity</dt><dd>{occurrence.requiredCapacity} required; {occurrence.currentRoomCapacity == null ? 'current room capacity unavailable' : `${occurrence.currentRoomCapacity} current`}</dd></div>}
                {occurrence.validityContext && <>
                  <div><dt>Configuration</dt><dd>{detailValue(occurrence.validityContext.configurationIdentifier)} · revision {detailValue(occurrence.validityContext.configurationRevision)}</dd></div>
                  <div><dt>Final teaching</dt><dd>{detailValue(occurrence.validityContext.finalTeachingDate)} at {detailValue(occurrence.validityContext.finalTeachingEndTime)}</dd></div>
                  <div><dt>Source</dt><dd>{detailValue(occurrence.validityContext.source)}</dd></div>
                </>}
                {occurrence.recommendationContext && <div><dt>Recommended period</dt><dd>{detailValue(occurrence.recommendationContext.recommendedStartDate)}–{detailValue(occurrence.recommendationContext.recommendedEndDate)}{occurrence.recommendationContext.recommendationWasOverridden ? ' · planner override' : ''}</dd></div>}
              </>
            )}
          </dl>
          <section aria-labelledby="session-pane-warnings"><h3 id="session-pane-warnings">Current warnings</h3>{findings.length ? <ul>{findings.map((item) => <li key={item.findingRef}>{calendarFindingLabel(item)}</li>)}</ul> : <p>No current warnings.</p>}</section>
          {workspace.selectedRevision.readOnly ? (
            <p className="read-only-note">Correction actions are unavailable for Current Published. Open the Working revision to make changes.</p>
          ) : actionUnavailableReason ? (
            <p className="read-only-note">{actionUnavailableReason}</p>
          ) : (
            <div className="session-pane-actions">
              {onRequestEdit && <button type="button" onClick={onRequestEdit}>Edit session</button>}
              {onRequestDelete && <button type="button" className="destructive-button" onClick={onRequestDelete}>Delete with confirmation</button>}
            </div>
          )}
        </>
      )}
    </aside>
  )
}

function stateLabel(state: string) {
  if (state === 'ready_for_review') return 'Ready for review'
  return state === 'published' ? 'Published' : 'Draft'
}

function detailValue(value: unknown) {
  return value == null || value === '' ? 'Unavailable' : String(value)
}

function trapFocus(event: KeyboardEvent, container: HTMLElement | null) {
  if (!container) return
  const focusable = [...container.querySelectorAll<HTMLElement>('button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])')]
  if (focusable.length === 0) return
  const first = focusable[0]
  const last = focusable[focusable.length - 1]
  if (event.shiftKey && document.activeElement === first) {
    event.preventDefault()
    last.focus()
  } else if (!event.shiftKey && document.activeElement === last) {
    event.preventDefault()
    first.focus()
  }
}
