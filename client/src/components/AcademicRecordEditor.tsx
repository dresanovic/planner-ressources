import { useState, type FormEvent } from 'react'
import { AcademicCatalogApiError } from '../api/academicCatalog'
import { WEEKDAY_NAMES, weeklySortOrder } from '../utils/weekdays'
import { label as term } from '../config/terminology'
import { EuropeanDateField } from './EuropeanDateField'
import { ActionableProblemList, problemDescriptionIds } from './ActionableProblemList'
import { fieldProblem, operationProblem, type UserProblem } from '../utils/userProblems'

export type AcademicCategory = 'semesters' | 'cohorts' | 'courses' | 'study-types' | 'time-windows'
type Option = { id: number; name: string }
type EditorOptions = { semesters?: Option[]; cohorts?: Option[]; studyTypes?: Option[]; lecturers?: Option[]; rooms?: Option[] }

const defaults = { name: '', startDate: '', endDate: '', studentCount: '', totalUnits: '', minSessionUnits: '', maxSessionUnits: '', semesterId: '', cohortId: '', studyTypeId: '', lecturerId: '', roomId: '', weekday: '0', startTime: '', endTime: '' }

export function AcademicRecordEditor({ category, options = {}, initialValues = {}, submitLabel = 'Speichern', includeCourseResources = true, onSubmit }: { category: AcademicCategory; options?: EditorOptions; initialValues?: Record<string, string | number>; submitLabel?: string; includeCourseResources?: boolean; onSubmit: (value: Record<string, string | number>) => Promise<unknown> }) {
  const [values, setValues] = useState<Record<string, string>>(() => ({ ...defaults, ...Object.fromEntries(Object.entries(initialValues).map(([key, value]) => [key, String(value)])) }))
  const [problems, setProblems] = useState<UserProblem[]>([])
  const fieldDefinitions: Record<string, { id: string; label: string; expectation: string }> = {
    name: { id: 'academic-name', label: 'Name', expectation: 'ein eindeutiger Name' },
    startDate: { id: 'academic-startDate', label: 'Beginn', expectation: 'ein gültiges Datum im Format TT.MM.JJJJ' },
    endDate: { id: 'academic-endDate', label: 'Ende', expectation: 'ein gültiges Datum im Format TT.MM.JJJJ, das nicht vor dem Beginn liegt' },
    studentCount: { id: 'academic-studentCount', label: 'Anzahl Studierende', expectation: 'eine positive ganze Zahl' },
    totalUnits: { id: 'academic-totalUnits', label: 'Gesamteinheiten', expectation: 'eine positive ganze Zahl' },
    minSessionUnits: { id: 'academic-minSessionUnits', label: 'Minimale Einheiten je Termin', expectation: 'eine positive ganze Zahl innerhalb des Gesamtumfangs' },
    maxSessionUnits: { id: 'academic-maxSessionUnits', label: 'Maximale Einheiten je Termin', expectation: 'eine positive ganze Zahl innerhalb des Gesamtumfangs' },
    semesterId: { id: 'academic-semesterId', label: 'Semester', expectation: 'ein vorhandenes Semester' },
    cohortId: { id: 'academic-cohortId', label: term('cohort.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    studyTypeId: { id: 'academic-studyTypeId', label: 'Studienform', expectation: 'eine vorhandene Studienform' },
    lecturerId: { id: 'academic-lecturerId', label: term('lecturer.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    roomId: { id: 'academic-roomId', label: term('room.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    weekday: { id: 'academic-weekday', label: 'Wochentag', expectation: 'einen gültigen Wochentag' },
    startTime: { id: 'academic-startTime', label: 'Beginn', expectation: 'eine gültige Beginnzeit' },
    endTime: { id: 'academic-endTime', label: 'Ende', expectation: 'eine gültige Endzeit nach dem Beginn' },
  }
  const aliases: Record<string, string> = { start_date: 'startDate', end_date: 'endDate', student_count: 'studentCount', total_units: 'totalUnits', min_session_units: 'minSessionUnits', max_session_units: 'maxSessionUnits', semester_id: 'semesterId', cohort_id: 'cohortId', study_type_id: 'studyTypeId', lecturer_id: 'lecturerId', room_id: 'roomId', start_time: 'startTime', end_time: 'endTime' }
  const set = (name: string, value: string) => { setProblems([]); setValues((current) => ({ ...current, [name]: value })) }
  const fieldState = (name: string) => {
    const id = fieldDefinitions[name]?.id ?? `academic-${name}`
    return { id, invalid: problems.some((problem) => problem.fieldId === id), describedBy: problemDescriptionIds(problems, id) }
  }
  const input = (name: string, fieldLabel: string, type = 'text') => type === 'date'
    ? <EuropeanDateField id={fieldState(name).id} name={name} className="catalog-field" label={fieldLabel} value={values[name]} onChange={(value) => set(name, value ?? '')} required invalid={fieldState(name).invalid} describedBy={fieldState(name).describedBy} />
    : <label className="catalog-field" htmlFor={fieldState(name).id}><span>{fieldLabel}</span><input id={fieldState(name).id} name={name} type={type} value={values[name]} aria-invalid={fieldState(name).invalid || undefined} aria-describedby={fieldState(name).describedBy} onInput={(event) => set(name, event.currentTarget.value)} required /></label>
  const select = (name: string, fieldLabel: string, choices: Option[]) => <label className="catalog-field" htmlFor={fieldState(name).id}><span>{fieldLabel}</span><select id={fieldState(name).id} name={name} value={values[name]} aria-invalid={fieldState(name).invalid || undefined} aria-describedby={fieldState(name).describedBy} onChange={(event) => set(name, event.target.value)} required><option value="">{fieldLabel} auswählen</option>{choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.name}</option>)}</select></label>
  async function submit(event: FormEvent) {
    event.preventDefault(); setProblems([])
    const numeric = new Set(['studentCount', 'totalUnits', 'minSessionUnits', 'maxSessionUnits', 'semesterId', 'cohortId', 'studyTypeId', 'lecturerId', 'roomId', 'weekday', 'sortOrder'])
    const submittedValues = category === 'time-windows'
      ? { ...values, sortOrder: String(weeklySortOrder(Number(values.weekday), values.startTime)) }
      : values
    const payload = Object.fromEntries(Object.entries(submittedValues).filter(([, value]) => value !== '').map(([key, value]) => [key, numeric.has(key) ? Number(value) : value]))
    try {
      await onSubmit(payload)
    } catch (reason) {
      if (reason instanceof AcademicCatalogApiError) {
        const fieldProblems = reason.errors.flatMap((item, index) => {
          const fieldName = item.field ? aliases[item.field] ?? item.field : null
          const definition = fieldName ? fieldDefinitions[fieldName] : undefined
          if (!definition) return []
          const problem = fieldProblem(definition.id, definition.label, definition.expectation)
          return [{ ...problem, key: `${problem.key}-${item.code}-${index}` }]
        })
        if (fieldProblems.length > 0) {
          setProblems(fieldProblems)
          queueMicrotask(() => document.getElementById(fieldProblems[0].fieldId!)?.focus())
          return
        }
        const category = reason.status === 409 ? 'stale' : reason.status === 403 ? 'permission' : reason.status === 0 ? 'connectivity' : 'unexpected'
        setProblems([operationProblem(category, { action: 'Speichern des Datensatzes', item: values.name.trim() || undefined, inputPreserved: true, outcomeUnknown: category === 'connectivity' || category === 'unexpected' })])
        return
      }
      setProblems([operationProblem('unexpected', { action: 'Speichern des Datensatzes', item: values.name.trim() || undefined, inputPreserved: true, outcomeUnknown: true })])
    }
  }
  const missingLecturers = category === 'courses' && includeCourseResources && (options.lecturers?.length ?? 0) === 0
  const missingRooms = category === 'courses' && includeCourseResources && (options.rooms?.length ?? 0) === 0
  return <form className="catalog-editor" onSubmit={submit}>
    {category !== 'time-windows' && input('name', 'Name')}
    {category === 'semesters' && <>{input('startDate', 'Beginn', 'date')}{input('endDate', 'Ende', 'date')}</>}
    {category === 'cohorts' && input('studentCount', 'Anzahl Studierende', 'number')}
    {category === 'courses' && <>{input('totalUnits', 'Gesamteinheiten', 'number')}{input('minSessionUnits', 'Minimale Einheiten je Termin', 'number')}{input('maxSessionUnits', 'Maximale Einheiten je Termin', 'number')}{select('semesterId', 'Semester', options.semesters ?? [])}{select('cohortId', term('cohort.fieldLabel'), options.cohorts ?? [])}{select('studyTypeId', 'Studienform', options.studyTypes ?? [])}{includeCourseResources && <>{select('lecturerId', term('lecturer.fieldLabel'), options.lecturers ?? [])}{select('roomId', term('room.fieldLabel'), options.rooms ?? [])}</>}</>}
    {category === 'time-windows' && <>{select('studyTypeId', 'Studienform', options.studyTypes ?? [])}<label className="catalog-field" htmlFor={fieldState('weekday').id}><span>Wochentag</span><select id={fieldState('weekday').id} name="weekday" value={values.weekday} aria-invalid={fieldState('weekday').invalid || undefined} aria-describedby={fieldState('weekday').describedBy} onChange={(event) => set('weekday', event.target.value)} required>{WEEKDAY_NAMES.map((name, weekday) => <option key={name} value={weekday}>{name}</option>)}</select></label>{input('startTime', 'Beginn', 'time')}{input('endTime', 'Ende', 'time')}</>}
    {missingLecturers && <p role="alert" className="inline-error">Es ist keine {term('lecturer.singular')} verfügbar. Legen Sie die benötigte Ressource an, bevor Sie eine {term('course.singular')} erstellen.</p>}
    {missingRooms && <p role="alert" className="inline-error">Es ist kein {term('room.singular')} verfügbar. Legen Sie die benötigte Ressource an, bevor Sie eine {term('course.singular')} erstellen.</p>}
    <ActionableProblemList problems={problems} className="catalog-editor-problems" />
    <button type="submit" disabled={missingLecturers || missingRooms}>{submitLabel}</button>
  </form>
}
