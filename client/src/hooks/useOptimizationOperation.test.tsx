import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, expect, it, vi } from 'vitest'
import { PLANNER_AUTH_INVALIDATED_EVENT } from '../api/plannerFetch'
import { useOptimizationOperation } from './useOptimizationOperation'
import * as api from '../api/conflictAwareGeneration'
import { deferredResponse, operationStatusFixture, optimizationPreparationFixture, decisionRequiredGenerationFixture, directSavedGenerationFixture } from '../test/optimizationFixtures'

vi.mock('../api/conflictAwareGeneration', async (original) => ({
  ...await original<typeof api>(), startOptimizationOperation: vi.fn(), getOptimizationOperation: vi.fn(),
  decideOptimizationOperation: vi.fn(), cancelOptimizationOperation: vi.fn(), continueOptimizationOperation: vi.fn(),
}))
let root: ReturnType<typeof createRoot> | undefined
afterEach(() => { act(() => root?.unmount()); vi.clearAllMocks(); vi.useRealTimers(); sessionStorage.clear(); document.body.innerHTML='' })

function mount() {
  let value!: ReturnType<typeof useOptimizationOperation>
  function Probe({active}: {active:boolean}) { value=useOptimizationOperation(); return <div hidden={!active}>{value.busy ? 'busy' : 'idle'}</div> }
  root=createRoot(document.body.appendChild(document.createElement('div')))
  act(()=>root!.render(<Probe active />))
  return { current:()=>value, hide:()=>act(()=>root!.render(<Probe active={false}/>)) }
}

it('continues the same reviewed operation without cancellation or new preparation', async()=>{
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_prep,ctx)=>({...operationStatusFixture,operationId:ctx.operationId,phase:'awaiting_decision',canAccept:true,review:decisionRequiredGenerationFixture}))
  vi.mocked(api.continueOptimizationOperation).mockImplementation(async(ctx)=>({...operationStatusFixture,operationId:ctx.operationId,phase:'optimizing'}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  const context=vi.mocked(api.startOptimizationOperation).mock.calls[0][1]
  await act(async()=>{await hook.current().continueOptimization()})
  expect(api.continueOptimizationOperation).toHaveBeenCalledWith(context,decisionRequiredGenerationFixture.candidateFingerprint,expect.any(String),expect.anything())
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
  expect(api.startOptimizationOperation).toHaveBeenCalledTimes(1)
  expect(hook.current().status?.phase).toBe('optimizing')
})

it.each(['cohort','lecturer','standard_optimized'] as const)('keeps %s identity and waits for explicit acceptance', async algorithm=>{
  const identity={algorithm,strategyProfile:algorithm === 'standard_optimized' ? 'standard-optimized-v1' as const : 'heuristic-v1' as const,strategySettings:{version:'teaching-v1'}}
  const review={...decisionRequiredGenerationFixture,...identity,proof:null}
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_prep,ctx)=>({...operationStatusFixture,...identity,operationId:ctx.operationId,phase:'awaiting_decision',canAccept:true,review}))
  vi.mocked(api.decideOptimizationOperation).mockImplementation(async(ctx)=>({...operationStatusFixture,...identity,operationId:ctx.operationId,phase:'saved',saved:true,result:{...directSavedGenerationFixture,...identity}}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  expect(hook.current().status?.algorithm).toBe(algorithm)
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
  await act(async()=>{await hook.current().accept()})
  expect(vi.mocked(api.decideOptimizationOperation).mock.calls[0][2]).toBe(false)
  expect(hook.current().status?.result?.algorithm).toBe(algorithm)
})

it('acknowledges start immediately and retains a late review result after navigation', async()=>{
  const response=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockReturnValue(response.promise)
  vi.mocked(api.cancelOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'cancelled'})
  const hook=mount()
  let started!: Promise<void>
  act(()=>{ started=hook.current().start(optimizationPreparationFixture) })
  expect(hook.current().busy).toBe(true)
  const context=vi.mocked(api.startOptimizationOperation).mock.calls[0][1]
  expect(context.contextSecret).toMatch(/^[0-9a-f]{64}$/)
  expect(JSON.stringify(sessionStorage)).not.toContain(context.contextSecret)
  hook.hide()
  await act(async()=>{response.resolve({...operationStatusFixture,operationId:context.operationId,phase:'awaiting_decision',review:decisionRequiredGenerationFixture,canAccept:true});await started})
  expect(hook.current().status?.review).toEqual(decisionRequiredGenerationFixture)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
})

