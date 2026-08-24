import { useCallback, useEffect, useRef, useState } from 'react'
import './App.css'
import {
  ApplicationNavigation,
  type AcademicDataCategory,
  type PlannerView,
  type ScheduleDestination,
} from './components/ApplicationNavigation'
import {
  CourseSchedulePage,
  type ScheduleNavigationRequest,
} from './pages/CourseSchedulePage'
import { AcademicDataPage } from './pages/AcademicDataPage'
import {
  readNavigationPinned,
  writeNavigationPinned,
} from './navigationPreference'
import { label } from './config/terminology'
import type { CurrentAccount } from './api/authentication'
import { PlannerAccountsPage } from './pages/PlannerAccountsPage'

function App({ currentAccount, onCurrentAccountChange, onLogout, onPasswordChange }: { currentAccount?: CurrentAccount; onCurrentAccountChange?: (account: CurrentAccount) => void; onLogout?: () => void; onPasswordChange?: () => void }) {
  const [view, setView] = useState<PlannerView>('schedule')
  const [scheduleDestination, setScheduleDestination] = useState<ScheduleDestination>('calendar')
  const [scheduleExpanded, setScheduleExpanded] = useState(true)
  const [selectedCategory, setSelectedCategory] = useState<AcademicDataCategory>('semesters')
  const [academicExpanded, setAcademicExpanded] = useState(false)
  const [navigationOpen, setNavigationOpen] = useState(false)
  const [navigationPinned, setNavigationPinned] = useState(readNavigationPinned)
  const [catalogRevision, setCatalogRevision] = useState(0)
  const contentRef = useRef<HTMLElement>(null)
  const focusContent = useRef(false)
  const scheduleNavigationRequester = useRef<((request: ScheduleNavigationRequest) => void) | null>(null)

  useEffect(() => {
    if (!focusContent.current) return
    focusContent.current = false
    contentRef.current?.focus()
  }, [scheduleDestination, view, selectedCategory])

  useEffect(() => {
    writeNavigationPinned(navigationPinned)
  }, [navigationPinned])

  const activeView: PlannerView = view === 'accounts' && !currentAccount?.isAdministrator ? 'schedule' : view

  const setNavigationVisibility = useCallback((open: boolean) => setNavigationOpen(open), [])
  const setScheduleNavigationRequester = useCallback((
    requester: ((request: ScheduleNavigationRequest) => void) | null,
  ) => {
    scheduleNavigationRequester.current = requester
  }, [])

  function selectScheduleDestination(destination: ScheduleDestination) {
    if (view === 'schedule' && scheduleDestination === destination) return
    const commit = () => commitScheduleDestination(destination)
    if (scheduleNavigationRequester.current) {
      scheduleNavigationRequester.current({
        label: `${label('schedule.navigation')}: ${destination}`,
        commit,
      })
    } else {
      commit()
    }
  }

  function commitScheduleDestination(destination: ScheduleDestination) {
      focusContent.current = true
      setScheduleExpanded(true)
      setScheduleDestination(destination)
      setView('schedule')
  }

  function selectCategory(category: AcademicDataCategory) {
    setAcademicExpanded(true)
    if (view === 'academic' && selectedCategory === category) return
    const commit = () => {
      focusContent.current = true
      setSelectedCategory(category)
      setView('academic')
    }
    if (view === 'schedule' && scheduleNavigationRequester.current) {
      scheduleNavigationRequester.current({
        label: `${label('academicData.navigation')}: ${category}`,
        commit,
      })
    } else {
      commit()
    }
  }

  function toggleAcademic() {
    if (view === 'academic' && academicExpanded) return
    setAcademicExpanded((expanded) => !expanded)
  }

  function toggleSchedule() {
    if (view === 'schedule' && scheduleExpanded) return
    setScheduleExpanded((expanded) => !expanded)
  }

  function selectAccounts() {
    focusContent.current = true
    setView('accounts')
  }

  return (
    <div className="application-shell" data-navigation-pinned={navigationPinned ? 'true' : 'false'}>
      <ApplicationNavigation
        view={activeView}
        selectedCategory={selectedCategory}
        selectedScheduleDestination={scheduleDestination}
        scheduleExpanded={scheduleExpanded}
        academicExpanded={academicExpanded}
        navigationOpen={navigationOpen}
        navigationPinned={navigationPinned}
        onToggleAcademic={toggleAcademic}
        onToggleSchedule={toggleSchedule}
        onSelectScheduleDestination={selectScheduleDestination}
        onSelectCategory={selectCategory}
        onNavigationOpenChange={setNavigationVisibility}
        onNavigationPinnedChange={setNavigationPinned}
        currentAccount={currentAccount}
        onSelectAccounts={selectAccounts}
        onLogout={onLogout}
        onPasswordChange={onPasswordChange}
      />
      <main
        ref={contentRef}
        className="application-content"
        tabIndex={-1}
        aria-label={activeView === 'schedule' ? label('schedule.heading') : activeView === 'academic' ? `${label('academicData.heading')}: ${selectedCategory}` : 'Planer-Konten'}
        aria-hidden={navigationOpen || undefined}
        inert={navigationOpen || undefined}
      >
        <div hidden={activeView !== 'schedule'}><CourseSchedulePage active={activeView === 'schedule'} catalogRevision={catalogRevision} destination={scheduleDestination} onNavigationRequesterChange={setScheduleNavigationRequester} onScheduleDestinationChange={commitScheduleDestination} /></div>
        {activeView === 'academic' && <AcademicDataPage category={selectedCategory} onCatalogChanged={() => setCatalogRevision((value) => value + 1)} />}
        {activeView === 'accounts' && currentAccount?.isAdministrator && <PlannerAccountsPage currentAccount={currentAccount} onCurrentAccountChange={onCurrentAccountChange} />}
      </main>
    </div>
  )
}

export default App
