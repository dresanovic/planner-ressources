import type { LoadedCalendarWorkspace } from '../api/calendarWorkspace'
import type { ExamSession } from '../api/examScheduling'
import { formatCalendarDate, formatCalendarDateRange } from '../utils/datePresentation'
import type { UserProblem } from '../utils/userProblems'

export function outsideRecommendedWindowProblem({
  exam,
  courseName,
  saved,
  editable,
}: {
  exam: ExamSession
  courseName: string
  saved: boolean
  editable: boolean
}): UserProblem {
  const savedText = saved
    ? 'Die Planung bleibt gespeichert und nutzbar.'
    : 'Der neue Termin ist noch nicht gespeichert.'
  const guidance = editable
    ? 'Verwenden Sie „Bearbeiten“, um den Termin zu ändern. Sie können die Abweichung auch bewusst beibehalten.'
    : 'Prüfen Sie den Termin und geben Sie bei Bedarf über die vorhandene Rückmeldemöglichkeit Bescheid; die Abweichung kann bewusst beibehalten werden.'
  return {
    key: `outside-recommended-window-${exam.id}`,
    tone: 'warning',
    title: `Prüfung für „${courseName}“ außerhalb des empfohlenen Zeitraums`,
    details: [
      `Der Termin am ${formatCalendarDate(exam.date)} liegt außerhalb des empfohlenen Zeitraums ${formatCalendarDateRange(exam.recommendedStartDate, exam.recommendedEndDate)}.`,
      `Dieser Hinweis ist nicht blockierend. ${savedText}`,
      guidance,
    ],
  }
}

export function calendarFindingLabel(
  finding: LoadedCalendarWorkspace['validationFindings'][number],
): string {
  const details = finding.details
  if (details.kind === 'conflict') {
    const subject = details.conflictType === 'lecturer' ? 'Lehrperson' : details.conflictType === 'room' ? 'Raum' : 'Kohorte'
    return `${subject} ist in mehreren Terminen gleichzeitig eingeplant. Prüfen und ändern Sie einen der betroffenen Termine.`
  }
  if (details.kind === 'capacity') {
    return `Der Raum „${details.roomName}“ hat ${details.currentCapacity} Plätze; benötigt werden ${details.requiredCapacity}. Wählen Sie einen ausreichend großen Raum.`
  }
  if (details.kind === 'holiday') {
    return `Der Termin liegt am Feiertag „${details.holidayName}“ (${formatCalendarDate(details.holidayDate)}). Prüfen Sie den Termin und ändern oder bestätigen Sie ihn bewusst.`
  }
  return 'Für diesen Termin liegt ein prüfbarer Hinweis vor. Öffnen Sie die Details und prüfen Sie die betroffenen Angaben.'
}
