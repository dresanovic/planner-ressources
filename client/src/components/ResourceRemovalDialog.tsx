import { useEffect, useRef } from 'react'
import type { ResourceUsageAssessment } from '../api/resourceCatalog'

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
    <h2 id="resource-removal-title">Remove {resourceName}?</h2>
    <p>{willInactivate ? 'This resource is protected and will be placed inactive.' : 'This unused resource will be permanently deleted.'}</p>
    {assessment.activeCourses.length > 0 && <section><h3>Active courses</h3><ul>{assessment.activeCourses.map((course) => <li key={course.id}>{course.name}</li>)}</ul></section>}
    {assessment.inactiveCourses.length > 0 && <p>{assessment.inactiveCourses.length} inactive course link{assessment.inactiveCourses.length === 1 ? '' : 's'} will be removed on deletion.</p>}
    <p>{assessment.sessionUsage.draftSessionCount} saved sessions across {assessment.sessionUsage.draftScheduleCount} schedules.</p>
    <p>{assessment.examUsage.examSessionCount} saved exams and {assessment.examUsage.currentConfigurationCount} enabled exam configuration{assessment.examUsage.currentConfigurationCount === 1 ? '' : 's'}.</p>
    <div className="dialog-actions"><button ref={cancelRef} type="button" className="secondary-button" onClick={onClose}>Cancel</button><button type="button" onClick={onConfirm}>{willInactivate ? 'Place inactive' : 'Delete permanently'}</button></div>
  </section></div>
}
