import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listSemesters: vi.fn(), listCohorts: vi.fn(), listCourses: vi.fn(), listStudyTypes: vi.fn(), listTimeWindows: vi.fn(),
  createSemester: vi.fn(), createCohort: vi.fn(), createCourse: vi.fn(), createStudyType: vi.fn(), createTimeWindow: vi.fn(),
  updateSemester: vi.fn(), updateCohort: vi.fn(), updateCourse: vi.fn(), updateStudyType: vi.fn(), updateTimeWindow: vi.fn(),
  deleteAcademicRecord: vi.fn(), setAcademicLifecycle: vi.fn(), getPlanningOptions: vi.fn(),
}))

vi.mock('../api/academicCatalog', async () => ({
  ...(await vi.importActual('../api/academicCatalog')),
  ...Object.fromEntries(Object.entries(mocks).filter(([name]) => name !== 'getPlanningOptions')),
}))
vi.mock('../api/planningOptions', () => ({ getPlanningOptions: mocks.getPlanningOptions }))

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
  for (const name of ['createSemester', 'createCohort', 'createCourse', 'createStudyType', 'createTimeWindow', 'updateSemester', 'updateCohort', 'updateCourse', 'updateStudyType', 'updateTimeWindow', 'deleteAcademicRecord', 'setAcademicLifecycle'] as const) {
    mocks[name].mockResolvedValue(undefined)
  }
})

afterEach(() => { document.body.innerHTML = '' })

async function renderPage() {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<AcademicDataPage onCatalogChanged={() => undefined} />); await new Promise((resolve) => setTimeout(resolve, 0)) })
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent === label)
}

describe('AcademicDataPage', () => {
  it('shows all catalog categories and a usable empty state', async () => {
    await renderPage()
    expect(document.body.textContent).toContain('Semesters')
    expect(document.body.textContent).toContain('Cohorts')
    expect(document.body.textContent).toContain('Courses')
    expect(document.body.textContent).toContain('Study types')
    expect(document.body.textContent).toContain('No semesters yet')
    expect(document.body.textContent).toContain('Create semester')
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

    await renderPage()
    await act(async () => { button('Time windows')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

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

    await renderPage()
    await act(async () => { button('Courses')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    act(() => button('Edit')?.click())

    expect(document.body.textContent).toContain('Assign a Semester to complete repair')
    expect(document.querySelector<HTMLSelectElement>('select[name="semesterId"]')?.value).toBe('')
  })

  it('shows lifecycle failures instead of leaving an unhandled rejection', async () => {
    mocks.listCohorts.mockResolvedValue(page([{
      id: 2, name: 'AI 1', nameRepairRequired: false, studentCount: 20, isActive: true, revision: 1, usage: { ...usage, recordId: 2 },
    }]))
    mocks.setAcademicLifecycle.mockRejectedValue(new Error('Refresh and review the current record.'))

    await renderPage()
    await act(async () => { button('Cohorts')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { button('Archive')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Refresh and review the current record.')
  })
})
