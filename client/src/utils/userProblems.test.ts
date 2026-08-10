import { describe, expect, it, vi } from 'vitest'

import {
  fieldProblem,
  operationProblem,
  type ProblemContext,
} from './userProblems'

describe('userProblems', () => {
  const context: ProblemContext = {
    action: 'Lehrveranstaltung speichern',
    item: 'KI Grundlagen',
    inputPreserved: true,
  }

  it('describes known field, stale, connectivity, permission, and unexpected states', () => {
    expect(fieldProblem('course-date', 'Prüfungstermin', 'TT.MM.JJJJ')).toMatchObject({
      tone: 'blocking',
      fieldId: 'course-date',
      title: 'Prüfungstermin korrigieren',
    })
    expect(operationProblem('stale', context).details.join(' ')).toContain('aktualisiert')
    expect(operationProblem('connectivity', context).details.join(' ')).toContain('Verbindung')
    expect(operationProblem('permission', context).details.join(' ')).toContain('Berechtigung')
    expect(operationProblem('unexpected', context).details.join(' ')).toContain('genaue Ursache')
  })

  it('offers Retry only for safe reads and requires verification for ambiguous writes', () => {
    const retry = vi.fn()
    const read = operationProblem('connectivity', {
      action: 'Terminplan laden',
      safeRetry: retry,
    })
    expect(read.action?.label).toBe('Erneut versuchen')
    expect(read.action?.onClick).toBe(retry)

    const write = operationProblem('connectivity', {
      ...context,
      outcomeUnknown: true,
      safeRetry: retry,
    })
    expect(write.action).toBeUndefined()
    expect(write.details.join(' ')).toContain('aktuellen Stand')
  })

  it('never includes raw exception text or secrets in its safe fallback', () => {
    const problem = operationProblem('unexpected', context, new Error('Bearer secret database host'))
    expect(JSON.stringify(problem)).not.toMatch(/Bearer|secret|database|host/)
  })
})
