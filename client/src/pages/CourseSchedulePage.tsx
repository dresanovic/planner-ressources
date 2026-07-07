import { useState } from 'react'
import {
  generateDraftSchedule,
  type DraftSchedule,
  type GenerationFailure,
} from '../api/draftSchedule'
import { DraftSchedulePanel } from '../components/DraftSchedulePanel'

const COURSE_ID = 1
const SEMESTER_ID = 1
const SELECTED_TIME_WINDOW_ID = 1

export function CourseSchedulePage() {
  const [schedule, setSchedule] = useState<DraftSchedule | null>(mockSchedule)
  const [errors, setErrors] = useState<GenerationFailure[]>([])
  const [isLoading, setIsLoading] = useState(false)

  async function handleGenerate() {
    setIsLoading(true)
    setErrors([])
    try {
      const generated = await generateDraftSchedule(
        COURSE_ID,
        SEMESTER_ID,
        SELECTED_TIME_WINDOW_ID,
      )
      setSchedule(generated)
    } catch (error) {
      setSchedule(null)
      setErrors(Array.isArray(error) ? error : [{ code: 'UNKNOWN', message: 'Generation failed.' }])
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="planner-shell">
      <aside className="sidebar">
        <div className="brand-mark">RP</div>
        <nav aria-label="Planner navigation">
          <a href="#dashboard">Dashboard</a>
          <a href="#courses">Courses</a>
          <a href="#cohorts">Cohorts</a>
          <a href="#rooms">Rooms</a>
          <a className="active" href="#schedule">
            Schedule
          </a>
        </nav>
      </aside>

      <section className="workbench">
        <header className="page-header">
          <div>
            <h1>Resource Planner</h1>
            <p>Draft schedule generation for one course</p>
          </div>
          <div className="metadata-pill">Fall semester</div>
        </header>

        <div className="planner-grid">
          <section className="input-summary" aria-labelledby="input-summary-title">
            <h2 id="input-summary-title">Planning inputs</h2>
            <dl>
              <div>
                <dt>Course</dt>
                <dd>Planning 101</dd>
              </div>
              <div>
                <dt>Units</dt>
                <dd>20</dd>
              </div>
              <div>
                <dt>Session preference</dt>
                <dd>2-4 units</dd>
              </div>
              <div>
                <dt>Cohort</dt>
                <dd>AI 1, 30 students</dd>
              </div>
              <div>
                <dt>Room</dt>
                <dd>R1, capacity 40</dd>
              </div>
              <div>
                <dt>Selected window</dt>
                <dd>Monday 08:00-12:00</dd>
              </div>
            </dl>
          </section>

          <DraftSchedulePanel
            schedule={schedule}
            errors={errors}
            isLoading={isLoading}
            onGenerate={handleGenerate}
          />
        </div>
      </section>
    </main>
  )
}

const mockSchedule: DraftSchedule = {
  draftScheduleId: 1,
  courseId: COURSE_ID,
  semesterId: SEMESTER_ID,
  selectedTimeWindowId: SELECTED_TIME_WINDOW_ID,
  sessions: [
    {
      id: 1,
      date: '2026-09-07',
      startTime: '08:00',
      endTime: '11:30',
      units: 4,
      timeWindowId: 1,
    },
    {
      id: 2,
      date: '2026-09-14',
      startTime: '08:00',
      endTime: '11:30',
      units: 4,
      timeWindowId: 1,
    },
  ],
}
