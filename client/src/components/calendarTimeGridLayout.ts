import { formatCalendarDate } from '../utils/datePresentation'
import { calendarFindingLabel } from './calendarFindingLabel'
import type { SourceWindow, TeachingWindowContext, WorkspaceOccurrence, ValidationFinding, WorkspaceCourse, LoadedCalendarWorkspace } from '../api/calendarWorkspace'

export const PIXELS_PER_HOUR = 72
export const DAY_HEIGHT = 24 * PIXELS_PER_HOUR

export function calendarGroups(courses: WorkspaceCourse[], contexts: TeachingWindowContext[] = []) {
  const groups = new Map<string, { key: string; label: string; courses: WorkspaceCourse[]; context?: TeachingWindowContext }>()
  for (const course of courses) {
    const context = contexts.find(c => c.courseRef === course.courseRef)
    const identity = course.cohortCalendarRef ?? `unknown:${course.courseRef}`
    const profile = context ? JSON.stringify({ availability: context.availability, basis: context.basis,
      isCustom: context.isCustom, sourceRevision: context.sourceRevision, start: context.planningStartDate,
      end: context.planningEndDate, windows: context.windows, days: context.days }) : course.courseRef
    const key = JSON.stringify([course.cohort, identity, profile])
    const group = groups.get(key)
    if (group) group.courses.push(course)
    else groups.set(key, { key, label: `${course.cohortCalendar} (${course.cohortCalendarRef ?? `Identität unbekannt · ${course.name}`})`, courses: [course], context })
  }
  return [...groups.values()]
}
// Cohorts currently have a name only; keep existing short codes and retain year/semester suffixes.
export function cohortAbbreviation(name: string): string {
  if (name.length <= 16) return name
  return name.split(/\s+/).map(word => {
    if (/^(?:[A-ZÄÖÜ\d&/.-]+|[A-Z][a-z]?[A-Z][a-z]?)$/.test(word)) return word
    if (/^\d/.test(word)) return word.replace(/Semester/gi, 'Sem.')
    return word[0]?.toLocaleUpperCase('de-AT') ?? ''
  }).join(' ').replace(/(?<=\b[A-Z]) (?=[A-Z]\b)/g, '')
}

export const minuteOffset = (clock: string) => {
  const [h, m, s = '0'] = clock.split(':')
  return Number(h) * 60 + Number(m) + Number(s) / 60
}
export const minuteClock = (minute: number) => `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(Math.floor(minute % 60)).padStart(2, '0')}`

export function enumerateDates(start: string, end: string) {
  const dates: string[] = []
  for (let day = new Date(`${start}T12:00:00Z`); day.toISOString().slice(0, 10) <= end; day = new Date(day.getTime() + 86400000)) {
    dates.push(day.toISOString().slice(0, 10))
  }
  return dates
}

export function monthDates(anchor: string) {
  const start = new Date(`${anchor.slice(0, 7)}-01T12:00:00Z`)
  const end = new Date(start)
  end.setUTCMonth(end.getUTCMonth() + 1, 0)
  start.setUTCDate(start.getUTCDate() - (start.getUTCDay() + 6) % 7)
  end.setUTCDate(end.getUTCDate() + (7 - end.getUTCDay()) % 7)
  return enumerateDates(start.toISOString().slice(0, 10), end.toISOString().slice(0, 10))
}

export function monthEntries(occurrences: WorkspaceOccurrence[], findings: ValidationFinding[]) {
  return {
    entries: [...occurrences].sort((a, b) => minuteOffset(a.startTime) - minuteOffset(b.startTime)
      || minuteOffset(a.endTime) - minuteOffset(b.endTime) || a.occurrenceRef.localeCompare(b.occurrenceRef)),
    affectedCount: new Set(occurrences.filter(o => hasWindowFinding(o, findings)).map(o => o.occurrenceRef)).size,
  }
}

type Interval = { occurrenceRef: string; startTime: string; endTime: string }
export function layoutIntervals<T extends Interval>(intervals: T[]) {
  const sorted = [...intervals].sort((a, b) => minuteOffset(a.startTime) - minuteOffset(b.startTime)
    || minuteOffset(a.endTime) - minuteOffset(b.endTime) || a.occurrenceRef.localeCompare(b.occurrenceRef))
  const result: (T & { top: number; height: number; lane: number; laneCount: number })[] = []
  let group: typeof result = []
  let ends: number[] = []
  let groupEnd = -1
  function finish() {
    for (const block of group) block.laneCount = ends.length
    group = []
    ends = []
  }
  for (const item of sorted) {
    const start = minuteOffset(item.startTime), end = minuteOffset(item.endTime)
    if (start >= groupEnd) finish()
    let lane = ends.findIndex(value => value <= start)
    if (lane < 0) lane = ends.length
    ends[lane] = end
    const block = { ...item, top: start * 1.2, height: (end - start) * 1.2, lane, laneCount: 1 }
    result.push(block)
    group.push(block)
    groupEnd = Math.max(group.length === 1 ? end : groupEnd, end)
  }
  finish()
  return result
}

