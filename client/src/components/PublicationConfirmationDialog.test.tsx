import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { publicationFixture } from '../test/lifecycleFixtures'
import type { PublicationPreparation } from '../api/scheduleLifecycle'
import { PublicationConfirmationDialog } from './PublicationConfirmationDialog'


afterEach(() => { document.body.innerHTML = '' })


describe('PublicationConfirmationDialog', () => {
  it('shows contextual German publication facts without rendering backend messages or raw codes', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy={false} onConfirm={vi.fn()} onCancel={vi.fn()} />))
    expect(document.body.textContent).toContain('Revision 1 veröffentlichen')
    expect(document.body.textContent).toContain('Entwurf')
    expect(document.body.textContent).toContain('erste Veröffentlichung')
    expect(document.body.textContent).toContain('2 Lehreinheiten sind noch offen')
    expect(document.body.textContent).toContain('verhindern die Veröffentlichung nicht')
    expect(document.body.textContent).not.toContain('2 units remain')
    expect(document.body.textContent).not.toContain('course_units_remaining')
  })

  it('supports cancellation, Escape, focus containment, focus return, and busy duplicate prevention', () => {
    const cancel = vi.fn()
    const confirm = vi.fn()
    const opener = document.body.appendChild(document.createElement('button'))
    opener.focus()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy={false} onConfirm={confirm} onCancel={cancel} />))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    expect(document.activeElement).toBe(dialog)
    const buttons = [...(dialog?.querySelectorAll<HTMLButtonElement>('button') ?? [])]
    buttons.at(-1)?.focus()
    act(() => buttons.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(buttons[0])
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(cancel).toHaveBeenCalledOnce()
    act(() => root.render(<PublicationConfirmationDialog preparation={publicationFixture()} busy onConfirm={confirm} onCancel={cancel} />))
    expect([...(dialog?.querySelectorAll('button') ?? [])].every((button) => button.disabled)).toBe(true)
    act(() => root.unmount())
    expect(document.activeElement).toBe(opener)
  })

  it('shows the affected exam, scheduled date, recommendation, saved status, and edit-or-retain guidance', () => {
    const preparation: PublicationPreparation = publicationFixture()
    preparation.conditions = [{
      code: 'exam_outside_recommendation', message: 'SECRET RAW MESSAGE', courseId: 1,
      sessionKind: 'exam', sourceSessionId: 7,
      details: { courseName: 'KI Grundlagen', examDate: '2026-09-11', recommendedStartDate: '2026-09-15', recommendedEndDate: '2026-09-30' },
    }]
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<PublicationConfirmationDialog preparation={preparation} busy={false} onConfirm={vi.fn()} onCancel={vi.fn()} />))
    expect(document.body.textContent).toContain('KI Grundlagen')
    expect(document.body.textContent).toContain('11.09.2026')
    expect(document.body.textContent).toContain('15.09.2026–30.09.2026')
    expect(document.body.textContent).toContain('nicht blockierend')
    expect(document.body.textContent).toContain('gespeichert')
    expect(document.body.textContent).toContain('bearbeiten oder bewusst beibehalten')
    expect(document.body.textContent).not.toContain('SECRET RAW MESSAGE')
  })

  it('renders safe affected context and recovery guidance for every other known publication condition', () => {
    const cases: Array<{ condition: PublicationPreparation['conditions'][number]; expected: string[] }> = [
      {
        condition: { code: 'course_units_remaining', message: 'SECRET UNITS', courseId: 1, sessionKind: 'teaching', sourceSessionId: null, details: { courseName: 'KI Grundlagen', remainingUnits: 3 } },
        expected: ['KI Grundlagen', '3 Lehreinheiten', 'Planung vervollständigen', 'bewusst fortsetzen'],
      },
      {
        condition: { code: 'teaching_validation_alert', message: 'SECRET TEACHING', courseId: 1, sessionKind: 'teaching', sourceSessionId: 4, details: { courseName: 'KI Grundlagen', sessionDate: '2026-10-05', alertCode: 'ROOM_CAPACITY' } },
        expected: ['KI Grundlagen', '05.10.2026', 'Raumkapazität', 'bearbeiten', 'bewusst'],
      },
      {
        condition: { code: 'exam_validity_issue', message: 'SECRET EXAM', courseId: 1, sessionKind: 'exam', sourceSessionId: 7, details: { courseName: 'KI Grundlagen', examDate: '2026-12-10', issueCode: 'ROOM_UNAVAILABLE' } },
        expected: ['KI Grundlagen', '10.12.2026', 'Raum', 'nicht verfügbar', 'bearbeiten'],
      },
      {
        condition: { code: 'enabled_exam_unscheduled', message: 'SECRET UNSCHEDULED', courseId: 1, sessionKind: 'exam', sourceSessionId: null, details: { courseName: 'KI Grundlagen', configurationId: 9 } },
        expected: ['KI Grundlagen', 'noch kein Prüfungstermin', 'planen', 'bewusst'],
      },
    ]
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    for (const { condition, expected } of cases) {
      const preparation: PublicationPreparation = publicationFixture()
      preparation.conditions = [condition]
      act(() => root.render(<PublicationConfirmationDialog preparation={preparation} busy={false} onConfirm={vi.fn()} onCancel={vi.fn()} />))
      for (const text of expected) expect(document.body.textContent).toContain(text)
      expect(document.body.textContent).not.toContain(condition.message)
      expect(document.body.textContent).not.toContain(condition.code)
    }
  })
})