it('automatically finalizes a fully proven new selection without another click', async()=>{
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_prep,ctx)=>({...operationStatusFixture,operationId:ctx.operationId,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture}))
  vi.mocked(api.decideOptimizationOperation).mockImplementation(async(ctx)=>({...operationStatusFixture,operationId:ctx.operationId,phase:'saved',saved:true,result:directSavedGenerationFixture}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  expect(vi.mocked(api.decideOptimizationOperation).mock.calls[0].slice(1,3)).toEqual(['a'.repeat(64),true])
  expect(hook.current().status?.saved).toBe(true)
})

it('recovers a lost start response using the same live context and can finish saving', async()=>{
  vi.mocked(api.startOptimizationOperation).mockRejectedValue(new Error('lost response'))
  vi.mocked(api.getOptimizationOperation).mockImplementation(async(id)=>({...operationStatusFixture,operationId:id,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture}))
  vi.mocked(api.decideOptimizationOperation).mockImplementation(async(c)=>({...operationStatusFixture,operationId:c.operationId,phase:'saved',saved:true,result:directSavedGenerationFixture}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  const context=vi.mocked(api.startOptimizationOperation).mock.calls[0][1]
  expect(api.getOptimizationOperation).toHaveBeenCalledWith(context.operationId,context.contextSecret,expect.anything())
  expect(hook.current().status?.saved).toBe(true)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
})

it('blocks a new start while the previous receipt remains unknown',async()=>{
  const receipt=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockRejectedValue(new Error('response lost'))
  vi.mocked(api.getOptimizationOperation).mockReturnValue(receipt.promise)
  vi.mocked(api.cancelOptimizationOperation).mockReturnValue(receipt.promise)
  const hook=mount()
  await act(async()=>{void hook.current().start(optimizationPreparationFixture);await Promise.resolve()})
  expect(hook.current().unknown).toBe(true)
  expect(hook.current().busy).toBe(true)
  await act(async()=>{void hook.current().start(optimizationPreparationFixture);await Promise.resolve()})
  expect(api.startOptimizationOperation).toHaveBeenCalledTimes(1)
  await act(async()=>receipt.resolve({...operationStatusFixture,phase:'cancelled'}))
})

it.each(['BUDGET_POLICY_CHANGED','revision_not_editable','working_revision_required','stale_lifecycle_state','semester_not_found'])('treats definitive rejected start %s as re-preparation, without polling a missing receipt',async(code)=>{
  vi.mocked(api.startOptimizationOperation).mockRejectedValue([{code,message:'Bitte neu vorbereiten.'}])
  vi.mocked(api.cancelOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'cancelled'})
  vi.mocked(api.getOptimizationOperation).mockRejectedValue([{code:'OPERATION_NOT_FOUND',message:'Lauf nicht gefunden.'}])
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  expect(hook.current().unknown).toBe(false)
  expect(hook.current().busy).toBe(false)
  expect(api.getOptimizationOperation).not.toHaveBeenCalled()
  expect(sessionStorage.length).toBe(0)
})

it('marks a stalled decision unknown within five seconds of the last confirmed status',async()=>{
  vi.useFakeTimers()
  const decision=deferredResponse<api.OptimizationOperationStatus>()
  const receipt=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_prep,ctx)=>({...operationStatusFixture,operationId:ctx.operationId,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture}))
  vi.mocked(api.decideOptimizationOperation).mockReturnValue(decision.promise)
  vi.mocked(api.getOptimizationOperation).mockReturnValue(receipt.promise)
  vi.mocked(api.cancelOptimizationOperation).mockReturnValue(receipt.promise)
  const hook=mount()
  await act(async()=>{void hook.current().start(optimizationPreparationFixture);await Promise.resolve()})
  expect(hook.current().action).toBe('saving')
  await act(async()=>{vi.advanceTimersByTime(5001);await Promise.resolve()})
  expect(hook.current().unknown).toBe(true)
  await act(async()=>{receipt.resolve({...operationStatusFixture,phase:'cancelled'});decision.resolve({...operationStatusFixture,phase:'cancelled'})})
})

it.each(['pagehide','auth'])('invalidates review authority on %s and ignores late decision availability',async(boundary)=>{
  const response=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockReturnValue(response.promise)
  vi.mocked(api.cancelOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'cancelled'})
  const hook=mount()
  let pending!:Promise<void>
  act(()=>{pending=hook.current().start(optimizationPreparationFixture)})
  const context=vi.mocked(api.startOptimizationOperation).mock.calls[0][1]
  act(()=>{
    window.dispatchEvent(new Event(boundary==='auth'?PLANNER_AUTH_INVALIDATED_EVENT:'pagehide'))
  })
  await act(async()=>{response.resolve({...operationStatusFixture,operationId:context.operationId,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture});await pending})
  expect(api.cancelOptimizationOperation).toHaveBeenCalledWith(context.operationId,'context_lost',true)
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
  expect(hook.current().status?.review).toBeFalsy()
  vi.restoreAllMocks()
})

