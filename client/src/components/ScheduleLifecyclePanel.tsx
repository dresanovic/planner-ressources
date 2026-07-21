import type { ScheduleLifecycleOverview, ScheduleRevisionSummary, TransitionAction } from '../api/scheduleLifecycle'


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
    <section className="lifecycle-panel" aria-label="Schedule publication lifecycle">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Versioned schedule</p>
          <h2>{overview.semesterName}</h2>
        </div>
        {overview.allowedActions.createWorkingRevision && (
          <button type="button" disabled={busy} onClick={onStartDraft}>{overview.currentPublication ? 'Start new revision' : 'Start Draft'}</button>
        )}
      </div>
      <div className="lifecycle-designations">
        <Designation label="Active working revision" revision={overview.activeWorkingRevision} />
        <Designation label="Current publication" revision={overview.currentPublication} />
      </div>
      {selected && (
        <div className="lifecycle-selected" aria-live="polite">
          <strong>Revision {selected.revisionNumber}</strong>
          <span className={`lifecycle-state state-${selected.state}`}>{stateLabel(selected.state)}</span>
          {selected.allowedActions.preparePublication && (
            <button type="button" disabled={busy} onClick={() => onPreparePublication(selected)}>Publish revision</button>
          )}
          {selected.allowedActions.markReady && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'mark_ready')}>Mark ready for review</button>}
          {selected.allowedActions.returnToDraft && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'return_to_draft')}>Return to Draft</button>}
          {selected.allowedActions.abandon && <button type="button" className="destructive-button" disabled={busy} onClick={() => onAbandon(selected)}>Abandon revision</button>}
          {selected.allowedActions.restore && <button type="button" className="secondary-button" disabled={busy} onClick={() => onTransition(selected, 'restore')}>Restore revision</button>}
        </div>
      )}
      {overview.revisions.length > 0 && (
        <ol className="lifecycle-history" aria-label="Revision history">
          {overview.revisions.map((revision) => (
            <li key={revision.revisionId}>
              <button type="button" className={revision.revisionId === selected?.revisionId ? 'selected-revision' : 'secondary-button'} disabled={busy} onClick={() => onSelectRevision(revision.revisionId)}>
                Revision {revision.revisionNumber} · {stateLabel(revision.state)}
              </button>
              <div className="lifecycle-event-history">
                {revision.originRevisionId && <small>Origin revision ID {revision.originRevisionId}</small>}
                {revision.events.map((event) => <small key={event.eventSequence}>{eventLabel(event.eventType)} <time dateTime={event.occurredAt}>{formatVienna(event.occurredAt)}</time></small>)}
              </div>
            </li>
          ))}
        </ol>
      )}
    </section>
  )
}


function Designation({ label, revision }: { label: string; revision: ScheduleRevisionSummary | null }) {
  return <div className="lifecycle-designation"><span>{label}</span><strong>{revision ? `Revision ${revision.revisionNumber} · ${stateLabel(revision.state)}` : 'None'}</strong></div>
}

function stateLabel(state: ScheduleRevisionSummary['state']) {
  return ({ draft: 'Draft', ready_for_review: 'Ready for review', published: 'Published', superseded: 'Superseded', abandoned: 'Abandoned' })[state]
}

function eventLabel(event: ScheduleRevisionSummary['events'][number]['eventType']) {
  return ({ created: 'Created', marked_ready: 'Marked ready', returned_to_draft: 'Returned to Draft', published: 'Published', superseded: 'Superseded', abandoned: 'Abandoned', restored: 'Restored' })[event]
}

function formatVienna(value: string) {
  return new Intl.DateTimeFormat('en-GB', { dateStyle: 'medium', timeStyle: 'short', timeZone: 'Europe/Vienna' }).format(new Date(value)) + ' Europe/Vienna'
}
