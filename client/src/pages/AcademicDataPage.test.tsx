import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  listSemesters: vi.fn(), listCohorts: vi.fn(), listCourses: vi.fn(), listCohortCalendars: vi.fn(), listTimeWindows: vi.fn(),
  createSemester: vi.fn(), createCohort: vi.fn(), createCourse: vi.fn(), createCohortCalendar: vi.fn(), createTimeWindow: vi.fn(),
  updateSemester: vi.fn(), updateCohort: vi.fn(), updateCourse: vi.fn(), updateCohortCalendar: vi.fn(), updateTimeWindow: vi.fn(),
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
vi.mock('../components/HolidayAdministration', () => ({
  HolidayAdministration: ({ onChanged }: { onChanged: () => void }) => <section><h2>Holiday administration</h2><button onClick={onChanged}>Mock holiday mutation</button></section>,
}))

import { administrationCatalog, legacyCourse, otherSemesterCourse, laterPageCourses, targetCohort, otherCohort, emptyCohort, courseListSemester } from '../test/fixtures/courseLists'
import { AcademicDataPage } from './AcademicDataPage'
import { AcademicCatalogApiError } from '../api/academicCatalog'

const usage = { recordId: 1, revision: 1, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] }
const page = <T,>(items: T[], total = items.length, pageNumber = 1) => ({ page: pageNumber, pageSize: 200, total, items })

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset())
  mocks.listSemesters.mockResolvedValue(page([]))
  mocks.listCohorts.mockResolvedValue(page([]))
  mocks.listCourses.mockResolvedValue(page([]))
  mocks.listCohortCalendars.mockResolvedValue(page([]))
  mocks.listTimeWindows.mockResolvedValue([])
  mocks.getPlanningOptions.mockResolvedValue({ courses: [], semesters: [], timeWindows: [], lecturers: [], rooms: [] })
  mocks.listLecturers.mockResolvedValue(page([]))
  mocks.listRooms.mockResolvedValue(page([]))
  mocks.listUnavailability.mockResolvedValue([])
  mocks.getCourseResourceConfiguration.mockResolvedValue({ courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [], eligibleRoomIds: [], lecturerCandidates: [], roomCandidates: [], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
  for (const name of ['createSemester', 'createCohort', 'createCourse', 'createCohortCalendar', 'createTimeWindow', 'updateSemester', 'updateCohort', 'updateCourse', 'updateCohortCalendar', 'updateTimeWindow', 'deleteAcademicRecord', 'setAcademicLifecycle'] as const) {
    mocks[name].mockResolvedValue(undefined)
  }
})

afterEach(() => { document.body.innerHTML = '' })

