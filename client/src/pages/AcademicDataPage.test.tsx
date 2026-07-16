import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listSemesters: vi.fn(), listCohorts: vi.fn(), listCourses: vi.fn(), listStudyTypes: vi.fn(), listTimeWindows: vi.fn(),
  createSemester: vi.fn(), createCohort: vi.fn(), createCourse: vi.fn(), createStudyType: vi.fn(), createTimeWindow: vi.fn(),
  updateSemester: vi.fn(), updateCohort: vi.fn(), updateCourse: vi.fn(), updateStudyType: vi.fn(), updateTimeWindow: vi.fn(),
  deleteAcademicRecord: vi.fn(), setAcademicLifecycle: vi.fn(), getPlanningOptions: vi.fn(),
  listLecturers: vi.fn(), listRooms: vi.fn(), createLecturer: vi.fn(), createRoom: vi.fn(),
  updateLecturer: vi.fn(), updateRoom: vi.fn(), getResourceUsage: vi.fn(), removeResource: vi.fn(), reactivateResource: vi.fn(),
  listUnavailability: vi.fn(),
  getCourseResourceConfiguration: vi.fn(), updateCourseResourceEligibility: vi.fn(),
}))

vi.mock('../api/academicCatalog', async () => ({
  ...(await vi.importActual('../api/academicCatalog')),
  ...Object.fromEntries(Object.entries(mocks).filter(([name]) => name !== 'getPlanningOptions')),
}))
vi.mock('../api/planningOptions', () => ({ getPlanningOptions: mocks.getPlanningOptions }))
vi.mock('../api/resourceCatalog', async () => ({
  ...(await vi.importActual('../api/resourceCatalog')),
  listLecturers: mocks.listLecturers, listRooms: mocks.listRooms,
  createLecturer: mocks.createLecturer, createRoom: mocks.createRoom,
  updateLecturer: mocks.updateLecturer, updateRoom: mocks.updateRoom,
  getResourceUsage: mocks.getResourceUsage, removeResource: mocks.removeResource,
  reactivateResource: mocks.reactivateResource,
  listUnavailability: mocks.listUnavailability,
  getCourseResourceConfiguration: mocks.getCourseResourceConfiguration,
  updateCourseResourceEligibility: mocks.updateCourseResourceEligibility,
}))

import { AcademicDataPage } from './AcademicDataPage'

const usage = { recordId: 1, revision: 1, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }
const page = <T,>(items: T[], total = items.length, pageNumber = 1) => ({ page: pageNumber, pageSize: 200, total, items })

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset())
  mocks.listSemesters.mockResolvedValue(page([]))
  mocks.listCohorts.mockResolvedValue(page([]))
  mocks.listCourses.mockResolvedValue(page([]))
  mocks.listStudyTypes.mockResolvedValue(page([]))
  mocks.listTimeWindows.mockResolvedValue([])
  mocks.getPlanningOptions.mockResolvedValue({ courses: [], semesters: [], timeWindows: [], lecturers: [], rooms: [] })
  mocks.listLecturers.mockResolvedValue(page([]))
  mocks.listRooms.mockResolvedValue(page([]))
  mocks.listUnavailability.mockResolvedValue([])
  mocks.getCourseResourceConfiguration.mockResolvedValue({ courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [], eligibleRoomIds: [], lecturerCandidates: [], roomCandidates: [], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
  for (const name of ['createSemester', 'createCohort', 'createCourse', 'createStudyType', 'createTimeWindow', 'updateSemester', 'updateCohort', 'updateCourse', 'updateStudyType', 'updateTimeWindow', 'deleteAcademicRecord', 'setAcademicLifecycle'] as const) {
    mocks[name].mockResolvedValue(undefined)
  }
})

afterEach(() => { document.body.innerHTML = '' })

async function renderPage(category: 'semesters' | 'cohorts' | 'courses' | 'study-types' | 'time-windows' | 'lecturers' | 'rooms' = 'semesters') {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<AcademicDataPage category={category} onCatalogChanged={() => undefined} />); await new Promise((resolve) => setTimeout(resolve, 0)) })
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent === label)
}

