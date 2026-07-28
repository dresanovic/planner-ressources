import { act } from 'react'; import { createRoot } from 'react-dom/client'; import { afterEach, expect, it, vi } from 'vitest'; import { ExamRequirementEditor } from './ExamRequirementEditor'
let host: HTMLDivElement; afterEach(() => host?.remove())
it('enables and saves a complete configuration with anchor guidance', async () => { host=document.createElement('div'); document.body.append(host); const root=createRoot(host); const onSave=vi.fn(); await act(async()=>root.render(<ExamRequirementEditor state={{ courseId:1, courseName:'A', semesterId:1, cohortId:1, cohortName:'C', enabled:false, configuration:null, finalTeachingAnchor:null, activeExam:null, pastExams:[], generationEligibility:{eligible:false,code:'DISABLED',message:null}, inputSnapshotToken:'x' }} lecturers={[{id:1,name:'Ada'}]} busy={false} onSave={onSave}/>)); expect(host.textContent).not.toContain('No final teaching session'); const enable=host.querySelector('input[type=checkbox]') as HTMLInputElement; await act(async()=>enable.click()); expect(host.textContent).toContain('No final teaching session'); expect(host.querySelector('input[name=exam-identifier]')).not.toBeNull(); await act(async()=>root.unmount()) })

it('keeps an active exam requirement read-only', async () => {
  host = document.createElement('div')
  document.body.append(host)
  const root = createRoot(host)
  await act(async () => root.render(
    <ExamRequirementEditor
      state={{
        courseId: 1,
        courseName: 'A',
        semesterId: 1,
        cohortId: 1,
        cohortName: 'C',
        enabled: true,
        configuration: {
          id: 7,
          revision: 3,
          identifier: 'Final',
          durationMinutes: 90,
          recommendedStartOverride: null,
          recommendedEndOverride: null,
          recommendedStartDate: '2026-10-01',
          recommendedEndDate: '2026-10-08',
          requiredCapacity: 20,
          examType: 'Written',
          responsibleLecturerId: 1,
        },
        finalTeachingAnchor: null,
        activeExam: { id: 8 },
        pastExams: [],
        generationEligibility: { eligible: false, code: 'ACTIVE_EXAM_EXISTS', message: 'Active exam exists.' },
        inputSnapshotToken: 'x',
      } as never}
      lecturers={[{ id: 1, name: 'Ada' }]}
      busy={false}
      onSave={vi.fn()}
    />,
  ))

  expect(host.textContent).toContain('consumed configuration is read-only')
  expect([...host.querySelectorAll<HTMLInputElement | HTMLSelectElement | HTMLButtonElement>('input, select, button')]
    .every((control) => control.disabled)).toBe(true)
  await act(async () => root.unmount())
})

it('saves the established payload and Cancel restores the saved values', async () => {
  host = document.createElement('div')
  document.body.append(host)
  const root = createRoot(host)
  const onSave = vi.fn()
  await act(async () => root.render(
    <ExamRequirementEditor
      state={{
        courseId: 1,
        courseName: 'A',
        semesterId: 4,
        cohortId: 1,
        cohortName: 'C',
        enabled: true,
        configuration: {
          id: 7,
          revision: 3,
          identifier: 'Final',
          durationMinutes: 90,
          recommendedStartOverride: null,
          recommendedEndOverride: null,
          recommendedStartDate: '2026-10-01',
          recommendedEndDate: '2026-10-08',
          requiredCapacity: 20,
          examType: 'Written',
          responsibleLecturerId: 1,
        },
        finalTeachingAnchor: { date: '2026-09-20' },
        activeExam: null,
        pastExams: [],
        generationEligibility: { eligible: true, code: 'ELIGIBLE', message: null },
        inputSnapshotToken: 'x',
      } as never}
      lecturers={[{ id: 1, name: 'Ada' }]}
      busy={false}
      onSave={onSave}
    />,
  ))

  const identifier = host.querySelector<HTMLInputElement>('input[name=exam-identifier]')!
  await act(async () => {
    const valueSetter = Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set
    valueSetter?.call(identifier, 'Changed')
    identifier.dispatchEvent(new Event('input', { bubbles: true }))
  })
  await act(async () => [...host.querySelectorAll<HTMLButtonElement>('button')]
    .find((button) => button.textContent === 'Cancel changes')?.click())
  expect(identifier.value).toBe('Final')

  await act(async () => [...host.querySelectorAll<HTMLButtonElement>('button')]
    .find((button) => button.textContent === 'Save exam requirement')?.click())
  expect(onSave).toHaveBeenCalledWith({
    semesterId: 4,
    enabled: true,
    expectedRevision: 3,
    configuration: {
      identifier: 'Final',
      durationMinutes: 90,
      recommendedStartOverride: null,
      recommendedEndOverride: null,
      requiredCapacity: 20,
      examType: 'Written',
      responsibleLecturerId: 1,
    },
  })
  await act(async () => root.unmount())
})