it('keeps the unsaved copy correctable after marker-only duplicate feedback and cancels without another request',async()=>{
  mocks.listCohortCalendars.mockResolvedValue(page([{id:1,name:'Form',isActive:true,revision:1,usage}]))
  mocks.listTimeWindows.mockResolvedValue([{id:10,cohortCalendarId:1,kind:'dated',date:'2026-11-09',weekday:null,isIntensive:true,startTime:'09:00',endTime:'12:00',sortOrder:7,isActive:false,revision:3,usage}])
  mocks.createTimeWindow.mockRejectedValueOnce(new AcademicCatalogApiError(409,[{code:'DUPLICATE_TIME_WINDOW',message:'duplicate',field:null}]))
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  await act(async()=>root.render(<AcademicDataPage category="time-windows" onCatalogChanged={vi.fn()}/>))
  await act(async()=>[...document.querySelectorAll('button')].find(b=>b.textContent==='Kopieren')?.click())
  await act(async()=>document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
  expect(document.body.textContent).toContain('Zeitfenster bereits vorhanden')
  expect(document.querySelector<HTMLInputElement>('[name=date]')?.value).toBe('09.11.2026')
  await act(async()=>[...document.querySelectorAll('button')].find(b=>b.textContent==='Kopie verwerfen')?.click())
  expect(mocks.createTimeWindow).toHaveBeenCalledTimes(1)
  expect(mocks.updateTimeWindow).not.toHaveBeenCalled()
})

it('opens an independent unsaved marked copy, cancels without writes and submits one ordinary create without source identity', async () => {
  mocks.listCohortCalendars.mockResolvedValue(page([{id:1,name:'Form',isActive:true,revision:1,usage}]))
  mocks.listTimeWindows.mockResolvedValue([{id:10,cohortCalendarId:1,kind:'dated',date:'2026-11-09',weekday:null,isIntensive:true,startTime:'09:00',endTime:'12:00',sortOrder:7,isActive:true,revision:3,usage}])
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  await act(async()=>root.render(<AcademicDataPage category="time-windows" onCatalogChanged={vi.fn()}/>))
  const copy=[...document.querySelectorAll('button')].find(b=>b.textContent==='Kopieren')!
  expect(copy).toBeDefined()
  await act(async()=>{ copy.focus();copy.click() })
  expect(document.body.textContent).toContain('Ungespeicherte Kopie')
  expect(document.activeElement?.getAttribute('name')).toBe('cohortCalendarId')
  expect(document.querySelector<HTMLInputElement>('input[name="isIntensive"]')?.checked).toBe(true)
  expect(mocks.createTimeWindow).not.toHaveBeenCalled()
  await act(async()=>[...document.querySelectorAll('button')].find(b=>b.textContent==='Kopie verwerfen')?.click())
  expect(mocks.createTimeWindow).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(copy)
  await act(async()=>copy.click())
  await act(async()=>document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
  expect(mocks.createTimeWindow).toHaveBeenCalledTimes(1)
  const [owner,payload]=mocks.createTimeWindow.mock.calls[0]
  expect(owner).toBe(1)
  expect(payload).toMatchObject({kind:'dated',date:'2026-11-09',weekday:null,isIntensive:true,sortOrder:7})
  expect(payload).not.toHaveProperty('id')
  expect(payload).not.toHaveProperty('expectedRevision')
  expect(mocks.updateTimeWindow).not.toHaveBeenCalled()
})

it('groups weekly before dated windows in chronological order and invalidates at save acknowledgement', async () => {
  mocks.listCohortCalendars.mockResolvedValue(page([{ id:1,name:'Form',isActive:true,revision:1,usage }]))
  mocks.listTimeWindows.mockResolvedValue([
    {id:1,cohortCalendarId:1,kind:'dated',date:'2026-11-10',weekday:null,isIntensive:true,startTime:'09:00',endTime:'12:00',isActive:true,revision:1,usage,overlapNotice:'Überschneidung schafft keine zusätzliche Kapazität.'},
    {id:2,cohortCalendarId:1,weekday:4,startTime:'09:00',endTime:'12:00',isActive:true,revision:1,usage},
    {id:3,cohortCalendarId:1,kind:'dated',date:'2026-11-09',weekday:null,isIntensive:false,startTime:'09:00',endTime:'12:00',isActive:true,revision:1,usage},
  ])
  const changed = vi.fn()
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<AcademicDataPage category="time-windows" onCatalogChanged={changed} />))
  const text = document.body.textContent!
  expect(text.indexOf('Freitag')).toBeLessThan(text.indexOf('09.11.2026'))
  expect(text.indexOf('09.11.2026')).toBeLessThan(text.indexOf('10.11.2026'))
  expect(text).toContain('Intensivwoche')
  expect(text).toContain('Überschneidung schafft keine zusätzliche Kapazität.')
  mocks.listCohortCalendars.mockRejectedValue(new Error('reload failed'))
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', {bubbles:true,cancelable:true})))
  expect(changed).toHaveBeenCalledTimes(1)
})

async function renderPage(category: 'semesters' | 'cohorts' | 'courses' | 'cohort-calendars' | 'time-windows' | 'lecturers' | 'rooms' | 'holidays' = 'semesters') {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<AcademicDataPage category={category} onCatalogChanged={() => undefined} />); await new Promise((resolve) => setTimeout(resolve, 0)) })
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent === label)
}

