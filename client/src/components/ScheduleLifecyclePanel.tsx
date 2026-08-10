import type { ScheduleLifecycleOverview, ScheduleRevisionSummary, TransitionAction } from '../api/scheduleLifecycle'
import { formatViennaDateTime } from '../utils/datePresentation'


type Props = {
  overview: ScheduleLifecycleOverview
  selectedRevisionId: number | null
  busy: boolean
  onStartDraft: () => void
  onSelectRevision: (revisionId: number) => void
  onPreparePublication: (revision: ScheduleRevisionSummary) => void
  onTransition: (revision: ScheduleRevisionSummary, action: TransitionAction) => void
  onAbandon: (revision: ScheduleRevisionSummary) => void
}


export function ScheduleLifecyclePanel({ overview, selectedRevisionId, busy, onStartDraft, onSelectRevision, onPreparePublication, onTransition, onAbandon }: Props) {
  const selected = overview.revisions.find((item) => item.revisionId === selectedRevisionId) ?? overview.activeWorkingRevision ?? overview.currentPublication
  return (
    <section className="lifecycle-panel" aria-label="Veröffentlichungsstatus der Planung">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Versionierte Planung</p>
          <h2>{overview.semesterName}</h2>
        </div>
        {overview.allowedActions.createWorkingRevision && (
          <button type="button" disabled={busy} onClick={onStartDraft}>{overview.currentPublication ? 'Neue Revision starten' : 'Entwurf starten'}</button>
        )}
      </div>
      <div className="lifecycle-designations">
        <Designation label="Aktive Arbeitsrevision" revision={overview.activeWorkingRevision} />
        <Designation label="Aktuelle Veröffentlichung" revision={overview.currentPublication} />
      </div>
      {selected && (
        <div className="lifecycle-selected" aria-live="polite">
          <strong>Revision {selected.revisionNumber}</strong>
          <span className={`lifecycle-state state-${selected.state}`}>{stateLabel(selected.state)}</span>
          {selected.allowedActions.preparePublication && (
            <button type="button" disabled={busy} onClick={() => onPreparePublication(selected)}>Revision veröffentlichen</button>
          )}
          {selected.allowedActions.markReady && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'mark_ready')}>Als prüfbereit markieren</button>}
          {selected.allowedActions.returnToDraft && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'return_to_draft')}>In Entwurf zurücksetzen</button>}
          {selected.allowedActions.abandon && <button type="button" className="destructive-button" disabled={busy} onClick={() => onAbandon(selected)}>Revision verwerfen</button>}
          {selected.allowedActions.restore && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'restore')}>Revision wiederherstellen</button>}
        </div>
      )}
      {overview.revisions.length > 0 && (
        <ol className="lifecycle-history" aria-label="Revisionsverlauf">
          {overview.revisions.map((revision) => (
            <li key={revision.revisionId} data-revision-id={revision.revisionId}>
              <details>
                <summary>
                  <strong>Revision {revision.revisionNumber}</strong>
                  <span className={`lifecycle-state state-${revision.state}`}>{stateLabel(revision.state)}</span>
                </summary>
                <div className="lifecycle-event-history">
                  <button type="button" className={revision.revisionId === selected?.revisionId ? 'selected-revision' : 'secondary-button'} disabled={busy || revision.revisionId === selected?.revisionId} onClick={() => onSelectRevision(revision.revisionId)}>
                    {revision.revisionId === selected?.revisionId ? 'Aktuelle Auswahl' : `Revision ${revision.revisionNumber} öffnen`}
                  </button>
                  {revision.originRevisionId && <small>Ursprungsrevision {revision.originRevisionId}</small>}
                  {revision.events.map((event) => <small key={event.eventSequence}>{eventLabel(event.eventType)} <time dateTime={event.occurredAt}>{formatVienna(event.occurredAt)}</time></small>)}
                </div>
              </details>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}


function Designation({ label, revision }: { label: string; revision: ScheduleRevisionSummary | null }) {
  return <div className="lifecycle-designation"><span>{label}</span><strong>{revision ? `Revision ${revision.revisionNumber} · ${stateLabel(revision.state)}` : 'Keine'}</strong></div>
}

function stateLabel(state: ScheduleRevisionSummary['state']) {
  return ({ draft: 'Entwurf', ready_for_review: 'Bereit zur Prüfung', published: 'Veröffentlicht', superseded: 'Ersetzt', abandoned: 'Verworfen' })[state]
}

function eventLabel(event: ScheduleRevisionSummary['events'][number]['eventType']) {
  return ({ created: 'Erstellt', marked_ready: 'Als prüfbereit markiert', returned_to_draft: 'In Entwurf zurückgesetzt', published: 'Veröffentlicht', superseded: 'Ersetzt', abandoned: 'Verworfen', restored: 'Wiederhergestellt' })[event]
}

function formatVienna(value: string) {
  return `${formatViennaDateTime(value)} Europe/Vienna`
}
