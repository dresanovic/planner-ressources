import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import { PLANNER_AUTH_INVALIDATED_EVENT } from '../api/plannerFetch'
import { startOptimizationOperation, getOptimizationOperation, decideOptimizationOperation, cancelOptimizationOperation,
  type OptimizationOperationContext, type OptimizationOperationStatus, type OptimizationPreparation, type OptimizationError } from '../api/conflictAwareGeneration'

const STORAGE_KEY='teaching-optimization-operation-id'
const terminal=new Set(['saved','cancelled','failed','stale','interrupted','timeout_no_candidate'])
const rejectedStart=new Set(['BUDGET_POLICY_CHANGED','OPTIMIZATION_CONFIGURATION_INVALID','INVALID_REQUEST','INVALID_OPTIMIZATION_SIZE','DUPLICATE_COURSE_SELECTION','OPERATION_ID_CONFLICT','csrf_protection_required','json_required',
  'revision_not_editable','working_revision_required','stale_lifecycle_state','semester_not_found'])
type Action = 'starting' | 'saving' | 'cancelling' | null

export function useOptimizationOperation(active: boolean, contextKey: string) {
  const [status,setStatus]=useState<OptimizationOperationStatus|null>(null)
  const [action,setAction]=useState<Action>(null)
  const [unknown,setUnknown]=useState(false)
  const [errors,setErrors]=useState<OptimizationError[]>([])
  const live=useRef<OptimizationOperationContext|null>(null)
  const startPreparation=useRef<OptimizationPreparation|null>(null)
  const cancellationReason=useRef('context_lost')
  const unresolved=useRef<string|null>(null)
  const epoch=useRef(0)
  const timer=useRef<ReturnType<typeof setTimeout>|undefined>(undefined)
  const watchdog=useRef<ReturnType<typeof setTimeout>|undefined>(undefined)
  const request=useRef<AbortController|null>(null)
  const currentStatus=useRef<OptimizationOperationStatus|null>(null)
  const decisionPending=useRef(false)
  const lastConfirmed=useRef(0)
  const mounted=useRef(true)
  const enabled=useRef(active)
  const observe=useRef<(id:string,generation:number)=>Promise<void>>(async()=>{})
  const consume=useRef<(value:OptimizationOperationStatus,generation:number)=>Promise<void>>(async()=>{})
  const expire=useRef<(id:string,generation:number)=>void>(()=>{})

  const clearObservation=useCallback(()=>{
    clearTimeout(timer.current);clearTimeout(watchdog.current)
    request.current?.abort();request.current=null
  },[])

  const arm=useCallback((id:string,generation:number)=>{
    clearTimeout(watchdog.current)
    // Browsers throttle background timers. Visibility alone does not lose the
    // planning context; enforce connected freshness when the page is visible.
    if(document.hidden) return
    watchdog.current=setTimeout(()=>expire.current(id,generation),Math.max(0,lastConfirmed.current+5000-Date.now()))
  },[])

  const publish=useCallback((value:OptimizationOperationStatus)=>{
    currentStatus.current=value
    if(mounted.current) {setStatus(value);setAction(null)}
    if(terminal.has(value.phase)) {
      clearTimeout(timer.current);clearTimeout(watchdog.current)
      unresolved.current=null;live.current=null;startPreparation.current=null;decisionPending.current=false
      sessionStorage.removeItem(STORAGE_KEY)
      if(mounted.current) setUnknown(false)
    }
  },[])

  const reconcile=useCallback(async(id:string,generation:number)=>{
    if(epoch.current!==generation || !mounted.current || unresolved.current!==id) return
    clearObservation();live.current=null;startPreparation.current=null
    setUnknown(true);setAction(null);setStatus(null);currentStatus.current=null
    // Discarded context cannot regain authority. Cancellation may lose to a save.
    void cancelOptimizationOperation(id,cancellationReason.current).catch(()=>{})
    await observe.current(id,generation)
  },[clearObservation])

  const reconnect=useCallback(async(id:string,generation:number,delay=false)=>{
    if(epoch.current!==generation || !mounted.current || unresolved.current!==id) return
    // A failed/slow status request does not change the user's planning context.
    // Keep its memory-only authority, hide decisions, and confirm the same run.
    // Bump the epoch so an aborted request cannot publish a late response.
    clearObservation()
    const next=++epoch.current
    decisionPending.current=false
    setUnknown(true);setAction(null);setStatus(null);currentStatus.current=null
    lastConfirmed.current=Date.now();arm(id,next)
    if(delay) timer.current=setTimeout(()=>void observe.current(id,next),2000)
    else await observe.current(id,next)
  },[arm,clearObservation])

  const rejectStart=useCallback((failures:OptimizationError[])=>{
    clearObservation();++epoch.current
    unresolved.current=null;live.current=null;startPreparation.current=null;decisionPending.current=false
    sessionStorage.removeItem(STORAGE_KEY)
    currentStatus.current=null
    setErrors(failures);setStatus(null);setAction(null);setUnknown(false)
  },[clearObservation])

  const consumeStatus=useCallback(async(value:OptimizationOperationStatus,generation:number)=>{
    if(epoch.current!==generation || !mounted.current || unresolved.current!==value.operationId) return
    lastConfirmed.current=Date.now()
    const context=live.current
    const safe=context ? value : {...value,review:null,canAccept:false,canFinalize:false}
    if(context) setUnknown(false)
    publish(safe)
    if(terminal.has(value.phase)) return
    // If an explicit cancellation/departure request was lost, retry that intent.
    // Only unchanged live contexts may recover from transport interruptions.
    if(!context) void cancelOptimizationOperation(value.operationId,cancellationReason.current).catch(()=>{})
    arm(value.operationId,generation)
    if(value.canFinalize && context && !decisionPending.current) {
      decisionPending.current=true;setAction('saving')
      const controller=new AbortController();request.current=controller
      try { await consume.current(await decideOptimizationOperation(context,value.review!.candidateFingerprint,true,controller.signal),generation) }
      catch { if(epoch.current===generation && live.current) await reconnect(context.operationId,generation,true) }
      finally { if(epoch.current===generation) decisionPending.current=false; if(request.current===controller) request.current=null }
      return
    }
    timer.current=setTimeout(()=>void observe.current(value.operationId,generation),2000)
  },[arm,publish,reconnect])

  const observeStatus=useCallback(async(id:string,generation:number)=>{
    if(epoch.current!==generation || !mounted.current || unresolved.current!==id) return
    const controller=new AbortController();request.current=controller
    if(!live.current) lastConfirmed.current=Date.now() // Already unknown: bound this outcome-only request.
    arm(id,generation)
    try {
      let value:OptimizationOperationStatus
      try { value=await getOptimizationOperation(id,live.current?.contextSecret,controller.signal) }
      catch(error) {
        // The start request may not have arrived before its response was lost.
        // Reuse its original ID and payload; the server deduplicates dispatch.
        const context=live.current,prepared=startPreparation.current
        if(epoch.current!==generation || !context || !prepared || !Array.isArray(error)
          || !error.some(item=>item.code==='OPERATION_NOT_FOUND')) throw error
        try { value=await startOptimizationOperation(prepared,context,controller.signal) }
        catch(error) {
          if(epoch.current===generation && Array.isArray(error) && error.some(item=>rejectedStart.has(item.code))) {
            rejectStart(error)
          }
          throw error
        }
      }
      await consume.current(value,generation)
    } catch {
      if(epoch.current!==generation || !mounted.current || unresolved.current!==id) return
      await reconnect(id,generation,true)
    } finally { if(request.current===controller) request.current=null }
  },[arm,reconnect,rejectStart])

  useLayoutEffect(()=>{
    enabled.current=active;consume.current=consumeStatus;observe.current=observeStatus
    expire.current=(id,generation)=>{
      if(epoch.current!==generation || unresolved.current!==id || !mounted.current) return
      setUnknown(true);setAction(null);setStatus(null);currentStatus.current=null
      // Five seconds means unconfirmed status, not a failed request. Give a
      // slow response time to finish before replacing a genuinely stuck one.
      if(request.current) watchdog.current=setTimeout(()=>void reconnect(id,generation),25000)
      else void reconnect(id,generation)
    }
  },[active,consumeStatus,observeStatus,reconnect])

  const cancel=useCallback(async(reason='cancel',keepalive=false)=>{
    const id=unresolved.current
    if(!id) return
    const generation=++epoch.current
    cancellationReason.current=reason
    live.current=null;startPreparation.current=null;decisionPending.current=false;clearObservation()
    if(mounted.current) {setStatus(null);setAction('cancelling');setErrors([])}
    currentStatus.current=null;lastConfirmed.current=Date.now();arm(id,generation)
    try {
      const outcome=await cancelOptimizationOperation(id,reason,keepalive)
      if(mounted.current && generation===epoch.current) {publish(outcome);return outcome}
    } catch {
      if(mounted.current && generation===epoch.current) await reconcile(id,generation)
    }
  },[arm,clearObservation,publish,reconcile])

  const start=useCallback(async(preparation:OptimizationPreparation)=>{
    if(!enabled.current || unresolved.current || decisionPending.current) return
    clearObservation()
    const generation=++epoch.current
    const bytes=crypto.getRandomValues(new Uint8Array(32))
    const context={operationId:crypto.randomUUID(),contextSecret:[...bytes].map(b=>b.toString(16).padStart(2,'0')).join('')}
    cancellationReason.current='context_lost'
    live.current=context;startPreparation.current=preparation;unresolved.current=context.operationId;sessionStorage.setItem(STORAGE_KEY,context.operationId)
    setAction('starting');setUnknown(false);setErrors([]);setStatus(null);currentStatus.current=null
    lastConfirmed.current=Date.now();arm(context.operationId,generation)
    const controller=new AbortController();request.current=controller
    try { await consume.current(await startOptimizationOperation(preparation,context,controller.signal),generation) }
    catch(error) {
      if(generation!==epoch.current || !live.current) return
      if(Array.isArray(error)) setErrors(error)
      if(Array.isArray(error) && error.some(item=>rejectedStart.has(item.code))) {
        rejectStart(error)
      } else await reconnect(context.operationId,generation)
    } finally { if(request.current===controller) request.current=null }
  },[arm,clearObservation,reconnect,rejectStart])

  const accept=useCallback(async()=>{
    const context=live.current,preview=currentStatus.current?.review
    if(!context || !preview || !currentStatus.current?.canAccept || decisionPending.current) return
    decisionPending.current=true;setAction('saving');clearObservation()
    const generation=epoch.current
    const controller=new AbortController();request.current=controller;arm(context.operationId,generation)
    try { await consume.current(await decideOptimizationOperation(context,preview.candidateFingerprint,false,controller.signal),generation) }
    catch(error) {
      if(epoch.current!==generation) return
      if(Array.isArray(error)) setErrors(error)
      if(live.current) await reconnect(context.operationId,generation)
      return Array.isArray(error) ? error as OptimizationError[] : undefined
    } finally {if(epoch.current===generation) decisionPending.current=false; if(request.current===controller) request.current=null}
  },[arm,clearObservation,reconnect])

  useEffect(()=>{
    mounted.current=true
    const stored=sessionStorage.getItem(STORAGE_KEY)
    if(stored && !unresolved.current) {unresolved.current=stored;void reconcile(stored,epoch.current)}
    const invalidate=()=>{void cancel('context_lost',true)}
    const visibilityChanged=()=>{
      clearTimeout(watchdog.current)
      const id=unresolved.current
      if(document.hidden || !id) return
      lastConfirmed.current=Date.now()
      arm(id,epoch.current)
      if(!request.current && !decisionPending.current) {
        clearTimeout(timer.current)
        void observe.current(id,epoch.current)
      }
    }
    window.addEventListener('pagehide',invalidate)
    window.addEventListener(PLANNER_AUTH_INVALIDATED_EVENT,invalidate)
    document.addEventListener('visibilitychange',visibilityChanged)
    return ()=>{
      mounted.current=false;void cancel('navigation',true);clearObservation()
      window.removeEventListener('pagehide',invalidate)
      window.removeEventListener(PLANNER_AUTH_INVALIDATED_EVENT,invalidate)
      document.removeEventListener('visibilitychange',visibilityChanged)
    }
  },[arm,cancel,clearObservation,reconcile])

  useEffect(()=>{
    if(!active) void cancel('navigation')
    return ()=>{void cancel('navigation',true)}
  },[active,contextKey,cancel])

  const busy=Boolean(action) || unknown || Boolean(status && ['preparing','optimizing','checking','saving'].includes(status.phase))
  return {status,busy,unknown,errors,action,start,accept,cancel}
}
