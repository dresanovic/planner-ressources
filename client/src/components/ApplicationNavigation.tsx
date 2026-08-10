import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { label } from '../config/terminology'

// Shared with the controlled Academic Data page and contract tests.
// eslint-disable-next-line react-refresh/only-export-components
export const ACADEMIC_DATA_CATEGORIES = [
  { id: 'semesters', label: 'Semester', singular: 'Semester' },
  { id: 'holidays', label: 'Feiertage', singular: 'Feiertag' },
  { id: 'cohorts', label: label('cohort.navigation'), singular: label('cohort.singular') },
  { id: 'courses', label: label('course.navigation'), singular: label('course.singular') },
  { id: 'study-types', label: 'Studienformen', singular: 'Studienform' },
  { id: 'time-windows', label: 'Zeitfenster', singular: 'Zeitfenster' },
  { id: 'lecturers', label: label('lecturer.navigation'), singular: label('lecturer.singular') },
  { id: 'rooms', label: label('room.navigation'), singular: label('room.singular') },
] as const

export type AcademicDataCategory = (typeof ACADEMIC_DATA_CATEGORIES)[number]['id']
export type PlannerView = 'schedule' | 'academic'
export type ScheduleDestination = 'calendar' | 'versions' | 'exams' | 'reviews'

// Shared with the application shell and navigation contract tests.
// eslint-disable-next-line react-refresh/only-export-components
export const SCHEDULE_DESTINATIONS: { id: ScheduleDestination; label: string }[] = [
  { id: 'calendar', label: 'Kalender' },
  { id: 'versions', label: 'Versionen' },
  { id: 'exams', label: 'Prüfungen' },
  { id: 'reviews', label: 'Abstimmung mit Lehrenden' },
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
        {isNarrow ? 'Menü' : 'Navigation öffnen'}
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
          <span id="navigation-title">Ressourcenplanung</span>
          <button ref={closeRef} className="navigation-close" type="button" aria-label="Menü schließen" title="Menü schließen" onClick={() => closePanel()}>
            <span className="sr-only">Menü schließen</span>
            <span className="navigation-close-symbol" aria-hidden="true">×</span>
          </button>
          {!isNarrow && <button type="button" className={`navigation-pin${navigationPinned ? ' is-pinned' : ''}`} aria-label={navigationPinned ? 'Navigation lösen' : 'Navigation anheften'} title={navigationPinned ? 'Navigation lösen' : 'Navigation anheften'} onClick={() => setPinned(!navigationPinned)}>
            <svg className="navigation-pin-symbol" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M7 3h10l-2.5 7v3l2.5 3H7l2.5-3v-3L7 3Z" />
              <path d="M12 16v5" />
            </svg>
            <span className="sr-only">{navigationPinned ? 'Navigation lösen' : 'Navigation anheften'}</span>
          </button>}
        </div>
        <nav aria-label="Hauptnavigation">
          <button
            ref={scheduleRef}
            type="button"
            className={`navigation-parent${view === 'schedule' ? ' is-active' : ''}`}
            aria-expanded={scheduleExpanded}
            aria-controls="schedule-navigation-children"
            onClick={toggleSchedule}
          >
            <span>{label('schedule.navigation')}</span><span aria-hidden="true">{scheduleExpanded ? '−' : '+'}</span>
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
            <span>{label('academicData.navigation')}</span><span aria-hidden="true">{academicExpanded ? '−' : '+'}</span>
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
