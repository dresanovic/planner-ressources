import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { BatchResultSummary } from './BatchResultSummary'
import { mixedOptimizationResultFixture, optimizationResultFixture, candidateProofFixture } from '../test/optimizationFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('BatchResultSummary', () => {
  it('shows the saved arrangement intensive facts and cohort/date counts', () => {
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const intensiveFacts={totalUnits:14,intensiveLe:{numerator:1_800_000_000,denominator:2_700_000_000 as const},dailyVariety:1,
      cohortDates:[{cohortId:1,date:'2026-11-09',distinctCourseIds:[1,2],distinctLvCount:2,varietyContribution:1}],
      preparedSnapshotToken:'d'.repeat(64),candidateFingerprint:'a'.repeat(64)}
    act(()=>root.render(<BatchResultSummary result={{...optimizationResultFixture,intensiveFacts}} onRetryFailed={vi.fn()}/>))
    expect(document.body.textContent).toContain('Intensive LE: 0,666')
    expect(document.body.textContent).toContain('09.11.2026')
    expect(document.body.textContent).toContain('2 verschiedene LVs')
    expect(document.body.textContent).toContain('Eine einzelne LV bleibt zulässig')
  })
  it('describes zero-unit saved coverage and excluded holidays without claiming improvement or a failed save',()=>{
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const result={...optimizationResultFixture,
      outcomes:[{...optimizationResultFixture.outcomes[0],status:'improved_partial' as const,
        courseName:'Communication & Presentation',scheduledUnits:0,remainingUnits:34,improvement:null,
        reasons:[{code:'INSTITUTION_HOLIDAY',message:'Excluded date.',relatedCount:1,holidayDate:'2027-03-20',holidayName:'Osterferien'},
          {code:'SELECTED_COURSE_COMPETITION',message:'Shared capacity.',relatedCount:1}]}],
      summary:{...optimizationResultFixture.summary,total:1,complete:0,improvedPartial:1,scheduledUnits:0,remainingUnits:34}}
    act(()=>root.render(<BatchResultSummary result={result} onRetryFailed={vi.fn()}/>))
    expect(document.body.textContent).toContain('1 unvollständig')
    expect(document.body.textContent).not.toContain('verbessert')
    expect(document.body.textContent).toContain('als mögliche Lehrtermine ausgeschlossen')
    expect(document.body.textContent).toContain('gemeinsame Zeitfenster oder Ressourcen')
    expect(document.body.textContent).not.toContain('Ein betroffener Termin liegt auf einem Feiertag')
    expect(document.body.textContent).not.toContain('Die Aktion konnte nicht abgeschlossen werden')
  })
  it('keeps accepted unproven work saved and retains the original proof scope',()=>{
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    act(()=>root.render(<BatchResultSummary result={{...optimizationResultFixture,proof:candidateProofFixture,
      summary:{...optimizationResultFixture.summary,optimalForPreparedSnapshot:false}}} onRetryFailed={vi.fn()}/>))
    expect(document.body.textContent).toContain('Gespeichert nach ausdrücklicher Übernahme')
    expect(document.body.textContent).toContain('höchstens 10 zusätzliche Lehreinheiten')
    expect(document.body.textContent).not.toContain('Eingaben nicht gelöst werden konnten')
  })
  it('shows all outcome counts, progress, reasons, proof scope, and retry action', () => {
    const retry = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(<BatchResultSummary result={mixedOptimizationResultFixture} onRetryFailed={retry} />))
    expect(document.body.textContent).toContain('1 vollständig · 1 unvollständig · 1 unverändert · 1 fehlgeschlagen · 1 veraltet')
    expect(document.body.textContent).toContain('Raumkonflikt')
    expect(document.body.textContent).toContain('Blockierende aktive Prüfung #44')
    expect(document.body.textContent).toContain('Für den vorbereiteten Datenstand als optimal nachgewiesen')
    const button = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Fehlgeschlagene oder veraltete Lehrveranstaltungen erneut versuchen')
    act(() => button?.click())
    expect(retry).toHaveBeenCalledOnce()
  })

  it('does not claim optimality when preparation became stale before solving', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const result = {
      ...mixedOptimizationResultFixture,
      summary: { ...mixedOptimizationResultFixture.summary, optimalForPreparedSnapshot: false as const },
    }

    act(() => root.render(<BatchResultSummary result={result} onRetryFailed={() => undefined} />))

    expect(document.body.textContent).toContain('Es wurde kein Optimalitätsnachweis erzeugt')
    expect(document.body.textContent).not.toContain('Für den vorbereiteten Datenstand als optimal nachgewiesen')
  })

  it('renders separate named evidence for holidays sharing the same reason code', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const result = {
      ...mixedOptimizationResultFixture,
      outcomes: [{
        ...mixedOptimizationResultFixture.outcomes[0],
        reasons: [
          { code: 'INSTITUTION_HOLIDAY', message: 'Founders Day on 2026-09-07.', relatedCount: 1, holidayDate: '2026-09-07', holidayName: 'Founders Day' },
          { code: 'INSTITUTION_HOLIDAY', message: 'Winter Holiday on 2026-12-25.', relatedCount: 1, holidayDate: '2026-12-25', holidayName: 'Winter Holiday' },
        ],
      }, ...mixedOptimizationResultFixture.outcomes.slice(1)],
    }

    act(() => root.render(<BatchResultSummary result={result} onRetryFailed={() => undefined} />))

    expect(document.body.textContent).toContain('Feiertag „Founders Day“, betroffenes Datum: 07.09.2026')
    expect(document.body.textContent).toContain('Feiertag „Winter Holiday“, betroffenes Datum: 25.12.2026')
  })

  it('distinguishes lecturer, room, cohort, and exam-boundary blockers with their source', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const result = {
      ...mixedOptimizationResultFixture,
      outcomes: [{
        ...mixedOptimizationResultFixture.outcomes[0],
        reasons: [
          { code: 'LECTURER_OCCUPIED', message: 'Occupied.', relatedCount: 2, sourceKind: 'teaching_session' as const, sourceId: 41 },
          { code: 'ROOM_OCCUPIED', message: 'Occupied.', relatedCount: 1, sourceKind: 'active_exam' as const, sourceId: 52 },
          { code: 'COHORT_OCCUPIED', message: 'Occupied.', relatedCount: 3, sourceKind: 'teaching_session' as const, sourceId: 43 },
          { code: 'ACTIVE_EXAM_BOUNDARY', message: 'Boundary.', relatedCount: 1, sourceKind: 'active_exam' as const, sourceId: 52 },
        ],
      }],
      summary: { ...mixedOptimizationResultFixture.summary, total: 1 },
    }

    act(() => root.render(<BatchResultSummary result={result} onRetryFailed={() => undefined} />))

    expect(document.body.textContent).toContain('Lehrpersonenkonflikt')
    expect(document.body.textContent).toContain('Raumkonflikt')
    expect(document.body.textContent).toContain('Kohortenkonflikt')
    expect(document.body.textContent).toContain('Prüfungsgrenze')
    expect(document.body.textContent).toContain('Blockierender Lehrtermin #41')
    expect(document.body.textContent).toContain('Blockierende aktive Prüfung #52')
    expect(document.body.textContent).not.toContain('bevor Sie eine neue Prüfung erzeugen')
  })
})
