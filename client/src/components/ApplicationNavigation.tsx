import { useEffect, useRef, useState, type KeyboardEvent } from 'react'

// Shared with the controlled Academic Data page and contract tests.
// eslint-disable-next-line react-refresh/only-export-components
export const ACADEMIC_DATA_CATEGORIES = [
  { id: 'semesters', label: 'Semesters', singular: 'semester' },
  { id: 'cohorts', label: 'Cohorts', singular: 'cohort' },
  { id: 'courses', label: 'Courses', singular: 'course' },
  { id: 'study-types', label: 'Study types', singular: 'study type' },
  { id: 'time-windows', label: 'Time windows', singular: 'time window' },
  { id: 'lecturers', label: 'Lecturers', singular: 'lecturer' },
  { id: 'rooms', label: 'Rooms', singular: 'room' },
] as const

export type AcademicDataCategory = (typeof ACADEMIC_DATA_CATEGORIES)[number]['id']
export type PlannerView = 'schedule' | 'academic'

type ApplicationNavigationProps = {
  view: PlannerView
  selectedCategory: AcademicDataCategory
  academicExpanded: boolean
  navigationOpen: boolean
  onToggleAcademic: () => void
  onSelectSchedule: () => void
  onSelectCategory: (category: AcademicDataCategory) => void
  onNavigationOpenChange: (open: boolean) => void
}

const NARROW_QUERY = '(max-width: 820px)'

export function ApplicationNavigation({
  view,
  selectedCategory,
  academicExpanded,
  navigationOpen,
  onToggleAcademic,
  onSelectSchedule,
  onSelectCategory,
  onNavigationOpenChange,
}: ApplicationNavigationProps) {
  const [isNarrow, setIsNarrow] = useState(() => globalThis.matchMedia?.(NARROW_QUERY).matches ?? false)
  const openerRef = useRef<HTMLButtonElement>(null)
  const panelRef = useRef<HTMLElement>(null)
  const closeRef = useRef<HTMLButtonElement>(null)
  const academicRef = useRef<HTMLButtonElement>(null)
  const previousOpen = useRef(false)

  useEffect(() => {
    const query = globalThis.matchMedia?.(NARROW_QUERY)
    if (!query) return
    const update = () => {
      if (!query.matches && navigationOpen && panelRef.current?.contains(document.activeElement)) {
        queueMicrotask(() => panelRef.current?.querySelector<HTMLElement>('[aria-current="page"]')?.focus())
      }
      setIsNarrow(query.matches)
      if (!query.matches) onNavigationOpenChange(false)
    }
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [navigationOpen, onNavigationOpenChange])

  useEffect(() => {
    if (isNarrow && navigationOpen) closeRef.current?.focus()
    if (isNarrow && previousOpen.current && !navigationOpen && panelRef.current?.contains(document.activeElement)) {
      openerRef.current?.focus()
    }
    previousOpen.current = navigationOpen
  }, [isNarrow, navigationOpen])

  function closePanel(restoreFocus = true) {
    onNavigationOpenChange(false)
    if (restoreFocus) queueMicrotask(() => openerRef.current?.focus())
  }

  function activateSchedule() {
    const changed = view !== 'schedule'
    onSelectSchedule()
    if (isNarrow) closePanel(!changed)
  }

  function activateCategory(category: AcademicDataCategory) {
    const changed = view !== 'academic' || selectedCategory !== category
    onSelectCategory(category)
    if (isNarrow) closePanel(!changed)
  }

  function handlePanelKeyDown(event: KeyboardEvent<HTMLElement>) {
    if (!isNarrow || !navigationOpen) return
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

  return (
    <>
      <button ref={openerRef} className="navigation-opener" type="button" aria-controls="application-navigation" aria-expanded={isNarrow ? navigationOpen : undefined} onClick={() => onNavigationOpenChange(true)}>
        Menu
      </button>
      {isNarrow && navigationOpen && <div className="navigation-backdrop" aria-hidden="true" />}
      <aside
        ref={panelRef}
        id="application-navigation"
        className={`application-navigation${navigationOpen ? ' is-open' : ''}`}
        role={isNarrow ? 'dialog' : undefined}
        aria-modal={isNarrow ? true : undefined}
        aria-labelledby={isNarrow ? 'navigation-title' : undefined}
        onKeyDown={handlePanelKeyDown}
      >
        <div className="navigation-heading">
          <div className="brand-mark" aria-hidden="true">RP</div>
          <span id="navigation-title">Resource Planner</span>
          <button ref={closeRef} className="navigation-close" type="button" onClick={() => closePanel()}>Close menu</button>
        </div>
        <nav aria-label="Primary navigation">
          <button type="button" className="navigation-leaf" aria-current={view === 'schedule' ? 'page' : undefined} onClick={activateSchedule}>
            <span className="navigation-marker" aria-hidden="true" />Schedule
          </button>
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
