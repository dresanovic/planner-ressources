import { useEffect, useId, useRef } from 'react'
import type { LoadedCalendarWorkspace, WorkspaceCourse, WorkspaceOccurrence, TeachingWindowContext } from '../api/calendarWorkspace'
import { formatCalendarDate } from '../utils/datePresentation'
import { applicableWindows, calendarGroups, DAY_HEIGHT, hasWindowFinding, layoutIntervals, minuteOffset, occurrenceFacts, outsideIntervals, minuteClock } from './calendarTimeGridLayout'

export type CalendarSurfaceProps = {
  dates: string[]
  workspace: LoadedCalendarWorkspace
  occurrences: WorkspaceOccurrence[]
  courses: WorkspaceCourse[]
  selectedRef: string | null
  onSelect: (ref: string) => void
}

export function WindowDisclosure({ context, date }: { context?: TeachingWindowContext; date: string }) {
  const windows = applicableWindows(context, date)
  if (context?.availability === 'not_applicable') return <p>Lehrzeitfenster nicht anwendbar.</p>
  if (windows === null) return <p>Lehrzeitfenster unbekannt / außerhalb der gelieferten Datumsabdeckung. {context?.reason}</p>
  const day = context!.days.find(d => d.date === date)!
  return <div className="window-disclosure">
    <p>{context!.basis === 'captured_published' ? 'Erfasste Veröffentlichung' : 'Aktuelle Arbeitsrevision'} · {context!.isCustom ? 'Kursspezifisches Profil' : 'Kohortenkalender'}{context!.sourceRevision != null ? ` · Profilrevision ${context!.sourceRevision}` : ''}</p>
    {day.periodStatus === 'outside_period' ? <p>Außerhalb des Planungszeitraums · keine erlaubten Lehrstunden.</p> : windows.length === 0 ? <p>Keine erlaubten Lehrstunden an diesem Datum.</p> : <ul>{windows.map(w => <li key={w.windowRef}>Erlaubte Lehrstunden {w.startTime}–{w.endTime} · {w.kind === 'dated' ? `Datumsfenster ${formatCalendarDate(w.date!)}` : `Wöchentlich (Mo=0): ${w.weekday}`}{w.isIntensive ? ' · Intensiv' : ''} · Quelle {w.sourceTimeWindowId ?? w.windowRef}</li>)}</ul>}
    <details><summary>Alle Quellen des Profils</summary><ul>{context!.windows.map(w => <li key={w.windowRef}>{w.kind === 'dated' ? w.date : `Wochentag ${w.weekday}`} · {w.startTime}–{w.endTime}{w.isIntensive ? ' · Intensiv' : ''} · {w.windowRef}</li>)}</ul><p>Getrennte Quellen bleiben getrennte Regeln; ihre Darstellung erlaubt kein Zusammenfügen.</p></details>
  </div>
}

