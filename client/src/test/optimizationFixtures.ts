import type { OptimizationGenerationResult, OptimizationPreparation } from '../api/conflictAwareGeneration'

export const optimizationPreparationFixture: OptimizationPreparation = {
  semesterId: 1,
  scheduleRevisionId: 11,
  unavailableDates: ['2026-10-26'],
  sharedSnapshotToken: 'shared-snapshot',
  replacementCourseIds: [2],
  courses: [
    { courseId: 1, courseName: 'Algorithms', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-1' },
    { courseId: 2, courseName: 'Databases', available: true, draftScheduleId: 9, draftRevision: 3, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, inputSnapshotToken: 'course-2' },
  ],
}

export const optimizationResultFixture: OptimizationGenerationResult = {
  semesterId: 1,
  summary: { total: 2, complete: 1, improvedPartial: 1, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 14, remainingUnits: 2, elapsedMilliseconds: 245, optimalForPreparedSnapshot: true },
  outcomes: [
    { courseId: 1, courseName: 'Algorithms', status: 'complete', draftScheduleId: 10, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] },
    { courseId: 2, courseName: 'Databases', status: 'improved_partial', draftScheduleId: 9, draftRevision: 4, scheduledUnits: 6, remainingUnits: 2, saved: true, improvement: { addedUnits: 2, reducedConflicts: 0, reducedLecturerChanges: 1, reducedRoomChanges: 0 }, reasons: [{ code: 'ROOM_OCCUPIED', message: 'Eligible rooms are occupied.', relatedCount: 2 }], errors: [] },
  ],
}

export const mixedOptimizationResultFixture: OptimizationGenerationResult = {
  ...optimizationResultFixture,
  summary: { total: 5, complete: 1, improvedPartial: 1, unchanged: 1, failed: 1, stale: 1, scheduledUnits: 20, remainingUnits: 12, elapsedMilliseconds: 812, optimalForPreparedSnapshot: true },
  outcomes: [
    ...optimizationResultFixture.outcomes,
    { courseId: 3, courseName: 'Networks', status: 'unchanged', draftScheduleId: 11, draftRevision: 2, scheduledUnits: 4, remainingUnits: 4, saved: false, improvement: null, reasons: [{ code: 'SELECTED_COURSE_COMPETITION', message: 'Other selected courses use the limited capacity.', relatedCount: 1 }], errors: [] },
    { courseId: 4, courseName: 'Security', status: 'failed', draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 4, saved: false, improvement: null, reasons: [], errors: [{ code: 'INVALID_PLANNING_INPUT', message: 'Course input is incomplete.' }] },
    { courseId: 5, courseName: 'Compilers', status: 'stale', draftScheduleId: 12, draftRevision: 5, scheduledUnits: 2, remainingUnits: 2, saved: false, improvement: null, reasons: [{ code: 'STALE_PLANNING_INPUT', message: 'Planning inputs changed.', relatedCount: 1 }], errors: [] },
  ],
}
