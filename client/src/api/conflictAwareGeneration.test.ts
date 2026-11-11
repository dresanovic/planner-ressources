import { afterEach, describe, expect, it, vi } from 'vitest'

import { acceptConflictAwareSchedules, generateConflictAwareSchedules, prepareConflictAwareGeneration,
  startOptimizationOperation, getOptimizationOperation, decideOptimizationOperation, cancelOptimizationOperation, continueOptimizationOperation } from './conflictAwareGeneration'
import type { OptimizationOperationStatus } from './conflictAwareGeneration'
import { decodeCandidateProof, decodeCourseComparison, decodeOptimizationStatus, teachingAlgorithmLabel } from './conflictAwareGeneration'
import strategyContracts from '../test/teachingStrategyContracts.json'
import { candidateProofFixture, decisionRequiredGenerationFixture, directSavedGenerationFixture, optimizationPreparationFixture, optimizationResultFixture, operationStatusFixture } from '../test/optimizationFixtures'

afterEach(() => vi.restoreAllMocks())

describe('teaching strategy response decoding', () => {
  it('accepts Standard Optimized with its own ordered distribution profile and explicit review', () => {
    const original = candidateProofFixture
    const proof = { ...original, objectiveProfile: 'standard-optimized-v1',
      objectives: [...original.objectives.slice(0,4), { ...original.objectives[4], objectiveKey:'weekly_spread', direction:'min' }, ...original.objectives.slice(4)] }
    expect(decodeCandidateProof(proof).objectiveProfile).toBe('standard-optimized-v1')
    expect(teachingAlgorithmLabel('standard_optimized')).toBe('Standard optimiert')
    expect(decodeOptimizationStatus({ ...operationStatusFixture, algorithm:'standard_optimized', strategyProfile:'standard-optimized-v1',
      phase:'awaiting_decision', canAccept:true, review:{ ...decisionRequiredGenerationFixture, algorithm:'standard_optimized', strategyProfile:'standard-optimized-v1', proof },
      termination:'standard_optimized_completed' }).algorithm).toBe('standard_optimized')
    expect(() => decodeOptimizationStatus({ ...operationStatusFixture, algorithm:'standard_optimized', strategyProfile:'standard-v1' })).toThrow()
    expect(() => decodeOptimizationStatus({ ...operationStatusFixture, algorithm:'standard_optimized', strategyProfile:'standard-optimized-v1', phase:'ready_to_save', canFinalize:true })).toThrow()
  })
  for (const extra of [{algorithm:'unknown'},{algorithm:'cohort',strategyProfile:'standard-v1'}]) {
    it(`rejects unsupported preparation identity ${JSON.stringify(extra)}`, async () => {
      vi.spyOn(globalThis,'fetch').mockResolvedValue(new Response(JSON.stringify({...optimizationPreparationFixture,...extra}),{status:200}))
      await expect(prepareConflictAwareGeneration(1,11,[1,2])).rejects.toBeDefined()
    })
  }
  for (const entry of strategyContracts.cases.filter(row => row.kind === 'proof' || row.kind === 'comparison')) {
    it(entry.name, () => {
      const decode = entry.kind === 'proof' ? decodeCandidateProof : decodeCourseComparison
      if (entry.valid) expect(() => decode(entry.value)).not.toThrow()
      else expect(() => decode(entry.value)).toThrow()
    })
  }
  for (const entry of strategyContracts.cases.filter(row => row.kind === 'status')) {
    it(entry.name, async () => {
      vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(entry.value), { status: 200 }))
      const response = getOptimizationOperation('00000000-0000-4000-8000-000000000001')
      if (entry.valid) await expect(response).resolves.toMatchObject(entry.value)
      else await expect(response).rejects.toBeDefined()
    })
  }
})

