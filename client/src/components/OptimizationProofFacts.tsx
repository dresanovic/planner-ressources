import type { CandidateProof } from '../api/conflictAwareGeneration'

const objectiveLabels: Record<string,string> = {
  total_units:'Geplante Lehreinheiten', conflicts:'Überschneidungen',
  schedule_shape:'Wochenverteilung und Termingröße', lecturer_changes:'Wechsel der Lehrperson',
  room_changes:'Raumwechsel', retained_drafts:'Beibehaltene Entwürfe',
  canonical_temporal:'Eindeutige zeitliche Reihenfolge', canonical_resource:'Eindeutige Ressourcenauswahl',
}
const proofLabels = {proven:'Nachgewiesen',unfinished:'Unvollständig nachgewiesen',not_attempted:'Nicht versucht',conditional:'Nur bedingt nachgewiesen'}

export function OptimizationProofFacts({proof}: {proof:CandidateProof}) {
  return <section className="optimization-proof" aria-label="Gültigkeit und Nachweise">
    <h3>Harte Regeln geprüft</h3>
    <p>Ein gültiger Stundenplan muss nicht vollständig oder optimal sein. {proof.coverageProven ? 'Die maximale Abdeckung ist für die vorbereitete Auswahl nachgewiesen.' : 'Die maximale Abdeckung ist nicht nachgewiesen; weitere Lehreinheiten könnten möglich sein.'}</p>
    <p>Verbleibende erforderliche Lehreinheiten: {Math.max(proof.requiredUnits-proof.scheduledUnits,0)}.</p>
    <p>{proof.gapKnown ? `Nach der verfügbaren Obergrenze ${proof.unitUpperBound} sind höchstens ${proof.additionalPossibleUnits} zusätzliche Lehreinheiten möglich. Dies ist keine Zusage, dass die Obergrenze erreichbar ist.` : 'Abstand zum möglichen Maximum unbekannt. Es gibt keine belastbare Obergrenze.'}</p>
    <p>{proof.preferencesProven ? 'Auch die nachgeordneten Ziele sind in ihrer Prioritätsfolge nachgewiesen.' : 'Wochenverteilung, Wechsel der Lehrperson oder Raumwahl könnten verbessert werden. Vollständige Abdeckung bedeutet keine optimalen Präferenzen.'}</p>
    <ol className="optimization-objectives">{proof.objectives.map(objective=><li key={objective.objectiveKey}>
      <strong>{objectiveLabels[objective.objectiveKey] ?? objective.objectiveKey}</strong>: {proofLabels[objective.proofStatus]}
      {objective.value != null ? ` · Wert ${objective.value}` : ' · Wert unbekannt'}
      {objective.condition && <span> · Bedingung: {Object.entries(objective.condition).map(([key,value])=>`${objectiveLabels[key]??key} = ${value}`).join(', ')}</span>}
    </li>)}</ol>
    <p>Der Nachweis gilt für die vorbereitete Auswahl ({proof.selectedCourseIds.length} Lehrveranstaltungen) mit der damaligen festen Belegung; keine Aussage über ein globales Semesteroptimum oder unabhängige Kursmaxima. Nach dem Speichern werden diese Termine für spätere Auswahlen zur festen Belegung und können deren Möglichkeiten einschränken.</p>
  </section>
}
