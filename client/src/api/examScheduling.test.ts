import { afterEach, describe, expect, it, vi } from 'vitest'
import { createManualExam, deleteExam, generateExams, getExamPlanningOverview, prepareExamGeneration, saveExamConfiguration, updateExam } from './examScheduling'

afterEach(() => vi.unstubAllGlobals())

describe('exam scheduling API', () => {
  it('serializes overview, configuration, preparation, generation, and manual mutations exactly', async () => {
    const responses = [
      { semesterId: 1, institutionToday: '2026-09-01', courses: [] },
      { courseId: 1 },
      { semesterId: 1, institutionToday: '2026-09-01', sharedSnapshotToken: 'shared', courses: [] },
      { semesterId: 1, summary: {}, outcomes: [] },
      { courseId: 1 }, { courseId: 1 }, { deletedExamId: 2 },
    ]
    const fetchMock = vi.fn().mockImplementation(async () => ({ ok: true, status: 200, json: async () => responses.shift() }))
    vi.stubGlobal('fetch', fetchMock)
    await getExamPlanningOverview(1)
    await saveExamConfiguration(1, { semesterId: 1, enabled: false, expectedRevision: null, configuration: null })
    await prepareExamGeneration(1, [1])
    await generateExams({ semesterId: 1, institutionToday: '2026-09-01', sharedSnapshotToken: 'shared', courses: [] })
    await createManualExam(1, { semesterId: 1, date: '2026-10-16', startTime: '09:00', lecturerId: 1, roomId: 1, expectedConfigurationRevision: 1, inputSnapshotToken: 'c' })
    await updateExam(2, { date: '2026-10-17', startTime: '10:00', lecturerId: 1, roomId: 1, expectedExamRevision: 1, inputSnapshotToken: 'e' })
    await deleteExam(2, { confirmed: true, expectedExamRevision: 2, inputSnapshotToken: 'e2' })
    expect(fetchMock.mock.calls.map(([path]) => path)).toEqual(['/api/exam-planning?semesterId=1', '/api/courses/1/exam-configuration', '/api/exams/generation/prepare', '/api/exams/generation', '/api/courses/1/exam-sessions', '/api/exam-sessions/2', '/api/exam-sessions/2'])
    expect(fetchMock.mock.calls[6][1].method).toBe('DELETE')
  })

  it('validates 1-100 unique selections and retains structured stale state', async () => {
    await expect(prepareExamGeneration(1, [])).rejects.toMatchObject({ errors: [{ code: 'INVALID_SELECTION' }] })
    await expect(prepareExamGeneration(1, [1, 1])).rejects.toMatchObject({ errors: [{ code: 'INVALID_SELECTION' }] })
    const fetchMock = vi.fn().mockResolvedValue({ ok: false, status: 409, json: async () => ({ errors: [{ code: 'STALE_INPUT_SNAPSHOT', message: 'Changed', field: null }], currentState: { courseId: 1 } }) })
    vi.stubGlobal('fetch', fetchMock)
    await expect(getExamPlanningOverview(1)).rejects.toMatchObject({ status: 409, currentState: { courseId: 1 } })
  })
})
