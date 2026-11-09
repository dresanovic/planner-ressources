import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { expect, it, vi } from 'vitest'

import { AcademicRecordEditor } from './AcademicRecordEditor'
import { AcademicCatalogApiError } from '../api/academicCatalog'

it('shows separate teaching and overall units and submits independent values', async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  await act(async () => root.render(<AcademicRecordEditor category="courses" includeCourseResources={false}
    initialValues={{ name: 'Course', totalUnits: 8, overallUnits: 20 }} onSubmit={onSubmit} />))
  expect(host.querySelector('label[for="academic-totalUnits"]')?.textContent).toBe('Lehreinheiten')
  expect(host.querySelector('label[for="academic-overallUnits"]')?.textContent).toBe('Total Einheiten')
  await act(async () => host.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ totalUnits: 8, overallUnits: 20 }))
  await act(async () => root.unmount())
  host.remove()
})

it('retains precise window times when editing or copying an existing window', async () => {
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  const host = document.body.appendChild(document.createElement('div'))
  const root = createRoot(host)
  await act(async () => root.render(<AcademicRecordEditor category="time-windows" lockKind
    options={{ studyTypes: [{ id: 1, name: 'Form' }] }}
    initialValues={{ kind: 'dated', studyTypeId: 1, date: '2026-11-09', startTime: '09:00:00.000001', endTime: '12:00:00.000001' }} onSubmit={onSubmit} />))
  expect(host.querySelector<HTMLInputElement>('[name=startTime]')!.value).toBe('09:00:00.000001')
  expect(host.querySelector<HTMLInputElement>('[name=endTime]')!.value).toBe('12:00:00.000001')
  expect(host.querySelector('form')!.checkValidity()).toBe(true)
  await act(async () => host.querySelector<HTMLButtonElement>('[type=submit]')!.click())
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ startTime: '09:00:00.000001', endTime: '12:00:00.000001' }))
  await act(async () => root.unmount())
  host.remove()
})

it('explains duplicate identity separately from a stale revision while retaining copied values',async()=>{
  const onSubmit=vi.fn().mockRejectedValue(new AcademicCatalogApiError(409,[{code:'DUPLICATE_TIME_WINDOW',message:'duplicate',field:null,meta:{conflictingRecordId:12}}]))
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  await act(async()=>root.render(<AcademicRecordEditor category="time-windows" lockKind initialValues={{kind:'dated',date:'2026-11-09',isIntensive:true,studyTypeId:1,startTime:'09:00',endTime:'12:00'}} onSubmit={onSubmit}/>))
  await act(async()=>document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
  expect(document.querySelector('[role="alert"]')?.textContent).toContain('Zeitfenster bereits vorhanden')
  expect(document.body.textContent).toContain('archivierte')
  expect(document.body.textContent).toContain('Markierung')
  expect(document.body.textContent).not.toContain('zwischenzeitlich aktualisiert')
  expect(document.querySelector<HTMLInputElement>('[name=date]')?.value).toBe('09.11.2026')
  expect(document.querySelector<HTMLInputElement>('[name=isIntensive]')?.checked).toBe(true)
  expect(onSubmit).toHaveBeenCalledTimes(1)
})

it('retains actual stale-revision refresh guidance',async()=>{
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit=vi.fn().mockRejectedValue(new AcademicCatalogApiError(409,[{code:'STALE_REVISION',message:'changed',field:null}]))
  await act(async()=>root.render(<AcademicRecordEditor category="time-windows" onSubmit={onSubmit}/>))
  await act(async()=>document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
  expect(document.body.textContent).toContain('zwischenzeitlich aktualisiert')
  expect(document.body.textContent).not.toContain('Zeitfenster bereits vorhanden')
})

it('associates all detected errors including marker and focuses the first invalid field in visual order',async()=>{
  const onSubmit=vi.fn().mockRejectedValue(new AcademicCatalogApiError(422,[
    {code:'VALIDATION_ERROR',field:'endTime',message:'Ende prüfen'},
    {code:'VALIDATION_ERROR',field:'date',message:'Datum prüfen'},
    {code:'VALIDATION_ERROR',field:'isIntensive',message:'Markierung prüfen'},
  ]))
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  await act(async()=>root.render(<AcademicRecordEditor category="time-windows" initialValues={{kind:'dated',date:'2026-11-09'}} onSubmit={onSubmit}/>))
  expect(document.activeElement?.getAttribute('name')).toBe('kind')
  await act(async()=>document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true})))
  expect(document.activeElement?.getAttribute('name')).toBe('date')
  for(const name of ['date','endTime','isIntensive']){
    const input=document.querySelector(`[name="${name}"]`)!
    expect(input.getAttribute('aria-invalid')).toBe('true')
    expect(input.getAttribute('aria-describedby')).toBeTruthy()
  }
  expect(document.querySelector('[role="alert"]')?.textContent).toContain('Intensivwoche')
})

