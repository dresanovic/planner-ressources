import { act } from 'react'; import { createRoot } from 'react-dom/client'; import { afterEach, expect, it } from 'vitest'; import { ExamGenerationPanel } from './ExamGenerationPanel'
let host: HTMLDivElement; afterEach(()=>host?.remove())
it('groups eligible and unavailable courses using the authoritative eligibility boolean', async()=>{ host=document.createElement('div');document.body.append(host);const root=createRoot(host);await act(async()=>root.render(<ExamGenerationPanel semesterId={1} courses={[{courseId:1,courseName:'Ready',generationEligibility:{eligible:true,code:'ELIGIBLE',message:null}},{courseId:2,courseName:'Missing anchor',generationEligibility:{eligible:false,code:'FINAL_TEACHING_SESSION_MISSING',message:'Save teaching first.'}},{courseId:3,courseName:'Disabled',generationEligibility:{eligible:false,code:'DISABLED',message:null}},{courseId:4,courseName:'Already active',generationEligibility:{eligible:false,code:'ACTIVE_EXAM_EXISTS',message:'Active exam exists.'}}] as never} disabled={false} onChanged={()=>{}}/>));const boxes=[...host.querySelectorAll<HTMLInputElement>('input[type=checkbox]')];expect(host.textContent).toContain('Geeignete Lehrveranstaltungen');expect(host.textContent).toContain('Nicht verfügbare Lehrveranstaltungen');expect(host.textContent).toContain('Prüfungsanforderung');expect(boxes.map((item)=>item.disabled)).toEqual([false,true,true,true]);expect(host.textContent).toContain('Wählen Sie mindestens eine geeignete Lehrveranstaltung');expect(host.textContent).toContain('Prüfungen vorbereiten');await act(async()=>root.unmount())})

it('prunes a selected course when refreshed eligibility makes it unavailable', async () => {
  host = document.createElement('div')
  document.body.append(host)
  const root = createRoot(host)
  const eligible = [{
    courseId: 1,
    courseName: 'Ready',
    generationEligibility: { eligible: true, code: 'ELIGIBLE', message: null },
  }]
  await act(async () => root.render(
    <ExamGenerationPanel semesterId={1} courses={eligible as never} disabled={false} onChanged={() => {}} />,
  ))
  await act(async () => host.querySelector<HTMLInputElement>('input[type=checkbox]')?.click())
  expect(host.textContent).toContain('1 ausgewählt')

  await act(async () => {
    root.render(
      <ExamGenerationPanel
        semesterId={1}
        courses={[{
          ...eligible[0],
          generationEligibility: {
            eligible: false,
            code: 'ACTIVE_EXAM_EXISTS',
            message: 'An active exam already exists.',
          },
        }] as never}
        disabled={false}
        onChanged={() => {}}
      />,
    )
    await Promise.resolve()
  })

  expect(host.textContent).toContain('0 ausgewählt')
  expect(host.textContent).toContain('Die Auswahl wurde aktualisiert')
  expect(host.textContent).toContain('Prüfungsanforderung')
  await act(async () => root.unmount())
})
