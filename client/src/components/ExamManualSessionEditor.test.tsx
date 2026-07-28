import { act } from 'react'; import { createRoot } from 'react-dom/client'; import { afterEach, expect, it, vi } from 'vitest'; import { ExamManualSessionEditor } from './ExamManualSessionEditor'; import type { ExamPlacementDraft } from './examPlacementModel'
let host:HTMLDivElement;afterEach(()=>host?.remove())
it('allows non-window manual times and keeps duration fixed',async()=>{host=document.createElement('div');document.body.append(host);const root=createRoot(host);await act(async()=>root.render(<ExamManualSessionEditor mode="create" configuration={{revision:1,durationMinutes:90} as never} snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>));expect(host.textContent).toContain('90 minutes');expect(host.querySelector('input[type=time]')).not.toBeNull();await act(async()=>root.unmount())})

it('uses the retained exam duration while correcting history',async()=>{host=document.createElement('div');document.body.append(host);const root=createRoot(host);await act(async()=>root.render(<ExamManualSessionEditor mode="edit" configuration={{revision:2,durationMinutes:120} as never} exam={{revision:1,durationMinutes:90,date:'2026-10-16',startTime:'09:00',lecturer:{id:1},room:{id:1},lifecycleStatus:'past'} as never} snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>));expect(host.textContent).toContain('90 minutes');expect(host.textContent).not.toContain('120 minutes');await act(async()=>root.unmount())})

it('reports controlled changes and dirty state while retaining the supplied draft', async () => {
  host=document.createElement('div');document.body.append(host);const root=createRoot(host)
  const baseline: ExamPlacementDraft={day:'2026-10-16',startTime:'09:00',lecturerId:1,roomId:1}
  const changed={...baseline,startTime:'10:00'}
  const onDraftChange=vi.fn();const onDirtyChange=vi.fn()
  await act(async()=>root.render(<ExamManualSessionEditor mode="edit" exam={{revision:1,durationMinutes:90,date:baseline.day,startTime:baseline.startTime,lecturer:{id:1},room:{id:1},lifecycleStatus:'planned'} as never} draft={changed} baseline={baseline} onDraftChange={onDraftChange} onDirtyChange={onDirtyChange} headingLevel="h2" snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>))
  expect(host.querySelector('h2')?.textContent).toContain('Correct planned exam')
  expect(host.querySelector<HTMLInputElement>('input[type=time]')?.value).toBe('10:00')
  expect(onDirtyChange).toHaveBeenLastCalledWith(true)
  const date=host.querySelector<HTMLInputElement>('input[type=date]')!
  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set?.call(date,'2026-10-17');date.dispatchEvent(new Event('input',{bubbles:true}));date.dispatchEvent(new Event('change',{bubbles:true}))})
  expect(onDraftChange).toHaveBeenCalledWith({...changed,day:'2026-10-17'})
  await act(async()=>root.unmount())
})
