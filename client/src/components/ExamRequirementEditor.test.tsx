import { act } from 'react'; import { createRoot } from 'react-dom/client'; import { afterEach, expect, it, vi } from 'vitest'; import { ExamRequirementEditor } from './ExamRequirementEditor'
let host: HTMLDivElement; afterEach(() => host?.remove())
it('enables and saves a complete configuration with anchor guidance', async () => { host=document.createElement('div'); document.body.append(host); const root=createRoot(host); const onSave=vi.fn(); await act(async()=>root.render(<ExamRequirementEditor state={{ courseId:1, courseName:'A', semesterId:1, cohortId:1, cohortName:'C', enabled:false, configuration:null, finalTeachingAnchor:null, activeExam:null, pastExams:[], generationEligibility:{eligible:false,code:'DISABLED',message:null}, inputSnapshotToken:'x' }} lecturers={[{id:1,name:'Ada'}]} busy={false} saving={false} onSave={onSave}/>)); expect(host.textContent).not.toContain('Noch kein letzter Lehrtermin'); const enable=host.querySelector('input[type=checkbox]') as HTMLInputElement; await act(async()=>enable.click()); expect(host.textContent).toContain('Noch kein letzter Lehrtermin'); expect(host.querySelector('input[name=exam-identifier]')).not.toBeNull(); await act(async()=>root.unmount()) })

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
      saving={false}
      onSave={vi.fn()}
    />,
  ))

  expect(host.textContent).toContain('verwendete Konfiguration ist schreibgeschützt')
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
      saving={false}
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
    .find((button) => button.textContent === 'Änderungen verwerfen')?.click())
  expect(identifier.value).toBe('Final')

  await act(async () => [...host.querySelectorAll<HTMLButtonElement>('button')]
    .find((button) => button.textContent === 'Prüfungsanforderung speichern')?.click())
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

it('keeps validation problems separate, associates fields, and focuses the first invalid field', async () => {
  host = document.createElement('div')
  document.body.append(host)
  const root = createRoot(host)
  const onSave = vi.fn()
  await act(async () => root.render(<ExamRequirementEditor state={{ courseId: 1, courseName: 'KI Grundlagen', semesterId: 1, cohortId: 1, cohortName: 'C', enabled: true, configuration: null, finalTeachingAnchor: null, activeExam: null, pastExams: [], generationEligibility: { eligible: false, code: 'DISABLED', message: null }, inputSnapshotToken: 'x' }} lecturers={[]} busy={false} saving={false} onSave={onSave} />))
  const identifier = host.querySelector<HTMLInputElement>('input[name="exam-identifier"]')!
  await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(identifier, '')
    identifier.dispatchEvent(new Event('input', { bubbles: true }))
    ;[...host.querySelectorAll<HTMLButtonElement>('button')].find((button) => button.textContent === 'Prüfungsanforderung speichern')?.click()
  })
  expect(onSave).not.toHaveBeenCalled()
  expect(host.querySelectorAll('.actionable-problem').length).toBeGreaterThan(1)
  expect(identifier.getAttribute('aria-invalid')).toBe('true')
  expect(identifier.getAttribute('aria-describedby')).toContain('exam-identifier-error')
  expect(document.activeElement).toBe(identifier)
})

it('associates and focuses the end field when the recommended range is reversed', async () => {
  host = document.createElement('div'); document.body.append(host)
  const root = createRoot(host); const onSave = vi.fn()
  await act(async () => root.render(<ExamRequirementEditor state={{ courseId: 1, courseName: 'A', semesterId: 1, cohortId: 1, cohortName: 'C', enabled: true, configuration: null, finalTeachingAnchor: { date: '2026-09-01', endTime: '10:00', teachingSessionId: 1 }, activeExam: null, pastExams: [], generationEligibility: { eligible: true, code: 'ELIGIBLE', message: null }, inputSnapshotToken: 'x' }} lecturers={[{ id: 1, name: 'Ada' }]} busy={false} saving={false} onSave={onSave} />))
  const checks = host.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
  await act(async () => checks[1].click())
  const start = host.querySelector<HTMLInputElement>('#exam-recommendation-start')!
  const end = host.querySelector<HTMLInputElement>('#exam-recommendation-end')!
  const setValue = (input: HTMLInputElement, value: string) => { Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(input, value); input.dispatchEvent(new Event('input', { bubbles: true })) }
  await act(async () => { setValue(start, '30.09.2026'); setValue(end, '15.09.2026') })
  await act(async () => { [...host.querySelectorAll<HTMLButtonElement>('button')].find((button) => button.textContent === 'Prüfungsanforderung speichern')?.click(); await Promise.resolve() })
  expect(onSave).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(end)
  expect(end.getAttribute('aria-invalid')).toBe('true')
  expect(end.getAttribute('aria-describedby')).toContain('exam-recommendation-end-error')
})

it.each([
  { name: 'both range dates are missing', endValue: '' },
  { name: 'only the start date is missing', endValue: '30.09.2026' },
])('associates and focuses the start field when $name', async ({ endValue }) => {
  host = document.createElement('div'); document.body.append(host)
  const root = createRoot(host); const onSave = vi.fn()
  await act(async () => root.render(<ExamRequirementEditor state={{ courseId: 1, courseName: 'A', semesterId: 1, cohortId: 1, cohortName: 'C', enabled: true, configuration: null, finalTeachingAnchor: { date: '2026-09-01', endTime: '10:00', teachingSessionId: 1 }, activeExam: null, pastExams: [], generationEligibility: { eligible: true, code: 'ELIGIBLE', message: null }, inputSnapshotToken: 'x' }} lecturers={[{ id: 1, name: 'Ada' }]} busy={false} saving={false} onSave={onSave} />))
  const checks = host.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
  await act(async () => checks[1].click())
  const start = host.querySelector<HTMLInputElement>('#exam-recommendation-start')!
  const end = host.querySelector<HTMLInputElement>('#exam-recommendation-end')!
  if (endValue) await act(async () => {
    Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(end, endValue)
    end.dispatchEvent(new Event('input', { bubbles: true }))
  })
  await act(async () => { [...host.querySelectorAll<HTMLButtonElement>('button')].find((button) => button.textContent === 'Prüfungsanforderung speichern')?.click(); await Promise.resolve() })
  expect(onSave).not.toHaveBeenCalled()
  expect(document.activeElement).toBe(start)
  expect(start.getAttribute('aria-invalid')).toBe('true')
  expect(start.getAttribute('aria-describedby')).toContain('exam-recommendation-start-error')
})
