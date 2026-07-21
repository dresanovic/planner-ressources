import { useEffect, useRef } from 'react'

import type { PublicationPreparation } from '../api/scheduleLifecycle'


export function PublicationConfirmationDialog({ preparation, busy, onConfirm, onCancel }: { preparation: PublicationPreparation; busy: boolean; onConfirm: () => void; onCancel: () => void }) {
  const dialogRef = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    dialogRef.current?.focus()
    return () => opener?.focus()
  }, [])
  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key === 'Escape' && !busy) { event.preventDefault(); onCancel(); return }
    if (event.key !== 'Tab') return
    const controls = [...(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    if (controls.length === 0) { event.preventDefault(); dialogRef.current?.focus(); return }
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) { event.preventDefault(); last.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }
  const consequence = preparation.consequence === 'first_publication'
    ? 'This creates the semester’s first publication.'
    : `This replaces revision ${preparation.currentPublication?.revisionNumber}.`
  return (
    <div className="modal-backdrop">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="publication-title" className="confirmation-dialog" tabIndex={-1} onKeyDown={onKeyDown}>
        <p className="eyebrow">{preparation.semesterName}</p>
        <h2 id="publication-title">Publish revision {preparation.targetRevision.revisionNumber}</h2>
        <p>{consequence}</p>
        <p>{preparation.scheduledUnits} of {preparation.totalUnits} teaching units are scheduled; {preparation.remainingUnits} remain.</p>
        {preparation.conditions.length > 0 ? <><p>These conditions do not prevent publication:</p><ul className="publication-conditions">{preparation.conditions.map((condition, index) => <li key={`${condition.code}-${condition.sourceSessionId ?? index}`}>{condition.message}</li>)}</ul></> : <p>No known non-blocking conditions were found.</p>}
        <div className="dialog-actions">
          <button type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Cancel</button>
          <button type="button" disabled={busy} onClick={onConfirm}>{busy ? 'Publishing…' : 'Publish explicitly'}</button>
        </div>
      </div>
    </div>
  )
}