it('suppresses repeated submissions in the same event batch while a write is pending', async () => {
  let resolve: (value:unknown)=>void = ()=>undefined
  const onSubmit=vi.fn().mockImplementation(()=>new Promise(done=>{resolve=done}))
  const root=createRoot(document.body.appendChild(document.createElement('div')))
  await act(async()=>root.render(<AcademicRecordEditor category="time-windows" initialValues={{studyTypeId:1,weekday:0,startTime:'09:00',endTime:'12:00'}} onSubmit={onSubmit}/>))
  act(()=>{
    document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))
    document.querySelector('form')!.dispatchEvent(new Event('submit',{bubbles:true,cancelable:true}))
  })
  expect(onSubmit).toHaveBeenCalledTimes(1)
  await act(async()=>resolve(undefined))
})

it('creates an exact German date with a default-off intensive marker and retains failed input', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockRejectedValue(new AcademicCatalogApiError(422, [{ code: 'VALIDATION_ERROR', message: 'Datum prüfen', field: 'date' }]))
  await act(async () => root.render(<AcademicRecordEditor category="time-windows"
    options={{ studyTypes: [{ id: 1, name: 'Berufsbegleitend' }] }}
    initialValues={{ kind: 'dated', studyTypeId: 1, date: '2026-11-09', startTime: '09:00', endTime: '12:00' }} onSubmit={onSubmit} />))
  expect(document.querySelector<HTMLInputElement>('input[name="date"]')?.value).toBe('09.11.2026')
  expect(document.querySelector<HTMLInputElement>('input[name="isIntensive"]')?.checked).toBe(false)
  expect(document.querySelector('select[name="weekday"]')).toBeNull()
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ kind: 'dated', date: '2026-11-09', weekday: null, isIntensive: false }))
  expect(document.querySelector<HTMLInputElement>('input[name="date"]')?.value).toBe('09.11.2026')
  expect(document.activeElement?.getAttribute('name')).toBe('date')
})

it('round-trips optional preferred units and allows clearing to the midpoint default', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  await act(async () => root.render(<AcademicRecordEditor category="courses" includeCourseResources={false}
    initialValues={{ minSessionUnits: 2, maxSessionUnits: 6, preferredSessionUnits: 3 }} onSubmit={onSubmit} />))
  const input = document.querySelector<HTMLInputElement>('input[name="preferredSessionUnits"]')!
  expect(input.value).toBe('3')
  expect(input.required).toBe(false)
  expect(input.step).toBe('0.5')
  expect(input.min).toBe('2')
  expect(input.max).toBe('6')
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit).toHaveBeenLastCalledWith(expect.objectContaining({ preferredSessionUnits: 3 }))
  act(() => { input.value = ''; input.dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit.mock.lastCall?.[0]).not.toHaveProperty('preferredSessionUnits')
})

