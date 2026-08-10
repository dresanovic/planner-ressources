import type { UnavailabilityPeriod } from '../api/resourceCatalog'
import { WEEKDAY_NAMES } from './weekdays'
import { formatCalendarDate } from './datePresentation'

export function formatUnavailabilityPeriod(period: UnavailabilityPeriod) {
  if (period.kind === 'recurring') return `${period.weekdays.map((day) => WEEKDAY_NAMES[day]).join(', ')} · ${period.startTime}–${period.endTime}`
  return `${formatCalendarDate(period.startDate)} ${period.startTime}–${formatCalendarDate(period.endDate)} ${period.endTime}`
}