describe('AcademicDataPage', () => {
  it('renders its controlled category without page-local navigation', async () => {
    await renderPage()
    expect(document.body.textContent).toContain('Semesters')
    expect(document.body.textContent).toContain('No semesters yet')
    expect(document.body.textContent).toContain('Create semester')
    expect(document.querySelector('nav')).toBeNull()
  })

  it('cleans up edit state and loads again when the controlled category changes', async () => {
    mocks.listSemesters.mockResolvedValue(page([{
      id: 1, name: 'Fall 2026', startDate: '2026-09-01', endDate: '2027-01-31',
      isActive: true, revision: 1, nameRepairRequired: false, usage,
    }]))
    const root = await renderPage('semesters')
    act(() => button('Edit')?.click())
    expect(button('Cancel edit')).toBeDefined()
    act(() => root.render(<AcademicDataPage category="cohorts" onCatalogChanged={() => undefined} />))
    expect(button('Cancel edit')).toBeUndefined()
    expect(document.body.textContent).toContain('Create cohort')
    expect(document.body.textContent).not.toContain('Edit cohort')
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(mocks.listCohorts).toHaveBeenCalled()
    expect(document.querySelector('nav')).toBeNull()
  })

  it('loads every paginated record so later records remain maintainable', async () => {
    const records = Array.from({ length: 200 }, (_, index) => ({
      id: index + 1, name: `Semester ${String(index + 1).padStart(3, '0')}`, nameRepairRequired: false,
      startDate: '2026-01-01', endDate: '2026-06-01', isActive: true, revision: 1,
      usage: { ...usage, recordId: index + 1 },
    }))
    const finalRecord = { ...records[0], id: 201, name: 'Semester 201', usage: { ...usage, recordId: 201 } }
    mocks.listSemesters.mockImplementation(async (_status, pageNumber) => pageNumber === 2 ? page([finalRecord], 201, 2) : page(records, 201, 1))

    await renderPage()

    expect(document.body.textContent).toContain('Semester 201')
    expect(mocks.listSemesters).toHaveBeenCalledWith('all', 1, 200)
    expect(mocks.listSemesters).toHaveBeenCalledWith('all', 2, 200)
  })

  it('loads Time Windows from every Study Type', async () => {
    const studyTypes = [1, 2].map((id) => ({ id, name: `Type ${id}`, nameRepairRequired: false, timeWindows: [], isActive: true, revision: 1, usage: { ...usage, recordId: id } }))
    mocks.listStudyTypes.mockResolvedValue(page(studyTypes))
    mocks.listTimeWindows.mockImplementation(async (studyTypeId) => [{
      id: studyTypeId, studyTypeId, weekday: studyTypeId - 1, startTime: '08:00', endTime: '10:00', sortOrder: 0,
      isActive: studyTypeId === 1, revision: 1, availability: { available: studyTypeId === 1, reasons: studyTypeId === 1 ? [] : ['RECORD_INACTIVE'] }, usage: { ...usage, recordId: studyTypeId },
    }])

    await renderPage('time-windows')

    expect(mocks.listTimeWindows).toHaveBeenCalledWith(1)
    expect(mocks.listTimeWindows).toHaveBeenCalledWith(2)
    expect(document.querySelectorAll('.catalog-list li')).toHaveLength(2)
    expect(document.body.textContent).toContain('Type 1 · Monday, 08:00–10:00')
    expect(document.body.textContent).toContain('Type 2 · Tuesday, 08:00–10:00')
    expect(document.body.textContent).not.toContain('Day 1')

    const status = document.querySelector<HTMLSelectElement>('.page-header select')!
    await act(async () => { status.value = 'active'; status.dispatchEvent(new Event('change', { bubbles: true })); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.querySelectorAll('.catalog-list li')).toHaveLength(1)
  })

  it('keeps a migrated unassigned Course editable for Semester repair', async () => {
    const course = {
      id: 9, name: 'Legacy Course', nameRepairRequired: false, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4,
      semester: null, cohort: { id: 2, name: 'AI 1' }, studyType: { id: 3, name: 'Full-time' },
      lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R1' }, isActive: true, revision: 1,
      availability: { available: false, reasons: ['SEMESTER_ASSIGNMENT_REQUIRED'] }, usage: { ...usage, recordId: 9 },
    }
    mocks.listCourses.mockResolvedValue(page([course]))
    mocks.listSemesters.mockResolvedValue(page([{ id: 1, name: 'Fall', nameRepairRequired: false, startDate: '2026-01-01', endDate: '2026-06-01', isActive: true, revision: 1, usage }]))
    mocks.listCohorts.mockResolvedValue(page([{ id: 2, name: 'AI 1' }]))
    mocks.listStudyTypes.mockResolvedValue(page([{ id: 3, name: 'Full-time' }]))
    mocks.getPlanningOptions.mockResolvedValue({ courses: [], semesters: [], timeWindows: [], lecturers: [{ id: 4, name: 'Ada' }], rooms: [{ id: 5, name: 'R1' }] })

    await renderPage('courses')
    act(() => button('Edit')?.click())

    expect(document.body.textContent).toContain('Assign a Semester to complete repair')
    expect(document.querySelector<HTMLSelectElement>('select[name="semesterId"]')?.value).toBe('')
  })

  it('shows lifecycle failures instead of leaving an unhandled rejection', async () => {
    mocks.listCohorts.mockResolvedValue(page([{
      id: 2, name: 'AI 1', nameRepairRequired: false, studentCount: 20, isActive: true, revision: 1, usage: { ...usage, recordId: 2 },
    }]))
    mocks.setAcademicLifecycle.mockRejectedValue(new Error('Refresh and review the current record.'))

    await renderPage('cohorts')
    await act(async () => { button('Archive')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Refresh and review the current record.')
  })

  it('navigates coded Lecturer and Room administration with active-default loading', async () => {
    mocks.listLecturers.mockResolvedValue(page([{ id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 }]))
    mocks.listRooms.mockResolvedValue(page([{ id: 2, name: 'R1', referenceCode: 'R-1', capacity: 30, isActive: true, revision: 1 }]))
    const root = await renderPage('lecturers')
    expect(mocks.listLecturers).toHaveBeenCalledWith(expect.objectContaining({ status: 'active' }))
    expect(document.body.textContent).toContain('Ada · A-1')
    await act(async () => { root.render(<AcademicDataPage category="rooms" onCatalogChanged={() => undefined} />); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('R1 · R-1')
  })

  it('retains the selected resource and last-known content when refresh fails', async () => {
    mocks.listLecturers.mockResolvedValueOnce(page([{ id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 }])).mockRejectedValueOnce(new Error('offline'))
    await renderPage('lecturers')
    await act(async () => { button('Edit')?.click() })
    const refresh = button('Refresh')
    await act(async () => { refresh?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Could not refresh resources')
    expect(document.querySelector<HTMLInputElement>('input[name="name"]')?.value).toBe('Ada')
  })

  it('ignores an older availability response after another resource is selected', async () => {
    const firstPeriod = { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0], startTime: '08:00', endTime: '09:00', revision: 1 }
    const secondPeriod = { id: 2, resourceType: 'lecturer', resourceId: 2, kind: 'recurring', weekdays: [1], startTime: '10:00', endTime: '11:00', revision: 1 }
    let resolveFirst: (periods: typeof firstPeriod[]) => void = () => undefined
    const delayedFirst = new Promise<typeof firstPeriod[]>((resolve) => { resolveFirst = resolve })
    mocks.listLecturers.mockResolvedValue(page([
      { id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 },
      { id: 2, name: 'Grace', referenceCode: 'G-1', isActive: true, revision: 1 },
    ]))
    mocks.listUnavailability.mockReturnValueOnce(delayedFirst).mockResolvedValueOnce([secondPeriod])

    await renderPage('lecturers')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Edit')
    await act(async () => { editButtons()[0]?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Tuesday · 10:00–11:00')

    await act(async () => { resolveFirst([firstPeriod]); await delayedFirst })

    expect(document.body.textContent).toContain('Tuesday · 10:00–11:00')
    expect(document.body.textContent).not.toContain('Monday · 08:00–09:00')
  })

  it('ignores an older availability response after returning to the same resource', async () => {
    const stalePeriod = { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0], startTime: '08:00', endTime: '09:00', revision: 1 }
    const otherPeriod = { id: 2, resourceType: 'lecturer', resourceId: 2, kind: 'recurring', weekdays: [1], startTime: '10:00', endTime: '11:00', revision: 1 }
    const currentPeriod = { id: 3, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [2], startTime: '12:00', endTime: '13:00', revision: 1 }
    let resolveStale: (periods: typeof stalePeriod[]) => void = () => undefined
    const delayedStale = new Promise<typeof stalePeriod[]>((resolve) => { resolveStale = resolve })
    mocks.listLecturers.mockResolvedValue(page([
      { id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 },
      { id: 2, name: 'Grace', referenceCode: 'G-1', isActive: true, revision: 1 },
    ]))
    mocks.listUnavailability
      .mockReturnValueOnce(delayedStale)
      .mockResolvedValueOnce([otherPeriod])
      .mockResolvedValueOnce([currentPeriod])

    await renderPage('lecturers')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Edit')
    await act(async () => { editButtons()[0]?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Wednesday · 12:00–13:00')

    await act(async () => { resolveStale([stalePeriod]); await delayedStale })

    expect(document.body.textContent).toContain('Wednesday · 12:00–13:00')
    expect(document.body.textContent).not.toContain('Monday · 08:00–09:00')
  })

  it('clears another resource availability when the new selection cannot be loaded', async () => {
    const firstPeriod = { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0], startTime: '08:00', endTime: '09:00', revision: 1 }
    mocks.listLecturers.mockResolvedValue(page([
      { id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 },
      { id: 2, name: 'Grace', referenceCode: 'G-1', isActive: true, revision: 1 },
    ]))
    mocks.listUnavailability.mockResolvedValueOnce([firstPeriod]).mockRejectedValueOnce(new Error('offline'))

    await renderPage('lecturers')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Edit')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Monday · 08:00–09:00')

    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Could not refresh resource availability')
    expect(document.body.textContent).not.toContain('Monday · 08:00–09:00')
  })

  it('loads and preserves Course eligibility beside Course administration', async () => {
    const course = { id: 1, name: 'Course', nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, studyType: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision: 1, availability: { available: true, reasons: [] }, usage }
    mocks.listCourses.mockResolvedValue(page([course]))
    mocks.getCourseResourceConfiguration.mockResolvedValue({ courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [4], eligibleRoomIds: [5], lecturerCandidates: [{ id: 4, name: 'Ada', referenceCode: 'A', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: 5, name: 'R', referenceCode: 'R', kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
    await renderPage('courses')
    await act(async () => { button('Edit')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(mocks.getCourseResourceConfiguration).toHaveBeenCalledWith(1)
    expect(document.body.textContent).toContain('Eligible lecturers and rooms')
    expect(document.body.textContent).toContain('Ada · A')
  })

  it('never renders or saves eligibility from a previously selected Course after refresh failure', async () => {
    const course = (id: number, name: string) => ({ id, name, nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, studyType: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision: 1, availability: { available: true, reasons: [] }, usage: { ...usage, recordId: id } })
    const firstConfiguration = { courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [4], eligibleRoomIds: [5], lecturerCandidates: [{ id: 4, name: 'First Course Lecturer', referenceCode: 'A', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: 5, name: 'First Course Room', referenceCode: 'R', kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } }
    mocks.listCourses.mockResolvedValue(page([course(1, 'First Course'), course(2, 'Second Course')]))
    mocks.getCourseResourceConfiguration
      .mockResolvedValueOnce(firstConfiguration)
      .mockRejectedValueOnce(new Error('offline'))

    await renderPage('courses')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Edit')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('First Course Lecturer')

    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Could not refresh Course eligibility')
    expect(document.body.textContent).not.toContain('First Course Lecturer')
    expect(button('Save eligibility')).toBeUndefined()
    expect(mocks.updateCourseResourceEligibility).not.toHaveBeenCalled()
  })

  it('does not apply a completed eligibility save to a different selected Course', async () => {
    const course = (id: number, name: string, revision: number) => ({ id, name, nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, studyType: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision, availability: { available: true, reasons: [] }, usage: { ...usage, recordId: id } })
    const configuration = (courseId: number, courseRevision: number, lecturerName: string) => ({ courseId, courseRevision, cohortSize: 20, eligibleLecturerIds: [courseId + 10], eligibleRoomIds: [courseId + 20], lecturerCandidates: [{ id: courseId + 10, name: lecturerName, referenceCode: `L-${courseId}`, kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: courseId + 20, name: `Room ${courseId}`, referenceCode: `R-${courseId}`, kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
    const firstConfiguration = configuration(1, 1, 'First Lecturer')
    const secondConfiguration = configuration(2, 7, 'Second Lecturer')
    let finishFirstSave: (value: typeof firstConfiguration) => void = () => undefined
    const firstSave = new Promise<typeof firstConfiguration>((resolve) => { finishFirstSave = resolve })
    mocks.listCourses.mockResolvedValue(page([course(1, 'First Course', 1), course(2, 'Second Course', 7)]))
    mocks.getCourseResourceConfiguration.mockResolvedValueOnce(firstConfiguration).mockResolvedValueOnce(secondConfiguration)
    mocks.updateCourseResourceEligibility.mockReturnValueOnce(firstSave)

    await renderPage('courses')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Edit')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { button('Save eligibility')?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Second Lecturer')

    await act(async () => { finishFirstSave({ ...firstConfiguration, courseRevision: 2 }); await firstSave })

    expect(document.body.textContent).toContain('Second Lecturer')
    expect(document.body.textContent).not.toContain('First Lecturer')
    expect(button('Save eligibility')).toBeDefined()
  })

  it('explains Cohort growth room cleanup and Courses left without a Room', async () => {
    const cohort = { id: 2, name: 'AI 1', nameRepairRequired: false, studentCount: 20, isActive: true, revision: 1, usage: { ...usage, recordId: 2 } }
    mocks.listCohorts.mockResolvedValue(page([cohort]))
    mocks.updateCohort.mockResolvedValue({
      ...cohort,
      revision: 2,
      cohort: { ...cohort, revision: 2 },
      capacityImpact: {
        removedRelationships: [{ courseId: 7, roomId: 8, courseRevision: 4 }],
        coursesWithoutRooms: [{ id: 7, name: 'Advanced Planning' }],
      },
    })
    await renderPage('cohorts')
    await act(async () => { button('Edit')?.click() })
    await act(async () => { button('Save changes')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Removed 1 newly insufficient room relationship')
    expect(document.body.textContent).toContain('Advanced Planning')
  })

  it('excludes inactive resources from new Course choices', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      courses: [], semesters: [], timeWindows: [],
      lecturers: [
        { id: 1, name: 'Active Lecturer', referenceCode: 'L-A', isActive: true, revision: 1 },
        { id: 2, name: 'Inactive Lecturer', referenceCode: 'L-I', isActive: false, revision: 2 },
      ],
      rooms: [
        { id: 1, name: 'Active Room', referenceCode: 'R-A', capacity: 40, isActive: true, revision: 1 },
        { id: 2, name: 'Inactive Room', referenceCode: 'R-I', capacity: 40, isActive: false, revision: 2 },
      ],
      courseResources: [],
    })

    await renderPage('courses')

    const lecturers = Array.from(document.querySelector<HTMLSelectElement>('select[name="lecturerId"]')!.options).map((item) => item.textContent)
    const rooms = Array.from(document.querySelector<HTMLSelectElement>('select[name="roomId"]')!.options).map((item) => item.textContent)
    expect(lecturers).toContain('Active Lecturer')
    expect(lecturers).not.toContain('Inactive Lecturer')
    expect(rooms).toContain('Active Room')
    expect(rooms).not.toContain('Inactive Room')
  })

  it('reports saved-session usage when it is the only resource retirement blocker', async () => {
    const lecturer = { id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 }
    mocks.listLecturers.mockResolvedValue(page([lecturer]))
    mocks.getResourceUsage.mockResolvedValue({ resourceId: 1, revision: 1, disposition: 'inactivate', activeCourses: [], inactiveCourses: [], sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 } })
    mocks.removeResource.mockResolvedValue({ outcome: 'inactivated', resource: { ...lecturer, isActive: false, revision: 2 }, activeCourses: [], sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 } })

    await renderPage('lecturers')
    await act(async () => { button('Remove')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { button('Place inactive')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.querySelector('[role="status"]')?.textContent).toContain('2 saved sessions across 1 schedule')
    expect(document.querySelector('[role="status"]')?.textContent).not.toContain('active course')
  })
})
