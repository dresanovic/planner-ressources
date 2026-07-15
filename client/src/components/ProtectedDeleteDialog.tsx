import { useEffect, useRef, type KeyboardEvent } from 'react'
import type { UsageSummary } from '../api/academicCatalog'

export function ProtectedDeleteDialog({ name, usage, canArchive = true, onClose, onDelete, onArchive }: { name: string; usage: UsageSummary; canArchive?: boolean; onClose: () => void; onDelete: () => void; onArchive: () => void }) {
  const dialog = useRef<HTMLDivElement>(null)
  useEffect(() => {
    const previous = document.activeElement as HTMLElement | null
    dialog.current?.querySelector<HTMLButtonElement>('button')?.focus()
    return () => previous?.focus()
  }, [])
  function keyDown(event: KeyboardEvent) {
    if (event.key === 'Escape') onClose()
    if (event.key !== 'Tab' || !dialog.current) return
    const controls = Array.from(dialog.current.querySelectorAll<HTMLElement>('button:not(:disabled)'))
    if (!controls.length) return
    const first = controls[0], last = controls[controls.length - 1]
    if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() }
    if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() }
  }
  const dependent = usage.blockers.filter((blocker) => blocker.kind === 'dependent')
  const saved = usage.blockers.filter((blocker) => blocker.kind === 'saved_schedule')
  return <div className="dialog-backdrop"><div ref={dialog} role="dialog" aria-modal="true" aria-labelledby="delete-title" className="replacement-dialog protected-delete-dialog" onKeyDown={keyDown}><h2 id="delete-title">Delete {name}?</h2>{dependent.length > 0 && <section><h3>Dependent records</h3>{dependent.map((blocker) => <p key={`${blocker.type}-${blocker.count}`}>{blocker.message}</p>)}</section>}{saved.length > 0 && <section><h3>Saved schedules</h3>{saved.map((blocker) => <p key={`${blocker.type}-${blocker.count}`}>{blocker.message}</p>)}</section>}{!usage.canDelete && <p>Permanent deletion is protected. {canArchive ? 'Archiving keeps dependent records unchanged.' : 'This record is already inactive.'}</p>}<div className="dialog-actions"><button type="button" className="secondary-button" onClick={onClose}>Cancel</button>{canArchive && <button type="button" className="secondary-button" onClick={onArchive}>Archive</button>}<button type="button" disabled={!usage.canDelete} onClick={onDelete}>Delete permanently</button></div></div></div>
}