it('retains controlled values and renders required course relationships', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockRejectedValue(new Error('invalid'))
  await act(async () => root.render(<AcademicRecordEditor category="courses" options={{ semesters: [{ id: 1, name: 'Fall' }], cohorts: [{ id: 2, name: 'AI 1' }], studyTypes: [{ id: 3, name: 'Full-time' }], lecturers: [{ id: 4, name: 'Ada' }], rooms: [{ id: 5, name: 'R1' }] }} onSubmit={onSubmit} />))
  const name = document.querySelector<HTMLInputElement>('input[name="name"]')!
  act(() => { name.value = 'Scheduling 101'; name.dispatchEvent(new Event('input', { bubbles: true })) })
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(name.value).toBe('Scheduling 101')
  expect(document.body.textContent).toContain('Semester')
  expect(document.body.textContent).toContain('Lehrende Person')
  expect(document.body.textContent).toContain('Raum')
})

it('blocks Course creation with actionable feedback when read-only resources are unavailable', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => root.render(<AcademicRecordEditor category="courses" options={{ semesters: [{ id: 1, name: 'Fall' }], cohorts: [{ id: 2, name: 'AI 1' }], studyTypes: [{ id: 3, name: 'Full-time' }], lecturers: [], rooms: [] }} onSubmit={vi.fn()} />))
  expect(document.body.textContent).toContain('Es ist keine Lehrende Person verfügbar')
  expect(document.body.textContent).toContain('Es ist kein Raum verfügbar')
  expect(document.querySelector<HTMLButtonElement>('button[type="submit"]')?.disabled).toBe(true)
})

it('shows every structured correction returned by catalog validation', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockRejectedValue(new AcademicCatalogApiError(422, [
    { code: 'VALIDATION_ERROR', message: 'Total units must be positive.', field: 'totalUnits' },
    { code: 'REQUIRED_RELATIONSHIP_INVALID', message: 'Semester does not exist.', field: 'semesterId' },
  ]))
  await act(async () => root.render(<AcademicRecordEditor category="courses" options={{ semesters: [{ id: 1, name: 'Fall' }], cohorts: [{ id: 2, name: 'AI 1' }], studyTypes: [{ id: 3, name: 'Vollzeit' }], lecturers: [{ id: 4, name: 'Ada' }], rooms: [{ id: 5, name: 'R1' }] }} onSubmit={onSubmit} />))
  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  const totalUnits = document.querySelector<HTMLInputElement>('#academic-totalUnits')!
  const semester = document.querySelector<HTMLSelectElement>('#academic-semesterId')!
  expect(document.querySelectorAll('.actionable-problem')).toHaveLength(2)
  expect(document.body.textContent).toContain('Lehreinheiten korrigieren')
  expect(document.body.textContent).toContain('Semester korrigieren')
  expect(document.body.textContent).not.toContain('totalUnits')
  expect(document.body.textContent).not.toContain('semesterId')
  expect(totalUnits.getAttribute('aria-invalid')).toBe('true')
  expect(semester.getAttribute('aria-invalid')).toBe('true')
  expect(document.getElementById(totalUnits.getAttribute('aria-describedby')!)).not.toBeNull()
  expect(document.activeElement).toBe(totalUnits)
})

it('uses weekday names and preserves supplied stable order without exposing Sort order', async () => {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  const onSubmit = vi.fn().mockResolvedValue(undefined)
  await act(async () => root.render(<AcademicRecordEditor
    category="time-windows"
    options={{ studyTypes: [{ id: 3, name: 'Part-time' }] }}
    initialValues={{ studyTypeId: 3, weekday: 4, startTime: '18:00', endTime: '22:00', sortOrder: 99 }}
    onSubmit={onSubmit}
  />))

  const weekday = document.querySelector<HTMLSelectElement>('select[name="weekday"]')!
  expect(Array.from(weekday.options).map((option) => option.textContent)).toEqual([
    'Montag', 'Dienstag', 'Mittwoch', 'Donnerstag', 'Freitag', 'Samstag', 'Sonntag',
  ])
  expect(weekday.value).toBe('4')
  expect(document.querySelector('[name="sortOrder"]')).toBeNull()

  await act(async () => document.querySelector('form')!.dispatchEvent(new Event('submit', { bubbles: true, cancelable: true })))
  expect(onSubmit).toHaveBeenCalledWith(expect.objectContaining({ weekday: 4, sortOrder: 99 }))
})
