import type { UnavailabilityPeriod } from '../api/resourceCatalog'
import { WEEKDAY_NAMES } from './weekdays'

export function formatUnavailabilityPeriod(period: UnavailabilityPeriod) {
  if (period.kind === 'recurring') return `${period.weekdays.map((day) => WEEKDAY_NAMES[day]).join(', ')} · ${period.startTime}–${period.endTime}`
  const dateLabel = new Intl.DateTimeFormat('en-GB', { day: 'numeric', month: 'short', year: 'numeric', timeZone: 'UTC' })
  return `${dateLabel.format(new Date(`${period.startDate}T00:00:00Z`))} ${period.startTime}–${dateLabel.format(new Date(`${period.endDate}T00:00:00Z`))} ${period.endTime}`
}
