export function lifecycleOverviewFixture(timestamp = '2026-07-20T10:00:00Z') {
  const revision = {
    revisionId: 11, semesterId: 1, revisionNumber: 1, revisionVersion: 1, state: 'draft' as const,
    originRevisionId: null, isActiveWorking: true, isCurrentPublication: false,
    createdAt: timestamp, stateChangedAt: timestamp, publishedAt: null,
    events: [{ eventSequence: 1, eventType: 'created' as const, fromState: null, toState: 'draft' as const, occurredAt: timestamp }],
    allowedActions: { markReady: true, returnToDraft: false, preparePublication: true, abandon: true, restore: false, editSchedule: true },
  }
  return { semesterId: 1, semesterName: 'Fall 2026', stateToken: 'state-1', activeWorkingRevision: revision, currentPublication: null, revisions: [revision], allowedActions: { createWorkingRevision: false } }
}

export const snapshotFixture = () => ({ schemaVersion: 1, capturedAt: '2026-07-20T10:00:00Z', semester: { sourceId: 1, name: 'Fall 2026', startDate: '2026-09-01', endDate: '2026-12-20' }, courses: [], examSessions: [], capturedConditions: [] })
export const publicationFixture = () => ({ preparationToken: 'publication-1', preparedAt: '2026-07-20T10:00:00Z', semesterId: 1, semesterName: 'Fall 2026', targetRevision: lifecycleOverviewFixture().activeWorkingRevision!, consequence: 'first_publication' as const, currentPublication: null, courseCount: 1, totalUnits: 4, scheduledUnits: 2, remainingUnits: 2, conditions: [{ code: 'course_units_remaining', message: '2 units remain', courseId: 1, sessionKind: 'teaching' as const, sourceSessionId: null, details: { remainingUnits: 2 } }] })