it('keeps optimization alive across background timer throttling and resumes status checks on return',async()=>{
  vi.useFakeTimers()
  const hidden=vi.spyOn(document,'hidden','get').mockReturnValue(false)
  const poll=deferredResponse<api.OptimizationOperationStatus>()
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockReturnValue(poll.promise)
  const hook=mount()
  try {
    await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
    act(()=>{hidden.mockReturnValue(true);document.dispatchEvent(new Event('visibilitychange'))})
    await act(async()=>{await vi.advanceTimersByTimeAsync(60000)})
    expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
    expect(hook.current().unknown).toBe(false)
    expect(hook.current().busy).toBe(true)
    expect(api.getOptimizationOperation).toHaveBeenCalledTimes(1)
    act(()=>{hidden.mockReturnValue(false);document.dispatchEvent(new Event('visibilitychange'))})
    await act(async()=>{await vi.advanceTimersByTimeAsync(1000)})
    expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
    await act(async()=>poll.resolve({...operationStatusFixture,operationId:id,phase:'awaiting_decision',canAccept:true,review:decisionRequiredGenerationFixture}))
    expect(hook.current().status?.canAccept).toBe(true)
    expect(hook.current().unknown).toBe(false)
  } finally { hidden.mockRestore() }
})

it('checks status immediately on return without waiting for the background polling timer',async()=>{
  vi.useFakeTimers()
  const hidden=vi.spyOn(document,'hidden','get').mockReturnValue(false)
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'optimizing'}))
  const hook=mount()
  try {
    await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
    act(()=>{hidden.mockReturnValue(true);document.dispatchEvent(new Event('visibilitychange'))})
    await act(async()=>{await vi.advanceTimersByTimeAsync(1000)})
    await act(async()=>{hidden.mockReturnValue(false);document.dispatchEvent(new Event('visibilitychange'))})
    expect(api.getOptimizationOperation).toHaveBeenCalledTimes(1)
    await act(async()=>{await vi.advanceTimersByTimeAsync(1000)})
    expect(api.getOptimizationOperation).toHaveBeenCalledTimes(1)
    expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
  } finally { hidden.mockRestore() }
})

it('marks a stalled connection unknown after returning and recovers without cancelling the run',async()=>{
  vi.useFakeTimers()
  const hidden=vi.spyOn(document,'hidden','get').mockReturnValue(false)
  const pending=deferredResponse<api.OptimizationOperationStatus>()
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockReturnValue(pending.promise)
  vi.mocked(api.cancelOptimizationOperation).mockReturnValue(pending.promise)
  const hook=mount()
  try {
    await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
    act(()=>{hidden.mockReturnValue(true);document.dispatchEvent(new Event('visibilitychange'))})
    await act(async()=>{await vi.advanceTimersByTimeAsync(60000)})
    act(()=>{hidden.mockReturnValue(false);document.dispatchEvent(new Event('visibilitychange'))})
    await act(async()=>{await vi.advanceTimersByTimeAsync(4999)})
    expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
    await act(async()=>{await vi.advanceTimersByTimeAsync(2)})
    expect(hook.current().unknown).toBe(true)
    expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
    await act(async()=>pending.resolve({...operationStatusFixture,operationId:id,phase:'optimizing'}))
    expect(hook.current().unknown).toBe(false)
    expect(hook.current().status?.phase).toBe('optimizing')
  } finally { hidden.mockRestore() }
})

it('reconciles refresh by identifier without recovering a secret or acceptance authority',async()=>{
  sessionStorage.setItem('teaching-optimization-operation-id',operationStatusFixture.operationId)
  vi.mocked(api.cancelOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'cancelled'})
  vi.mocked(api.getOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'saved',saved:true,result:directSavedGenerationFixture})
  const hook=mount()
  await act(async()=>{await Promise.resolve()})
  expect(api.getOptimizationOperation).toHaveBeenCalledWith(operationStatusFixture.operationId,undefined,expect.anything())
  expect(hook.current().status?.saved).toBe(true)
  expect(hook.current().status?.review).toBeNull()
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
})

