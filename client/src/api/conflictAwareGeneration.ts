import { plannerFetch } from './plannerFetch'

export type OptimizationStatus = 'complete' | 'improved_partial' | 'unchanged' | 'failed' | 'stale'
export type TeachingAlgorithm = 'standard' | 'cohort' | 'lecturer' | 'standard_optimized'
export type StrategyIdentity = {
  algorithm?: TeachingAlgorithm
  strategyProfile?: 'standard-v1' | 'heuristic-v1' | 'standard-optimized-v1'
  strategySettings?: Record<string, unknown>
}
export const teachingAlgorithmLabel = (algorithm: TeachingAlgorithm = 'standard') =>
  ({ standard: 'Standard', standard_optimized: 'Standard optimiert', cohort: 'Kohorte', lecturer: 'Lehrperson' })[algorithm]
export function teachingTerminationLabel(termination?: string | null): string {
  return ({heuristic_completed:'Heuristische Suche beendet — Optimalität nicht nachgewiesen', repair_limit:'Reparaturlimit erreicht — Optimalität nicht nachgewiesen', deadline:'Zeitlimit erreicht', cancelled:'Abgebrochen', failed:'Fehlgeschlagen',standard_completed:'Standard-Suche beendet',standard_optimized_completed:'Standard-optimiert-Suche beendet'} as Record<string,string>)[termination ?? ''] ?? ''
}

export type OptimizationError = {
  code: string
  message: string
  replacementCourseIds?: number[]
}

export type BlockingReason = {
  code: string
  message: string
  relatedCount: number
  holidayDate?: string
  holidayName?: string
  sourceKind?: 'teaching_session' | 'active_exam'
  sourceId?: number
}

export type PreparedOptimizationCourse = {
  courseId: number
  courseName: string | null
  available: boolean
  unavailableReasons: BlockingReason[]
  draftScheduleId: number | null
  draftRevision: number | null
  scheduledUnits: number
  remainingUnits: number
  replacementRequired: boolean
  effectiveConstraints: GenerationConstraints
  inputSnapshotToken: string
}

export type OptimizationPreparation = StrategyIdentity & {
  semesterId: number
  scheduleRevisionId: number
  unavailableDates: string[]
  sharedSnapshotToken: string
  courses: PreparedOptimizationCourse[]
  replacementCourseIds: number[]
  budgetPolicy: OptimizationBudgetPolicy
}

export type OptimizationBudgetPolicy = {
  activeAlgorithm?: TeachingAlgorithm
  strategyProfile?: 'standard-v1' | 'heuristic-v1' | 'standard-optimized-v1'
  strategySettings?: Record<string, unknown>
  defaultSeconds: number
  ceilingSeconds: number
  policyFingerprint: string
}

export type OptimizationOperationPhase =
  | 'preparing' | 'optimizing' | 'checking' | 'ready_to_save' | 'awaiting_decision'
  | 'saving' | 'saved' | 'cancelled' | 'timeout_no_candidate' | 'failed' | 'stale' | 'interrupted'

/** Live authority is memory-only and never part of a status or saved receipt. */
export type OptimizationOperationContext = { operationId: string; contextSecret: string }
export type OptimizationOutcomeIdentity = { operationId: string }
export type OptimizationOperationStatus = StrategyIdentity & {
  termination?: 'standard_completed' | 'standard_optimized_completed' | 'heuristic_completed' | 'repair_limit' | 'deadline' | 'cancelled' | 'failed' | null
  operationId: string
  semesterId: number
  scheduleRevisionId: number
  selectedCourseIds: number[]
  selectionCount: number
  phase: OptimizationOperationPhase
  budgetSeconds: number
  elapsedMilliseconds: number
  budgetExhausted: boolean
  currentObjectiveKey: string | null
  saved: boolean
  canAccept: boolean
  canFinalize: boolean
  review: OptimizationDecisionRequiredResult | null
  result: OptimizationGenerationResult | null
  errors: OptimizationError[]
  terminalCode: string | null
}

export type OptimizationOperationStart = OptimizationOperationContext & {
  policyFingerprint: string
  preparation: PreparedGenerationEvidence
}

