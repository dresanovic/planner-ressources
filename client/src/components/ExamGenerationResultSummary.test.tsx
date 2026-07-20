import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it } from 'vitest'
import { ExamGenerationResultSummary } from './ExamGenerationResultSummary'

let host: HTMLDivElement | null = null
afterEach(() => host?.remove())

it('renders every mixed outcome and understandable reason', async () => {
  host = document.createElement('div'); document.body.append(host)
  const root = createRoot(host)
  await act(async () => root.render(<ExamGenerationResultSummary result={{ semesterId: 1, summary: { total: 3, scheduled: 1, failed: 1, stale: 1, skippedActive: 0, skippedDisabled: 0, elapsedMilliseconds: 2, optimalForPreparedSnapshot: true }, outcomes: [{ courseId: 1, courseName: 'A', configurationId: 1, configurationIdentifier: 'Exam', status: 'scheduled', saved: true, exam: null, reasons: [] }, { courseId: 2, courseName: 'B', configurationId: 2, configurationIdentifier: 'Exam', status: 'failed', saved: false, exam: null, reasons: [{ code: 'FINAL_TEACHING_SESSION_MISSING', message: 'Save teaching first.', relatedDate: null, relatedResource: null, relatedSessionId: null, holidayName: null }] }, { courseId: 3, courseName: 'C', configurationId: 3, configurationIdentifier: 'Exam', status: 'stale', saved: false, exam: null, reasons: [] }] }} />))
  expect(host.textContent).toContain('scheduled')
  expect(host.textContent).toContain('Save teaching first.')
  expect(host.textContent).toContain('stale')
  await act(async () => root.unmount())
})