it('does not add the polling delay to the five-second unconfirmed limit',async()=>{
  vi.useFakeTimers()
  const pending=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>({...operationStatusFixture,operationId:c.operationId,phase:'optimizing'}))
  vi.mocked(api.getOptimizationOperation).mockReturnValue(pending.promise)
  vi.mocked(api.cancelOptimizationOperation).mockReturnValue(pending.promise)
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  await act(async()=>{vi.advanceTimersByTime(4999);await Promise.resolve()})
  expect(hook.current().unknown).toBe(false)
  await act(async()=>{vi.advanceTimersByTime(2);await Promise.resolve()})
  expect(hook.current().unknown).toBe(true)
  await act(async()=>pending.resolve({...operationStatusFixture,phase:'cancelled'}))
})

it('guards duplicate acceptance and reconciles a lost decision response to the saved receipt',async()=>{
  const decision=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>({...operationStatusFixture,operationId:c.operationId,phase:'awaiting_decision',canAccept:true,review:decisionRequiredGenerationFixture}))
  vi.mocked(api.decideOptimizationOperation).mockReturnValue(decision.promise)
  vi.mocked(api.cancelOptimizationOperation).mockResolvedValue({...operationStatusFixture,phase:'saved',saved:true,result:directSavedGenerationFixture})
  let id=''
  vi.mocked(api.getOptimizationOperation).mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'saved',saved:true,result:directSavedGenerationFixture}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  id=vi.mocked(api.startOptimizationOperation).mock.calls[0][1].operationId
  let saving!:Promise<api.OptimizationError[]|undefined|void>
  act(()=>{saving=hook.current().accept();void hook.current().accept()})
  expect(api.decideOptimizationOperation).toHaveBeenCalledTimes(1)
  expect(hook.current().action).toBe('saving')
  await act(async()=>{decision.reject(new Error('response lost'));await saving})
  expect(hook.current().status?.saved).toBe(true)
  expect(hook.current().unknown).toBe(false)
  expect(hook.current().status?.review).toBeNull()
})

it.each(['failed','stalled'])('survives a %s status request after 100 seconds and saves the same operation',async(failure)=>{
  vi.useFakeTimers()
  let id=''
  const delayed=deferredResponse<api.OptimizationOperationStatus>()
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'optimizing'}))
  vi.mocked(api.decideOptimizationOperation).mockImplementation(async(c)=>({...operationStatusFixture,operationId:c.operationId,phase:'saved',saved:true,result:directSavedGenerationFixture}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  await act(async()=>{await vi.advanceTimersByTimeAsync(98000)})
  vi.mocked(api.getOptimizationOperation).mockReturnValueOnce(delayed.promise)
  await act(async()=>{await vi.advanceTimersByTimeAsync(2000)})
  const stalledSignal=vi.mocked(api.getOptimizationOperation).mock.calls.at(-1)![2]!
  if(failure==='failed') await act(async()=>delayed.reject(new Error('temporary network failure')))
  else {
    vi.mocked(api.getOptimizationOperation).mockReturnValueOnce(deferredResponse<api.OptimizationOperationStatus>().promise)
    await act(async()=>{await vi.advanceTimersByTimeAsync(3001)})
    expect(stalledSignal.aborted).toBe(false)
    await act(async()=>{await vi.advanceTimersByTimeAsync(25000)})
    expect(stalledSignal.aborted).toBe(true)
  }
  expect(hook.current().unknown).toBe(true)
  expect(hook.current().busy).toBe(true)
  expect(hook.current().status?.canAccept).toBeFalsy()
  await act(async()=>{await hook.current().accept();await hook.current().start(optimizationPreparationFixture)})
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
  expect(api.startOptimizationOperation).toHaveBeenCalledTimes(1)
  vi.mocked(api.getOptimizationOperation).mockResolvedValue({...operationStatusFixture,operationId:id,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture})
  await act(async()=>{await vi.advanceTimersByTimeAsync(failure==='stalled'?30001:5001)})
  expect(hook.current().status?.saved).toBe(true)
  expect(hook.current().unknown).toBe(false)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
  expect(vi.mocked(api.decideOptimizationOperation).mock.calls[0][0].operationId).toBe(id)
  if(failure==='stalled') {
    await act(async()=>delayed.resolve({...operationStatusFixture,operationId:id,phase:'awaiting_decision',canAccept:true,review:decisionRequiredGenerationFixture}))
    expect(hook.current().status?.saved).toBe(true)
  }
})