export async function startOptimizationOperation(preparation: OptimizationPreparation, context: OptimizationOperationContext, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  validateSelection(preparation.courses.map(course=>course.courseId))
  return operationRequest('/operations', {
    method:'POST', signal, body:JSON.stringify({...context,policyFingerprint:preparation.budgetPolicy.policyFingerprint,
      preparation:{semesterId:preparation.semesterId,scheduleRevisionId:preparation.scheduleRevisionId,
        unavailableDates:preparation.unavailableDates,sharedSnapshotToken:preparation.sharedSnapshotToken,
        courses:preparation.courses.map(course=>({courseId:course.courseId,expectedDraftScheduleId:course.draftScheduleId,
          expectedDraftRevision:course.draftRevision,inputSnapshotToken:course.inputSnapshotToken}))}}),
  }, true)
}

export function getOptimizationOperation(operationId: string, secret?: string, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(operationId)}`, {
    signal, headers:secret ? {'X-Optimization-Context':secret} : {},
  })
}

export function decideOptimizationOperation(context: OptimizationOperationContext, candidateFingerprint: string, finalize=false, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(context.operationId)}/${finalize ? 'finalize' : 'accept'}`, {
    method:'POST',signal,body:JSON.stringify({contextSecret:context.contextSecret,candidateFingerprint}),
  }, true)
}

