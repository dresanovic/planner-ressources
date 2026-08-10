import { useEffect, useRef, type KeyboardEvent } from 'react'
import type { UsageSummary } from '../api/academicCatalog'

function dependentLabel(type: string, count: number): string {
  const labels: Record<string, [string, string]> = {
    course: ['abhängiger Datensatz', 'abhängige Datensätze'],
    cohort: ['abhängige Kohorte', 'abhängige Kohorten'],
    lecturer: ['abhängige Zuordnung', 'abhängige Zuordnungen'],
    room: ['abhängige Zuordnung', 'abhängige Zuordnungen'],
    semester: ['abhängiges Semester', 'abhängige Semester'],
  }
  const [singular, plural] = labels[type] ?? ['abhängiger Datensatz', 'abhängige Datensätze']
  return `${count} ${count === 1 ? singular : plural}`
}

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
  return <div className="dialog-backdrop"><div ref={dialog} role="dialog" aria-modal="true" aria-labelledby="delete-title" className="replacement-dialog protected-delete-dialog" onKeyDown={keyDown}><h2 id="delete-title">„{name}“ löschen?</h2>{dependent.length > 0 && <section><h3>Abhängige Datensätze</h3>{dependent.map((blocker) => <p key={`${blocker.type}-${blocker.count}`}>{dependentLabel(blocker.type, blocker.count)} verhindert das dauerhafte Löschen. Entfernen Sie zuerst die Zuordnung oder archivieren Sie den Datensatz.</p>)}</section>}{saved.length > 0 && <section><h3>Gespeicherte Planungen</h3>{saved.map((blocker) => <p key={`${blocker.type}-${blocker.count}`}>Der Datensatz wird in {blocker.count} gespeicherten {blocker.count === 1 ? 'Planung' : 'Planungen'} verwendet. Die Planung bleibt unverändert; archivieren Sie den Datensatz, wenn er nicht mehr auswählbar sein soll.</p>)}</section>}{!usage.canDelete && <p>Das dauerhafte Löschen ist blockiert. {canArchive ? 'Beim Archivieren bleiben abhängige Datensätze und gespeicherte Planungen unverändert.' : 'Dieser Datensatz ist bereits inaktiv.'}</p>}<div className="dialog-actions"><button type="button" className="secondary-button" onClick={onClose}>Abbrechen</button>{canArchive && <button type="button" className="secondary-button" onClick={onArchive}>Archivieren</button>}<button type="button" disabled={!usage.canDelete} onClick={onDelete}>Dauerhaft löschen</button></div></div></div>
}
