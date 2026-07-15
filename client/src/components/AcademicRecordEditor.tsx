import { useState, type FormEvent } from 'react'
import { AcademicCatalogApiError } from '../api/academicCatalog'
import { WEEKDAY_NAMES, weeklySortOrder } from '../utils/weekdays'

export type AcademicCategory = 'semesters' | 'cohorts' | 'courses' | 'study-types' | 'time-windows'
type Option = { id: number; name: string }
type EditorOptions = { semesters?: Option[]; cohorts?: Option[]; studyTypes?: Option[]; lecturers?: Option[]; rooms?: Option[] }

const defaults = { name: '', startDate: '', endDate: '', studentCount: '', totalUnits: '', minSessionUnits: '', maxSessionUnits: '', semesterId: '', cohortId: '', studyTypeId: '', lecturerId: '', roomId: '', weekday: '0', startTime: '', endTime: '' }

export function AcademicRecordEditor({ category, options = {}, initialValues = {}, submitLabel = 'Save', includeCourseResources = true, onSubmit }: { category: AcademicCategory; options?: EditorOptions; initialValues?: Record<string, string | number>; submitLabel?: string; includeCourseResources?: boolean; onSubmit: (value: Record<string, string | number>) => Promise<unknown> }) {
  const [values, setValues] = useState<Record<string, string>>(() => ({ ...defaults, ...Object.fromEntries(Object.entries(initialValues).map(([key, value]) => [key, String(value)])) }))
  const [errors, setErrors] = useState<string[]>([])
  const set = (name: string, value: string) => setValues((current) => ({ ...current, [name]: value }))
  const input = (name: string, label: string, type = 'text') => <label className="catalog-field">{label}<input name={name} type={type} value={values[name]} onInput={(event) => set(name, event.currentTarget.value)} required /></label>
  const select = (name: string, label: string, choices: Option[]) => <label className="catalog-field">{label}<select name={name} value={values[name]} onChange={(event) => set(name, event.target.value)} required><option value="">Select {label.toLowerCase()}</option>{choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.name}</option>)}</select></label>
  async function submit(event: FormEvent) {
    event.preventDefault(); setErrors([])
    const numeric = new Set(['studentCount', 'totalUnits', 'minSessionUnits', 'maxSessionUnits', 'semesterId', 'cohortId', 'studyTypeId', 'lecturerId', 'roomId', 'weekday', 'sortOrder'])
    const submittedValues = category === 'time-windows'
      ? { ...values, sortOrder: String(weeklySortOrder(Number(values.weekday), values.startTime)) }
      : values
    const payload = Object.fromEntries(Object.entries(submittedValues).filter(([, value]) => value !== '').map(([key, value]) => [key, numeric.has(key) ? Number(value) : value]))
    try {
      await onSubmit(payload)
    } catch (reason) {
      setErrors(reason instanceof AcademicCatalogApiError
        ? reason.errors.map((item) => item.message)
        : [reason instanceof Error ? reason.message : 'Could not save this record.'])
    }
  }
  const missingLecturers = category === 'courses' && includeCourseResources && (options.lecturers?.length ?? 0) === 0
  const missingRooms = category === 'courses' && includeCourseResources && (options.rooms?.length ?? 0) === 0
  return <form className="catalog-editor" onSubmit={submit}>
    {category !== 'time-windows' && input('name', 'Name')}
    {category === 'semesters' && <>{input('startDate', 'Start date', 'date')}{input('endDate', 'End date', 'date')}</>}
    {category === 'cohorts' && input('studentCount', 'Student count', 'number')}
    {category === 'courses' && <>{input('totalUnits', 'Total units', 'number')}{input('minSessionUnits', 'Minimum session units', 'number')}{input('maxSessionUnits', 'Maximum session units', 'number')}{select('semesterId', 'Semester', options.semesters ?? [])}{select('cohortId', 'Cohort', options.cohorts ?? [])}{select('studyTypeId', 'Study type', options.studyTypes ?? [])}{includeCourseResources && <>{select('lecturerId', 'Lecturer', options.lecturers ?? [])}{select('roomId', 'Room', options.rooms ?? [])}</>}</>}
    {category === 'time-windows' && <>{select('studyTypeId', 'Study type', options.studyTypes ?? [])}<label className="catalog-field">Day of week<select name="weekday" value={values.weekday} onChange={(event) => set('weekday', event.target.value)} required>{WEEKDAY_NAMES.map((name, weekday) => <option key={name} value={weekday}>{name}</option>)}</select></label>{input('startTime', 'Start time', 'time')}{input('endTime', 'End time', 'time')}</>}
    {missingLecturers && <p role="alert" className="inline-error">No Lecturer records are available. Add the required read-only planning resource before creating a Course.</p>}
    {missingRooms && <p role="alert" className="inline-error">No Room records are available. Add the required read-only planning resource before creating a Course.</p>}
    {errors.length > 0 && <div role="alert" className="inline-error">{errors.map((error, index) => <p key={`${error}-${index}`}>{error}</p>)}</div>}
    <button type="submit" disabled={missingLecturers || missingRooms}>{submitLabel}</button>
  </form>
}
