import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  getPlanningOptions: vi.fn(),
  getGenerationConstraints: vi.fn(),
  getDraftSchedules: vi.fn(),
  generateDraftSchedule: vi.fn(),
  clearGenerationConstraints: vi.fn(),
  updateDraftSession: vi.fn(),
  createManualDraftSession: vi.fn(),
  deleteDraftSession: vi.fn(),
  clearCourseDraft: vi.fn(),
  prepare: vi.fn(),
  generateBatch: vi.fn(),
  getExamPlanningOverview: vi.fn(),
  saveExamConfiguration: vi.fn(),
  createManualExam: vi.fn(),
  updateExam: vi.fn(),
  deleteExam: vi.fn(),
  getScheduleLifecycle: vi.fn(),
  createWorkingRevision: vi.fn(),
  prepareSchedulePublication: vi.fn(),
  transitionScheduleRevision: vi.fn(),
  getScheduleRevision: vi.fn(),
}))

vi.mock('../api/planningOptions', () => ({ getPlanningOptions: mocks.getPlanningOptions }))
vi.mock('../api/draftSchedule', () => ({
  getGenerationConstraints: mocks.getGenerationConstraints,
  getDraftSchedules: mocks.getDraftSchedules,
  generateDraftSchedule: mocks.generateDraftSchedule,
  clearGenerationConstraints: mocks.clearGenerationConstraints,
  updateDraftSession: mocks.updateDraftSession,
  createManualDraftSession: mocks.createManualDraftSession,
  deleteDraftSession: mocks.deleteDraftSession,
  clearCourseDraft: mocks.clearCourseDraft,
}))
vi.mock('../api/conflictAwareGeneration', () => ({
  prepareConflictAwareGeneration: mocks.prepare,
  generateConflictAwareSchedules: mocks.generateBatch,
}))
vi.mock('../api/examScheduling', () => ({
  getExamPlanningOverview: mocks.getExamPlanningOverview,
  saveExamConfiguration: mocks.saveExamConfiguration,
  createManualExam: mocks.createManualExam,
  updateExam: mocks.updateExam,
  deleteExam: mocks.deleteExam,
}))
vi.mock('../api/scheduleLifecycle', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/scheduleLifecycle')>()),
  getScheduleLifecycle: mocks.getScheduleLifecycle,
  createWorkingRevision: mocks.createWorkingRevision,
  prepareSchedulePublication: mocks.prepareSchedulePublication,
  transitionScheduleRevision: mocks.transitionScheduleRevision,
  getScheduleRevision: mocks.getScheduleRevision,
}))

import { CourseSchedulePage } from './CourseSchedulePage'
import { draftScheduleFixture, generationConstraintsFixture } from '../test/draftScheduleFixtures'
import { lifecycleOverviewFixture } from '../test/lifecycleFixtures'

const entity = (id: number, name: string) => ({ id, name })
const options = {
  courses: [1, 2].map((id) => ({
    id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
    lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
  })),
  semesters: [{ id: 1, name: 'Fall 2026', startDate: '2026-09-07', endDate: '2026-12-20' }],
  timeWindows: [], rooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', capacity: 40, isActive: true, revision: 1 }], lecturers: [], courseResources: [],
}
const examOverview = {
  semesterId: 1,
  institutionToday: '2026-07-20',
  courses: [1, 2].map((courseId) => ({
    courseId,
    courseName: `Course ${courseId}`,
    semesterId: 1,
    cohortId: courseId,
    cohortName: `C${courseId}`,
    enabled: false,
    configuration: null,
    finalTeachingAnchor: null,
    activeExam: null,
    pastExams: [],
    generationEligibility: { eligible: false, code: 'DISABLED', message: 'Exam planning is disabled.' },
    inputSnapshotToken: `exam-course-${courseId}`,
  })),
}

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset())
  mocks.getPlanningOptions.mockResolvedValue(options)
  mocks.getGenerationConstraints.mockResolvedValue(generationConstraintsFixture)
  mocks.getDraftSchedules.mockResolvedValue([])
  mocks.getExamPlanningOverview.mockResolvedValue(examOverview)
  mocks.getScheduleLifecycle.mockResolvedValue(lifecycleOverviewFixture())
})

