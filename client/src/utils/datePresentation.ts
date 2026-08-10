const ISO_DATE = /^(\d{4})-(\d{2})-(\d{2})$/
const EUROPEAN_DATE = /^(\d{2})\.(\d{2})\.(\d{4})$/
const VIENNA_TIME_ZONE = 'Europe/Vienna'

function isLeapYear(year: number): boolean {
  return year % 4 === 0 && (year % 100 !== 0 || year % 400 === 0)
}

function isCalendarDay(year: number, month: number, day: number): boolean {
  if (year < 1 || year > 9999 || month < 1 || month > 12 || day < 1) return false
  const monthLengths = [31, isLeapYear(year) ? 29 : 28, 31, 30, 31, 30, 31, 31, 30, 31, 30, 31]
  return day <= monthLengths[month - 1]
}

export function isIsoCalendarDate(value: string): boolean {
  const match = ISO_DATE.exec(value)
  if (!match) return false
  return isCalendarDay(Number(match[1]), Number(match[2]), Number(match[3]))
}

export function formatCalendarDate(value: string): string {
  const match = ISO_DATE.exec(value)
  if (!match || !isCalendarDay(Number(match[1]), Number(match[2]), Number(match[3]))) {
    throw new RangeError('Invalid ISO calendar date')
  }
  return `${match[3]}.${match[2]}.${match[1]}`
}

export function parseEuropeanDate(value: string): string | null {
  const match = EUROPEAN_DATE.exec(value)
  if (!match) return null
  const day = Number(match[1])
  const month = Number(match[2])
  const year = Number(match[3])
  if (!isCalendarDay(year, month, day)) return null
  return `${match[3]}-${match[2]}-${match[1]}`
}

export function formatCalendarDateRange(
  start: string | null | undefined,
  end: string | null | undefined,
): string {
  if (start && end) return `${formatCalendarDate(start)}–${formatCalendarDate(end)}`
  if (start) return `ab ${formatCalendarDate(start)}`
  if (end) return `bis ${formatCalendarDate(end)}`
  return 'Zeitraum nicht verfügbar'
}

function partsForVienna(value: Date): Record<string, string> {
  const formatter = new Intl.DateTimeFormat('de-AT', {
    timeZone: VIENNA_TIME_ZONE,
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
    hourCycle: 'h23',
  })
  return Object.fromEntries(
    formatter.formatToParts(value).map((part) => [part.type, part.value]),
  )
}

export function formatViennaDateTime(value: string | Date): string {
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) throw new RangeError('Invalid timestamp')
  const parts = partsForVienna(date)
  return `${parts.day}.${parts.month}.${parts.year}, ${parts.hour}:${parts.minute}`
}

export function institutionLocalToday(now: Date = new Date()): string {
  if (Number.isNaN(now.getTime())) throw new RangeError('Invalid timestamp')
  const parts = partsForVienna(now)
  return `${parts.year}-${parts.month}-${parts.day}`
}