export function cancelOptimizationOperation(operationId: string, reason='cancel', keepalive=false): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(operationId)}/cancel`,{
    method:'POST',body:JSON.stringify({reason}),keepalive,
  },true)
}

export function continueOptimizationOperation(context: OptimizationOperationContext, candidateFingerprint: string, continuationId: string, signal?: AbortSignal): Promise<OptimizationOperationStatus> {
  return operationRequest(`/operations/${encodeURIComponent(context.operationId)}/continue`, {
    method:'POST', signal, body:JSON.stringify({contextSecret:context.contextSecret,candidateFingerprint,continuationId}),
  }, true)
}

async function operationRequest(path: string, init: RequestInit, activity=false): Promise<OptimizationOperationStatus> {
  const response=await plannerFetch(`/api/draft-schedules/optimization${path}`, {...init,...(activity ? {activity:'user' as const} : {})})
  if (!response.ok) throw await parseOptimizationError(response)
  return decodeOptimizationStatus(await response.json())
}

export function decodeOptimizationStatus(value: unknown): OptimizationOperationStatus {
  if (!value || typeof value !== 'object') throw new Error('Ungültige Optimierungsantwort')
  const row = value as Record<string, unknown>
  const {algorithm, strategyProfile: profile} = decodeStrategyIdentity(row)
  if (row.termination != null && !['standard_completed', 'standard_optimized_completed', 'heuristic_completed', 'repair_limit', 'deadline', 'cancelled', 'failed'].includes(String(row.termination))) throw new Error('Unbekannter Suchabschluss')
  if (algorithm !== 'standard' && (row.canFinalize || row.phase === 'ready_to_save')) throw new Error('Ausdrückliche Übernahme erforderlich')
  for (const name of ['review', 'result']) {
    const payload = row[name]
    if (payload && typeof payload === 'object') {
      const result = payload as Record<string, unknown>
      if (decodeStrategyIdentity(result).algorithm !== algorithm) throw new Error('Abweichende Ergebnisidentität')
      if (result.proof) decodeCandidateProof(result.proof)
      if (name === 'review' && result.comparison && typeof result.comparison === 'object') {
        const comparison = result.comparison as { courses?: unknown[] }
        comparison.courses?.forEach(decodeCourseComparison)
      }
    }
  }
  return { ...row, algorithm, strategyProfile: profile } as OptimizationOperationStatus
}

function decodeStrategyIdentity(row: Record<string, unknown>): {algorithm:TeachingAlgorithm;strategyProfile:'standard-v1'|'heuristic-v1'|'standard-optimized-v1'} {
  const algorithm = row.algorithm === undefined ? 'standard' : row.algorithm
  if (algorithm !== 'standard' && algorithm !== 'cohort' && algorithm !== 'lecturer' && algorithm !== 'standard_optimized') throw new Error('Unbekannter Algorithmus')
  const profile = row.strategyProfile === undefined && algorithm === 'standard' ? 'standard-v1' : row.strategyProfile
  if (profile !== 'standard-v1' && profile !== 'heuristic-v1' && profile !== 'standard-optimized-v1') throw new Error('Unbekanntes Strategieprofil')
  if (profile !== (algorithm === 'standard' ? 'standard-v1' : algorithm === 'standard_optimized' ? 'standard-optimized-v1' : 'heuristic-v1')) throw new Error('Unbekanntes Strategieprofil')
  return {algorithm, strategyProfile:profile}
}

const standardObjectiveKeys = ['total_units','intensive_teaching_time','daily_variety','conflicts','schedule_shape','lecturer_changes','room_changes','retained_drafts','canonical_temporal','canonical_resource']
const optimizedObjectiveKeys = [...standardObjectiveKeys.slice(0,4), 'weekly_spread', ...standardObjectiveKeys.slice(4)]
const heuristicObjectiveKeys = ['total_units','intensive_teaching_time','daily_variety','preferred_size_deviation','course_rhythm_penalty','owner_balance_penalty','extra_cohort_day_rooms','course_room_changes']
function decodedObject(value: unknown): Record<string, unknown> {
  if (!value || typeof value !== 'object' || Array.isArray(value)) throw new Error('Ungültige Optimierungsdaten')
  return value as Record<string, unknown>
}
function whole(value: unknown): value is number { return typeof value === 'number' && Number.isSafeInteger(value) && value >= 0 }

export function decodeCandidateProof(value: unknown): CandidateProof {
  const row = decodedObject(value)
  const profile = row.objectiveProfile === undefined ? 'standard-v1' : row.objectiveProfile
  if (profile !== 'standard-v1' && profile !== 'heuristic-v1' && profile !== 'standard-optimized-v1') throw new Error('Unbekanntes Nachweisprofil')
  const keys = profile === 'standard-v1' ? standardObjectiveKeys : profile === 'standard-optimized-v1' ? optimizedObjectiveKeys : heuristicObjectiveKeys
  if (!Array.isArray(row.objectives) || row.objectives.length !== keys.length) throw new Error('Unvollständige Zielreihenfolge')
  let prefix = true
  row.objectives.forEach((value, index) => {
    const item = decodedObject(value)
    const key = keys[index]
    if (item.objectiveKey !== key || item.direction !== (['total_units','intensive_teaching_time','daily_variety','retained_drafts'].includes(key) ? 'max' : 'min')) throw new Error('Falsche Zielreihenfolge')
    if (item.preparedSnapshotToken !== row.preparedSnapshotToken || item.candidateFingerprint !== row.candidateFingerprint) throw new Error('Abweichende Nachweisidentität')
    if (!['proven','unfinished','not_attempted','conditional'].includes(String(item.proofStatus))) throw new Error('Unbekannter Nachweisstatus')
    if (item.value !== null && (typeof item.value !== 'number' || !Number.isFinite(item.value))) throw new Error('Ungültiger Messwert')
    if (item.proofStatus === 'proven' && !prefix) throw new Error('Unterbrochener Prioritätsnachweis')
    if (profile === 'heuristic-v1' && index > 0 && ['proven','conditional'].includes(String(item.proofStatus))) throw new Error('Heuristische Präferenzen sind nicht bewiesen')
    if (item.proofStatus === 'conditional' && (!item.condition || !Object.keys(decodedObject(item.condition)).length || Object.keys(decodedObject(item.condition)).some(k=>!keys.slice(0,index).includes(k)))) throw new Error('Ungültige Nachweisbedingung')
    prefix = prefix && item.proofStatus === 'proven'
  })
  const objectives = row.objectives as ObjectiveProof[]
  if (row.coverageProven !== (objectives[0].proofStatus === 'proven') || row.preferencesProven !== prefix) throw new Error('Widersprüchliche Nachweise')
  if (!whole(row.requiredUnits) || !whole(row.scheduledUnits) || row.scheduledUnits > row.requiredUnits) throw new Error('Ungültige Abdeckung')
  if (row.gapKnown !== (row.unitUpperBound !== null) || (row.additionalPossibleUnits === null) !== (row.unitUpperBound === null)) throw new Error('Widersprüchliche Obergrenze')
  if (row.unitUpperBound !== null && (!whole(row.unitUpperBound) || row.unitUpperBound < row.scheduledUnits || row.additionalPossibleUnits !== row.unitUpperBound-row.scheduledUnits)) throw new Error('Ungültiger Abstand zur Obergrenze')
  return { ...row, objectiveProfile: profile } as CandidateProof
}

export function decodeCourseComparison(value: unknown): CourseRegenerationComparison {
  const row = decodedObject(value)
  const generated = decodedObject(row.generated)
  if (!whole(generated.requiredUnits) || !whole(generated.scheduledUnits) || !whole(generated.remainingUnits) || generated.requiredUnits !== generated.scheduledUnits+generated.remainingUnits) throw new Error('Ungültige Kursabdeckung')
  const portions = row.lecturerPortions === undefined ? [] : row.lecturerPortions
  if (!Array.isArray(portions)) throw new Error('Ungültige Lehrpersonenanteile')
  const ids = new Set()
  let required = 0, scheduled = 0
  let previous: [string,number] | undefined
  portions.forEach((value,index)=>{
    const item = decodedObject(value)
    if (!whole(item.lecturerId) || item.lecturerId < 1 || ids.has(item.lecturerId) || item.sequenceIndex !== index || typeof item.lecturerCode !== 'string' || !['derived','explicit'].includes(String(item.source))) throw new Error('Ungültige Anteilsreihenfolge')
    const code = item.lecturerCode.trim().toLowerCase()
    if (previous && (code < previous[0] || code === previous[0] && item.lecturerId < previous[1])) throw new Error('Ungültige Codereihenfolge')
    previous = [code,item.lecturerId]; ids.add(item.lecturerId)
    if (!whole(item.requiredUnits) || !whole(item.scheduledUnits) || !whole(item.remainingUnits) || item.requiredUnits !== item.scheduledUnits+item.remainingUnits) throw new Error('Ungültige Anteilssumme')
    if (item.remainingUnits && (!item.reasonCode || !item.reason)) throw new Error('Fehlende Anteilserklärung')
    required += item.requiredUnits; scheduled += item.scheduledUnits
  })
  if (portions.length && (required !== generated.requiredUnits || scheduled !== generated.scheduledUnits)) throw new Error('Abweichende Kurssumme')
  return row as CourseRegenerationComparison
}

export type ArrangementImprovement = {
  addedUnits: number
  reducedConflicts: number
  reducedLecturerChanges: number
  reducedRoomChanges: number
}

export type CourseOptimizationOutcome = {
  lecturerPortions?: LecturerPortionFacts[]
  courseId: number
  courseName: string | null
  status: OptimizationStatus
  draftScheduleId: number | null
  draftRevision: number | null
  scheduledUnits: number
  remainingUnits: number
  saved: boolean
  improvement: ArrangementImprovement | null
  reasons: BlockingReason[]
  errors: OptimizationError[]
}

export type OptimizationGenerationResult = StrategyIdentity & {
  termination?: OptimizationOperationStatus['termination']
  intensiveFacts?: IntensiveFacts | null
  proof?: CandidateProof | null
  mode: 'direct_saved'
  semesterId: number
  summary: {
    total: number
    complete: number
    improvedPartial: number
    unchanged: number
    failed: number
    stale: number
    scheduledUnits: number
    remainingUnits: number
    elapsedMilliseconds: number
    optimalForPreparedSnapshot: boolean
  }
  outcomes: CourseOptimizationOutcome[]
}

export type CoverageFacts = {
  intensiveFacts?: IntensiveFacts | null
  requiredUnits: number
  scheduledUnits: number
  remainingUnits: number
  status: 'complete' | 'partial'
}

export type ResolvedWarning = { code: string; count: number }

export type IntensiveFacts = {
  totalUnits: number
  intensiveLe: { numerator: number; denominator: 2700000000 }
  dailyVariety: number
  cohortDates: Array<{ cohortId: number; date: string; distinctCourseIds: number[]; distinctLvCount: number; varietyContribution: number }>
  preparedSnapshotToken: string
  candidateFingerprint: string
}

export type CourseRegenerationComparison = {
  lecturerPortions?: LecturerPortionFacts[]
  courseId: number
  courseName: string | null
  current: CoverageFacts
  generated: CoverageFacts
  resolvedCurrentWarnings: ResolvedWarning[]
  remainingReasons: BlockingReason[]
}

export type LecturerPortionFacts = {
  lecturerId: number; lecturerCode: string; sequenceIndex: number; source: 'derived' | 'explicit'
  requiredUnits: number; scheduledUnits: number; remainingUnits: number
  reasonCode?: string | null; reason?: string | null
}

export type RegenerationComparison = {
  selectedCourseIds: number[]
  current: CoverageFacts
  generated: CoverageFacts
  courses: CourseRegenerationComparison[]
  replacesAllSelectedSessions: true
  mayReplacePlannerEdits: true
}

export type PreparedGenerationEvidence = {
  semesterId: number
  scheduleRevisionId: number
  unavailableDates: string[]
  sharedSnapshotToken: string
  courses: {
    courseId: number
    expectedDraftScheduleId?: number | null
    expectedDraftRevision?: number | null
    inputSnapshotToken: string
  }[]
}

export type OptimizationDecisionRequiredResult = StrategyIdentity & {
  proof?: CandidateProof | null
  hasSavedSessions?: boolean
  mode: 'decision_required'
  saved: false
  candidateFingerprint: string
  preparedEvidence: PreparedGenerationEvidence
  comparison: RegenerationComparison
}

export type ObjectiveProof = {
  objectiveKey: string
  direction: 'max' | 'min'
  proofStatus: 'proven' | 'unfinished' | 'not_attempted' | 'conditional'
  value: number | null
  preparedSnapshotToken: string
  candidateFingerprint: string
  condition: Record<string, number> | null
}

export type CandidateProof = {
  objectiveProfile?: 'standard-v1' | 'heuristic-v1' | 'standard-optimized-v1'
  preparedSnapshotToken: string
  candidateFingerprint: string
  selectedCourseIds: number[]
  requiredUnits: number
  scheduledUnits: number
  coverageProven: boolean
  preferencesProven: boolean
  objectives: ObjectiveProof[]
  unitUpperBound: number | null
  additionalPossibleUnits: number | null
  gapKnown: boolean
}

export type OptimizationGenerationResponse =
  | OptimizationGenerationResult
  | OptimizationDecisionRequiredResult

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function prepareConflictAwareGeneration(
  semesterId: number,
  scheduleRevisionId: number,
  courseIds: number[],
  unavailableDates: string[] = [],
): Promise<OptimizationPreparation> {
  validateSelection(courseIds)
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/prepare`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ semesterId, scheduleRevisionId, courseIds, unavailableDates }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  const value = await response.json()
  return { ...value, ...decodeStrategyIdentity(decodedObject(value)) }
}

