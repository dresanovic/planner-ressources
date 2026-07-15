import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ResourceCatalogList } from './ResourceCatalogList'
import { ResourceEditor } from './ResourceEditor'
import { ResourceRemovalDialog } from './ResourceRemovalDialog'

afterEach(() => { document.body.innerHTML = '' })

async function render(element: React.ReactNode) {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => { root.render(element); await Promise.resolve() })
  return root
}

function button(label: string) {
  return Array.from(document.querySelectorAll('button')).find((item) => item.textContent === label)
}

describe('resource administration components', () => {
  it('renders coded active/inactive resources and room capacity', async () => {
    await render(<ResourceCatalogList resourceType="rooms" records={[
      { id: 1, name: 'Room One', referenceCode: 'R-1', capacity: 30, isActive: true, revision: 1 },
      { id: 2, name: 'Room Two', referenceCode: 'R-2', capacity: 20, isActive: false, revision: 2 },
    ]} onSelect={() => undefined} />)
    expect(document.body.textContent).toContain('Room One · R-1')
    expect(document.body.textContent).toContain('Capacity 30')
    expect(document.body.textContent).toContain('Inactive')
  })

  it('retains controlled invalid input and exposes save feedback', async () => {
    const onSubmit = vi.fn().mockRejectedValue(new Error('Code already exists.'))
    await render(<ResourceEditor resourceType="lecturers" initial={{ id: 1, name: 'Ada', referenceCode: 'A-1', isActive: true, revision: 1 }} onSubmit={onSubmit} onCancel={() => undefined} />)
    const code = document.querySelector<HTMLInputElement>('input[name="referenceCode"]')!
    await act(async () => { button('Save lecturer')?.click(); await Promise.resolve() })
    expect(code.value).toBe('A-1')
    expect(document.querySelector('[role="alert"]')?.textContent).toContain('Code already exists')
  })

  it('shows consequences and cancellation issues no removal request', async () => {
    const onConfirm = vi.fn()
    const onClose = vi.fn()
    await render(<ResourceRemovalDialog resourceName="Ada · A-1" assessment={{ resourceId: 1, revision: 1, disposition: 'inactivate', activeCourses: [{ id: 2, name: 'Scheduling' }], inactiveCourses: [], sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 } }} onConfirm={onConfirm} onClose={onClose} />)
    expect(document.body.textContent).toContain('Scheduling')
    expect(document.body.textContent).toContain('2 saved sessions')
    await act(async () => { button('Cancel')?.click() })
    expect(onClose).toHaveBeenCalledOnce()
    expect(onConfirm).not.toHaveBeenCalled()
  })

  it('contains keyboard focus, closes with Escape, and restores trigger focus', async () => {
    const trigger = document.body.appendChild(document.createElement('button'))
    trigger.textContent = 'Open removal'
    trigger.focus()
    const host = document.body.appendChild(document.createElement('div'))
    const root = createRoot(host)
    const onClose = vi.fn(() => root.render(null))
    await act(async () => {
      root.render(<ResourceRemovalDialog resourceName="Ada · A-1" assessment={{ resourceId: 1, revision: 1, disposition: 'delete', activeCourses: [], inactiveCourses: [], sessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 } }} onConfirm={vi.fn()} onClose={onClose} />)
      await Promise.resolve()
    })
    const cancel = button('Cancel')!
    const confirm = button('Delete permanently')!
    expect(document.activeElement).toBe(cancel)

    confirm.focus()
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true }))
    expect(document.activeElement).toBe(cancel)
    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true }))
    await act(async () => { await Promise.resolve() })

    expect(onClose).toHaveBeenCalledOnce()
    expect(document.activeElement).toBe(trigger)
  })
})
