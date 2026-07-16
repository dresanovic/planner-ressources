import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import {
  ApplicationNavigation,
  type AcademicDataCategory,
  type PlannerView,
} from './components/ApplicationNavigation'
import { CourseSchedulePage } from './pages/CourseSchedulePage'
import { AcademicDataPage } from './pages/AcademicDataPage'

function App() {
  const [view, setView] = useState<PlannerView>('schedule')
  const [selectedCategory, setSelectedCategory] = useState<AcademicDataCategory>('semesters')
  const [academicExpanded, setAcademicExpanded] = useState(false)
  const [navigationOpen, setNavigationOpen] = useState(false)
  const [catalogRevision, setCatalogRevision] = useState(0)
  const contentRef = useRef<HTMLElement>(null)
  const focusContent = useRef(false)

  useEffect(() => {
    if (!focusContent.current) return
    focusContent.current = false
    contentRef.current?.focus()
  }, [view, selectedCategory])

  const setNavigationVisibility = useCallback((open: boolean) => setNavigationOpen(open), [])

  function selectSchedule() {
    if (view === 'schedule') return
    focusContent.current = true
    setView('schedule')
  }

  function selectCategory(category: AcademicDataCategory) {
    setAcademicExpanded(true)
    if (view === 'academic' && selectedCategory === category) return
    focusContent.current = true
    setSelectedCategory(category)
    setView('academic')
  }

  function toggleAcademic() {
    if (view === 'academic' && academicExpanded) return
    setAcademicExpanded((expanded) => !expanded)
  }

  return (
    <div className="application-shell">
      <ApplicationNavigation
        view={view}
        selectedCategory={selectedCategory}
        academicExpanded={academicExpanded}
        navigationOpen={navigationOpen}
        onToggleAcademic={toggleAcademic}
        onSelectSchedule={selectSchedule}
        onSelectCategory={selectCategory}
        onNavigationOpenChange={setNavigationVisibility}
      />
      <main
        ref={contentRef}
        className="application-content"
        tabIndex={-1}
        aria-label={view === 'schedule' ? 'Schedule' : `Academic Data: ${selectedCategory}`}
        aria-hidden={navigationOpen || undefined}
        inert={navigationOpen || undefined}
      >
        <div hidden={view !== 'schedule'}><CourseSchedulePage catalogRevision={catalogRevision} /></div>
        {view === 'academic' && <AcademicDataPage category={selectedCategory} onCatalogChanged={() => setCatalogRevision((value) => value + 1)} />}
      </main>
    </div>
  )
}

export default App
