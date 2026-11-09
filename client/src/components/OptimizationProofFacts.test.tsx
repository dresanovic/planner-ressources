import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it } from 'vitest'
import { OptimizationProofFacts } from './OptimizationProofFacts'
import type { CandidateProof } from '../api/conflictAwareGeneration'

it('labels intensive priorities and converts exact microseconds to LE without overstating proof', () => {
  const scope = 'a'.repeat(64), fingerprint='b'.repeat(64)
  const proof: CandidateProof = { preparedSnapshotToken:scope,candidateFingerprint:fingerprint,selectedCourseIds:[1],requiredUnits:2,scheduledUnits:2,
    coverageProven:true,preferencesProven:false,unitUpperBound:2,additionalPossibleUnits:0,gapKnown:true,
    objectives:[{objectiveKey:'total_units',direction:'max',proofStatus:'proven',value:2,preparedSnapshotToken:scope,candidateFingerprint:fingerprint,condition:null},
      {objectiveKey:'intensive_teaching_time',direction:'max',proofStatus:'unfinished',value:1_800_000_000,preparedSnapshotToken:scope,candidateFingerprint:fingerprint,condition:null},
      {objectiveKey:'daily_variety',direction:'max',proofStatus:'not_attempted',value:null,preparedSnapshotToken:scope,candidateFingerprint:fingerprint,condition:null}] }
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  act(() => root.render(<OptimizationProofFacts proof={proof} />))
  expect(document.body.textContent).toContain('Intensive Lehreinheiten')
  expect(document.body.textContent).toContain('0,666')
  expect(document.body.textContent).toContain('Tägliche LV-Vielfalt')
  expect(document.body.textContent).not.toContain('1800000000')
  expect(document.body.textContent).toContain('Unvollständig nachgewiesen')
})

it('explains measured unattempted objective values and the composite penalty', () => {
  const scope = 'a'.repeat(64), fingerprint = 'b'.repeat(64)
  const proof: CandidateProof = { preparedSnapshotToken: scope, candidateFingerprint: fingerprint, selectedCourseIds: [1],
    requiredUnits: 34, scheduledUnits: 33, coverageProven: false, preferencesProven: false,
    unitUpperBound: null, additionalPossibleUnits: null, gapKnown: false,
    objectives: [{ objectiveKey: 'schedule_shape', direction: 'min', proofStatus: 'not_attempted', value: 16179,
      preparedSnapshotToken: scope, candidateFingerprint: fingerprint, condition: null },
      { objectiveKey: 'room_changes', direction: 'min', proofStatus: 'not_attempted', value: 28,
        preparedSnapshotToken: scope, candidateFingerprint: fingerprint, condition: null }] }
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  act(() => root.render(<OptimizationProofFacts proof={proof} />))
  expect(host.textContent).toContain('Gemessener Kandidatenwert')
  expect(host.textContent).toContain('Zusammengesetzter Strafwert')
  expect(host.textContent).toContain('keine Lehreinheiten oder Minuten')
  expect(host.textContent).toContain('noch nicht gezielt optimiert')
  expect(host.textContent).toContain('16179')
  expect(host.textContent).toContain('Nicht versucht')
  expect(host.textContent).toContain('Raumwechseln innerhalb einer LV und zusätzlichen Räumen je Kohorte und Tag')
  act(() => root.unmount())
  host.remove()
})
