import { useState } from 'react'
import './App.css'
import { CourseSchedulePage } from './pages/CourseSchedulePage'
import { AcademicDataPage } from './pages/AcademicDataPage'

function App() {
  const [view, setView] = useState<'schedule' | 'academic'>('schedule')
  const [catalogRevision, setCatalogRevision] = useState(0)
  return <><div className="view-navigation" aria-label="Planner views"><button onClick={() => setView('schedule')} className={view === 'schedule' ? 'active' : ''}>Schedule</button><button onClick={() => setView('academic')} className={view === 'academic' ? 'active' : ''}>Academic Data</button></div><div hidden={view !== 'schedule'}><CourseSchedulePage catalogRevision={catalogRevision} /></div>{view === 'academic' && <AcademicDataPage onCatalogChanged={() => setCatalogRevision((value) => value + 1)} />}</>
}

export default App
