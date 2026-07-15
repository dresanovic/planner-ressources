export const WEEKDAY_NAMES = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
] as const

export function weeklySortOrder(weekday: number, startTime: string): number {
  const [hours = 0, minutes = 0] = startTime.split(':').map(Number)
  return weekday * 24 * 60 + hours * 60 + minutes
}
