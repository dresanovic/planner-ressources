import type {
  OptimizationDecisionRequiredResult,
  OptimizationGenerationResult,
  OptimizationPreparation,
  RegenerationComparison,
  OptimizationOperationStatus,
  CandidateProof,
} from '../api/conflictAwareGeneration'

const effectiveConstraints = {
  courseId: 1,
  semesterId: 1,
  planningPeriod: { startDate: '2026-09-07', endDate: '2026-12-20' },
  allowedTeachingWindows: [{ sourceTimeWindowId: 1, weekday: 0, startTime: '08:00', endTime: '12:00' }],
  isCustom: false,
  constraintSetId: null,
  revision: null,
  studyType: { id: 1, name: 'Full-time' },
}

export const optimizationPreparationFixture: OptimizationPreparation = {
  budgetPolicy: { defaultSeconds: 300, ceilingSeconds: 1800, policyFingerprint: 'c'.repeat(64) },
  semesterId: 1,
  scheduleRevisionId: 11,
  unavailableDates: ['2026-10-26'],
  sharedSnapshotToken: 'shared-snapshot',
  replacementCourseIds: [2],
  courses: [
    { courseId: 1, courseName: 'Algorithms', available: true, unavailableReasons: [], draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, effectiveConstraints, inputSnapshotToken: 'course-1' },
    { courseId: 2, courseName: 'Databases', available: true, unavailableReasons: [], draftScheduleId: 9, draftRevision: 3, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, effectiveConstraints: { ...effectiveConstraints, courseId: 2 }, inputSnapshotToken: 'course-2' },
  ],
}

export const optimizationResultFixture: OptimizationGenerationResult = {
  mode: 'direct_saved',
  semesterId: 1,
  summary: { total: 2, complete: 1, improvedPartial: 1, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 14, remainingUnits: 2, elapsedMilliseconds: 245, optimalForPreparedSnapshot: true },
  outcomes: [
    { courseId: 1, courseName: 'Algorithms', status: 'complete', draftScheduleId: 10, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] },
    { courseId: 2, courseName: 'Databases', status: 'improved_partial', draftScheduleId: 9, draftRevision: 4, scheduledUnits: 6, remainingUnits: 2, saved: true, improvement: { addedUnits: 2, reducedConflicts: 0, reducedLecturerChanges: 1, reducedRoomChanges: 0 }, reasons: [{ code: 'ROOM_OCCUPIED', message: 'Eligible rooms are occupied.', relatedCount: 2, sourceKind: 'active_exam', sourceId: 44 }], errors: [] },
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

export const regenerationComparisonFixture: RegenerationComparison = {
  selectedCourseIds: [1, 2],
  current: { requiredUnits: 16, scheduledUnits: 4, remainingUnits: 12, status: 'partial' },
  generated: { requiredUnits: 16, scheduledUnits: 14, remainingUnits: 2, status: 'partial' },
  replacesAllSelectedSessions: true,
  mayReplacePlannerEdits: true,
  courses: [
    {
      courseId: 1,
      courseName: 'Algorithms',
      current: { requiredUnits: 8, scheduledUnits: 0, remainingUnits: 8, status: 'partial' },
      generated: { requiredUnits: 8, scheduledUnits: 8, remainingUnits: 0, status: 'complete' },
      resolvedCurrentWarnings: [],
      remainingReasons: [],
    },
    {
      courseId: 2,
      courseName: 'Databases',
      current: { requiredUnits: 8, scheduledUnits: 4, remainingUnits: 4, status: 'partial' },
      generated: { requiredUnits: 8, scheduledUnits: 6, remainingUnits: 2, status: 'partial' },
      resolvedCurrentWarnings: [{ code: 'OUTSIDE_ALLOWED_WINDOW', count: 1 }],
      remainingReasons: [{ code: 'ROOM_OCCUPIED', message: 'Geeignete Räume sind belegt.', relatedCount: 2 }],
    },
  ],
}

export const decisionRequiredGenerationFixture: OptimizationDecisionRequiredResult = {
  mode: 'decision_required',
  saved: false,
  candidateFingerprint: 'a'.repeat(64),
  preparedEvidence: {
    semesterId: optimizationPreparationFixture.semesterId,
    scheduleRevisionId: optimizationPreparationFixture.scheduleRevisionId,
    unavailableDates: optimizationPreparationFixture.unavailableDates,
    sharedSnapshotToken: optimizationPreparationFixture.sharedSnapshotToken,
    courses: optimizationPreparationFixture.courses.map((course) => ({
      courseId: course.courseId,
      expectedDraftScheduleId: course.draftScheduleId,
      expectedDraftRevision: course.draftRevision,
      inputSnapshotToken: course.inputSnapshotToken,
    })),
  },
  comparison: regenerationComparisonFixture,
}

export const directSavedGenerationFixture: OptimizationGenerationResult = {
  ...optimizationResultFixture,
}

export const operationIdFixture = '00000000-0000-4000-8000-000000000001'
export const contextSecretFixture = 'ab'.repeat(32)
export const budgetPolicyFixture = {
  defaultSeconds: 300,
  ceilingSeconds: 1800,
  policyFingerprint: 'c'.repeat(64),
}

export const operationStatusFixture: OptimizationOperationStatus = {
  operationId: operationIdFixture,
  semesterId: 1,
  scheduleRevisionId: 11,
  selectedCourseIds: [1, 2],
  selectionCount: 2,
  phase: 'optimizing',
  budgetSeconds: 300,
  elapsedMilliseconds: 65001,
  budgetExhausted: false,
  currentObjectiveKey: 'total_units',
  saved: false,
  canAccept: false,
  canFinalize: false,
  review: null,
  result: null,
  errors: [],
  terminalCode: null,
}

/** A controllable transport response for polling, navigation and decision races. */
export function deferredResponse<T>() {
  let resolve!: (value: T) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<T>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

export const objectiveKeysFixture = [
  'total_units', 'conflicts', 'schedule_shape', 'lecturer_changes',
  'room_changes', 'retained_drafts', 'canonical_temporal', 'canonical_resource',
] as const

export function objectiveEvidenceFixture(unfinishedIndex = 0) {
  return objectiveKeysFixture.map((objectiveKey, index) => ({
    objectiveKey,
    direction: objectiveKey === 'total_units' || objectiveKey === 'retained_drafts' ? 'maximize' : 'minimize',
    proofStatus: index < unfinishedIndex ? 'proven' : index === unfinishedIndex ? 'unfinished' : 'not_attempted',
    value: index === 0 ? 80 : null,
    preparedSnapshotToken: 'd'.repeat(64),
    candidateFingerprint: 'a'.repeat(64),
    condition: null,
  }))
}

export const candidateProofFixture: CandidateProof = {
  preparedSnapshotToken:'d'.repeat(64), candidateFingerprint:'a'.repeat(64),
  selectedCourseIds:[1,2], requiredUnits:100, scheduledUnits:80,
  coverageProven:false,preferencesProven:false,
  objectives:objectiveKeysFixture.map((objectiveKey,index)=>({
    objectiveKey,direction:objectiveKey==='total_units'||objectiveKey==='retained_drafts'?'max':'min',
    proofStatus:index===0?'unfinished':'not_attempted',value:index===0?80:null,
    preparedSnapshotToken:'d'.repeat(64),candidateFingerprint:'a'.repeat(64),condition:null,
  })),
  unitUpperBound:90,additionalPossibleUnits:10,gapKnown:true,
}
