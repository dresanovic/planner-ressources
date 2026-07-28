import type { LoadedCalendarWorkspace } from '../api/calendarWorkspace'

export function calendarFindingLabel(
  finding: LoadedCalendarWorkspace['validationFindings'][number],
): string {
  const details = finding.details
  if (details.kind === 'conflict') {
    return `${details.conflictType} conflict · ${details.occurrenceRefs.join(', ')}`
  }
  if (details.kind === 'capacity') {
    return `${details.roomName} capacity ${details.currentCapacity}; ${details.requiredCapacity} required`
  }
  if (details.kind === 'holiday') {
    return `${details.holidayName} · ${details.holidayDate}`
  }
  return details.issueCode.replaceAll('_', ' ')
}
