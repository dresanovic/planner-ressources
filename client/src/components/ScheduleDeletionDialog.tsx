import { useEffect, useRef, type KeyboardEvent } from 'react'
import { formatCalendarDate } from '../utils/datePresentation'
import type { UserProblem } from '../utils/userProblems'
import { ActionableProblemList } from './ActionableProblemList'

export type ScheduleDeletionScope =
  | {
      kind: 'session'
      courseName: string
      semesterName: string
      date: string
      startTime: string
      endTime: string
      unitsRemoved: number
      resultingRemainingUnits: number
      lastSession: boolean
    }
  | {
      kind: 'courseDraft'
      courseName: string
      semesterName: string
      sessionCount: number
      unitsRemoved: number
      resultingRemainingUnits: number
    }

type ScheduleDeletionDialogProps = {
  scope: ScheduleDeletionScope
  isBusy: boolean
  problems?: UserProblem[]
  onCancel: () => void
  onConfirm: () => void
}

export function ScheduleDeletionDialog({ scope, isBusy, problems = [], onCancel, onConfirm }: ScheduleDeletionDialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null)
  const titleId = `schedule-deletion-${scope.kind}-title`
  const descriptionId = `schedule-deletion-${scope.kind}-description`

  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    dialogRef.current?.querySelector<HTMLButtonElement>('button:not(:disabled)')?.focus()
    return () => previous?.focus()
  }, [])

  function handleKeyDown(event: KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape' && !isBusy) {
      event.preventDefault()
      onCancel()
      return
    }
    if (event.key !== 'Tab' || !dialogRef.current) return
    const controls = [...dialogRef.current.querySelectorAll<HTMLElement>('button:not(:disabled)')]
    if (controls.length === 0) return
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  const isSession = scope.kind === 'session'
  return (
    <div className="dialog-backdrop">
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        className="replacement-dialog schedule-deletion-dialog"
        onKeyDown={handleKeyDown}
      >
        <h2 id={titleId}>{isSession ? 'Diesen Entwurfstermin löschen?' : 'Diesen Planungsentwurf leeren?'}</h2>
        <div id={descriptionId} className="deletion-consequence">
          <p><strong>{scope.courseName}</strong> · {scope.semesterName}</p>
          {isSession ? (
            <>
              <p>{formatCalendarDate(scope.date)}, {scope.startTime}-{scope.endTime}</p>
              <p>{scope.unitsRemoved} Lehreinheiten werden aus dem geplanten Umfang entfernt; {scope.resultingRemainingUnits} Lehreinheiten bleiben offen.</p>
              {scope.lastSession && <p>Dies ist der letzte Termin; deshalb wird auch der leere Planungsentwurf entfernt.</p>}
            </>
          ) : (
            <>
              <p>{scope.sessionCount} {scope.sessionCount === 1 ? 'Termin wird' : 'Termine werden'} gelöscht; {scope.unitsRemoved} geplante Lehreinheiten werden entfernt; {scope.resultingRemainingUnits} Lehreinheiten bleiben offen.</p>
              <p>Datensätze, akademische Planungsdaten und gespeicherte Erzeugungsregeln bleiben erhalten.</p>
            </>
          )}
        </div>
        <ActionableProblemList problems={problems} className="deletion-problems" />
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onCancel} disabled={isBusy}>Abbrechen</button>
          <button type="button" onClick={onConfirm} disabled={isBusy}>
            {isBusy ? 'Wird gelöscht…' : isSession ? 'Termin löschen' : 'Planungsentwurf leeren'}
          </button>
        </div>
      </div>
    </div>
  )
}
