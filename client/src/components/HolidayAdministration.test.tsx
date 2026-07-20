import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { HolidayAdministration } from './HolidayAdministration'
import { HolidayCalendarApiError } from '../api/holidayCalendar'

const mocks = vi.hoisted(() => ({
  listHolidays: vi.fn(),
  createHoliday: vi.fn(),
  updateHoliday: vi.fn(),
  deleteHoliday: vi.fn(),
}))

vi.mock('../api/holidayCalendar', async () => {
  const actual = await vi.importActual('../api/holidayCalendar')
  return { ...actual, ...mocks }
})

afterEach(() => {
  document.body.innerHTML = ''
  vi.clearAllMocks()
})

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent?.trim() === label) as HTMLButtonElement
}

function setInput(input: HTMLInputElement, value: string) {
  Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value)
  input.dispatchEvent(new Event('input', { bubbles: true }))
}

describe('HolidayAdministration', () => {
  it('creates, edits, and confirms deletion while notifying only after success', async () => {
    const original = { id: 1, date: '2026-12-25', name: 'Winter Holiday', revision: 1 }
    const changed = { ...original, name: 'Winter Break', revision: 2 }
    mocks.listHolidays.mockResolvedValueOnce([]).mockResolvedValueOnce([original]).mockResolvedValueOnce([changed]).mockResolvedValueOnce([])
    mocks.createHoliday.mockResolvedValue(original)
    mocks.updateHoliday.mockResolvedValue(changed)
    mocks.deleteHoliday.mockResolvedValue(undefined)
    const onChanged = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => { root.render(<HolidayAdministration onChanged={onChanged} />); await Promise.resolve() })
    const dateInput = document.querySelector<HTMLInputElement>('input[type="date"]')!
    const nameInput = document.querySelector<HTMLInputElement>('input[name="holiday-name"]')!
    await act(async () => {
      setInput(dateInput, '2026-12-25')
      setInput(nameInput, 'Winter Holiday')
    })
    await act(async () => { button('Create holiday').click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(onChanged).toHaveBeenCalledTimes(1)
    await act(async () => button('Edit').click())
    expect(nameInput.value).toBe('Winter Holiday')
    await act(async () => {
      setInput(nameInput, 'Winter Break')
      button('Save changes').click(); await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(onChanged).toHaveBeenCalledTimes(2)
    await act(async () => button('Delete').click())
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
    await act(async () => { button('Remove holiday').click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(onChanged).toHaveBeenCalledTimes(3)
  })

  it('shows multiple years and recovers stale edits without emitting a change signal', async () => {
    const past = { id: 1, date: '2024-02-29', name: 'Leap Day', revision: 1 }
    const future = { id: 2, date: '2027-01-01', name: 'New Year', revision: 1 }
    const current = { ...past, name: 'Current Leap Day', revision: 2 }
    const saved = { ...current, name: 'My stale edit', revision: 3 }
    mocks.listHolidays
      .mockResolvedValueOnce([past, future])
      .mockResolvedValueOnce([current, future])
      .mockResolvedValueOnce([saved, future])
    mocks.updateHoliday
      .mockRejectedValueOnce(new HolidayCalendarApiError(409, [{ code: 'STALE_REVISION', message: 'Refresh and try again.' }]))
      .mockResolvedValueOnce(saved)
    const onChanged = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => { root.render(<HolidayAdministration onChanged={onChanged} />); await Promise.resolve() })

    expect(document.body.textContent).toContain('2024-02-29')
    expect(document.body.textContent).toContain('2027-01-01')
    await act(async () => button('Edit').click())
    const nameInput = document.querySelector<HTMLInputElement>('input[name="holiday-name"]')!
    await act(async () => {
      setInput(nameInput, 'My stale edit')
      button('Save changes').click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(onChanged).not.toHaveBeenCalled()
    expect(document.querySelector('[role="alert"]')?.textContent).toContain('Refresh and try again.')
    expect(nameInput.value).toBe('My stale edit')
    expect(mocks.listHolidays).toHaveBeenCalledTimes(2)

    await act(async () => {
      button('Save changes').click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(mocks.updateHoliday).toHaveBeenNthCalledWith(2, past.id, {
      date: past.date,
      name: 'My stale edit',
      expectedRevision: current.revision,
    })
    expect(onChanged).toHaveBeenCalledTimes(1)
    expect(document.body.textContent).toContain('Holiday updated.')
  })

  it('offers an accessible retry after the initial list request fails', async () => {
    mocks.listHolidays.mockRejectedValueOnce(new Error('Offline')).mockResolvedValueOnce([])
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => { root.render(<HolidayAdministration onChanged={() => undefined} />); await Promise.resolve() })

    expect(document.querySelector('[role="alert"]')?.textContent).toContain('Offline')
    await act(async () => { button('Retry holidays').click(); await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(document.body.textContent).toContain('No holidays yet')
    expect(document.querySelector('[role="alert"]')).toBeNull()
  })
})
