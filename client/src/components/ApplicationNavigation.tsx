import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

// Shared with the controlled Academic Data page and contract tests.
// eslint-disable-next-line react-refresh/only-export-components
export const ACADEMIC_DATA_CATEGORIES = [
  { id: 'semesters', label: 'Semesters', singular: 'semester' },
  { id: 'holidays', label: 'Holidays', singular: 'holiday' },
  { id: 'cohorts', label: 'Cohorts', singular: 'cohort' },
  { id: 'courses', label: 'Courses', singular: 'course' },
  { id: 'study-types', label: 'Study types', singular: 'study type' },
  { id: 'time-windows', label: 'Time windows', singular: 'time window' },
  { id: 'lecturers', label: 'Lecturers', singular: 'lecturer' },
  { id: 'rooms', label: 'Rooms', singular: 'room' },
] as const

export type AcademicDataCategory = (typeof ACADEMIC_DATA_CATEGORIES)[number]['id']
export type PlannerView = 'schedule' | 'academic'
export type ScheduleDestination = 'calendar' | 'versions' | 'exams' | 'reviews'

// Shared with the application shell and navigation contract tests.
// eslint-disable-next-line react-refresh/only-export-components
export const SCHEDULE_DESTINATIONS: { id: ScheduleDestination; label: string }[] = [
  { id: 'calendar', label: 'Calendar' },
  { id: 'versions', label: 'Versions' },
  { id: 'exams', label: 'Exams' },
  { id: 'reviews', label: 'Lecturer coordination' },
]

type ApplicationNavigationProps = {
  view: PlannerView
  selectedCategory: AcademicDataCategory
  selectedScheduleDestination: ScheduleDestination
  scheduleExpanded: boolean
  academicExpanded: boolean
  navigationOpen: boolean
  navigationPinned: boolean
  onToggleAcademic: () => void
  onToggleSchedule: () => void
  onSelectScheduleDestination: (destination: ScheduleDestination) => void
  onSelectCategory: (category: AcademicDataCategory) => void
  onNavigationOpenChange: (open: boolean) => void
  onNavigationPinnedChange: (pinned: boolean) => void
}

const NARROW_QUERY = '(max-width: 820px)'

