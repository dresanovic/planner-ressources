import { act, useState } from 'react'; import { createRoot } from 'react-dom/client'; import { afterEach, expect, it, vi } from 'vitest'; import { ExamManualSessionEditor } from './ExamManualSessionEditor'; import type { ExamPlacementDraft } from './examPlacementModel'
let host:HTMLDivElement;afterEach(()=>host?.remove())
it('allows non-window manual times and keeps duration fixed',async()=>{host=document.createElement('div');document.body.append(host);const root=createRoot(host);await act(async()=>root.render(<ExamManualSessionEditor mode="create" configuration={{revision:1,durationMinutes:90} as never} snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>));expect(host.textContent).toContain('90 Minuten');expect(host.querySelector('input[type=time]')).not.toBeNull();await act(async()=>root.unmount())})

it('uses the retained exam duration while correcting history',async()=>{host=document.createElement('div');document.body.append(host);const root=createRoot(host);await act(async()=>root.render(<ExamManualSessionEditor mode="edit" configuration={{revision:2,durationMinutes:120} as never} exam={{revision:1,durationMinutes:90,date:'2026-10-16',startTime:'09:00',lecturer:{id:1},room:{id:1},lifecycleStatus:'past'} as never} snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>));expect(host.textContent).toContain('90 Minuten');expect(host.textContent).not.toContain('120 Minuten');await act(async()=>root.unmount())})

it('reports controlled changes and dirty state while retaining the supplied draft', async () => {
  host=document.createElement('div');document.body.append(host);const root=createRoot(host)
  const baseline: ExamPlacementDraft={day:'2026-10-16',startTime:'09:00',lecturerId:1,roomId:1}
  const changed={...baseline,startTime:'10:00'}
  const onDraftChange=vi.fn();const onDirtyChange=vi.fn()
  await act(async()=>root.render(<ExamManualSessionEditor mode="edit" exam={{revision:1,durationMinutes:90,date:baseline.day,startTime:baseline.startTime,lecturer:{id:1},room:{id:1},lifecycleStatus:'planned'} as never} draft={changed} baseline={baseline} onDraftChange={onDraftChange} onDirtyChange={onDirtyChange} headingLevel="h2" snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} onCancel={()=>{}} onSubmit={async()=>{}}/>))
  expect(host.querySelector('h2')?.textContent).toContain('Prüfungstermin korrigieren')
  expect(host.querySelector<HTMLInputElement>('input[type=time]')?.value).toBe('10:00')
  expect(onDirtyChange).toHaveBeenLastCalledWith(true)
  const date=host.querySelector<HTMLInputElement>('input[inputmode="numeric"]')!
  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set?.call(date,'17.10.2026');date.dispatchEvent(new Event('input',{bubbles:true}))})
  expect(onDraftChange).toHaveBeenCalledWith({...changed,day:'2026-10-17'})
  await act(async()=>root.unmount())
})

it('renders local validation and a save failure as separate actionable problems', async () => {
  host=document.createElement('div');document.body.append(host);const root=createRoot(host)
  await act(async()=>root.render(<ExamManualSessionEditor
    mode="create"
    configuration={{revision:1,durationMinutes:90} as never}
    snapshotToken="x"
    semesterId={1}
    lecturers={[]}
    rooms={[]}
    busy={false}
    draft={{day:'2026-10-16',startTime:'',lecturerId:0,roomId:0}}
    baseline={{day:'2026-10-16',startTime:'',lecturerId:0,roomId:0}}
    serverError="Der Dienst konnte den Prüfungstermin nicht speichern."
    onCancel={()=>{}}
    onSubmit={async()=>{}}
  />))

  await act(async()=>host.querySelector<HTMLButtonElement>('button:last-of-type')?.click())

  const problems=host.querySelectorAll('.actionable-problem')
  expect(problems).toHaveLength(2)
  expect(problems[0].textContent).toContain('Prüfungstermin vervollständigen')
  expect(problems[1].textContent).toContain('Prüfungstermin konnte nicht gespeichert werden')
  expect(problems[1].textContent).toContain('Der Dienst konnte den Prüfungstermin nicht speichern.')
})

it('blocks and focuses an incomplete date before saving an exam placement', async () => {
  host=document.createElement('div');document.body.append(host);const root=createRoot(host)
  const onSubmit=vi.fn().mockResolvedValue(undefined)
  function ControlledEditor() {
    const [draft,setDraft]=useState<ExamPlacementDraft>({day:'2026-10-16',startTime:'09:00',lecturerId:1,roomId:1})
    return <ExamManualSessionEditor mode="create" configuration={{revision:1,durationMinutes:90} as never} snapshotToken="x" semesterId={1} lecturers={[{id:1,name:'Ada'}]} rooms={[{id:1,name:'R',capacity:50}]} busy={false} draft={draft} baseline={draft} onDraftChange={setDraft} onCancel={()=>{}} onSubmit={onSubmit}/>
  }
  await act(async()=>root.render(<ControlledEditor/>))
  const date=host.querySelector<HTMLInputElement>('#exam-placement-date')!
  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set?.call(date,'16.10.20');date.dispatchEvent(new Event('input',{bubbles:true}))})
  await act(async()=>host.querySelector<HTMLButtonElement>('button[type="submit"]')?.click())
  expect(onSubmit).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(date)
  expect(date.getAttribute('aria-invalid')).toBe('true')
  expect(host.textContent).toContain('TT.MM.JJJJ')

  await act(async()=>{Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value')?.set?.call(date,'17.10.2026');date.dispatchEvent(new Event('input',{bubbles:true}))})
  await act(async()=>host.querySelector<HTMLButtonElement>('button[type="submit"]')?.click())
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({date:'2026-10-17'}))
})
