import type {
  LoadedCalendarWorkspace,
  WorkspaceOccurrence,
} from '../api/calendarWorkspace'
import type { ReactNode } from 'react'
import { formatCalendarDate } from '../utils/datePresentation'

type Props = {
  workspace: LoadedCalendarWorkspace
  occurrences?: WorkspaceOccurrence[]
  selectedOccurrenceRef?: string | null
  onSelectOccurrence: (occurrenceRef: string) => void
  emptyMessage?: string
}

export function ScheduleOccurrenceList({
  workspace,
  occurrences = workspace.occurrences,
  selectedOccurrenceRef = null,
  onSelectOccurrence,
  emptyMessage = 'Keine Termine entsprechen den aktiven Filtern.',
}: Props) {
  const courseByRef = new Map(
    workspace.courses.map((course) => [course.courseRef, course]),
  )
  const ordered = [...occurrences].sort((left, right) =>
    `${left.date}-${left.startTime}-${left.occurrenceRef}`.localeCompare(
      `${right.date}-${right.startTime}-${right.occurrenceRef}`,
    ),
  )

  if (ordered.length === 0) {
    return <p className="empty-state">{emptyMessage}</p>
  }

  return (
    <div className="schedule-occurrence-list" role="list" aria-label="Planungstermine">
      {ordered.map((occurrence) => {
        const course = courseByRef.get(occurrence.courseRef)
        return (
          <div
            key={occurrence.occurrenceRef}
            className="schedule-occurrence-list-item"
            role="listitem"
          >
            <ScheduleOccurrenceRow
              occurrenceRef={occurrence.occurrenceRef}
              kind={occurrence.kind}
              selected={selectedOccurrenceRef === occurrence.occurrenceRef}
              onSelect={onSelectOccurrence}
            >
              <span className="occurrence-kind">
                {occurrence.kind === 'teaching' ? 'Lehrtermin' : 'Prüfungstermin'}
              </span>
              <strong>{course?.name ?? occurrence.courseRef}</strong>
              <span>{formatCalendarDate(occurrence.date)}</span>
              <span>{occurrence.startTime}–{occurrence.endTime}</span>
              <span>{occurrence.cohort}</span>
              {occurrence.findingRefs.length > 0 && (
                <span className="warning-label">
                  ⚠ {occurrence.findingRefs.length} {occurrence.findingRefs.length === 1 ? 'aktueller Hinweis' : 'aktuelle Hinweise'}
                  {occurrence.findingRefs.length === 1 ? '' : 's'}
                </span>
              )}
            </ScheduleOccurrenceRow>
          </div>
        )
      })}
    </div>
  )
}

export function ScheduleOccurrenceRow({
  occurrenceRef,
  kind,
  selected = false,
  onSelect,
  className = '',
  children,
}: {
  occurrenceRef: string
  kind: 'teaching' | 'exam'
  selected?: boolean
  onSelect?: (occurrenceRef: string) => void
  className?: string
  children: ReactNode
}) {
  const classes = `${className} schedule-occurrence-row ${kind}`.trim()
  if (onSelect) {
    return (
      <button
        type="button"
        className={classes}
        data-occurrence-ref={occurrenceRef}
        aria-pressed={selected}
        onClick={() => onSelect(occurrenceRef)}
      >
        {children}
      </button>
    )
  }
  return (
    <div
      className={classes}
      data-schedule-occurrence-ref={occurrenceRef}
    >
      {children}
    </div>
  )
}
