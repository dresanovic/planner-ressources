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
}))
vi.mock('../api/multiCourseDraftGeneration', () => ({
  prepareMultiCourseGeneration: mocks.prepare,
  generateMultiCourseDrafts: mocks.generateBatch,
}))

import { CourseSchedulePage } from './CourseSchedulePage'
import { generationConstraintsFixture } from '../test/draftScheduleFixtures'

const entity = (id: number, name: string) => ({ id, name })
const options = {
  courses: [1, 2].map((id) => ({
    id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4,
    lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
  })),
  semesters: [{ id: 1, name: 'Fall 2026', startDate: '2026-09-07', endDate: '2026-12-20' }],
  timeWindows: [], rooms: [],
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
    root.render(<CourseSchedulePage />)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
  return root
}

function button(label: string) {
  return [...document.querySelectorAll('button')].find((item) => item.textContent === label)
}

describe('CourseSchedulePage multi-course mode', () => {
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
