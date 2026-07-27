import type { CalendarWorkspace } from '../api/calendarWorkspace'
import type { ScheduleRevisionSummary } from '../api/scheduleLifecycle'

export function calendarWorkspaceMatchesSelection(
  workspace: CalendarWorkspace | null,
  semesterId: number | null,
  revision: ScheduleRevisionSummary | null,
) {
  if (workspace == null || workspace.semester.semesterId !== semesterId) return false
  if (revision == null) return workspace.workspaceState === 'no_revision'
  if (workspace.workspaceState !== 'loaded') return false
  const intendedDesignation = revision.isActiveWorking
    ? 'active_working'
    : revision.isCurrentPublication
      ? 'current_published'
      : null
  if (intendedDesignation == null) return false
  return workspace.selectedRevision.revisionId === revision.revisionId
    && workspace.selectedRevision.lifecycleState === revision.state
    && workspace.selectedRevision.designation === intendedDesignation
    && workspace.selectedRevision.readOnly === (intendedDesignation === 'current_published')
}
