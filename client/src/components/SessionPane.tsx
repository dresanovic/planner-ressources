import { useEffect, useRef, useState, type ReactNode } from 'react'
import type { LoadedCalendarWorkspace, WorkspaceOccurrence } from '../api/calendarWorkspace'
import { calendarFindingLabel } from './calendarFindingLabel'
import { formatCalendarDate, formatCalendarDateRange } from '../utils/datePresentation'
import { label } from '../config/terminology'

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
          <p className="eyebrow">{mode === 'editing' ? 'Termin bearbeiten' : 'Termindetails'}</p>
          <h2 id="session-pane-title" ref={headingRef} tabIndex={-1}>
            {occurrence.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'} · {course?.name ?? occurrence.courseRef}
          </h2>
        </div>
        <button type="button" className="session-pane-close" onClick={onRequestClose} disabled={busy} aria-label="Termindetails schließen">×</button>
      </div>

      {status && <p className="mutation-feedback" role="status" aria-live="polite">{status}</p>}
      {error && <div className="refresh-error" role="alert">{error}</div>}

      {restrictedReview ? (
        <>
          <dl className="session-pane-details restricted-session-details">
            <div><dt>Revision</dt><dd>{restrictedReview.revisionLabel}</dd></div>
            <div><dt>Status</dt><dd>{stateLabel(restrictedReview.lifecycleState)}</dd></div>
            <div><dt>{label('course.singular')}</dt><dd>{course ? `${course.code} · ${course.name}` : occurrence.courseRef}</dd></div>
            <div><dt>Studienart</dt><dd>{course?.studyType ?? 'Nicht verfügbar'}</dd></div>
            <div><dt>Datum und Uhrzeit</dt><dd>{formatCalendarDate(occurrence.date)}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
            <div><dt>{label('cohort.singular')}</dt><dd>{occurrence.cohort}</dd></div>
            <div><dt>{label('lecturer.singular')}</dt><dd>{restrictedReview.lecturerName}</dd></div>
            <div><dt>{label('room.singular')}</dt><dd>{restrictedReview.roomName}</dd></div>
            {occurrence.kind === 'teaching' ? (
              <div><dt>Lehreinheiten</dt><dd>{occurrence.teachingUnits}</dd></div>
            ) : (
              <>
                <div><dt>Prüfungsart</dt><dd>{occurrence.examType}</dd></div>
                <div><dt>Dauer</dt><dd>{occurrence.durationMinutes} Minuten</dd></div>
              </>
            )}
          </dl>
          <section aria-labelledby="session-pane-warnings">
            <h3 id="session-pane-warnings">Aktuelle Hinweise</h3>
            {restrictedReview.validationMessages.length > 0 ? (
              <ul>
                {restrictedReview.validationMessages.map((message) => (
                  <li key={message}>{message}</li>
                ))}
              </ul>
            ) : (
              <p>
                {restrictedReview.validationAvailability === 'complete'
                  ? 'Keine aktuellen Hinweise.'
                  : restrictedReview.validationAvailability === 'partial'
                    ? 'Die Prüfung ist unvollständig; ein vollständiges Ergebnis ohne Probleme liegt nicht vor.'
                    : 'Die aktuelle Prüfung ist nicht verfügbar.'}
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
            <div><dt>Status</dt><dd>{stateLabel(workspace.selectedRevision.lifecycleState)}</dd></div>
            <div><dt>Revision</dt><dd>R{workspace.selectedRevision.revisionNumber} · {workspace.selectedRevision.designation === 'active_working' ? 'Arbeitsrevision' : 'Aktuelle Veröffentlichung'}</dd></div>
            <div><dt>{label('course.singular')}</dt><dd>{course?.name ?? occurrence.courseRef}</dd></div>
            <div><dt>Studienart</dt><dd>{course?.studyType ?? 'Nicht verfügbar'}</dd></div>
            <div><dt>Datum und Uhrzeit</dt><dd>{formatCalendarDate(occurrence.date)}, {occurrence.startTime}–{occurrence.endTime}</dd></div>
            <div><dt>{label('cohort.singular')}</dt><dd>{occurrence.cohort}</dd></div>
            <div><dt>{label('lecturer.singular')}</dt><dd>{occurrence.lecturerRefs.join(', ')}</dd></div>
            <div><dt>{label('room.singular')}</dt><dd>{occurrence.kind === 'exam' ? `${occurrence.assignedRoomName} (${occurrence.roomRef})` : occurrence.roomRef}</dd></div>
            {occurrence.kind === 'teaching' ? (
              <>
                <div><dt>Lehreinheiten</dt><dd>{occurrence.teachingUnits}</dd></div>
                {occurrence.source !== undefined && <div><dt>Quelle</dt><dd>{sourceLabel(occurrence.source)}</dd></div>}
              </>
            ) : (
              <>
                <div><dt>Prüfungsart</dt><dd>{occurrence.examType}</dd></div>
                <div><dt>Dauer</dt><dd>{occurrence.durationMinutes} Minuten</dd></div>
                {occurrence.requiredCapacity !== undefined && <div><dt>Kapazität</dt><dd>{occurrence.requiredCapacity} erforderlich; {occurrence.currentRoomCapacity == null ? 'aktuelle Raumkapazität nicht verfügbar' : `${occurrence.currentRoomCapacity} aktuell`}</dd></div>}
                {occurrence.validityContext && <>
                  <div><dt>Konfiguration</dt><dd>{detailValue(occurrence.validityContext.configurationIdentifier)} · Revision {detailValue(occurrence.validityContext.configurationRevision)}</dd></div>
                  <div><dt>Letzte Lehrveranstaltung</dt><dd>{formatCalendarDate(occurrence.validityContext.finalTeachingDate)} um {detailValue(occurrence.validityContext.finalTeachingEndTime)}</dd></div>
                  <div><dt>Quelle</dt><dd>{sourceLabel(detailValue(occurrence.validityContext.source))}</dd></div>
                </>}
                {occurrence.recommendationContext && <div><dt>Empfohlener Zeitraum</dt><dd>{formatCalendarDateRange(occurrence.recommendationContext.recommendedStartDate, occurrence.recommendationContext.recommendedEndDate)}{occurrence.recommendationContext.recommendationWasOverridden ? ' · manuell festgelegt' : ''}</dd></div>}
              </>
            )}
          </dl>
          <section aria-labelledby="session-pane-warnings"><h3 id="session-pane-warnings">Aktuelle Hinweise</h3>{findings.length ? <ul>{findings.map((item) => <li key={item.findingRef}>{calendarFindingLabel(item)}</li>)}</ul> : <p>Keine aktuellen Hinweise.</p>}</section>
          {workspace.selectedRevision.readOnly ? (
            <p className="read-only-note">In der aktuellen Veröffentlichung sind keine Korrekturen möglich. Öffnen Sie die Arbeitsrevision, um Änderungen vorzunehmen.</p>
          ) : actionUnavailableReason ? (
            <p className="read-only-note">{actionUnavailableReason}</p>
          ) : (
            <div className="session-pane-actions">
              {onRequestEdit && <button type="button" onClick={onRequestEdit}>Termin bearbeiten</button>}
              {onRequestDelete && <button type="button" className="destructive-button" onClick={onRequestDelete}>Mit Bestätigung löschen</button>}
            </div>
          )}
        </>
      )}
    </aside>
  )
}

function stateLabel(state: string) {
  if (state === 'ready_for_review') return 'Bereit zur Prüfung'
  return state === 'published' ? 'Veröffentlicht' : 'Entwurf'
}

function detailValue(value: unknown) {
  return value == null || value === '' ? 'Nicht verfügbar' : String(value)
}

function sourceLabel(value: string): string {
  return ({ generated: 'Erzeugt', manual: 'Manuell' } as Record<string, string>)[value] ?? value
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