export function applicableWindows(context: TeachingWindowContext | undefined, date: string): SourceWindow[] | null {
  if (context?.availability !== 'available') return null
  const day = context.days.find(day => day.date === date)
  if (!day) return null
  return context.windows.filter(w => day.applicableWindowRefs.includes(w.windowRef))
}

export function outsideIntervals(startTime: string, endTime: string, windows: Pick<SourceWindow, 'startTime' | 'endTime'>[] | null) {
  if (windows === null) return []
  const end = minuteOffset(endTime)
  let cursor = minuteOffset(startTime)
  const outside: { start: number; end: number; minutes: number }[] = []
  for (const window of [...windows].sort((a, b) => minuteOffset(a.startTime) - minuteOffset(b.startTime))) {
    const start = Math.min(end, minuteOffset(window.startTime))
    if (start > cursor) outside.push({ start: cursor, end: start, minutes: start - cursor })
    cursor = Math.max(cursor, minuteOffset(window.endTime))
    if (cursor >= end) break
  }
  if (cursor < end) outside.push({ start: cursor, end, minutes: end - cursor })
  return outside
}

export function hasWindowFinding(occurrence: WorkspaceOccurrence, findings: ValidationFinding[]) {
  return findings.some(f => occurrence.findingRefs.includes(f.findingRef) && f.details.kind === 'other'
    && ['COHORT_CALENDAR_WINDOW_VIOLATION', 'GENERATION_CONSTRAINT_VIOLATION'].includes(f.details.issueCode))
}


export function occurrenceFacts(workspace: LoadedCalendarWorkspace, occurrence: WorkspaceOccurrence) {
  const course = workspace.courses.find(c => c.courseRef === occurrence.courseRef)
  const context = workspace.teachingWindowContexts?.find(c => c.courseRef === occurrence.courseRef)
  const windows = occurrence.kind === 'exam' ? null : applicableWindows(context, occurrence.date)
  const findings = workspace.validationFindings.filter(f => occurrence.findingRefs.includes(f.findingRef))
  const outside = hasWindowFinding(occurrence, findings) && occurrence.kind === 'teaching'
    ? outsideIntervals(occurrence.startTime, occurrence.endTime, windows) : []
  return [
    `${formatCalendarDate(occurrence.date)} · ${course?.cohortCalendar ?? occurrence.cohort} · ${course?.name ?? occurrence.courseRef}`,
    `${occurrence.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'} ${occurrence.startTime}–${occurrence.endTime}`,
    `Raum: ${workspace.filterFacets.rooms.find(r => r.value === occurrence.roomRef)?.label ?? (occurrence.kind === 'exam' ? occurrence.assignedRoomName : 'Nicht verfügbar')}`,
    occurrence.kind === 'exam' ? 'Lehrzeitfenster für Prüfung nicht anwendbar.' : windows === null ? 'Lehrzeitfenster unbekannt.'
      : windows.length ? `Erlaubte Lehrstunden: ${windows.map(w => `${w.startTime}–${w.endTime}${w.isIntensive ? ' (Intensiv)' : ''}`).join(', ')}` : 'Keine erlaubten Lehrstunden.',
    ...outside.map(i => `Außerhalb: ${minuteClock(i.start)}–${minuteClock(i.end)} · ${Math.floor(i.minutes / 60)} Std. ${i.minutes % 60} Min.`),
    ...(windows !== null && outside.length === 0 && findings.some(f => f.details.kind === 'other'
      && f.details.issueCode === 'COHORT_CALENDAR_WINDOW_VIOLATION')
      ? ['Bestehender Hinweis: Der Termin passt nicht vollständig in ein einzelnes Quellfenster. Getrennte Fenster dürfen nicht zu einer Erlaubnis zusammengefügt werden.'] : []),
    context?.basis === 'captured_published' ? 'Erfasste Veröffentlichung' : context?.basis === 'current_working' ? 'Aktuelle Arbeitsrevision' : 'Herkunft unbekannt',
    ...findings.map(calendarFindingLabel),
  ].join(' · ')
}

