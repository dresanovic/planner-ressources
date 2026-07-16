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
vi.mock('../api/multiCourseDraftGeneration', () => ({
  prepareMultiCourseGeneration: mocks.prepare,
  generateMultiCourseDrafts: mocks.generateBatch,
}))

import { CourseSchedulePage } from './CourseSchedulePage'
import { draftScheduleFixture, generationConstraintsFixture } from '../test/draftScheduleFixtures'

const entity = (id: number, name: string) => ({ id, name })
const options = {
  courses: [1, 2].map((id) => ({
    id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
    lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
  })),
  semesters: [{ id: 1, name: 'Fall 2026', startDate: '2026-09-07', endDate: '2026-12-20' }],
  timeWindows: [], rooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', capacity: 40, isActive: true, revision: 1 }], lecturers: [], courseResources: [],
}

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset())
  mocks.getPlanningOptions.mockResolvedValue(options)
  mocks.getGenerationConstraints.mockResolvedValue(generationConstraintsFixture)
  mocks.getDraftSchedules.mockResolvedValue([])
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
  it('renders scheduling content without page-owned or dead hash navigation', async () => {
    await renderPage()
    expect(document.querySelector('nav')).toBeNull()
    expect(document.querySelectorAll('a[href^="#"]')).toHaveLength(0)
    expect(document.body.textContent).not.toContain('Dashboard')
    expect(document.body.textContent).toContain('Resource Planner')
  })

  it('keeps focused single-course constraints isolated while selecting and generating several courses', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, operationKind: 'initial', replacementCourseIds: [],
      courses: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, available: true, draftScheduleId: null, draftRevision: null, replacementRequired: false })),
    })
    mocks.generateBatch.mockResolvedValue({
      semesterId: 1, operationKind: 'initial', summary: { total: 2, succeeded: 2, failed: 0 },
      outcomes: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, status: 'succeeded', draftScheduleId: courseId, draftRevision: 1, errors: [] })),
    })
    await renderPage()
    act(() => button('Several courses')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    expect(document.body.textContent).toContain('2 selected')
    await act(async () => {
      button('Generate selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.prepare).toHaveBeenCalledWith(1, 'initial', [1, 2])
    expect(mocks.generateBatch).toHaveBeenCalledOnce()
    expect(document.body.textContent).toContain('2 succeeded · 0 failed · 2 total')
    expect(mocks.getGenerationConstraints).toHaveBeenCalledTimes(1)
  })

  it('cancels replacement confirmation without execution', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, operationKind: 'initial', replacementCourseIds: [1],
      courses: [
        { courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: 5, draftRevision: 2, replacementRequired: true },
        { courseId: 2, courseName: 'Course 2', available: true, draftScheduleId: null, draftRevision: null, replacementRequired: false },
      ],
    })
    await renderPage()
    act(() => button('Several courses')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Generate selected courses')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).toContain('Replace existing Draft Schedules?')
    act(() => button('Cancel')?.click())
    expect(mocks.generateBatch).not.toHaveBeenCalled()
    expect(document.body.textContent).not.toContain('Replace existing Draft Schedules?')
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
    expect(mocks.deleteDraftSession).toHaveBeenCalledWith(1, 1, 1)
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
    expect(mocks.clearCourseDraft).toHaveBeenCalledWith(1, 1, 1, 1)
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