afterEach(() => { document.body.innerHTML = '' })

async function renderPage() {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => {
    root.render(<CourseSchedulePage catalogRevision={0} />)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
  return root
}

function button(label: string) {
  return [...document.querySelectorAll('button')].find((item) => item.textContent === label)
}

function summaryValue(label: string) {
  const term = [...document.querySelectorAll('dt')].find((item) => item.textContent === label)
  return term?.parentElement?.querySelector('dd')?.textContent
}

describe('CourseSchedulePage multi-course mode', () => {
  it('blocks further exam writes when an authoritative post-save refresh fails', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      lecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', isActive: true, revision: 1 }],
      courseResources: [{
        courseId: 1,
        eligibleLecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        eligibleRooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', kind: 'room', capacity: 40, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
      }],
    })
    const savedState = {
      ...examOverview.courses[0], enabled: true,
      configuration: { id: 10, revision: 1, identifier: 'Exam', durationMinutes: 90, recommendedStartOverride: null, recommendedEndOverride: null, requiredCapacity: 1, examType: 'Written', responsibleLecturerId: 1, configurationConsumed: false, recommendedStartDate: null, recommendedEndDate: null, recommendationWasOverridden: false },
      generationEligibility: { eligible: false, code: 'FINAL_TEACHING_SESSION_MISSING', message: 'Save teaching first.' },
    }
    mocks.saveExamConfiguration.mockResolvedValue(savedState)
    await renderPage()
    mocks.getExamPlanningOverview.mockRejectedValueOnce(new Error('refresh failed'))
    const requirement = [...document.querySelectorAll('label')].find((item) => item.textContent?.includes('This course requires an exam'))?.querySelector<HTMLInputElement>('input')
    await act(async () => requirement?.click())
    await act(async () => { button('Save exam requirement')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('saved, but the semester review could not be refreshed')
    expect(requirement?.disabled).toBe(true)
    expect(button('Saving…')?.disabled).toBe(true)
  })

  it('does not warn for disabled courses and explains an enabled course without a final teaching anchor', async () => {
    const root = await renderPage()
    expect(document.body.textContent).not.toContain('No final teaching session is saved yet.')

    await act(async () => root.unmount())
    document.body.innerHTML = ''

    mocks.getExamPlanningOverview.mockResolvedValue({
      ...examOverview,
      courses: examOverview.courses.map((course) => course.courseId === 1 ? {
        ...course,
        enabled: true,
        configuration: {
          id: 10, revision: 1, identifier: 'Final exam', durationMinutes: 90,
          recommendedStartOverride: null, recommendedEndOverride: null,
          requiredCapacity: 30, examType: 'Written', responsibleLecturerId: 1,
          configurationConsumed: false, recommendedStartDate: null,
          recommendedEndDate: null, recommendationWasOverridden: false,
        },
        generationEligibility: { eligible: false, code: 'FINAL_TEACHING_SESSION_MISSING', message: 'A final teaching session is required.' },
      } : course),
    })
    await renderPage()
    expect(document.body.textContent).toContain('No final teaching session is saved yet.')
    expect(document.body.textContent).toContain('automatic and manual placement remain unavailable')
  })

  it('renders scheduling content without page-owned or dead hash navigation', async () => {
    await renderPage()
    expect(document.querySelector('nav')).toBeNull()
    expect(document.querySelectorAll('a[href^="#"]')).toHaveLength(0)
    expect(document.body.textContent).not.toContain('Dashboard')
    expect(document.body.textContent).toContain('Resource Planner')
  })

  it('keeps focused single-course constraints isolated while selecting and generating several courses', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, unavailableDates: ['2026-10-26', '2026-11-02'], sharedSnapshotToken: 'shared', replacementCourseIds: [],
      courses: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: `course-${courseId}` })),
    })
    mocks.generateBatch.mockResolvedValue({
      semesterId: 1, summary: { total: 2, complete: 2, improvedPartial: 0, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 16, remainingUnits: 0, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
      outcomes: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, status: 'complete', draftScheduleId: courseId, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] })),
    })
    await renderPage()
    act(() => button('Several courses')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    const unavailableDates = document.querySelector<HTMLInputElement>('input[type="text"]')
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(unavailableDates, '2026-11-02, 2026-10-26, 2026-10-26')
      unavailableDates?.dispatchEvent(new Event('input', { bubbles: true }))
    })
    expect(document.body.textContent).toContain('2 selected')
    await act(async () => {
      button('Optimize selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.prepare).toHaveBeenCalledWith(1, 11, [1, 2], ['2026-10-26', '2026-11-02'])
    expect(mocks.generateBatch).toHaveBeenCalledOnce()
    expect(document.body.textContent).toContain('2 complete · 0 improved partial')
    expect(mocks.getGenerationConstraints).toHaveBeenCalledTimes(1)
  })

  it('clears the batch selection when the semester changes', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [...options.semesters, { id: 2, name: 'Spring 2027', startDate: '2027-02-01', endDate: '2027-06-20' }],
      courses: [
        { ...options.courses[0], semesterId: 1, availability: { available: true, reasons: [] } },
        { ...options.courses[1], semesterId: 2, availability: { available: true, reasons: [] } },
      ],
    })
    await renderPage()
    act(() => button('Several courses')?.click())
    act(() => document.querySelector<HTMLInputElement>('input[type="checkbox"]')?.click())
    expect(document.body.textContent).toContain('1 selected')

    const semesterSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')
    await act(async () => {
      if (semesterSelect) semesterSelect.value = '2'
      semesterSelect?.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('0 selected')
  })

  it('cancels replacement confirmation without execution', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, unavailableDates: [], sharedSnapshotToken: 'shared', replacementCourseIds: [1],
      courses: [
        { courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: 5, draftRevision: 2, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, inputSnapshotToken: 'course-1' },
        { courseId: 2, courseName: 'Course 2', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-2' },
      ],
    })
    await renderPage()
    act(() => button('Several courses')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Optimize selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).toContain('Optimize existing Draft Schedules?')
    act(() => button('Cancel')?.click())
    expect(mocks.generateBatch).not.toHaveBeenCalled()
    expect(document.body.textContent).not.toContain('Optimize existing Draft Schedules?')
  })

  it('re-prepares failed and stale courses before retrying and refreshes each result', async () => {
    const preparation = {
      semesterId: 1, unavailableDates: [], sharedSnapshotToken: 'shared', replacementCourseIds: [],
      courses: [{ courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-1' }],
    }
    mocks.prepare.mockResolvedValue(preparation)
    mocks.generateBatch
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 1, complete: 0, improvedPartial: 0, unchanged: 0, failed: 0, stale: 1, scheduledUnits: 0, remainingUnits: 8, elapsedMilliseconds: 100, optimalForPreparedSnapshot: false },
        outcomes: [{ courseId: 1, courseName: 'Course 1', status: 'stale', draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, saved: false, improvement: null, reasons: [{ code: 'STALE_PLANNING_INPUT', message: 'Refresh.', relatedCount: 1 }], errors: [] }],
      })
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 1, complete: 1, improvedPartial: 0, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 8, remainingUnits: 0, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
        outcomes: [{ courseId: 1, courseName: 'Course 1', status: 'complete', draftScheduleId: 1, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] }],
      })
    await renderPage()
    act(() => button('Several courses')?.click())
    act(() => document.querySelector<HTMLInputElement>('input[type="checkbox"]')?.click())
    await act(async () => {
      button('Optimize selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).toContain('1 stale')

    await act(async () => {
      button('Retry failed or stale courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(mocks.prepare).toHaveBeenCalledTimes(2)
    expect(mocks.prepare).toHaveBeenLastCalledWith(1, 11, [1], [])
    expect(mocks.generateBatch).toHaveBeenCalledTimes(2)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(3)
    expect(document.body.textContent).toContain('1 complete')
  })

  it('confirms replacement, shows mixed outcomes, and requires renewed confirmation for retry', async () => {
    const thirdCourse = { ...options.courses[1], id: 3, name: 'Course 3', lecturer: entity(3, 'L3'), cohort: entity(3, 'C3'), room: entity(3, 'R3') }
    mocks.getPlanningOptions.mockResolvedValue({ ...options, courses: [...options.courses, thirdCourse] })
    const initialPreparation = {
      semesterId: 1, unavailableDates: [], sharedSnapshotToken: 'shared-1', replacementCourseIds: [1],
      courses: [
        { courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: 5, draftRevision: 2, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, inputSnapshotToken: 'course-1' },
        { courseId: 2, courseName: 'Course 2', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-2' },
        { courseId: 3, courseName: 'Course 3', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-3' },
      ],
    }
    const retryPreparation = {
      semesterId: 1, unavailableDates: [], sharedSnapshotToken: 'shared-2', replacementCourseIds: [1],
      courses: [
        { ...initialPreparation.courses[0], draftRevision: 3, inputSnapshotToken: 'course-1-fresh' },
        { ...initialPreparation.courses[2], inputSnapshotToken: 'course-3-fresh' },
      ],
    }
    mocks.prepare.mockResolvedValueOnce(initialPreparation).mockResolvedValueOnce(retryPreparation)
    mocks.generateBatch
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 3, complete: 1, improvedPartial: 0, unchanged: 0, failed: 1, stale: 1, scheduledUnits: 8, remainingUnits: 12, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
        outcomes: [
          { courseId: 1, courseName: 'Course 1', status: 'stale', draftScheduleId: 5, draftRevision: 3, scheduledUnits: 4, remainingUnits: 4, saved: false, improvement: null, reasons: [{ code: 'STALE_PLANNING_INPUT', message: 'Refresh.', relatedCount: 1 }], errors: [] },
          { courseId: 2, courseName: 'Course 2', status: 'complete', draftScheduleId: 6, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] },
          { courseId: 3, courseName: 'Course 3', status: 'failed', draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, saved: false, improvement: null, reasons: [], errors: [{ code: 'INVALID_PLANNING_INPUT', message: 'Unavailable.' }] },
        ],
      })
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 2, complete: 2, improvedPartial: 0, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 16, remainingUnits: 0, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
        outcomes: [1, 3].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, status: 'complete', draftScheduleId: courseId + 10, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] })),
      })
    await renderPage()
    act(() => button('Several courses')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click(); boxes[2].click() })
    await act(async () => {
      button('Optimize selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).toContain('Optimize existing Draft Schedules?')

    await act(async () => {
      button('Confirm optimization')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.generateBatch).toHaveBeenLastCalledWith(initialPreparation, true)
    expect(document.body.textContent).toContain('1 complete')
    expect(document.body.textContent).toContain('1 failed')
    expect(document.body.textContent).toContain('1 stale')

    await act(async () => {
      button('Retry failed or stale courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.prepare).toHaveBeenLastCalledWith(1, 11, [1, 3], [])
    expect(mocks.generateBatch).toHaveBeenCalledTimes(1)
    expect(document.body.textContent).toContain('Optimize existing Draft Schedules?')

    await act(async () => {
      button('Confirm optimization')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.generateBatch).toHaveBeenLastCalledWith(retryPreparation, true)
    expect(mocks.generateBatch).toHaveBeenCalledTimes(2)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(3)
  })
})

describe('CourseSchedulePage academic option compatibility', () => {
  it('filters by assigned semester and retains an invalid prior selection without substitution', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [...options.semesters, { id: 2, name: 'Spring 2027', startDate: '2027-02-01', endDate: '2027-06-20' }],
      courses: [
        { ...options.courses[0], semesterId: 1, availability: { available: true, reasons: [] } },
        { ...options.courses[1], semesterId: 2, availability: { available: false, reasons: ['MISSING_ACTIVE_TIME_WINDOW'] } },
      ],
    })
    await renderPage()
    const selects = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    act(() => { selects[1].value = '2'; selects[1].dispatchEvent(new Event('change', { bubbles: true })) })
    expect(selects[0].value).toBe('1')
    expect(document.body.textContent).toContain('not assigned to the selected Semester')
    expect((button('Generate') as HTMLButtonElement).disabled).toBe(true)
  })

  it('refreshes options without replacing a still-valid selected Course', async () => {
    const root = await renderPage()
    const courseSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')!
    act(() => { courseSelect.value = '2'; courseSelect.dispatchEvent(new Event('change', { bubbles: true })) })

    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={1} />)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(courseSelect.value).toBe('2')
    expect(mocks.getPlanningOptions).toHaveBeenCalledTimes(2)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('retains and flags a selected Course removed by a catalog refresh', async () => {
    const root = await renderPage()
    const courseSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')!
    act(() => { courseSelect.value = '2'; courseSelect.dispatchEvent(new Event('change', { bubbles: true })) })
    mocks.getPlanningOptions.mockResolvedValue({ ...options, courses: [options.courses[0]] })

    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={1} />)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(courseSelect.value).toBe('2')
    expect(document.body.textContent).toContain('OPTION_NO_LONGER_AVAILABLE')
    expect((button('Generate') as HTMLButtonElement).disabled).toBe(true)
  })
})

describe('CourseSchedulePage manual session creation', () => {
  it('keeps remaining units unavailable and creation disabled until the current overview loads', async () => {
    const partialDraft = { ...draftScheduleFixture, sessions: draftScheduleFixture.sessions.slice(0, 1) }
    let resolveOverview: (value: typeof partialDraft[]) => void = () => undefined
    mocks.getDraftSchedules.mockReturnValue(new Promise((resolve) => { resolveOverview = resolve }))

    await renderPage()

    expect(summaryValue('Scheduled units')).toBe('Loading...')
    expect(summaryValue('Remaining units')).toBe('Loading...')
    expect((button('Add Draft Session') as HTMLButtonElement).disabled).toBe(true)

    await act(async () => {
      resolveOverview([partialDraft])
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(summaryValue('Scheduled units')).toBe('4')
    expect(summaryValue('Remaining units')).toBe('4')
    expect((button('Add Draft Session') as HTMLButtonElement).disabled).toBe(false)
  })

  it('locks the selected planning context while a manual creation and refresh are pending', async () => {
    let resolveCreation: (value: { courseId: number; semesterId: number; scheduledUnits: number; remainingUnits: number; draftSchedule: null }) => void = () => undefined
    mocks.createManualDraftSession.mockReturnValue(new Promise((resolve) => { resolveCreation = resolve }))
    await renderPage()

    act(() => button('Add Draft Session')?.click())

    const selectors = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    expect([...selectors].every((select) => select.disabled)).toBe(true)

    await act(async () => {
      resolveCreation({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: null })
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect([...selectors].every((select) => !select.disabled)).toBe(true)
  })

  it('shows selected-course progress, calculates an editable end time, and refreshes after save', async () => {
    mocks.createManualDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: null })
    await renderPage()

    expect(document.body.textContent).toContain('Scheduled units')
    expect(document.body.textContent).toContain('Remaining units')
    const start = document.querySelector<HTMLInputElement>('input[name="manual-start-time"]')!
    const end = document.querySelector<HTMLInputElement>('input[name="manual-end-time"]')!
    const units = document.querySelector<HTMLInputElement>('input[name="manual-units"]')!
    expect(start.value).toBe('08:00')
    expect(units.value).toBe('2')
    expect(end.value).toBe('09:40')

    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(end, '10:15')
      end.dispatchEvent(new Event('input', { bubbles: true }))
    })
    await act(async () => {
      button('Add Draft Session')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.createManualDraftSession).toHaveBeenCalledWith(1, expect.objectContaining({ endTime: '10:15', units: 2, roomId: 3 }))
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('reports a saved mutation whose overview refresh failed and blocks another write until retry succeeds', async () => {
    const partialDraft = { ...draftScheduleFixture, sessions: draftScheduleFixture.sessions.slice(0, 1) }
    let resolveRetry: (value: typeof partialDraft[]) => void = () => undefined
    const retry = new Promise<typeof partialDraft[]>((resolve) => { resolveRetry = resolve })
    mocks.getDraftSchedules
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error('refresh failed'))
      .mockReturnValueOnce(retry)
    mocks.createManualDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: partialDraft })
    await renderPage()

    await act(async () => {
      button('Add Draft Session')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('saved, but the overview could not be refreshed')
    expect(document.body.textContent).toContain('Could not refresh the Courses overview')
    const visibleMutationNotice = document.querySelector('.mutation-feedback')
    expect(visibleMutationNotice?.textContent).toContain('saved, but the overview could not be refreshed')
    expect(visibleMutationNotice?.classList.contains('sr-only')).toBe(false)
    expect((button('Add Draft Session') as HTMLButtonElement).disabled).toBe(true)

    await act(async () => {
      button('Retry refresh')?.click()
      await Promise.resolve()
    })
    const selectors = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    expect([...selectors].every((select) => select.disabled)).toBe(true)

    await act(async () => {
      resolveRetry([partialDraft])
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect((button('Add Draft Session') as HTMLButtonElement).disabled).toBe(false)
    expect([...selectors].every((select) => !select.disabled)).toBe(true)
  })
})

describe('CourseSchedulePage single-session deletion', () => {
  it('cancels without writing, then confirms exact-scope deletion and refreshes', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 4, remainingUnits: 4, draftSchedule: null })
    await renderPage()
    const firstDelete = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Delete')!
    act(() => firstDelete.click())
    expect(document.body.textContent).toContain('Delete this Draft Session?')
    act(() => button('Cancel')?.click())
    expect(mocks.deleteDraftSession).not.toHaveBeenCalled()

    act(() => firstDelete.click())
    await act(async () => {
      button('Delete session')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.deleteDraftSession).toHaveBeenCalledWith(1, 1, 1, 11)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('closes a stale confirmation, refreshes, and requires the action to be opened again', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Delete')?.click())
    await act(async () => {
      button('Delete session')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).not.toContain('Delete this Draft Session?')
    expect(document.body.textContent).toContain('changed')
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('blocks renewed deletion when the stale-state refresh fails', async () => {
    mocks.getDraftSchedules
      .mockResolvedValueOnce([draftScheduleFixture])
      .mockRejectedValueOnce(new Error('refresh failed'))
      .mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Delete')?.click())
    await act(async () => {
      button('Delete session')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('current state could not be refreshed')
    const deleteActions = [...document.querySelectorAll<HTMLButtonElement>('button')].filter((item) => item.textContent === 'Delete')
    expect(deleteActions.every((item) => item.disabled)).toBe(true)

    await act(async () => {
      button('Retry refresh')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(deleteActions.every((item) => item.disabled)).toBe(false)
    expect(document.body.textContent).not.toContain('current state could not be refreshed')
  })
})

describe('CourseSchedulePage complete draft clearing', () => {
  it('disables clearing without a selected draft, then supports cancel and exact-scope confirm', async () => {
    await renderPage()
    expect((button('Clear course draft') as HTMLButtonElement).disabled).toBe(true)
    document.body.innerHTML = ''

    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.clearCourseDraft.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 0, remainingUnits: 8, draftSchedule: null })
    await renderPage()
    act(() => button('Clear course draft')?.click())
    expect(document.body.textContent).toContain('2 sessions')
    act(() => button('Cancel')?.click())
    expect(mocks.clearCourseDraft).not.toHaveBeenCalled()

    act(() => button('Clear course draft')?.click())
    const confirm = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')].at(-1)
    await act(async () => {
      confirm?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.clearCourseDraft).toHaveBeenCalledWith(1, 1, 1, 1, 11)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(3)
  })

  it('refreshes and requires renewed confirmation when complete clearing is stale', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.clearCourseDraft.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => button('Clear course draft')?.click())
    const dialogButtons = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
    await act(async () => {
      dialogButtons.at(-1)?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).toContain('open deletion again')
  })
})
