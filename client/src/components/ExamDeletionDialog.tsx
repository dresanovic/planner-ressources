import { useEffect, useRef } from 'react'
import type { KeyboardEvent } from 'react'
import type { ExamSession } from '../api/examScheduling'
import { formatCalendarDate } from '../utils/datePresentation'

export function ExamDeletionDialog({ courseName, exam, busy, error, onCancel, onConfirm }: { courseName: string; exam: ExamSession; busy: boolean; error?: string; onCancel: () => void; onConfirm: () => Promise<void> }) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLElement>(null)
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; cancelRef.current?.focus(); return () => previous?.focus() }, [])
  function handleKeys(event: KeyboardEvent) { if (event.key==='Escape'&&!busy) onCancel(); if (event.key==='Tab') { const controls=[...(dialogRef.current?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)')??[])]; if (!controls.length) return; const current=controls.indexOf(document.activeElement as HTMLButtonElement); const next=event.shiftKey ? (current <= 0 ? controls.length-1 : current-1) : (current === controls.length-1 ? 0 : current+1); event.preventDefault(); controls[next].focus() } }
  return <div className="dialog-backdrop" onMouseDown={(event)=>{if(event.target===event.currentTarget&&!busy)onCancel()}}><section ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="exam-delete-title" className="replacement-dialog" onKeyDown={handleKeys}><h2 id="exam-delete-title">Prüfung löschen?</h2><p><strong>{courseName}</strong> · {exam.configurationIdentifier}</p><p>{formatCalendarDate(exam.date)} · {exam.startTime}–{exam.endTime}</p><p className="deletion-consequence">{exam.lifecycleStatus==='active'?'Die Konfiguration wird wieder aktiv und kann neu eingeplant werden.':'Nur dieser historische Prüfungstermin wird entfernt; die aktuelle Konfiguration bleibt unverändert.'}</p>{error&&<div role="alert" className="alert-item">Die Prüfung konnte nicht gelöscht werden. Laden Sie den aktuellen Stand neu und prüfen Sie den Termin vor einem weiteren Versuch.</div>}<div className="dialog-actions"><button ref={cancelRef} type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Abbrechen</button><button type="button" className="destructive-button" disabled={busy} onClick={()=>void onConfirm()}>{busy?'Löschen…':'Prüfung löschen'}</button></div></section></div>
}
