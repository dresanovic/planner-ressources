import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import type { UserProblem } from '../utils/userProblems'
import { ActionableProblemList, problemDescriptionIds } from './ActionableProblemList'

let root: ReturnType<typeof createRoot> | null = null

afterEach(() => {
  act(() => root?.unmount())
  root = null
})

function render(problems: UserProblem[]) {
  const host = document.createElement('div')
  document.body.append(host)
  root = createRoot(host)
  act(() => root?.render(<ActionableProblemList problems={problems} />))
  return host
}

describe('ActionableProblemList', () => {
  it('renders distinct repeated blocking problems in one alert announcement', () => {
    const host = render([
      { key: 'first', tone: 'blocking', title: 'Fehler', details: ['Erster Grund'] },
      { key: 'second', tone: 'blocking', title: 'Fehler', details: ['Zweiter Grund'] },
    ])
    expect(host.querySelectorAll('[role="alert"]')).toHaveLength(1)
    expect(host.querySelectorAll('[role="alert"] li')).toHaveLength(2)
    expect(host.textContent).toContain('Erster Grund')
    expect(host.textContent).toContain('Zweiter Grund')
  })

  it('uses polite non-blocking semantics and a native action', () => {
    const onClick = vi.fn()
    const host = render([{
      key: 'warning',
      tone: 'warning',
      title: 'Hinweis',
      details: ['Die Planung bleibt gespeichert.'],
      action: { label: 'Bearbeiten', onClick },
    }])
    expect(host.querySelector('[role="status"]')?.getAttribute('aria-live')).toBe('polite')
    expect(host.querySelector('[role="alert"]')).toBeNull()
    const button = host.querySelector('button')!
    act(() => button.click())
    expect(onClick).toHaveBeenCalledOnce()
  })

  it('creates stable field description IDs and wrapping hooks', () => {
    const problems: UserProblem[] = [{
      key: 'required',
      tone: 'blocking',
      title: 'Datum korrigieren',
      details: ['Verwenden Sie TT.MM.JJJJ.'],
      fieldId: 'exam-date',
    }]
    const host = render(problems)
    expect(problemDescriptionIds(problems, 'exam-date')).toBe('exam-date-problem-required')
    expect(host.querySelector('#exam-date-problem-required')).not.toBeNull()
    expect(host.querySelector('.actionable-problem')).not.toBeNull()
  })
})
