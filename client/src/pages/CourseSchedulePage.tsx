import { useEffect, useMemo, useState } from 'react'
import {
  clearGenerationConstraints,
  generateDraftSchedule,
  getGenerationConstraints,
  getDraftSchedule,
  type DraftSchedule,
  type GenerationConstraints,
  type GenerationFailure,
} from '../api/draftSchedule'
import {
  getPlanningOptions,
  type CourseOption,
  type PlanningOptions,
  type SemesterOption,
} from '../api/planningOptions'
import { DraftSchedulePanel } from '../components/DraftSchedulePanel'

export function CourseSchedulePage() {
  const [planningOptions, setPlanningOptions] = useState<PlanningOptions | null>(null)
  const [selectedCourseId, setSelectedCourseId] = useState<number | null>(null)
  const [selectedSemesterId, setSelectedSemesterId] = useState<number | null>(null)
  const [generationConstraints, setGenerationConstraints] = useState<GenerationConstraints | null>(null)
  const [schedule, setSchedule] = useState<DraftSchedule | null>(null)
  const [errors, setErrors] = useState<GenerationFailure[]>([])
  const [isLoading, setIsLoading] = useState(false)

  const selectedCourse = useMemo(
    () => planningOptions?.courses.find((course) => course.id === selectedCourseId) ?? null,
    [planningOptions, selectedCourseId],
  )
  const selectedSemester = useMemo(
    () => planningOptions?.semesters.find((semester) => semester.id === selectedSemesterId) ?? null,
    [planningOptions, selectedSemesterId],
  )

  useEffect(() => {
    let isCurrent = true

    async function loadPlanningOptions() {
      setIsLoading(true)
      setErrors([])
      try {
        const options = await getPlanningOptions()
        const firstCourse = options.courses[0]

        if (isCurrent) {
          setPlanningOptions(options)
          setSelectedCourseId(firstCourse?.id ?? null)
          setSelectedSemesterId(options.semesters[0]?.id ?? null)
          setSchedule(null)
        }
      } catch {
        if (isCurrent) {
          setErrors([{ code: 'REQUEST_FAILED', message: 'Could not load planning options.' }])
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false)
        }
      }
    }

    void loadPlanningOptions()

    return () => {
      isCurrent = false
    }
  }, [])

  useEffect(() => {
    if (!selectedCourseId || !selectedSemesterId) {
      return
    }

    let isCurrent = true

    async function loadConstraints() {
      setIsLoading(true)
      setErrors([])
      try {
        const constraints = await getGenerationConstraints(
          selectedCourseId as number,
          selectedSemesterId as number,
        )
        if (isCurrent) {
          setGenerationConstraints(constraints)
        }
      } catch (error) {
        if (isCurrent) {
          const failures = Array.isArray(error)
            ? error
            : [{ code: 'UNKNOWN', message: 'Could not load generation constraints.' }]
          setGenerationConstraints(null)
          setErrors(failures)
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false)
        }
      }
    }

    void loadConstraints()

    return () => {
      isCurrent = false
    }
  }, [selectedCourseId, selectedSemesterId])

  useEffect(() => {
    if (!selectedCourseId) {
      return
    }

    let isCurrent = true

    async function loadDraftSchedule() {
      setIsLoading(true)
      setErrors([])
      try {
        const current = await getDraftSchedule(selectedCourseId as number)
        if (isCurrent) {
          setSchedule(current)
        }
      } catch (error) {
        if (!isCurrent) {
          return
        }
        setSchedule(null)
        const failures = Array.isArray(error)
          ? error
          : [{ code: 'UNKNOWN', message: 'Could not load draft schedule.' }]
        if (!failures.some((failure) => failure.code === 'NOT_FOUND')) {
          setErrors(failures)
        }
      } finally {
        if (isCurrent) {
          setIsLoading(false)
        }
      }
    }

    void loadDraftSchedule()

    return () => {
      isCurrent = false
    }
  }, [selectedCourseId])

  async function handleGenerate() {
    if (!selectedCourseId || !selectedSemesterId || !generationConstraints) {
      setErrors([{ code: 'MISSING_SELECTION', message: 'Select a course and semester.' }])
      return
    }

    setIsLoading(true)
    setErrors([])
    try {
      const generated = await generateDraftSchedule(
        selectedCourseId,
        selectedSemesterId,
        generationConstraints.planningPeriod,
        generationConstraints.allowedTeachingWindows,
      )
      setSchedule(generated)
      const saved = await getGenerationConstraints(selectedCourseId, selectedSemesterId)
      setGenerationConstraints(saved)
    } catch (error) {
      setSchedule(null)
      setErrors(Array.isArray(error) ? error : [{ code: 'UNKNOWN', message: 'Generation failed.' }])
    } finally {
      setIsLoading(false)
    }
  }

  function handleCourseChange(courseId: number) {
    setSelectedCourseId(courseId)
    setSchedule(null)
  }

  async function handleClearGenerationConstraints() {
    if (!selectedCourseId || !selectedSemesterId) {
      return
    }
    setIsLoading(true)
    setErrors([])
    try {
      await clearGenerationConstraints(selectedCourseId, selectedSemesterId)
      const defaults = await getGenerationConstraints(selectedCourseId, selectedSemesterId)
      setGenerationConstraints(defaults)
    } catch (error) {
      setErrors(Array.isArray(error) ? error : [{ code: 'UNKNOWN', message: 'Could not clear constraints.' }])
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
          <div className="metadata-pill">{selectedSemester?.name ?? 'No semester selected'}</div>
        </header>

        <div className="planner-grid">
          <section className="input-summary" aria-labelledby="input-summary-title">
            <h2 id="input-summary-title">Planning inputs</h2>
            {planningOptions ? (
              <>
                <div className="planning-selectors">
                  <SelectField
                    label="Course"
                    value={selectedCourseId ?? ''}
                    options={planningOptions.courses}
                    getLabel={(course) => course.name}
                    onChange={(value) => handleCourseChange(Number(value))}
                  />
                  <SelectField
                    label="Semester"
                    value={selectedSemesterId ?? ''}
                    options={planningOptions.semesters}
                    getLabel={(semester) => semester.name}
                    onChange={(value) => setSelectedSemesterId(Number(value))}
                  />
                </div>

                <PlanningSummary
                  course={selectedCourse}
                  semester={selectedSemester}
                />
              </>
            ) : (
              <p className="empty-state">Loading planning options...</p>
            )}
          </section>

          <DraftSchedulePanel
            schedule={schedule}
            generationConstraints={generationConstraints}
            errors={errors}
            isLoading={isLoading}
            onGenerationConstraintsChange={setGenerationConstraints}
            onClearGenerationConstraints={handleClearGenerationConstraints}
            onGenerate={handleGenerate}
          />
        </div>
      </section>
    </main>
  )
}