describe('conflict-aware generation API', () => {
  it('uses short operation routes, passive outcome polling and memory-only decision evidence', async () => {
    const fetchMock=vi.spyOn(globalThis,'fetch').mockImplementation(async()=>new Response(JSON.stringify(operationStatusFixture),{status:200}))
    const context={operationId:'test-operation',contextSecret:'b'.repeat(64)}
    await startOptimizationOperation(optimizationPreparationFixture,context)
    expect(fetchMock.mock.calls[0][0]).toBe('/api/draft-schedules/optimization/operations')
    const start=JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(start.policyFingerprint).toBe(optimizationPreparationFixture.budgetPolicy.policyFingerprint)
    expect(start).not.toHaveProperty('budgetSeconds')
    expect(start.preparation).not.toHaveProperty('comparison')
    await getOptimizationOperation(context.operationId)
    let headers=new Headers(fetchMock.mock.calls[1][1]?.headers)
    expect(headers.has('X-Optimization-Context')).toBe(false)
    expect(headers.has('X-Planner-Activity')).toBe(false)
    expect(fetchMock.mock.calls[1][1]?.credentials).toBe('include')
    await getOptimizationOperation(context.operationId,context.contextSecret)
    headers=new Headers(fetchMock.mock.calls[2][1]?.headers)
    expect(headers.get('X-Optimization-Context')).toBe(context.contextSecret)
    expect(headers.has('X-Planner-Activity')).toBe(false)
    for(const finalize of [false,true]) await decideOptimizationOperation(context,'a'.repeat(64),finalize)
    expect(fetchMock.mock.calls[3][0]).toBe('/api/draft-schedules/optimization/operations/test-operation/accept')
    expect(fetchMock.mock.calls[4][0]).toBe('/api/draft-schedules/optimization/operations/test-operation/finalize')
    expect(JSON.parse(String(fetchMock.mock.calls[3][1]?.body))).toEqual({contextSecret:context.contextSecret,candidateFingerprint:'a'.repeat(64)})
    expect(new Headers(fetchMock.mock.calls[3][1]?.headers).get('X-CSRF-Protection')).toBe('1')
    await cancelOptimizationOperation(context.operationId,'navigation',true)
    expect(fetchMock.mock.calls[5][0]).toBe('/api/draft-schedules/optimization/operations/test-operation/cancel')
    expect(fetchMock.mock.calls[5][1]?.keepalive).toBe(true)
    expect(String(fetchMock.mock.calls[5][1]?.body)).not.toContain(context.contextSecret)
    await continueOptimizationOperation(context,'a'.repeat(64),'continued-round')
    expect(fetchMock.mock.calls[6][0]).toBe('/api/draft-schedules/optimization/operations/test-operation/continue')
    expect(JSON.parse(String(fetchMock.mock.calls[6][1]?.body))).toEqual({contextSecret:context.contextSecret,candidateFingerprint:'a'.repeat(64),continuationId:'continued-round'})
    expect(new Headers(fetchMock.mock.calls[6][1]?.headers).get('X-Planner-Activity')).toBe('user')
  })
  it('keeps outcome identity, nullable evidence and long-running status separate from live secrets', () => {
    const status: OptimizationOperationStatus = { ...operationStatusFixture, elapsedMilliseconds: 65001 }
    expect(status.review).toBeNull()
    expect(status.result).toBeNull()
    expect(status.canAccept).toBe(false)
    expect(status.elapsedMilliseconds).toBeGreaterThan(60000)
    expect(status).not.toHaveProperty('contextSecret')
  })
  it('prepares 1-20 courses with future unavailable dates', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(optimizationPreparationFixture), { status: 200 }))
    const result = await prepareConflictAwareGeneration(1, 11, [1, 2], ['2026-10-26'])
    expect(result.sharedSnapshotToken).toBe('shared-snapshot')
    expect(result.courses[0].effectiveConstraints.studyType.name).toBe('Full-time')
    expect(JSON.parse(String(fetchMock.mock.calls[0][1]?.body))).toEqual({ semesterId: 1, scheduleRevisionId: 11, courseIds: [1, 2], unavailableDates: ['2026-10-26'] })
  })

  it('echoes snapshot tokens without a pre-generation replacement decision', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }))
    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)
    expect(result.mode).toBe('direct_saved')
    if (result.mode !== 'direct_saved') throw new Error('Expected direct save')
    expect(result.summary).toEqual(expect.objectContaining({
      total: 2,
      complete: 1,
      improvedPartial: 1,
      unchanged: 0,
      failed: 0,
      stale: 0,
      scheduledUnits: 14,
      remainingUnits: 2,
      elapsedMilliseconds: 245,
      optimalForPreparedSnapshot: true,
    }))
    expect(result.outcomes[1].reasons[0]).toMatchObject({ sourceKind: 'active_exam', sourceId: 44 })
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload.sharedSnapshotToken).toBe('shared-snapshot')
    expect(payload).not.toHaveProperty('replacementConfirmed')
    expect(payload.courses[1].inputSnapshotToken).toBe('course-2')
  })

  it('returns the server-owned post-generation comparison and fingerprint', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(decisionRequiredGenerationFixture), { status: 200 }))

    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)

    expect(result.mode).toBe('decision_required')
    if (result.mode !== 'decision_required') throw new Error('Expected decision preview')
    expect(result.saved).toBe(false)
    expect(result.candidateFingerprint).toHaveLength(64)
    expect(result.comparison.generated.scheduledUnits).toBe(14)
    expect(result.comparison.courses[1].resolvedCurrentWarnings).toEqual([{ code: 'OUTSIDE_ALLOWED_WINDOW', count: 1 }])
  })

  it('accepts only the server-owned prepared evidence and candidate fingerprint', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }),
    )

    const result = await acceptConflictAwareSchedules(decisionRequiredGenerationFixture)

    expect(result.mode).toBe('direct_saved')
    expect(fetchMock.mock.calls[0][0]).toBe('/api/draft-schedules/optimization/accept')
    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload).toEqual({
      ...decisionRequiredGenerationFixture.preparedEvidence,
      candidateFingerprint: decisionRequiredGenerationFixture.candidateFingerprint,
    })
    expect(payload).not.toHaveProperty('comparison')
    expect(payload).not.toHaveProperty('sessions')
  })

  it('accepts mixed prepared evidence when an unplanned course omits nullable draft identity fields', async () => {
    const fetchMock = vi.spyOn(globalThis, 'fetch').mockResolvedValue(
      new Response(JSON.stringify(directSavedGenerationFixture), { status: 200 }),
    )
    const preview = {
      ...decisionRequiredGenerationFixture,
      preparedEvidence: {
        ...decisionRequiredGenerationFixture.preparedEvidence,
        courses: [
          decisionRequiredGenerationFixture.preparedEvidence.courses[0],
          { courseId: 2, inputSnapshotToken: 'course-2' },
        ],
      },
    }

    await acceptConflictAwareSchedules(preview)

    const payload = JSON.parse(String(fetchMock.mock.calls[0][1]?.body))
    expect(payload.courses[1]).toEqual({
      courseId: 2,
      inputSnapshotToken: 'course-2',
    })
  })

  it('preserves actionable stale acceptance errors for the planner workflow', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify({
      errors: [{ code: 'STALE_PLANNING_INPUT', message: 'Generate a new alternative.' }],
    }), { status: 409 }))

    await expect(acceptConflictAwareSchedules(decisionRequiredGenerationFixture)).rejects.toEqual([
      { code: 'STALE_PLANNING_INPUT', message: 'Generate a new alternative.' },
    ])
  })

  it('preserves paired holiday blocking context', async () => {
    const payload = {
      ...optimizationResultFixture,
      outcomes: [{
        ...optimizationResultFixture.outcomes[0],
        reasons: [{ code: 'INSTITUTION_HOLIDAY', message: 'Founders Day.', relatedCount: 1, holidayDate: '2026-09-07', holidayName: 'Founders Day' }],
      }],
    }
    vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(payload), { status: 200 }))

    const result = await generateConflictAwareSchedules(optimizationPreparationFixture)
    if (result.mode !== 'direct_saved') throw new Error('Expected direct save')
    expect(result.outcomes[0].reasons[0]).toMatchObject({ holidayDate: '2026-09-07', holidayName: 'Founders Day' })
  })

  it('parses validation and solver failures and normalizes network failure', async () => {
    vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ errors: [{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }] }), { status: 422 }))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'INVALID_OPTIMIZATION_SIZE', message: 'Bad selection.' }])
    vi.mocked(fetch).mockResolvedValueOnce(new Response(JSON.stringify({ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }), { status: 503 }))
    await expect(generateConflictAwareSchedules(optimizationPreparationFixture)).rejects.toEqual([{ code: 'OPTIMAL_RESULT_NOT_PROVEN', message: 'Timed out.', saved: false }])
    vi.mocked(fetch).mockRejectedValueOnce(new Error('offline'))
    await expect(prepareConflictAwareGeneration(1, 11, [1], [])).rejects.toEqual([{ code: 'NETWORK_ERROR', message: 'Could not reach the backend API.' }])
  })
})
