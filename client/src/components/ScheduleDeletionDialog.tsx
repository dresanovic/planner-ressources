import { useEffect, useRef, type KeyboardEvent, type ReactNode } from 'react'

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
  error?: ReactNode
  onCancel: () => void
  onConfirm: () => void
}

export function ScheduleDeletionDialog({ scope, isBusy, error, onCancel, onConfirm }: ScheduleDeletionDialogProps) {
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
        <h2 id={titleId}>{isSession ? 'Delete this Draft Session?' : 'Clear this course Draft Schedule?'}</h2>
        <div id={descriptionId} className="deletion-consequence">
          <p><strong>{scope.courseName}</strong> · {scope.semesterName}</p>
          {isSession ? (
            <>
              <p>{scope.date}, {scope.startTime}-{scope.endTime}</p>
              <p>{scope.unitsRemoved} units will be removed from scheduled coverage; {scope.resultingRemainingUnits} units remaining.</p>
              {scope.lastSession && <p>This is the last session, so the empty Draft Schedule will also be removed.</p>}
            </>
          ) : (
            <>
              <p>{scope.sessionCount} {scope.sessionCount === 1 ? 'session' : 'sessions'} will be deleted; {scope.unitsRemoved} scheduled units will be removed; {scope.resultingRemainingUnits} units remaining.</p>
              <p>Course records, academic planning data, and saved generation constraints will be preserved.</p>
            </>
          )}
        </div>
        {error && <div className="alert-item" role="alert">{error}</div>}
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onCancel} disabled={isBusy}>Cancel</button>
          <button type="button" onClick={onConfirm} disabled={isBusy}>
            {isBusy ? 'Deleting…' : isSession ? 'Delete session' : 'Clear course draft'}
          </button>
        </div>
      </div>
    </div>
  )
}
