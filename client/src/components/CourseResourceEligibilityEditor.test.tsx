import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { CourseResourceEligibilityEditor } from './CourseResourceEligibilityEditor'

afterEach(() => { document.body.innerHTML = '' })

it('shows coded searchable candidates, preserved invalid relationships, and fixed preferences', async () => {
  const save = vi.fn()
  const configuration = {
    courseId: 1, courseRevision: 2, cohortSize: 30, eligibleLecturerIds: [1], eligibleRoomIds: [3],
    lecturerCandidates: [{
      id: 1, name: 'Ada', referenceCode: 'A', kind: 'lecturer' as const, capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [],
      unavailabilityPeriods: [{ id: 8, resourceType: 'lecturer' as const, resourceId: 1, kind: 'recurring' as const, weekdays: [0], startTime: '09:00', endTime: '11:00', revision: 1 }],
      courseSessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 },
    }],
    roomCandidates: [
      { id: 2, name: 'Large', referenceCode: 'R2', kind: 'room' as const, capacity: 40, isActive: true, isEligible: false, isUsable: true, reasons: [], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } },
      { id: 3, name: 'Small', referenceCode: 'R3', kind: 'room' as const, capacity: 20, isActive: true, isEligible: true, isUsable: false, reasons: ['ROOM_CAPACITY_INSUFFICIENT'], unavailabilityPeriods: [], courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } },
    ],
    preferences: { minimizeLecturerChanges: true as const, minimizeRoomChanges: true as const },
  }
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<CourseResourceEligibilityEditor configuration={configuration} onSave={save} onCancel={() => undefined} />); await Promise.resolve() })
  expect(document.body.textContent).toContain('Ada · A')
  expect(document.body.textContent).toContain('Small · R3')
  expect(document.body.textContent).toContain('Capacity 20 · requires 30')
  expect(document.body.textContent).toContain('Minimize lecturer changes')
  expect(document.body.textContent).toContain('Monday · 09:00–11:00')
  expect(document.body.textContent).toContain('Assigned to 2 saved sessions across 1 schedule for this Course')
  expect(document.querySelector<HTMLInputElement>('input[value="3"]')?.checked).toBe(true)
  expect(document.querySelector<HTMLInputElement>('input[value="2"]')?.disabled).toBe(false)
})