it('accepts a slow status response after five seconds without repeatedly aborting it',async()=>{
  vi.useFakeTimers()
  const delayed=deferredResponse<api.OptimizationOperationStatus>()
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockReturnValue(delayed.promise)
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  await act(async()=>{await vi.advanceTimersByTimeAsync(12000)})
  expect(hook.current().unknown).toBe(true)
  expect(api.getOptimizationOperation).toHaveBeenCalledTimes(1)
  expect(vi.mocked(api.getOptimizationOperation).mock.calls[0][2]?.aborted).toBe(false)
  await act(async()=>delayed.resolve({...operationStatusFixture,operationId:id,phase:'awaiting_decision',canAccept:true,review:decisionRequiredGenerationFixture}))
  expect(hook.current().unknown).toBe(false)
  expect(hook.current().status?.canAccept).toBe(true)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
})

it('reissues an unregistered start with its original ID and preparation instead of creating another run',async()=>{
  vi.mocked(api.startOptimizationOperation)
    .mockRejectedValueOnce(new Error('request did not arrive'))
    .mockImplementation(async(_p,c)=>({...operationStatusFixture,operationId:c.operationId,phase:'optimizing'}))
  vi.mocked(api.getOptimizationOperation).mockRejectedValue([{code:'OPERATION_NOT_FOUND'}])
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  expect(api.startOptimizationOperation).toHaveBeenCalledTimes(2)
  const [first,repeated]=vi.mocked(api.startOptimizationOperation).mock.calls
  expect(repeated.slice(0,2)).toEqual(first.slice(0,2))
  expect(hook.current().status?.phase).toBe('optimizing')
  expect(hook.current().unknown).toBe(false)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
})

it('ends recovery cleanly when an unregistered start is definitively rejected',async()=>{
  vi.mocked(api.startOptimizationOperation)
    .mockRejectedValueOnce(new Error('request did not arrive'))
    .mockRejectedValueOnce([{code:'BUDGET_POLICY_CHANGED',message:'Bitte neu vorbereiten.'}])
  vi.mocked(api.getOptimizationOperation).mockRejectedValue([{code:'OPERATION_NOT_FOUND'}])
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  expect(hook.current().unknown).toBe(false)
  expect(hook.current().busy).toBe(false)
  expect(hook.current().errors[0].code).toBe('BUDGET_POLICY_CHANGED')
  expect(sessionStorage.length).toBe(0)
  expect(api.cancelOptimizationOperation).not.toHaveBeenCalled()
})

it.each(['pagehide','auth'])('still invalidates a reconnecting run on %s and ignores late status',async(boundary)=>{
  vi.useFakeTimers()
  const delayed=deferredResponse<api.OptimizationOperationStatus>()
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.getOptimizationOperation).mockReturnValue(delayed.promise)
  vi.mocked(api.cancelOptimizationOperation).mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'cancelled'}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  await act(async()=>{await vi.advanceTimersByTimeAsync(5001)})
  expect(hook.current().unknown).toBe(true)
  act(()=>window.dispatchEvent(new Event(boundary==='auth'?PLANNER_AUTH_INVALIDATED_EVENT:'pagehide')))
  await act(async()=>delayed.resolve({...operationStatusFixture,operationId:id,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture}))
  expect(api.cancelOptimizationOperation).toHaveBeenCalled()
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
  expect(hook.current().status?.phase).toBe('cancelled')
})

it('retries explicit cancellation after a lost cancel request and never restores acceptance',async()=>{
  vi.useFakeTimers()
  let id=''
  vi.mocked(api.startOptimizationOperation).mockImplementation(async(_p,c)=>{
    id=c.operationId
    return {...operationStatusFixture,operationId:id,phase:'optimizing'}
  })
  vi.mocked(api.cancelOptimizationOperation)
    .mockRejectedValueOnce(new Error('cancel request lost'))
    .mockRejectedValueOnce(new Error('connection still unavailable'))
    .mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'cancelled'}))
  vi.mocked(api.getOptimizationOperation)
    .mockImplementationOnce(async()=>({...operationStatusFixture,operationId:id,phase:'ready_to_save',canFinalize:true,review:decisionRequiredGenerationFixture}))
    .mockImplementation(async()=>({...operationStatusFixture,operationId:id,phase:'cancelled'}))
  const hook=mount()
  await act(async()=>{await hook.current().start(optimizationPreparationFixture)})
  await act(async()=>{await hook.current().cancel()})
  expect(hook.current().status?.review).toBeNull()
  expect(api.decideOptimizationOperation).not.toHaveBeenCalled()
  expect(vi.mocked(api.cancelOptimizationOperation).mock.calls.every(call=>call[1]==='cancel')).toBe(true)
  expect(api.cancelOptimizationOperation).toHaveBeenCalledTimes(3)
  await act(async()=>{await vi.advanceTimersByTimeAsync(2000)})
  expect(hook.current().status?.phase).toBe('cancelled')
  expect(hook.current().busy).toBe(false)
})
