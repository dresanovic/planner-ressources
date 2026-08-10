import { useEffect, useRef } from 'react'
import type { ResourceUsageAssessment } from '../api/resourceCatalog'
import { label } from '../config/terminology'

export function ResourceRemovalDialog({ resourceName, assessment, onConfirm, onClose }: {
  resourceName: string
  assessment: ResourceUsageAssessment
  onConfirm: () => void
  onClose: () => void
}) {
  const cancelRef = useRef<HTMLButtonElement>(null)
  const dialogRef = useRef<HTMLElement>(null)
  const closeRef = useRef(onClose)
  useEffect(() => { closeRef.current = onClose }, [onClose])
  useEffect(() => {
    const previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
    cancelRef.current?.focus()
    function focusableControls() {
      return Array.from(dialogRef.current?.querySelectorAll<HTMLElement>('button:not([disabled]), [href], input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])') ?? [])
    }
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        event.preventDefault()
        closeRef.current()
        return
      }
      if (event.key !== 'Tab') return
      const controls = focusableControls()
      if (!controls.length) return
      const first = controls[0]
      const last = controls[controls.length - 1]
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus()
      }
    }
    function containFocus(event: FocusEvent) {
      if (dialogRef.current && !dialogRef.current.contains(event.target as Node)) cancelRef.current?.focus()
    }
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('focusin', containFocus)
    return () => {
      document.removeEventListener('keydown', handleKeyDown)
      document.removeEventListener('focusin', containFocus)
      previousFocus?.focus()
    }
  }, [])
  const willInactivate = assessment.disposition === 'inactivate'
  return <div className="dialog-backdrop" role="presentation"><section ref={dialogRef} className="replacement-dialog resource-removal-dialog" role="dialog" aria-modal="true" aria-labelledby="resource-removal-title">
    <h2 id="resource-removal-title">„{resourceName}“ entfernen?</h2>
    <p>{willInactivate ? 'Diese Ressource wird noch verwendet und deshalb inaktiv gesetzt.' : 'Diese ungenutzte Ressource wird dauerhaft gelöscht.'}</p>
    {assessment.activeCourses.length > 0 && <section><h3>Aktive {label('course.plural')}</h3><ul>{assessment.activeCourses.map((course) => <li key={course.id}>{course.name}</li>)}</ul></section>}
    {assessment.inactiveCourses.length > 0 && <p>{assessment.inactiveCourses.length} {assessment.inactiveCourses.length === 1 ? `inaktive Zuordnung zu einer ${label('course.singular')} wird` : `inaktive Zuordnungen zu ${label('course.plural')} werden`} beim Löschen entfernt.</p>}
    <p>{assessment.sessionUsage.draftSessionCount} gespeicherte Termine in {assessment.sessionUsage.draftScheduleCount} {assessment.sessionUsage.draftScheduleCount === 1 ? 'Planung' : 'Planungen'}.</p>
    <p>{assessment.examUsage.examSessionCount} {assessment.examUsage.examSessionCount === 1 ? 'gespeicherte Prüfung' : 'gespeicherte Prüfungen'} und {assessment.examUsage.currentConfigurationCount} {assessment.examUsage.currentConfigurationCount === 1 ? 'aktivierte Prüfungskonfiguration' : 'aktivierte Prüfungskonfigurationen'}.</p>
    <div className="dialog-actions"><button ref={cancelRef} type="button" className="secondary-button" onClick={onClose}>Abbrechen</button><button type="button" onClick={onConfirm}>{willInactivate ? 'Inaktiv setzen' : 'Dauerhaft löschen'}</button></div>
  </section></div>
}
