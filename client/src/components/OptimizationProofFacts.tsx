import type { CandidateProof, IntensiveFacts, LecturerPortionFacts } from '../api/conflictAwareGeneration'
import { formatCalendarDate } from '../utils/datePresentation'

const objectiveLabels: Record<string,string> = {
  total_units:'Geplante Lehreinheiten', conflicts:'Überschneidungen',
  intensive_teaching_time:'Intensive Lehreinheiten', daily_variety:'Tägliche LV-Vielfalt',
  schedule_shape:'Wochenverteilung und Termingröße', lecturer_changes:'Wechsel der Lehrperson',
  weekly_spread:'Verteilung über den Lehrzeitraum',
  room_changes:'Raumwechsel', retained_drafts:'Beibehaltene Entwürfe',
  canonical_temporal:'Eindeutige zeitliche Reihenfolge', canonical_resource:'Eindeutige Ressourcenauswahl',
  preferred_size_deviation:'Abweichung von der bevorzugten Termingröße', course_rhythm_penalty:'Lücken und zusätzliche Wochentermine',
  owner_balance_penalty:'Wöchentliche Lehrlast', extra_cohort_day_rooms:'Zusätzliche Räume je Kohorte und Tag', course_room_changes:'Raumwechsel innerhalb der LV',
}
const proofLabels = {proven:'Nachgewiesen',unfinished:'Unvollständig nachgewiesen',not_attempted:'Nicht versucht',conditional:'Nur bedingt nachgewiesen'}

export function OrderedLecturerPortions({portions}: {portions?: LecturerPortionFacts[]}) {
  if (!portions?.length) return null
  return <section aria-label="Lehrpersonenanteile in fester Reihenfolge"><h4>Lehrpersonenanteile in fester Reihenfolge</h4>
    <ol>{portions.map(row=><li key={row.lecturerId}><strong>{row.lecturerCode}</strong>: {row.scheduledUnits} / {row.requiredUnits} LE · Verbleibend: {row.remainingUnits} LE{row.reason && <p>{row.reason}</p>}</li>)}</ol>
  </section>
}


function objectiveValue(key: string, value: number): string {
  return key === 'intensive_teaching_time' ? `${(value/2700000000).toLocaleString('de-AT',{maximumFractionDigits:6})} LE` : String(value)
}

export function IntensiveArrangementFacts({facts, label}: {facts:IntensiveFacts; label:string}) {
  return <section aria-label={label} className="intensive-facts">
    <h3>{label}</h3>
    <p>Gesamt: {facts.totalUnits} LE · Intensive LE: {(facts.intensiveLe.numerator/facts.intensiveLe.denominator).toLocaleString('de-AT',{maximumFractionDigits:6})} · Tägliche LV-Vielfalt: {facts.dailyVariety}</p>
    <p>Zuerst zählt die gesamte Lehre, dann die intensive Lehre, dann die tägliche LV-Vielfalt. Eine einzelne LV bleibt zulässig; eine Markierung garantiert keine Platzierung.</p>
    <ul>{facts.cohortDates.map(row=><li key={`${row.date}-${row.cohortId}`}>{formatCalendarDate(row.date)} · Kohorte {row.cohortId}: {row.distinctLvCount} verschiedene LVs · {row.varietyContribution} Vielfaltspunkte</li>)}</ul>
  </section>
}

export function OptimizationProofFacts({proof}: {proof:CandidateProof}) {
  return <section className="optimization-proof" aria-label="Gültigkeit und Nachweise">
    <h3>Harte Regeln geprüft</h3>
    <p>Ein gültiger Stundenplan muss nicht vollständig oder optimal sein. {proof.coverageProven ? 'Die maximale Abdeckung ist für die vorbereitete Auswahl nachgewiesen.' : 'Die maximale Abdeckung ist nicht nachgewiesen; weitere Lehreinheiten könnten möglich sein.'}</p>
    <p>Verbleibende erforderliche Lehreinheiten: {Math.max(proof.requiredUnits-proof.scheduledUnits,0)}.</p>
    <p>{proof.gapKnown ? `Nach der verfügbaren Obergrenze ${proof.unitUpperBound} sind höchstens ${proof.additionalPossibleUnits} zusätzliche Lehreinheiten möglich. Dies ist keine Zusage, dass die Obergrenze erreichbar ist.` : 'Abstand zum möglichen Maximum unbekannt. Es gibt keine belastbare Obergrenze.'}</p>
    <p>{proof.preferencesProven ? 'Auch die nachgeordneten Ziele sind in ihrer Prioritätsfolge nachgewiesen.' : 'Wochenverteilung, Wechsel der Lehrperson oder Raumwahl könnten verbessert werden. Vollständige Abdeckung bedeutet keine optimalen Präferenzen.'}</p>
    <p>Die angezeigten Werte beschreiben den aktuellen Kandidaten. „Nicht versucht“ bedeutet: Dieses Ziel wurde noch nicht gezielt optimiert. Ein gemessener Wert ist kein Optimalitätsnachweis.</p>
    <ol className="optimization-objectives">{proof.objectives.map(objective=><li key={objective.objectiveKey}>
      <strong>{objectiveLabels[objective.objectiveKey] ?? objective.objectiveKey}</strong>: {proofLabels[objective.proofStatus]}
      {objective.value != null ? ` · Gemessener Kandidatenwert ${objectiveValue(objective.objectiveKey,objective.value)}` : ' · Wert unbekannt'}
      {objective.objectiveKey === 'schedule_shape' && <span> · Zusammengesetzter Strafwert: zusätzliche Termine in derselben Woche und Abweichungen von der bevorzugten Termingröße; kleinere Werte sind günstiger. Dies sind keine Lehreinheiten oder Minuten.</span>}
      {objective.objectiveKey === 'weekly_spread' && <span> · Abweichung von gleichmäßig verteilten Lehreinheiten über die verfügbaren Wochen des Lehrzeitraums; kleinere Werte sind günstiger. Die Verteilung ist eine Präferenz und erzwingt keine gesperrten Termine.</span>}
      {objective.objectiveKey === 'room_changes' && <span> · Strafwert aus Raumwechseln innerhalb einer LV und zusätzlichen Räumen je Kohorte und Tag.</span>}
      {objective.condition && <span> · Bedingung: {Object.entries(objective.condition).map(([key,value])=>`${objectiveLabels[key]??key} = ${objectiveValue(key,value)}`).join(', ')}</span>}
    </li>)}</ol>
    <p>Der Nachweis gilt für die vorbereitete Auswahl ({proof.selectedCourseIds.length} Lehrveranstaltungen) mit der damaligen festen Belegung; keine Aussage über ein globales Semesteroptimum oder unabhängige Kursmaxima. Nach dem Speichern werden diese Termine für spätere Auswahlen zur festen Belegung und können deren Möglichkeiten einschränken.</p>
  </section>
}