export function ApplicationNavigation({
  view,
  selectedCategory,
  selectedScheduleDestination,
  scheduleExpanded,
  academicExpanded,
  navigationOpen,
  navigationPinned,
  onToggleAcademic,
  onToggleSchedule,
  onSelectScheduleDestination,
  onSelectCategory,
  onNavigationOpenChange,
  onNavigationPinnedChange,
}: ApplicationNavigationProps) {
  const [isNarrow, setIsNarrow] = useState(() => globalThis.matchMedia?.(NARROW_QUERY).matches ?? false)
  const openerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const academicRef = useRef<HTMLButtonElement>(null)
  const scheduleRef = useRef<HTMLButtonElement>(null)
  const previousOpen = useRef(false)
  const restoreFocusOnClose = useRef(true)
  const temporaryPanel = isNarrow || !navigationPinned
  const panelVisible = (!isNarrow && navigationPinned) || navigationOpen

  useEffect(() => {
    const query = globalThis.matchMedia?.(NARROW_QUERY)
    if (!query) return
    const update = () => {
      if (!query.matches && navigationOpen && panelRef.current?.contains(document.activeElement)) {
        queueMicrotask(() => panelRef.current?.querySelector<HTMLElement>('[aria-current="page"]')?.focus())
      }
      setIsNarrow(query.matches)
      if (!query.matches && navigationPinned) onNavigationOpenChange(false)
    }
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [navigationOpen, navigationPinned, onNavigationOpenChange])

  useEffect(() => {
    if (temporaryPanel && navigationOpen) closeRef.current?.focus()
    if (temporaryPanel && previousOpen.current && !navigationOpen && restoreFocusOnClose.current && panelRef.current?.contains(document.activeElement)) {
      openerRef.current?.focus()
    }
    if (!navigationOpen) restoreFocusOnClose.current = true
    previousOpen.current = navigationOpen
  }, [navigationOpen, temporaryPanel])

  function closePanel(restoreFocus = true) {
    restoreFocusOnClose.current = restoreFocus
    onNavigationOpenChange(false)
    if (restoreFocus) queueMicrotask(() => openerRef.current?.focus())
  }

  function activateScheduleDestination(destination: ScheduleDestination) {
    const changed = view !== 'schedule' || selectedScheduleDestination !== destination
    onSelectScheduleDestination(destination)
    if (temporaryPanel) closePanel(!changed)
  }

  function activateCategory(category: AcademicDataCategory) {
    const changed = view !== 'academic' || selectedCategory !== category
    onSelectCategory(category)
    if (temporaryPanel) closePanel(!changed)
  }

  function handlePanelKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (!temporaryPanel || !navigationOpen) return
    if (event.key === 'Escape') {
      event.preventDefault()
      closePanel()
      return
    }
    if (event.key !== 'Tab') return
    const controls = Array.from(panelRef.current?.querySelectorAll<HTMLElement>('button:not([disabled])') ?? [])
    if (controls.length === 0) return
    const first = controls[0]
    const last = controls[controls.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  function toggleAcademic() {
    if (view === 'academic' && academicExpanded) return
    if (academicExpanded && panelRef.current?.contains(document.activeElement)) academicRef.current?.focus()
    onToggleAcademic()
  }

  function toggleSchedule() {
    if (view === 'schedule' && scheduleExpanded) return
    if (scheduleExpanded && panelRef.current?.contains(document.activeElement)) scheduleRef.current?.focus()
    onToggleSchedule()
  }

  function setPinned(pinned: boolean) {
    onNavigationPinnedChange(pinned)
    onNavigationOpenChange(false)
    if (!pinned) queueMicrotask(() => openerRef.current?.focus())
  }

  return (
    <>
      <button
        ref={openerRef}
        className={`navigation-opener${!isNarrow && !navigationPinned ? ' is-unpinned' : ''}`}
        type="button"
        aria-controls="application-navigation"
        aria-expanded={temporaryPanel ? navigationOpen : undefined}
        aria-hidden={temporaryPanel && navigationOpen ? true : undefined}
        inert={temporaryPanel && navigationOpen ? true : undefined}
        onClick={() => onNavigationOpenChange(true)}
      >
        {isNarrow ? 'Menu' : 'Open navigation'}
      </button>
      {temporaryPanel && navigationOpen && <div className="navigation-backdrop" aria-hidden="true" onClick={() => closePanel()} />}
      <aside
        ref={panelRef}
        id="application-navigation"
        className={`application-navigation${panelVisible ? ' is-open' : ''}${!isNarrow && navigationPinned ? ' is-pinned' : ' is-temporary'}`}
        role={temporaryPanel ? 'dialog' : undefined}
        aria-modal={temporaryPanel ? true : undefined}
        aria-labelledby={temporaryPanel ? 'navigation-title' : undefined}
        onKeyDown={handlePanelKeyDown}
      >
        <div className="navigation-heading">
          <div className="brand-mark" aria-hidden="true">RP</div>
          <span id="navigation-title">Resource Planner</span>
          <button ref={closeRef} className="navigation-close" type="button" onClick={() => closePanel()}>Close menu</button>
          {!isNarrow && <button type="button" className="navigation-pin" onClick={() => setPinned(!navigationPinned)}>{navigationPinned ? 'Unpin navigation' : 'Pin navigation'}</button>}
        </div>
        <nav aria-label="Primary navigation">
          <button
            ref={scheduleRef}
            type="button"
            className={`navigation-parent${view === 'schedule' ? ' is-active' : ''}`}
            aria-expanded={scheduleExpanded}
            aria-controls="schedule-navigation-children"
            onClick={toggleSchedule}
          >
            <span>Schedule</span><span aria-hidden="true">{scheduleExpanded ? '−' : '+'}</span>
          </button>
          {scheduleExpanded && (
            <div id="schedule-navigation-children" className="navigation-children">
              {SCHEDULE_DESTINATIONS.map((destination) => (
                <button
                  type="button"
                  className="navigation-leaf navigation-child"
                  aria-current={view === 'schedule' && selectedScheduleDestination === destination.id ? 'page' : undefined}
                  key={destination.id}
                  onClick={() => activateScheduleDestination(destination.id)}
                >
                  <span className="navigation-marker" aria-hidden="true" />{destination.label}
                </button>
              ))}
            </div>
          )}
          <button
            ref={academicRef}
            type="button"
            className={`navigation-parent${view === 'academic' ? ' is-active' : ''}`}
            aria-expanded={academicExpanded}
            aria-controls="academic-navigation-children"
            onClick={toggleAcademic}
          >
            <span>Academic Data</span><span aria-hidden="true">{academicExpanded ? '−' : '+'}</span>
          </button>
          {academicExpanded && (
            <div id="academic-navigation-children" className="navigation-children">
              {ACADEMIC_DATA_CATEGORIES.map((category) => (
                <button
                  type="button"
                  className="navigation-leaf navigation-child"
                  aria-current={view === 'academic' && selectedCategory === category.id ? 'page' : undefined}
                  key={category.id}
                  onClick={() => activateCategory(category.id)}
                >
                  <span className="navigation-marker" aria-hidden="true" />{category.label}
                </button>
              ))}
            </div>
          )}
        </nav>
      </aside>
    </>
  )
}
