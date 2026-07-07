import type { DraftSchedule, GenerationFailure } from '../api/draftSchedule'

type DraftSchedulePanelProps = {
  schedule: DraftSchedule | null
  errors: GenerationFailure[]
  isLoading: boolean
  onGenerate: () => void
}

export function DraftSchedulePanel({
  schedule,
  errors,
  isLoading,
  onGenerate,
}: DraftSchedulePanelProps) {
  return (
    <section className="planner-panel" aria-labelledby="draft-schedule-title">
      <div className="panel-toolbar">
        <div>
          <p className="eyebrow">Draft generation</p>
          <h2 id="draft-schedule-title">Single-course schedule</h2>
        </div>
        <button type="button" onClick={onGenerate} disabled={isLoading}>
          {isLoading ? 'Generating...' : 'Generate'}
        </button>
      </div>

      {errors.length > 0 && (
        <div className="alert-list" role="alert">
          {errors.map((error) => (
            <div className="alert-item" key={error.code}>
              <strong>{error.code.replaceAll('_', ' ')}</strong>
              <span>{error.message}</span>
            </div>
          ))}
        </div>
      )}

      {schedule ? (
        <div className="session-table" aria-label="Generated draft sessions">
          <div className="session-row session-header">
            <span>Date</span>
            <span>Time</span>
            <span>Units</span>
            <span>Window</span>
          </div>
          {schedule.sessions.map((session) => (
            <div className="session-row" key={session.id}>
              <span>{session.date}</span>
              <span>
                {session.startTime}-{session.endTime}
              </span>
              <span>{session.units}</span>
              <span>#{session.timeWindowId}</span>
            </div>
          ))}
        </div>
      ) : (
        <p className="empty-state">No generated draft schedule yet.</p>
      )}
    </section>
  )
}
