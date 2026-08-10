import { useEffect, useRef } from 'react'

import type { PublicationCondition, PublicationPreparation } from '../api/scheduleLifecycle'
import { formatCalendarDate, formatCalendarDateRange, isIsoCalendarDate } from '../utils/datePresentation'

function lifecycleStateLabel(state: PublicationPreparation['targetRevision']['state']): string {
  return ({ draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung', published: 'Veröffentlicht', superseded: 'Ersetzt', abandoned: 'Verworfen' })[state]
}

function stringDetail(condition: PublicationCondition, key: string): string | null {
  const value = condition.details[key]
  return typeof value === 'string' && value.trim() ? value : null
}

function dateDetail(condition: PublicationCondition, key: string): string | null {
  const value = stringDetail(condition, key)
  return value && isIsoCalendarDate(value) ? value : null
}

function teachingAlertReason(code: string | null, holidayName: string | null): string {
  const reasons: Record<string, string> = {
    LECTURER_OVERLAP: 'Die Lehrperson ist zeitgleich einem anderen Termin zugeordnet.',
    ROOM_OVERLAP: 'Der Raum ist zeitgleich einem anderen Termin zugeordnet.',
    COHORT_OVERLAP: 'Die Kohorte hat zeitgleich einen anderen Termin.',
    ROOM_CAPACITY: 'Die Raumkapazität ist kleiner als die Kohortengröße.',
    GENERATION_CONSTRAINT_VIOLATION: 'Der Termin liegt außerhalb der aktuell gespeicherten Erzeugungsregeln.',
    STUDY_TYPE_WINDOW_VIOLATION: 'Der Termin liegt außerhalb des Zeitfensters der Studienart.',
    VALIDATION_DATA_MISSING: 'Erforderliche Daten für die vollständige Prüfung des Termins fehlen.',
    LECTURER_UNAVAILABLE: 'Die Lehrperson ist für diesen Zeitraum als nicht verfügbar eingetragen.',
    ROOM_UNAVAILABLE: 'Der Raum ist für diesen Zeitraum als nicht verfügbar eingetragen.',
    LECTURER_INELIGIBLE: 'Die zugeordnete Lehrperson ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.',
    ROOM_INELIGIBLE: 'Der zugeordnete Raum ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.',
    INSTITUTION_HOLIDAY: holidayName ? `Der Termin liegt am Hochschulfeiertag „${holidayName}“.` : 'Der Termin liegt an einem Hochschulfeiertag.',
  }
  return code && reasons[code] ? reasons[code] : 'Eine bekannte Planungsregel ist für diesen Termin nicht mehr erfüllt.'
}

function examIssueReason(code: string | null, holidayName: string | null): string {
  const reasons: Record<string, string> = {
    FINAL_TEACHING_SESSION_MISSING: 'Der letzte Lehrtermin ist nicht mehr vorhanden.',
    INVALID_EXAM_INTERVAL: 'Der Prüfungszeitraum endet nicht gültig am selben Kalendertag.',
    OUTSIDE_SEMESTER: 'Der Prüfungstermin liegt außerhalb des Semesters.',
    BEFORE_FINAL_TEACHING: 'Die Prüfung beginnt vor dem Ende des letzten Lehrtermins.',
    RESPONSIBLE_LECTURER_INELIGIBLE: 'Die verantwortliche Lehrperson ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.',
    ROOM_INELIGIBLE: 'Der Raum ist nicht aktiv oder für diese Lehrveranstaltung nicht freigegeben.',
    INSUFFICIENT_ROOM_CAPACITY: 'Die Raumkapazität reicht für die Prüfung nicht aus.',
    LECTURER_UNAVAILABLE: 'Die Lehrperson ist für den gesamten Prüfungszeitraum nicht verfügbar.',
    ROOM_UNAVAILABLE: 'Der Raum ist für den gesamten Prüfungszeitraum nicht verfügbar.',
    INSTITUTION_HOLIDAY: holidayName ? `Die Prüfung liegt am Hochschulfeiertag „${holidayName}“.` : 'Die Prüfung liegt an einem Hochschulfeiertag.',
    LECTURER_OCCUPIED: 'Die Lehrperson ist zeitgleich einem anderen Termin zugeordnet.',
    ROOM_OCCUPIED: 'Der Raum ist zeitgleich einem anderen Termin zugeordnet.',
    COHORT_OCCUPIED: 'Die Kohorte hat zeitgleich einen anderen Termin.',
  }
  return code && reasons[code] ? reasons[code] : 'Eine bekannte Gültigkeitsregel ist für diese Prüfung nicht mehr erfüllt.'
}

function conditionText(condition: PublicationCondition): string {
  const remaining = typeof condition.details.remainingUnits === 'number' ? condition.details.remainingUnits : null
  const courseName = stringDetail(condition, 'courseName')
  if (condition.code === 'course_units_remaining' && remaining != null) {
    const affected = courseName ? `Lehrveranstaltung „${courseName}“` : 'Eine Lehrveranstaltung'
    return `${affected}: ${remaining} Lehreinheiten sind noch offen. Dies ist nicht blockierend; Sie können die Planung vervollständigen oder die Veröffentlichung bewusst fortsetzen.`
  }
  if (condition.code === 'teaching_validation_alert') {
    const sessionDate = dateDetail(condition, 'sessionDate')
    const affected = courseName ? `Lehrtermin für „${courseName}“` : 'Ein Lehrtermin'
    const when = sessionDate ? ` am ${formatCalendarDate(sessionDate)}` : ''
    return `${affected}${when}: ${teachingAlertReason(stringDetail(condition, 'alertCode'), stringDetail(condition, 'holidayName'))} Der Hinweis ist nicht blockierend; bearbeiten Sie den Termin oder veröffentlichen Sie den geprüften Stand bewusst.`
  }
  if (condition.code === 'exam_validity_issue') {
    const examDate = dateDetail(condition, 'examDate')
    const affected = courseName ? `Prüfung für „${courseName}“` : 'Eine Prüfung'
    const when = examDate ? ` am ${formatCalendarDate(examDate)}` : ''
    return `${affected}${when}: ${examIssueReason(stringDetail(condition, 'issueCode'), stringDetail(condition, 'holidayName'))} Der Hinweis ist nicht blockierend; bearbeiten Sie die Prüfung oder veröffentlichen Sie den geprüften Stand bewusst.`
  }
  if (condition.code === 'enabled_exam_unscheduled') {
    const affected = courseName ? `Für „${courseName}“` : 'Für eine Lehrveranstaltung'
    return `${affected} ist eine Prüfung aktiviert, aber noch kein Prüfungstermin geplant. Dies ist nicht blockierend; planen Sie die Prüfung oder veröffentlichen Sie den Stand bewusst ohne Prüfungstermin.`
  }
  if (condition.code === 'exam_outside_recommendation') {
    const examDate = dateDetail(condition, 'examDate')
    const start = dateDetail(condition, 'recommendedStartDate')
    const end = dateDetail(condition, 'recommendedEndDate')
    if (courseName && examDate && start && end) {
      return `Prüfung für „${courseName}“: Der Termin am ${formatCalendarDate(examDate)} liegt außerhalb des empfohlenen Zeitraums ${formatCalendarDateRange(start, end)}. Der Hinweis ist nicht blockierend und die Planung bleibt gespeichert. Sie können den Termin vor der Veröffentlichung bearbeiten oder bewusst beibehalten.`
    }
    return 'Eine Prüfung liegt außerhalb ihres empfohlenen Zeitraums. Der Hinweis ist nicht blockierend und die Planung bleibt gespeichert. Prüfen Sie den Termin und bearbeiten oder behalten Sie ihn bewusst bei.'
  }
  return 'Eine bekannte nicht blockierende Bedingung liegt vor. Prüfen Sie die betroffene Planung und veröffentlichen Sie sie bewusst oder bearbeiten Sie sie zuvor.'
}

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
    ? 'Damit entsteht die erste Veröffentlichung des Semesters.'
    : `Damit wird die veröffentlichte Revision ${preparation.currentPublication?.revisionNumber} ersetzt.`
  return (
    <div className="modal-backdrop">
      <div ref={dialogRef} role="dialog" aria-modal="true" aria-labelledby="publication-title" className="confirmation-dialog" tabIndex={-1} onKeyDown={onKeyDown}>
        <p className="eyebrow">{preparation.semesterName}</p>
        <h2 id="publication-title">Revision {preparation.targetRevision.revisionNumber} veröffentlichen</h2>
        <p>Aktueller Status: <strong>{lifecycleStateLabel(preparation.targetRevision.state)}</strong>.</p>
        <p>{consequence}</p>
        <p>{preparation.scheduledUnits} von {preparation.totalUnits} Lehreinheiten sind geplant; {preparation.remainingUnits} sind noch offen.</p>
        {preparation.conditions.length > 0 ? <><p>Diese Hinweise verhindern die Veröffentlichung nicht:</p><ul className="publication-conditions">{preparation.conditions.map((condition, index) => <li key={`${condition.code}-${condition.sourceSessionId ?? index}`}>{conditionText(condition)}</li>)}</ul></> : <p>Es wurden keine bekannten nicht blockierenden Hinweise gefunden.</p>}
        <div className="dialog-actions">
          <button type="button" className="secondary-button" disabled={busy} onClick={onCancel}>Abbrechen</button>
          <button type="button" disabled={busy} onClick={onConfirm}>{busy ? 'Veröffentlichung läuft…' : 'Bewusst veröffentlichen'}</button>
        </div>
      </div>
    </div>
  )
}
