import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import { ResourceAvailabilityEditor } from './ResourceAvailabilityEditor'

afterEach(() => { vi.restoreAllMocks(); document.body.innerHTML = '' })

it('renders recurring weekday controls and chronological canonical periods', async () => {
  const onCreate = vi.fn().mockRejectedValue(new Error('This exact unavailable period already exists.'))
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<ResourceAvailabilityEditor periods={[
    { id: 2, resourceType: 'lecturer', resourceId: 1, kind: 'dated', startDate: '2026-09-08', startTime: '09:00', endDate: '2026-09-08', endTime: '11:00', revision: 1 },
    { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0, 2], startTime: '08:00', endTime: '10:00', revision: 1 },
  ]} onCreate={onCreate} onUpdate={vi.fn()} onDelete={vi.fn()} />); await Promise.resolve() })
  expect(document.body.textContent?.indexOf('Monday, Wednesday')).toBeLessThan(document.body.textContent?.indexOf('8 Sept 2026') ?? 0)
  expect(document.querySelectorAll('input[type="checkbox"]')).toHaveLength(7)
})

it('keeps the period and announces a failed deletion', async () => {
  vi.spyOn(window, 'confirm').mockReturnValue(true)
  const onDelete = vi.fn().mockRejectedValue(new Error('This unavailable period changed. Refresh and review the current values.'))
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(<ResourceAvailabilityEditor periods={[
    { id: 1, resourceType: 'lecturer', resourceId: 1, kind: 'recurring', weekdays: [0], startTime: '08:00', endTime: '10:00', revision: 1 },
  ]} onCreate={vi.fn()} onUpdate={vi.fn()} onDelete={onDelete} />); await Promise.resolve() })

  await act(async () => {
    Array.from(document.querySelectorAll('button')).find((item) => item.textContent === 'Delete')?.click()
    await Promise.resolve()
  })

  expect(onDelete).toHaveBeenCalledOnce()
  expect(document.querySelector('[role="alert"]')?.textContent).toContain('changed')
  expect(document.body.textContent).toContain('Monday')
})
