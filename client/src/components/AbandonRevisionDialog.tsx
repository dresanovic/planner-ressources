import { useEffect, useRef } from 'react'
import type { ScheduleRevisionSummary } from '../api/scheduleLifecycle'

export function AbandonRevisionDialog({ semesterName, revision, currentPublication, busy, onCancel, onConfirm }: { semesterName: string; revision: ScheduleRevisionSummary; currentPublication: ScheduleRevisionSummary | null; busy: boolean; onCancel: () => void; onConfirm: () => void }) {
  const dialogRef = useRef<HTMLElement>(null)
  const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => {
    const opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    cancelRef.current?.focus()
    return () => opener?.focus()
  }, [])
  function onKeyDown(event: React.KeyboardEvent<HTMLElement>) {
    if (event.key === 'Escape' && !busy) { event.preventDefault(); onCancel(); return }
    if (event.key !== 'Tab') return
    const controls = [...(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    if (controls.length === 0) { event.preventDefault(); dialogRef.current?.focus(); return }
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && (document.activeElement === first || document.activeElement === dialogRef.current)) { event.preventDefault(); last.focus() }
    else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }
  return <div className="dialog-backdrop"><section ref={dialogRef} className="confirmation-dialog" role="dialog" aria-modal="true" aria-labelledby="abandon-title" tabIndex={-1} onKeyDown={onKeyDown}>
    <h2 id="abandon-title">Revision {revision.revisionNumber} verwerfen?</h2>
    <p>Der Arbeitsstand für {semesterName} wird im Verlauf gespeichert und kann wiederhergestellt werden, solange keine andere Arbeitsrevision besteht.</p>
    <p>{currentPublication ? `Die aktuelle Veröffentlichung, Revision ${currentPublication.revisionNumber}, bleibt sichtbar und unverändert.` : 'Dieses Semester hat keine aktuelle Veröffentlichung.'}</p>
    <div className="dialog-actions"><button ref={cancelRef} type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Abbrechen</button><button type="button" className="destructive-button" disabled={busy} onClick={onConfirm}>{busy ? 'Wird verworfen…' : 'Revision verwerfen'}</button></div>
  </section></div>
}
