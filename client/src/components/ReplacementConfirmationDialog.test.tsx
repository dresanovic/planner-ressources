import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ReplacementConfirmationDialog } from './ReplacementConfirmationDialog'
import { decisionRequiredGenerationFixture, candidateProofFixture } from '../test/optimizationFixtures'

afterEach(() => { document.body.innerHTML = '' })

describe('ReplacementConfirmationDialog', () => {
  it('explains the separate Standard Optimized distribution objective without claiming optimality', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    const original = candidateProofFixture
    const proof = { ...original, objectiveProfile:'standard-optimized-v1' as const,
      objectives:[...original.objectives.slice(0,4), {...original.objectives[4], objectiveKey:'weekly_spread'}, ...original.objectives.slice(4)] }
    act(() => root.render(<ReplacementConfirmationDialog preview={{...decisionRequiredGenerationFixture,
      algorithm:'standard_optimized', strategyProfile:'standard-optimized-v1', proof}} onAccept={vi.fn()} onCancel={vi.fn()} />))
    expect(document.body.textContent).toContain('Standard optimiert')
    expect(document.body.textContent).toContain('Verteilung über den Lehrzeitraum')
    expect(document.body.textContent).toContain('gleichmäßig verteilten Lehreinheiten')
    expect(document.body.textContent).toContain('Vollständige Abdeckung bedeutet keine optimalen Präferenzen')
    act(() => root.unmount())
  })
  it('shows ordered lecturer shares and predecessor uncertainty without an editor', () => {
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const preview={...decisionRequiredGenerationFixture,algorithm:'lecturer' as const,
      comparison:{...decisionRequiredGenerationFixture.comparison,courses:[{
        ...decisionRequiredGenerationFixture.comparison.courses[0],lecturerPortions:[
          {lecturerId:1,lecturerCode:'A',sequenceIndex:0,source:'derived' as const,requiredUnits:11,scheduledUnits:9,remainingUnits:2,reasonCode:'SEARCH_UNCERTAIN',reason:'Weitere Termine sind nicht nachgewiesen.'},
          {lecturerId:2,lecturerCode:'B',sequenceIndex:1,source:'derived' as const,requiredUnits:11,scheduledUnits:0,remainingUnits:11,reasonCode:'PREDECESSOR_INCOMPLETE',reason:'Vorheriger Lehrpersonenanteil ist noch nicht vollständig geplant.'},
        ],
      }]}}
    act(()=>root.render(<ReplacementConfirmationDialog preview={preview} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    const list=document.querySelector('[aria-label="Lehrpersonenanteile in fester Reihenfolge"]')
    expect(list?.textContent).toContain('A')
    expect(list?.textContent).toContain('9 / 11 LE')
    expect(list?.textContent).toContain('Vorheriger Lehrpersonenanteil')
    expect(list?.querySelector('input,select')).toBeNull()
  })
  it('keeps current and generated intensive facts separate and hides mismatched prepared facts', () => {
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const scope='d'.repeat(64), fingerprint='a'.repeat(64)
    const makeFacts=(totalUnits:number,numerator:number,candidateFingerprint:string)=>({totalUnits,intensiveLe:{numerator,denominator:2700000000 as const},dailyVariety:0,cohortDates:[],preparedSnapshotToken:scope,candidateFingerprint})
    const preview={...decisionRequiredGenerationFixture,candidateFingerprint:fingerprint,
      proof:{...candidateProofFixture,preparedSnapshotToken:scope,candidateFingerprint:fingerprint},
      preparedEvidence:{...decisionRequiredGenerationFixture.preparedEvidence,sharedSnapshotToken:'b'.repeat(64)},
      comparison:{...decisionRequiredGenerationFixture.comparison,
        current:{...decisionRequiredGenerationFixture.comparison.current,intensiveFacts:makeFacts(4,2700000000,'c'.repeat(64))},
        generated:{...decisionRequiredGenerationFixture.comparison.generated,intensiveFacts:makeFacts(14,5400000000,fingerprint)}}}
    act(()=>root.render(<ReplacementConfirmationDialog preview={preview} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    expect(document.querySelector('[aria-label="Aktuelle intensive Planung"]')?.textContent).toContain('Intensive LE: 1')
    expect(document.querySelector('[aria-label="Erzeugte intensive Planung"]')?.textContent).toContain('Intensive LE: 2')
    preview.comparison.generated.intensiveFacts.preparedSnapshotToken='e'.repeat(64)
    act(()=>root.render(<ReplacementConfirmationDialog preview={preview} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    expect(document.querySelector('[aria-label="Erzeugte intensive Planung"]')).toBeNull()
  })
  it('localizes provisional holiday evidence from structured fields instead of displaying raw English',()=>{
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const courses=decisionRequiredGenerationFixture.comparison.courses.map((c,index)=>index?c:{...c,remainingReasons:[{
      code:'INSTITUTION_HOLIDAY',message:'Osterferien on 2027-03-20 removed an otherwise allowed date.',
      relatedCount:1,holidayDate:'2027-03-20',holidayName:'Osterferien'}]})
    act(()=>root.render(<ReplacementConfirmationDialog preview={{...decisionRequiredGenerationFixture,
      comparison:{...decisionRequiredGenerationFixture.comparison,courses}}} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    expect(document.body.textContent).toContain('20.03.2027')
    expect(document.body.textContent).toContain('als mögliche Lehrtermine ausgeschlossen')
    expect(document.body.textContent).not.toContain('removed an otherwise')
    expect(document.body.textContent).not.toContain('2027-03-20')
  })
  it('keeps aggregate subtraction distinct from per-course excess and shows conditional proof',()=>{
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const courses=decisionRequiredGenerationFixture.comparison.courses.map((course,index)=>({...course,
      current:{requiredUnits:index?60:40,scheduledUnits:index?40:50,remainingUnits:index?20:0,status:'partial' as const},
      remainingReasons:[]}))
    const proof={...candidateProofFixture,objectives:candidateProofFixture.objectives.map((o,i)=>i===1?{...o,proofStatus:'conditional' as const,condition:{total_units:80}}:o)}
    act(()=>root.render(<ReplacementConfirmationDialog preview={{...decisionRequiredGenerationFixture,proof,
      comparison:{...decisionRequiredGenerationFixture.comparison,courses,current:{requiredUnits:100,scheduledUnits:90,remainingUnits:10,status:'partial'}}}} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    const sides=[...document.querySelectorAll('[aria-label="Aktueller Stundenplan"]')]
    expect(sides[0].textContent).toContain('100 LEGeplant90 LEVerbleibend10 LE')
    expect(sides[1].textContent).toContain('40 LEGeplant50 LEVerbleibend0 LE')
    expect(sides[2].textContent).toContain('60 LEGeplant40 LEVerbleibend20 LE')
    expect(document.body.textContent).toContain('Nur bedingt nachgewiesen')
    expect(document.body.textContent).toContain('Geplante Lehreinheiten = 80')
    expect(document.body.textContent).toContain('keine belegten Gründe')
  })
  it('continues from the current proposal without a discard confirmation',()=>{
    const retry=vi.fn()
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    act(()=>root.render(<ReplacementConfirmationDialog preview={{...decisionRequiredGenerationFixture,proof:candidateProofFixture}} onContinue={retry} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    const button=(text:string)=>[...document.querySelectorAll('button')].find(b=>b.textContent===text)
    expect(document.body.textContent).toContain('Der bisherige Vorschlag bleibt erhalten')
    expect(button('Erneut optimieren')).toBeUndefined()
    expect(document.querySelectorAll('.optimization-objectives li')).toHaveLength(10)
    act(()=>button('Weiter optimieren')?.click())
    expect(retry).toHaveBeenCalledOnce()
  })
  it.each([true,false])('explains provisional validity, coverage and known/unknown gap (%s)', (known) => {
    const root=createRoot(document.body.appendChild(document.createElement('div')))
    const proof={...candidateProofFixture,unitUpperBound:known?90:null,additionalPossibleUnits:known?10:null,gapKnown:known}
    act(()=>root.render(<ReplacementConfirmationDialog preview={{...decisionRequiredGenerationFixture,hasSavedSessions:false,proof}} onAccept={vi.fn()} onCancel={vi.fn()}/>))
    expect(document.body.textContent).toContain('Noch nicht gespeichert')
    expect(document.body.textContent).toContain('Keine gespeicherten Lehrtermine')
    expect(document.body.textContent).toContain('Harte Regeln geprüft')
    expect(document.body.textContent).toContain('Verbleibende erforderliche Lehreinheiten: 20')
    expect(document.body.textContent).toContain(known?'höchstens 10 zusätzliche Lehreinheiten':'Abstand zum möglichen Maximum unbekannt')
    expect(document.body.textContent).toContain('Wochenverteilung und Termingröße')
    expect(document.querySelectorAll('.optimization-objectives li')).toHaveLength(10)
    expect(document.body.textContent).toContain('keine Aussage über ein globales Semesteroptimum')
  })
  it('shows factual aggregate and per-course comparison with only the atomic actions', () => {
    const cancel = vi.fn()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={cancel}
      />,
    ))

    expect(document.body.textContent).toContain('Aktueller Stundenplan')
    expect(document.body.textContent).toContain('Neu erzeugter Stundenplan')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).toContain('Databases')
    expect(document.body.textContent).toContain('16')
    expect(document.body.textContent).toContain('Aktuelle Regelverletzung: OUTSIDE_ALLOWED_WINDOW')
    expect(document.body.textContent).toContain('Geeignete Räume sind belegt.')
    expect(document.body.textContent).toContain('plannerseitig erstellter oder bearbeiteter Termine')
    expect(document.body.textContent).not.toContain('besser')
    expect(document.body.textContent).not.toContain('Optimierung bestätigen')
    const labels = [...document.querySelectorAll('button')].map((button) => button.textContent)
    expect(labels).toContain('Neu erzeugten Stundenplan übernehmen')
    expect(labels).toContain('Abbrechen')
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Abbrechen')?.click())
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('keeps a lower-unit partial candidate selectable', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={vi.fn()}
      />,
    ))
    const accept = [...document.querySelectorAll<HTMLButtonElement>('button')]
      .find((button) => button.textContent === 'Neu erzeugten Stundenplan übernehmen')
    expect(accept?.disabled).toBe(false)
  })

  it('moves focus into the modal, traps Tab, and supports Escape cancellation', () => {
    const cancel = vi.fn()
    const opener = document.body.appendChild(document.createElement('button'))
    opener.focus()
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        onAccept={vi.fn()}
        onCancel={cancel}
      />,
    ))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    const controls = [...(dialog?.querySelectorAll<HTMLButtonElement>('button:not(:disabled)') ?? [])]
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', shiftKey: true, bubbles: true })))
    expect(document.activeElement).toBe(controls.at(-1))
    act(() => controls.at(-1)?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(controls[0])
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })))
    expect(cancel).toHaveBeenCalledOnce()
  })

  it('keeps focus in the dialog and disables every action while acceptance is in flight', () => {
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    act(() => root.render(
      <ReplacementConfirmationDialog
        preview={decisionRequiredGenerationFixture}
        disabled
        onAccept={vi.fn()}
        onCancel={vi.fn()}
      />,
    ))
    const dialog = document.querySelector<HTMLElement>('[role="dialog"]')
    expect([...document.querySelectorAll<HTMLButtonElement>('button')].every((button) => button.disabled)).toBe(true)
    expect(document.activeElement).toBe(dialog)
    act(() => dialog?.dispatchEvent(new KeyboardEvent('keydown', { key: 'Tab', bubbles: true })))
    expect(document.activeElement).toBe(dialog)
  })
})
