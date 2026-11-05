import { act, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

import type { EditableDraftSessionRequest } from './sessionEditModel'
import { TeachingSessionEditor } from './TeachingSessionEditor'

afterEach(() => { document.body.innerHTML = '' })

it('calculates end from LE with breaks and preserves LE when end is overridden', async () => {
  let saved: EditableDraftSessionRequest | undefined
  function ControlledEditor() {
    const [draft, setDraft] = useState<EditableDraftSessionRequest>({
      date: '2027-02-20', startTime: '13:15', endTime: '14:55', units: 2, lecturerId: 1, roomId: 2,
    })
    return <TeachingSessionEditor session={{ id: 7, units: 2,
      lecturer: { id: 1, name: 'Ada' }, room: { id: 2, name: 'RC409' }, eligibleLecturers: [], eligibleRooms: [],
      context: { course: { name: 'Course' }, cohort: { name: 'Cohort' }, cohortSize: 20 },
    } as never} draft={draft} isSaving={false} isDisabled={false} errors={[]}
      onChange={setDraft} onCancel={() => undefined} onSave={() => { saved = draft }} />
  }
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ControlledEditor />))
  const units = document.querySelector<HTMLInputElement>('input[name="units"]')!
  expect(units.value).toBe('2')
  await act(async () => change(units, '3'))
  const end = document.querySelector<HTMLInputElement>('input[name="endTime"]')!
  expect(end.value).toBe('15:50')
  await act(async () => change(end, '16:00'))
  expect(units.value).toBe('3')
  await act(async () => document.querySelector<HTMLButtonElement>('button[type="submit"]')!.click())
  expect(saved).toMatchObject({ units: 3, endTime: '16:00' })
  await act(async () => change(units, '1'))
  expect(end.value).toBe('14:00')
})

function change(input: HTMLInputElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

it('blocks an incomplete European date, focuses it, and saves only after correction', async () => {
  const onSave = vi.fn()
  function ControlledEditor() {
    const [draft, setDraft] = useState<EditableDraftSessionRequest>({
      date: '2026-09-11', startTime: '09:00', endTime: '10:30', units: 2, lecturerId: 1, roomId: 2,
    })
    return <TeachingSessionEditor
      session={{
        id: 7,
        lecturer: { id: 1, name: 'Ada' },
        room: { id: 2, name: 'R1' },
        eligibleLecturers: [],
        eligibleRooms: [],
        context: { course: { name: 'Algorithmen' }, cohort: { name: 'A1' }, cohortSize: 20 },
      } as never}
      draft={draft}
      isSaving={false}
      isDisabled={false}
      errors={[]}
      onChange={setDraft}
      onCancel={() => undefined}
      onSave={onSave}
    />
  }

  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<ControlledEditor />))
  const date = document.querySelector<HTMLInputElement>('#teaching-date-7')!

  await act(async () => change(date, '1.09.2026'))
  await act(async () => {
    document.querySelector<HTMLButtonElement>('button[type="submit"]')?.click()
    await Promise.resolve()
  })

  expect(onSave).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(date)
  expect(date.getAttribute('aria-invalid')).toBe('true')
  expect(document.body.textContent).toContain('TT.MM.JJJJ')

  await act(async () => change(date, '12.09.2026'))
  await act(async () => document.querySelector<HTMLButtonElement>('button[type="submit"]')?.click())
  expect(onSave).toHaveBeenCalledOnce()
})