export function CalendarTimeGrid({ dates, workspace, occurrences, courses, selectedRef, onSelect }: CalendarSurfaceProps) {
  const scroller = useRef<HTMLDivElement>(null)
  const id = useId()
  const groups = calendarGroups(courses, workspace.teachingWindowContexts)
  const emptyGroup = { key: 'empty', label: '', courses: [], context: undefined }
  const columns = dates.flatMap(date => {
    const populated = groups.map(group => {
      const blocks = layoutIntervals(occurrences.filter(o => o.date === date && group.courses.some(c => c.courseRef === o.courseRef)))
      return { date, group, context: group.context, windows: applicableWindows(group.context, date), blocks }
    }).filter(column => column.blocks.length > 0)
    return populated.length ? populated : [{ date, group: emptyGroup, context: undefined, windows: null, blocks: [] }]
  })
  const starts = columns.flatMap(c => [...c.blocks.map(b => minuteOffset(b.startTime)), ...(c.windows ?? []).map(w => minuteOffset(w.startTime))])
  const initialMinute = starts.length ? Math.min(...starts) : 480
  const rangeKey = dates.join(',')
  useEffect(() => {
    if (scroller.current) scroller.current.scrollTop = initialMinute * 1.2
  }, [rangeKey, initialMinute])

  return <section className="hourly-calendar" aria-label="Stundenkalender">
    <p className="time-grid-legend">▧ Außerhalb der Lehrzeitfenster · ▫ Erlaubte Lehrstunden · ? Unbekannt · ■ Termin. Erlaubte Stunden garantieren keine Ressourcenverfügbarkeit.</p>
    <div className="time-grid-scroll" ref={scroller} role="region" aria-label="Stundenraster, horizontal und vertikal scrollbar, 00:00 bis 24:00" tabIndex={0}>
      <div className="time-grid-columns" style={{ gridTemplateColumns: `56px ${columns.map(c => `minmax(${Math.max(220, ...c.blocks.map(b => b.laneCount * 110))}px, 1fr)`).join(' ')}` }}>
        <div className="time-grid-axis"><div className="time-grid-header">Uhrzeit</div><div style={{ height: DAY_HEIGHT, position: 'relative' }}>{Array.from({ length: 25 }, (_, hour) => <span key={hour} style={{ position: 'absolute', top: Math.min(hour * 72, DAY_HEIGHT - 18) }}>{String(hour).padStart(2, '0')}:00</span>)}</div></div>
        {columns.map(({ date, group, windows, blocks }, column) => <section key={`${date}:${group.key}`} className="time-grid-column" aria-label={[formatCalendarDate(date), group.label, ...group.courses.map(c => c.name)].filter(Boolean).join(' · ')}>
          <h4 className="time-grid-header">{new Intl.DateTimeFormat('de-AT', { weekday: 'short', timeZone: 'UTC' }).format(new Date(`${date}T12:00Z`))}, {formatCalendarDate(date)}{group.label && <><br />{group.label} · {group.courses.map(c => c.name).join(', ')}</>}</h4>
          <div className={`time-grid-canvas ${blocks.length === 0 ? 'window-empty' : windows === null ? 'window-unknown' : 'window-known'}`} style={{ height: DAY_HEIGHT, minWidth: Math.max(220, ...blocks.map(b => b.laneCount * 110)) }}>
            <div aria-hidden="true" className="time-grid-paint">{(windows ?? []).map(w => <div className="time-grid-window" key={w.windowRef} style={{ top: minuteOffset(w.startTime) * 1.2, height: (minuteOffset(w.endTime) - minuteOffset(w.startTime)) * 1.2 }} />)}</div>
            {blocks.map(block => <button type="button" key={block.occurrenceRef} data-occurrence-ref={block.occurrenceRef}
              className={`calendar-occurrence time-grid-block ${block.kind}${block.findingRefs.length ? ' has-warning' : ''}`} aria-pressed={selectedRef === block.occurrenceRef}
              aria-label={occurrenceFacts(workspace, block)} aria-describedby={`${id}-${column}-${block.occurrenceRef.replace(':', '-')}`}
              onClick={() => onSelect(block.occurrenceRef)} style={{ top: block.top, height: block.height, left: `${block.lane / block.laneCount * 100}%`, width: `${100 / block.laneCount}%` }}>
              <span className="occurrence-kind">{block.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'}</span><strong>{workspace.courses.find(c => c.courseRef === block.courseRef)?.name}</strong><span>{block.startTime}–{block.endTime}</span>
              <span>{block.cohort}</span><span>Raum: {workspace.filterFacets.rooms.find(r => r.value === block.roomRef)?.label ?? (block.kind === 'exam' ? block.assignedRoomName : 'Nicht verfügbar')}</span>
              {block.findingRefs.length > 0 && <span>⚠ {block.findingRefs.length} aktuelle Hinweise</span>}
              {block.kind === 'teaching' && hasWindowFinding(block, workspace.validationFindings) && outsideIntervals(block.startTime, block.endTime, windows).map(segment => <span key={segment.start} aria-hidden="true" className="time-grid-outside-segment" style={{ top: (segment.start - minuteOffset(block.startTime)) * 1.2 - 2, height: segment.minutes * 1.2 }}>▧ Außerhalb {minuteClock(segment.start)}–{minuteClock(segment.end)}</span>)}
            </button>)}
          </div>
          <div className="sr-only">
            <ul>{blocks.map(block => <li id={`${id}-${column}-${block.occurrenceRef.replace(':', '-')}`} key={block.occurrenceRef}>{occurrenceFacts(workspace, block)}</li>)}</ul>
          </div>
        </section>)}
      </div>
    </div>
  </section>
}
