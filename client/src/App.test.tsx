import { act, useEffect } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({ schedule: vi.fn(), academic: vi.fn() }))
vi.mock('./pages/CourseSchedulePage', () => ({ CourseSchedulePage: () => { useEffect(() => { mocks.schedule() }, []); return <div>Schedule view</div> } }))
vi.mock('./pages/AcademicDataPage', () => ({ AcademicDataPage: ({ onCatalogChanged }: { onCatalogChanged: () => void }) => { mocks.academic(); return <button onClick={onCatalogChanged}>Mutate catalog</button> } }))

import App from './App'

afterEach(() => { document.body.innerHTML = ''; vi.clearAllMocks() })

it('keeps Schedule mounted while catalog mutations trigger an in-place refresh', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<App />))
  const find = (label: string) => Array.from(document.querySelectorAll('button')).find((item) => item.textContent === label)!
  act(() => find('Academic Data').click())
  act(() => find('Mutate catalog').click())
  act(() => find('Schedule').click())
  expect(document.body.textContent).toContain('Schedule view')
  expect(mocks.schedule).toHaveBeenCalledTimes(1)
})
