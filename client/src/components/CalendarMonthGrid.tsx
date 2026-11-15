import { useState } from 'react'
import { formatCalendarDate } from '../utils/datePresentation'
import { cohortAbbreviation, monthDates, monthEntries, occurrenceFacts } from './calendarTimeGridLayout'
import { type CalendarSurfaceProps } from './CalendarTimeGrid'

export function CalendarMonthGrid({ anchor, workspace, occurrences, selectedRef, onSelect, onDate }: Omit<CalendarSurfaceProps, 'dates'> & { anchor: string; onDate: (date: string) => void }) {
  const [expanded, setExpanded] = useState<Set<string>>(() => new Set())
  return <section aria-label="Monatskalender" className="month-calendar">
    <h3>{new Intl.DateTimeFormat('de-AT', { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(`${anchor}T12:00Z`))}</h3>
    <div className="month-grid-scroll" role="region" aria-label="Monatsraster, horizontal scrollbar" tabIndex={0}>
      <div className="month-grid">
        {['Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag'].map(day => <div className="month-weekday" key={day}>{day}</div>)}
        {monthDates(anchor).map(date => {
          const { entries, affectedCount } = monthEntries(occurrences.filter(o => o.date === date), workspace.validationFindings)
          const isExpanded = expanded.has(date)
          const adjacent = date.slice(0, 7) !== anchor.slice(0, 7)
          return <section key={date} data-month-date={date} className={`month-cell${adjacent ? ' adjacent-month' : ''}`} aria-label={formatCalendarDate(date)}>
            <button type="button" className="month-date-button" aria-label={`${formatCalendarDate(date)} in Tagesansicht öffnen`} onClick={() => onDate(date)}>{new Intl.DateTimeFormat('de-AT', { day: 'numeric', month: 'short', timeZone: 'UTC' }).format(new Date(`${date}T12:00Z`))}{adjacent ? ' · Nachbarmonat' : ''}</button>
            {workspace.holidays.filter(h => h.date === date).map(h => <p className="calendar-holiday" key={h.holidayRef}>Holiday: {h.name}</p>)}
            {affectedCount > 0 && <p className="month-window-findings">⚠ {affectedCount} Termine mit Lehrzeitfensterhinweisen (einschließlich ausgeblendeter Einträge)</p>}
            <ul className="month-entries">{(isExpanded ? entries : entries.slice(0, 3)).map(o => <li key={o.occurrenceRef}><button type="button" className={`calendar-occurrence month-entry ${o.kind}`} data-occurrence-ref={o.occurrenceRef} aria-label={occurrenceFacts(workspace, o)} aria-pressed={selectedRef === o.occurrenceRef} onClick={() => onSelect(o.occurrenceRef)}><span>{o.startTime}–{o.endTime}</span><span className="month-cohort-label" title={o.cohort} aria-label={`Kohorte: ${o.cohort}`}>{cohortAbbreviation(o.cohort)}</span><strong>{workspace.courses.find(c => c.courseRef === o.courseRef)?.name}</strong><span>{o.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'}{o.findingRefs.length ? ' · ⚠ Hinweise' : ''}</span></button></li>)}</ul>
            {entries.length > 3 && <button type="button" className="calendar-date-continuation" aria-expanded={isExpanded} aria-label={`${formatCalendarDate(date)}: ${isExpanded ? 'Weniger Termine anzeigen' : `+${entries.length - 3}, Alle ${entries.length} Termine anzeigen`}`} onClick={() => setExpanded(current => {
              const next = new Set(current)
              if (next.has(date)) next.delete(date)
              else next.add(date)
              return next
            })}>{isExpanded ? 'Weniger Termine anzeigen' : `+${entries.length - 3} · Alle ${entries.length} Termine anzeigen`}</button>}
          </section>
        })}
      </div>
    </div>
  </section>
}
