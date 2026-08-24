import { useEffect, useRef, type KeyboardEvent, type ReactNode } from 'react'

export function AccountActionDialog({ title, children, confirmLabel, busy = false, onConfirm, onCancel }: { title: string; children: ReactNode; confirmLabel: string; busy?: boolean; onConfirm: () => void; onCancel: () => void }) {
  const dialogRef = useRef<HTMLDivElement>(null); const cancelRef = useRef<HTMLButtonElement>(null)
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; cancelRef.current?.focus(); return () => previous?.focus() }, [])
  useEffect(() => { if (busy) cancelRef.current?.focus() }, [busy])
  function keyDown(event: KeyboardEvent) { if (event.key === 'Escape') { event.preventDefault(); onCancel(); return } if (event.key !== 'Tab') return; const controls = [...(dialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled])') ?? [])]; if (!controls.length) return; const first = controls[0]; const last = controls.at(-1)!; if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus() } else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus() } }
  return <div className="dialog-backdrop"><div ref={dialogRef} className="account-action-dialog" role="dialog" aria-modal="true" aria-labelledby="account-action-title" aria-busy={busy || undefined} onKeyDown={keyDown}><h2 id="account-action-title">{title}</h2>{children}<div className="auth-actions"><button ref={cancelRef} type="button" onClick={onCancel}>{busy ? 'Dialog schließen' : 'Abbrechen'}</button><button type="button" disabled={busy} onClick={onConfirm}>{confirmLabel}</button></div></div></div>
}