describe('AcademicDataPage', () => {
  it('mounts holiday administration and forwards only its successful-change signal', async () => {
    const changed = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => { root.render(<AcademicDataPage category="holidays" onCatalogChanged={changed} />) })

    expect(document.body.textContent).toContain('Holiday administration')
    act(() => button('Mock holiday mutation')?.click())
    expect(changed).toHaveBeenCalledOnce()
  })

  it('renders its controlled category without page-local navigation', async () => {
    await renderPage()
    expect(document.body.textContent).toContain('Semester')
    expect(document.body.textContent).toContain('Noch keine Semester')
    expect(document.body.textContent).toContain('Erstellen: Semester')
    expect(document.querySelector('nav')).toBeNull()
  })

  it('cleans up edit state and loads again when the controlled category changes', async () => {
    mocks.listSemesters.mockResolvedValue(page([{
      id: 1, name: 'Fall 2026', startDate: '2026-09-01', endDate: '2027-01-31',
      isActive: true, revision: 1, nameRepairRequired: false, usage,
    }]))
    const root = await renderPage('semesters')
    act(() => button('Bearbeiten')?.click())
    expect(button('Bearbeitung abbrechen')).toBeDefined()
    act(() => root.render(<AcademicDataPage category="cohorts" onCatalogChanged={() => undefined} />))
    expect(button('Bearbeitung abbrechen')).toBeUndefined()
    expect(document.body.textContent).toContain('Erstellen: Kohorte')
    expect(document.body.textContent).not.toContain('Bearbeiten: Kohorte')
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

  it('loads Time Windows from every Cohort Calendar', async () => {
    const cohortCalendars = [1, 2].map((id) => ({ id, name: `Type ${id}`, nameRepairRequired: false, timeWindows: [], isActive: true, revision: 1, usage: { ...usage, recordId: id } }))
    mocks.listCohortCalendars.mockResolvedValue(page(cohortCalendars))
    mocks.listTimeWindows.mockImplementation(async (cohortCalendarId) => [{
      id: cohortCalendarId, cohortCalendarId, weekday: cohortCalendarId - 1, startTime: '08:00', endTime: '10:00', sortOrder: 0,
      isActive: cohortCalendarId === 1, revision: 1, availability: { available: cohortCalendarId === 1, reasons: cohortCalendarId === 1 ? [] : ['RECORD_INACTIVE'] }, usage: { ...usage, recordId: cohortCalendarId },
    }])

    await renderPage('time-windows')

    expect(mocks.listTimeWindows).toHaveBeenCalledWith(1)
    expect(mocks.listTimeWindows).toHaveBeenCalledWith(2)
    expect(document.querySelectorAll('.catalog-list li')).toHaveLength(2)
    expect(document.body.textContent).toContain('Type 1 · Wöchentlich: Montag, 08:00–10:00')
    expect(document.body.textContent).toContain('Type 2 · Wöchentlich: Dienstag, 08:00–10:00')
    expect(document.body.textContent).not.toContain('Day 1')

    const status = document.querySelector<HTMLSelectElement>('.page-header select')!
    await act(async () => { status.value = 'active'; status.dispatchEvent(new Event('change', { bubbles: true })); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.querySelectorAll('.catalog-list li')).toHaveLength(1)
  })

  it('keeps a migrated unassigned Course editable for Semester repair', async () => {
    const course = {
      id: 9, name: 'Legacy Course', nameRepairRequired: false, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4,
      semester: null, cohort: { id: 2, name: 'AI 1' }, cohortCalendar: { id: 3, name: 'Full-time' },
      lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R1' }, isActive: true, revision: 1,
      availability: { available: false, reasons: ['SEMESTER_ASSIGNMENT_REQUIRED'] }, usage: { ...usage, recordId: 9 },
    }
    mocks.listCourses.mockResolvedValue(page([course]))
    mocks.listSemesters.mockResolvedValue(page([{ id: 1, name: 'Fall', nameRepairRequired: false, startDate: '2026-01-01', endDate: '2026-06-01', isActive: true, revision: 1, usage }]))
    mocks.listCohorts.mockResolvedValue(page([{ id: 2, name: 'AI 1' }]))
    mocks.listCohortCalendars.mockResolvedValue(page([{ id: 3, name: 'Full-time' }]))
    mocks.getPlanningOptions.mockResolvedValue({ courses: [], semesters: [], timeWindows: [], lecturers: [{ id: 4, name: 'Ada' }], rooms: [{ id: 5, name: 'R1' }] })

    await renderPage('courses')
    act(() => button('Bearbeiten')?.click())

    expect(document.body.textContent).toContain('Ordnen Sie vor dem Speichern')
    expect(document.querySelector<HTMLSelectElement>('select[name="semesterId"]')?.value).toBe('')
  })

  it('shows lifecycle failures instead of leaving an unhandled rejection', async () => {
    mocks.listCohorts.mockResolvedValue(page([{
      id: 2, name: 'AI 1', nameRepairRequired: false, studentCount: 20, isActive: true, revision: 1, usage: { ...usage, recordId: 2 },
    }]))
    mocks.setAcademicLifecycle.mockRejectedValue(new Error('Refresh and review the current record.'))

    await renderPage('cohorts')
    await act(async () => { button('Archivieren')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('aktuellen Stand neu')
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
    await act(async () => { button('Bearbeiten')?.click() })
    const refresh = button('Aktualisieren')
    await act(async () => { refresh?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Ressourcen konnten nicht aktualisiert werden')
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
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Bearbeiten')
    await act(async () => { editButtons()[0]?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Dienstag · 10:00–11:00')

    await act(async () => { resolveFirst([firstPeriod]); await delayedFirst })

    expect(document.body.textContent).toContain('Dienstag · 10:00–11:00')
    expect(document.body.textContent).not.toContain('Montag · 08:00–09:00')
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
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Bearbeiten')
    await act(async () => { editButtons()[0]?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Mittwoch · 12:00–13:00')

    await act(async () => { resolveStale([stalePeriod]); await delayedStale })

    expect(document.body.textContent).toContain('Mittwoch · 12:00–13:00')
    expect(document.body.textContent).not.toContain('Montag · 08:00–09:00')
  })

  it('clears another resource availability when the new selection cannot be loaded', async () => {
    const firstPeriod = { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0], startTime: '08:00', endTime: '09:00', revision: 1 }
    mocks.listLecturers.mockResolvedValue(page([
      { id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 },
      { id: 2, name: 'Grace', referenceCode: 'G-1', isActive: true, revision: 1 },
    ]))
    mocks.listUnavailability.mockResolvedValueOnce([firstPeriod]).mockRejectedValueOnce(new Error('offline'))

    await renderPage('lecturers')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Bearbeiten')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Montag · 08:00–09:00')

    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Ressourcenverfügbarkeit konnte nicht aktualisiert werden')
    expect(document.body.textContent).not.toContain('Montag · 08:00–09:00')
  })

  it('loads and preserves Course eligibility beside Course administration', async () => {
    const course = { id: 1, name: 'Course', nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, cohortCalendar: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision: 1, availability: { available: true, reasons: [] }, usage }
    mocks.listCourses.mockResolvedValue(page([course]))
    mocks.getCourseResourceConfiguration.mockResolvedValue({ courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [4], eligibleRoomIds: [5], lecturerCandidates: [{ id: 4, name: 'Ada', referenceCode: 'A', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: 5, name: 'R', referenceCode: 'R', kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
    await renderPage('courses')
    await act(async () => { button('Bearbeiten')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(mocks.getCourseResourceConfiguration).toHaveBeenCalledWith(1)
    expect(document.body.textContent).toContain('Geeignete Lehrende und Räume')
    expect(document.body.textContent).toContain('Ada · A')
  })

  it('never renders or saves eligibility from a previously selected Course after refresh failure', async () => {
    const course = (id: number, name: string) => ({ id, name, nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, cohortCalendar: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision: 1, availability: { available: true, reasons: [] }, usage: { ...usage, recordId: id } })
    const firstConfiguration = { courseId: 1, courseRevision: 1, cohortSize: 20, eligibleLecturerIds: [4], eligibleRoomIds: [5], lecturerCandidates: [{ id: 4, name: 'First Course Lecturer', referenceCode: 'A', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: 5, name: 'First Course Room', referenceCode: 'R', kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } }
    mocks.listCourses.mockResolvedValue(page([course(1, 'First Course'), course(2, 'Second Course')]))
    mocks.getCourseResourceConfiguration
      .mockResolvedValueOnce(firstConfiguration)
      .mockRejectedValueOnce(new Error('offline'))

    await renderPage('courses')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Bearbeiten')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('First Course Lecturer')

    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('Ressourceneignung für die ausgewählte Lehrveranstaltung konnte nicht aktualisiert werden')
    expect(document.body.textContent).not.toContain('First Course Lecturer')
    expect(button('Eignung speichern')).toBeUndefined()
    expect(mocks.updateCourseResourceEligibility).not.toHaveBeenCalled()
  })

  it('does not apply a completed eligibility save to a different selected Course', async () => {
    const course = (id: number, name: string, revision: number) => ({ id, name, nameRepairRequired: false, totalUnits: 4, minSessionUnits: 2, maxSessionUnits: 4, semester: { id: 1, name: 'Fall' }, cohort: { id: 2, name: 'C' }, cohortCalendar: { id: 3, name: 'Type' }, lecturer: { id: 4, name: 'Ada' }, room: { id: 5, name: 'R' }, isActive: true, revision, availability: { available: true, reasons: [] }, usage: { ...usage, recordId: id } })
    const configuration = (courseId: number, courseRevision: number, lecturerName: string) => ({ courseId, courseRevision, cohortSize: 20, eligibleLecturerIds: [courseId + 10], eligibleRoomIds: [courseId + 20], lecturerCandidates: [{ id: courseId + 10, name: lecturerName, referenceCode: `L-${courseId}`, kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], roomCandidates: [{ id: courseId + 20, name: `Room ${courseId}`, referenceCode: `R-${courseId}`, kind: 'room', capacity: 30, isActive: true, isEligible: true, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }], preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true } })
    const firstConfiguration = configuration(1, 1, 'First Lecturer')
    const secondConfiguration = configuration(2, 7, 'Second Lecturer')
    let finishFirstSave: (value: typeof firstConfiguration) => void = () => undefined
    const firstSave = new Promise<typeof firstConfiguration>((resolve) => { finishFirstSave = resolve })
    mocks.listCourses.mockResolvedValue(page([course(1, 'First Course', 1), course(2, 'Second Course', 7)]))
    mocks.getCourseResourceConfiguration.mockResolvedValueOnce(firstConfiguration).mockResolvedValueOnce(secondConfiguration)
    mocks.updateCourseResourceEligibility.mockReturnValueOnce(firstSave)

    await renderPage('courses')
    const editButtons = () => Array.from(document.querySelectorAll('button')).filter((item) => item.textContent === 'Bearbeiten')
    await act(async () => { editButtons()[0]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { button('Eignung speichern')?.click() })
    await act(async () => { editButtons()[1]?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('Second Lecturer')

    await act(async () => { finishFirstSave({ ...firstConfiguration, courseRevision: 2 }); await firstSave })

    expect(document.body.textContent).toContain('Second Lecturer')
    expect(document.body.textContent).not.toContain('First Lecturer')
    expect(button('Eignung speichern')).toBeDefined()
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
    await act(async () => { button('Bearbeiten')?.click() })
    await act(async () => { button('Änderungen speichern')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('1 wegen zu geringer Kapazität ungültige Raumzuordnung entfernt')
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
    mocks.getResourceUsage.mockResolvedValue({ resourceId: 1, revision: 1, disposition: 'inactivate', activeCourses: [], inactiveCourses: [], sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 }, examUsage: { examSessionCount: 0, currentConfigurationCount: 0 } })
    mocks.removeResource.mockResolvedValue({ outcome: 'inactivated', resource: { ...lecturer, isActive: false, revision: 2 }, activeCourses: [], sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 }, examUsage: { examSessionCount: 0, currentConfigurationCount: 0 } })

    await renderPage('lecturers')
    await act(async () => { button('Entfernen')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    await act(async () => { button('Inaktiv setzen')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.querySelector('[role="status"]')?.textContent).toContain('2 gespeicherte Termine in 1 Planung')
    expect(document.querySelector('[role="status"]')?.textContent).not.toContain('aktive Lehrveranstaltung')
  })
})


it('I-005 intersects full paginated course catalog with semester/cohort and preserves an open editor', async () => {
  const catalog = [...laterPageCourses, ...administrationCatalog, legacyCourse, otherSemesterCourse]
  mocks.listCourses.mockImplementation(async (_status, pageNumber) => page(catalog.slice((pageNumber - 1) * 200, pageNumber * 200), catalog.length, pageNumber))
  mocks.listSemesters.mockResolvedValue(page([courseListSemester, { ...courseListSemester, id: 2, name: '2027 W' }]))
  mocks.listCohorts.mockResolvedValue(page([targetCohort, otherCohort, emptyCohort]))
  mocks.listCohortCalendars.mockResolvedValue(page([{ id: 1, name: 'Vollzeit' }]))
  function Harness() {
    const [filters, setFilters] = useState<{semesterId: number | null; cohortId: number | null}>({semesterId: null, cohortId: null})
    return <AcademicDataPage category="courses" onCatalogChanged={vi.fn()} courseFilters={filters} onCourseFiltersChange={setFilters} />
  }
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<Harness />))
  expect(document.body.textContent).toContain('Legacy ohne Semester')
  const semester = document.querySelector<HTMLSelectElement>('[aria-label="Semester filtern"]')!
  const cohort = document.querySelector<HTMLSelectElement>('[aria-label="Kohorte filtern"]')!
  expect(semester).not.toBeNull()
  act(() => { semester.value = '1'; semester.dispatchEvent(new Event('change', {bubbles: true})); })
  act(() => { cohort.value = String(targetCohort.id); cohort.dispatchEvent(new Event('change', {bubbles: true})); })
  expect(document.querySelectorAll('.catalog-list li')).toHaveLength(11)
  expect(document.body.textContent).not.toContain('Legacy ohne Semester')
  await act(async () => document.querySelector<HTMLButtonElement>('.catalog-list button')!.click())
  const name = document.querySelector<HTMLInputElement>('.catalog-grid section:nth-child(2) input')!
  act(() => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')!.set!.call(name, 'Unsaved course'); name.dispatchEvent(new Event('input', { bubbles: true })) })
  act(() => { cohort.value = String(emptyCohort.id); cohort.dispatchEvent(new Event('change', {bubbles: true})); })
  expect(document.querySelectorAll('.catalog-list li')).toHaveLength(0)
  expect(name.value).toBe('Unsaved course')
  expect(document.body.textContent).toContain('Keine Treffer')
  act(() => button('Kohortenfilter zurücksetzen')!.click())
  expect(document.querySelectorAll('.catalog-list li')).toHaveLength(204)
  expect(name.value).toBe('Unsaved course')
  expect(mocks.createCourse).not.toHaveBeenCalled()
  expect(mocks.updateCourse).not.toHaveBeenCalled()
  expect(mocks.setAcademicLifecycle).not.toHaveBeenCalled()
  expect(mocks.listCourses).toHaveBeenCalledWith('all', 2, 200)
  act(() => root.unmount())
})


it('I-005 does not report successful zero matches when course retrieval fails', async () => {
  mocks.listCourses.mockRejectedValue(new Error('offline'))
  await renderPage('courses')
  expect(document.body.textContent).toContain('konnten nicht geladen werden')
  expect(document.body.textContent).not.toContain('0 Treffer')
  expect(document.body.textContent).not.toContain('Keine Lehrveranstaltungen in diesem Semester')
})


it('I-005 applies status retrieval alongside filters and resets cohort only on semester scope changes', async () => {
  mocks.listCourses.mockImplementation(async (status) => page(administrationCatalog.filter((course) => status === 'all' || course.isActive === (status === 'active'))))
  mocks.listSemesters.mockResolvedValue(page([courseListSemester, { ...courseListSemester, id: 2, name: '2027 W' }]))
  mocks.listCohorts.mockResolvedValue(page([targetCohort, otherCohort, emptyCohort]))
  function Harness() {
    const [filters, setFilters] = useState<{semesterId: number | null; cohortId: number | null}>({semesterId: 1, cohortId: targetCohort.id})
    return <AcademicDataPage category="courses" onCatalogChanged={vi.fn()} courseFilters={filters} onCourseFiltersChange={setFilters} />
  }
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<Harness />))
  expect(document.querySelectorAll('.catalog-list li')).toHaveLength(11)
  const status = document.querySelector<HTMLSelectElement>('.page-header select')!
  await act(async () => { status.value = 'inactive'; status.dispatchEvent(new Event('change', {bubbles: true})) })
  expect(mocks.listCourses).toHaveBeenLastCalledWith('inactive', 1, 200)
  expect(document.querySelectorAll('.catalog-list li')).toHaveLength(0)
  expect(document.querySelector<HTMLSelectElement>('[aria-label="Kohorte filtern"]')!.value).toBe('101')
  const semester = document.querySelector<HTMLSelectElement>('[aria-label="Semester filtern"]')!
  act(() => { semester.value = '2'; semester.dispatchEvent(new Event('change', {bubbles: true})) })
  expect(document.querySelector<HTMLSelectElement>('[aria-label="Kohorte filtern"]')!.value).toBe('')
  act(() => { semester.value = '1'; semester.dispatchEvent(new Event('change', {bubbles: true})) })
  expect(document.querySelector<HTMLSelectElement>('[aria-label="Kohorte filtern"]')!.value).toBe('')
  act(() => root.unmount())
})