type Selectable = {
  id: number
}

type SelectFieldProps<T extends Selectable> = {
  label: string
  value: number | ''
  options: T[]
  getLabel: (option: T) => string
  onChange: (value: string) => void
}

function SelectField<T extends Selectable>({
  label,
  value,
  options,
  getLabel,
  onChange,
}: SelectFieldProps<T>) {
  return (
    <label className="selector-field">
      <span>{label}</span>
      <select
        value={value}
        onChange={(event) => onChange(event.target.value)}
        disabled={options.length === 0}
      >
        {options.map((option) => (
          <option value={option.id} key={option.id}>
            {getLabel(option)}
          </option>
        ))}
      </select>
    </label>
  )
}

function PlanningSummary({
  course,
  semester,
}: {
  course: CourseOption | null
  semester: SemesterOption | null
}) {
  if (!course) {
    return <p className="empty-state">No courses are available.</p>
  }

  return (
    <dl>
      <div>
        <dt>Units</dt>
        <dd>{course.totalUnits}</dd>
      </div>
      <div>
        <dt>Session preference</dt>
        <dd>
          {course.minSessionUnits}-{course.maxSessionUnits} units
        </dd>
      </div>
      <div>
        <dt>Cohort</dt>
        <dd>{course.cohort.name}</dd>
      </div>
      <div>
        <dt>Lecturer</dt>
        <dd>{course.lecturer.name}</dd>
      </div>
      <div>
        <dt>Room</dt>
        <dd>{course.room.name}</dd>
      </div>
      <div>
        <dt>Study type</dt>
        <dd>{course.studyType.name}</dd>
      </div>
      <div>
        <dt>Semester dates</dt>
        <dd>{semester ? `${semester.startDate} - ${semester.endDate}` : 'No semester selected'}</dd>
      </div>
    </dl>
  )
}