export async function generateConflictAwareSchedules(
  preparation: OptimizationPreparation,
): Promise<OptimizationGenerationResponse> {
  validateSelection(preparation.courses.map((course) => course.courseId))
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/generate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      semesterId: preparation.semesterId,
      scheduleRevisionId: preparation.scheduleRevisionId,
      unavailableDates: preparation.unavailableDates,
      sharedSnapshotToken: preparation.sharedSnapshotToken,
      courses: preparation.courses.map((course) => ({
        courseId: course.courseId,
        expectedDraftScheduleId: course.draftScheduleId,
        expectedDraftRevision: course.draftRevision,
        inputSnapshotToken: course.inputSnapshotToken,
      })),
    }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

export async function acceptConflictAwareSchedules(
  preview: OptimizationDecisionRequiredResult,
): Promise<OptimizationGenerationResult> {
  const evidence = preview.preparedEvidence
  validateSelection(evidence.courses.map((course) => course.courseId))
  const response = await request(`${API_BASE}/api/draft-schedules/optimization/accept`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      ...evidence,
      candidateFingerprint: preview.candidateFingerprint,
    }),
  })
  if (!response.ok) throw await parseOptimizationError(response)
  return response.json()
}

function validateSelection(courseIds: number[]) {
  if (courseIds.length < 1 || courseIds.length > 20) {
    throw [{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Semester optimization requires 1-20 courses.' }]
  }
  if (new Set(courseIds).size !== courseIds.length) {
    throw [{ code: 'DUPLICATE_COURSE_SELECTION', message: 'Select each course only once.' }]
  }
}

async function parseOptimizationError(response: Response): Promise<OptimizationError[]> {
  try {
    const body = await response.json()
    if (Array.isArray(body.errors)) return body.errors
    if (Array.isArray(body.detail)) {
      return body.detail.map((item: { msg?: string }) => ({ code: 'INVALID_REQUEST', message: item.msg ?? 'The optimization request is invalid.' }))
    }
    if (body.code) return [body]
  } catch {
    // Use the safe fallback below.
  }
  return [{ code: 'REQUEST_FAILED', message: 'Could not complete semester optimization.' }]
}

async function request(input: RequestInfo | URL, init?: RequestInit): Promise<Response> {
  try {
    return await plannerFetch(input, { ...init, activity: 'user' })
  } catch {
    throw [{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }]
  }
}
import type { GenerationConstraints } from './draftSchedule'
