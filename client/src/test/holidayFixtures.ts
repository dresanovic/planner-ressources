import type { HolidayRecord } from '../api/holidayCalendar'

export const winterHoliday: HolidayRecord = {
  id: 1,
  date: '2026-12-25',
  name: 'Winter Holiday',
  revision: 1,
}

export const staleHolidayError = {
  code: 'STALE_REVISION',
  message: 'This holiday changed since it was opened. Refresh and try again.',
  field: null,
  meta: { currentRevision: 2 },
}

export const duplicateHolidayError = {
  code: 'DUPLICATE_HOLIDAY_DATE',
  message: 'Another holiday already uses this date.',
  field: 'date',
}

export const holidayGenerationEvidence = {
  code: 'INSTITUTION_HOLIDAY',
  message: 'Winter Holiday on 2026-12-25 is unavailable for automatic scheduling.',
  holidayDate: '2026-12-25',
  holidayName: 'Winter Holiday',
}

export const holidayReviewAlert = {
  code: 'INSTITUTION_HOLIDAY' as const,
  message: 'Winter Holiday on 2026-12-25 is an institution holiday.',
  holidayDate: '2026-12-25',
  holidayName: 'Winter Holiday',
  relatedSessions: [],
}
