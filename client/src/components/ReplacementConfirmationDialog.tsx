import { useEffect, useRef, type KeyboardEvent } from 'react'

type ReplacementPreparation = {
  courses: { courseId: number; courseName: string | null; replacementRequired: boolean }[]
}

type Props = {
  preparation: ReplacementPreparation
  disabled?: boolean
  onConfirm: () => void
  onCancel: () => void
}

export function ReplacementConfirmationDialog({ preparation, disabled = false, onConfirm, onCancel }: Props) {
  const replacements = preparation.courses.filter((course) => course.replacementRequired)
  const dialogRef = useRef<HTMLElement>(null)

  useEffect(() => {
    const returnFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    dialogRef.current?.focus()
    return () => returnFocus?.focus()
  }, [])

  useEffect(() => {
    if (disabled) dialogRef.current?.focus()
  }, [disabled])

  function handleKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !disabled) {
      event.preventDefault()
      onCancel()
      return
    }
    if (event.key !== 'Tab') return
    const controls = [...(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    if (controls.length === 0) {
      event.preventDefault()
      dialogRef.current?.focus()
      return
    }
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }
  return (
    <div className="dialog-backdrop" role="presentation">
      <section ref={dialogRef} className="replacement-dialog" role="dialog" aria-modal="true" aria-labelledby="replacement-title" tabIndex={-1} onKeyDown={handleKeyDown}>
        <h2 id="replacement-title">Optimize existing Draft Schedules?</h2>
        <p className="replacement-warning">
          Optimization may replace these schedules and manual session edits only when units do not decrease and the approved comparison is strictly better. This cannot be undone from this screen.
        </p>
        <ul>
          {replacements.map((course) => <li key={course.courseId}>{course.courseName ?? `Course ${course.courseId}`}</li>)}
        </ul>
        <div className="dialog-actions">
          <button type="button" className="secondary-button" onClick={onCancel} disabled={disabled}>Cancel</button>
          <button type="button" onClick={onConfirm} disabled={disabled}>
            {disabled ? 'Optimizing...' : 'Confirm optimization'}
          </button>
        </div>
      </section>
    </div>
  )
}
