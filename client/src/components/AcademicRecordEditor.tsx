import { useEffect, useRef, useState, type FormEvent } from 'react'
import { AcademicCatalogApiError } from '../api/academicCatalog'
import { WEEKDAY_NAMES, weeklySortOrder } from '../utils/weekdays'
import { label as term } from '../config/terminology'
import { EuropeanDateField } from './EuropeanDateField'
import { ActionableProblemList, problemDescriptionIds } from './ActionableProblemList'
import { fieldProblem, operationProblem, type UserProblem } from '../utils/userProblems'

export type AcademicCategory = 'semesters' | 'cohorts' | 'courses' | 'study-types' | 'time-windows'
type Option = { id: number; name: string }
type EditorOptions = { semesters?: Option[]; cohorts?: Option[]; studyTypes?: Option[]; lecturers?: Option[]; rooms?: Option[] }

export type AcademicEditorValues = Record<string, string | number | boolean | null>

const defaults = { kind: 'weekly', date: '', isIntensive: 'false', name: '', startDate: '', endDate: '', studentCount: '', totalUnits: '', overallUnits: '', minSessionUnits: '', maxSessionUnits: '', preferredSessionUnits: '', semesterId: '', cohortId: '', studyTypeId: '', lecturerId: '', roomId: '', weekday: '0', startTime: '', endTime: '' }

export function AcademicRecordEditor({ category, options = {}, initialValues = {}, submitLabel = 'Speichern', includeCourseResources = true, lockKind = false, onSubmit }: { category: AcademicCategory; options?: EditorOptions; initialValues?: AcademicEditorValues; submitLabel?: string; includeCourseResources?: boolean; lockKind?: boolean; onSubmit: (value: AcademicEditorValues) => Promise<unknown> }) {
  const [values, setValues] = useState<Record<string, string>>(() => ({ ...defaults, ...Object.fromEntries(Object.entries(initialValues).map(([key, value]) => [key, value == null ? '' : String(value)])) }))
  const formRef = useRef<HTMLFormElement>(null)
  const submittingRef = useRef(false)
  const [submitting, setSubmitting] = useState(false)
  useEffect(() => {
    if (category === 'time-windows') formRef.current?.querySelector<HTMLElement>(lockKind ? '[name=studyTypeId]' : '[name=kind]')?.focus()
  }, [category, lockKind])
  const [problems, setProblems] = useState<UserProblem[]>([])
  const fieldDefinitions: Record<string, { id: string; label: string; expectation: string }> = {
    name: { id: 'academic-name', label: 'Name', expectation: 'ein eindeutiger Name' },
    startDate: { id: 'academic-startDate', label: 'Beginn', expectation: 'ein gültiges Datum im Format TT.MM.JJJJ' },
    endDate: { id: 'academic-endDate', label: 'Ende', expectation: 'ein gültiges Datum im Format TT.MM.JJJJ, das nicht vor dem Beginn liegt' },
    studentCount: { id: 'academic-studentCount', label: 'Anzahl Studierende', expectation: 'eine positive ganze Zahl' },
    totalUnits: { id: 'academic-totalUnits', label: 'Lehreinheiten', expectation: 'eine positive ganze Zahl' },
    overallUnits: { id: 'academic-overallUnits', label: 'Total Einheiten', expectation: 'eine positive ganze Zahl' },
    preferredSessionUnits: { id: 'academic-preferredSessionUnits', label: 'Bevorzugte LE pro Termin', expectation: 'ganze oder halbe LE zwischen Minimum und Maximum; leer für den Mittelwert' },
    minSessionUnits: { id: 'academic-minSessionUnits', label: 'Minimale Einheiten je Termin', expectation: 'eine positive ganze Zahl innerhalb des Gesamtumfangs' },
    maxSessionUnits: { id: 'academic-maxSessionUnits', label: 'Maximale Einheiten je Termin', expectation: 'eine positive ganze Zahl innerhalb des Gesamtumfangs' },
    semesterId: { id: 'academic-semesterId', label: 'Semester', expectation: 'ein vorhandenes Semester' },
    cohortId: { id: 'academic-cohortId', label: term('cohort.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    studyTypeId: { id: 'academic-studyTypeId', label: 'Studienform', expectation: 'eine vorhandene Studienform' },
    lecturerId: { id: 'academic-lecturerId', label: term('lecturer.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    roomId: { id: 'academic-roomId', label: term('room.fieldLabel'), expectation: 'eine vorhandene Auswahl' },
    kind: { id: 'academic-kind', label: 'Art', expectation: 'Wöchentlich oder Einmaliges Datum' },
    date: { id: 'academic-date', label: 'Datum', expectation: 'ein gültiges vollständiges Datum mit Jahr' },
    isIntensive: { id: 'academic-isIntensive', label: 'Intensivwoche', expectation: 'Ja oder Nein' },
    weekday: { id: 'academic-weekday', label: 'Wochentag', expectation: 'einen gültigen Wochentag' },
    startTime: { id: 'academic-startTime', label: 'Beginn', expectation: 'eine gültige Beginnzeit' },
    endTime: { id: 'academic-endTime', label: 'Ende', expectation: 'eine gültige Endzeit nach dem Beginn' },
  }
  const aliases: Record<string, string> = { start_date: 'startDate', end_date: 'endDate', student_count: 'studentCount', total_units: 'totalUnits', overall_units: 'overallUnits', min_session_units: 'minSessionUnits', preferred_session_units: 'preferredSessionUnits', max_session_units: 'maxSessionUnits', semester_id: 'semesterId', cohort_id: 'cohortId', study_type_id: 'studyTypeId', lecturer_id: 'lecturerId', room_id: 'roomId', start_time: 'startTime', end_time: 'endTime' }
  const set = (name: string, value: string) => { setProblems([]); setValues((current) => ({ ...current, [name]: value })) }
  const fieldState = (name: string) => {
    const id = fieldDefinitions[name]?.id ?? `academic-${name}`
    return { id, invalid: problems.some((problem) => problem.fieldId === id), describedBy: problemDescriptionIds(problems, id) }
  }
  const input = (name: string, fieldLabel: string, type = 'text') => {
    const state = fieldState(name)
    if (type === 'date') return <EuropeanDateField id={state.id} name={name} className="catalog-field" label={fieldLabel} value={values[name]} onChange={(value) => set(name, value ?? '')} required invalid={state.invalid} describedBy={state.describedBy} />
    const precise = type === 'time' && (values[name].length > 5 || String(initialValues[name] ?? '').length > 5)
    const hintId = `${state.id}-clock-hint`
    const descriptions = `${state.describedBy ?? ''}${precise ? ` ${hintId}` : ''}`.trim() || undefined
    return <label className="catalog-field" htmlFor={state.id}><span>{fieldLabel}</span><input id={state.id} name={name} type={precise ? 'text' : type}
      pattern={precise ? '([01][0-9]|2[0-3]):[0-5][0-9](:[0-5][0-9]([.][0-9]{1,6})?)?' : undefined}
      value={values[name]} aria-invalid={state.invalid || undefined} aria-describedby={descriptions} onInput={(event) => set(name, event.currentTarget.value)} required={name !== 'preferredSessionUnits' && name !== 'overallUnits'} step={name === 'preferredSessionUnits' ? 0.5 : undefined} min={name === 'preferredSessionUnits' ? values.minSessionUnits || undefined : undefined} max={name === 'preferredSessionUnits' ? values.maxSessionUnits || undefined : undefined} />
      {precise && <small id={hintId}>Uhrzeit im Format HH:MM oder HH:MM:SS.ffffff. Vorhandene Sekundenbruchteile bleiben erhalten.</small>}</label>
  }
  const select = (name: string, fieldLabel: string, choices: Option[]) => <label className="catalog-field" htmlFor={fieldState(name).id}><span>{fieldLabel}</span><select id={fieldState(name).id} name={name} value={values[name]} aria-invalid={fieldState(name).invalid || undefined} aria-describedby={fieldState(name).describedBy} onChange={(event) => set(name, event.target.value)} required><option value="">{fieldLabel} auswählen</option>{choices.map((choice) => <option key={choice.id} value={choice.id}>{choice.name}</option>)}</select></label>
  async function submit(event: FormEvent) {
    event.preventDefault(); setProblems([])
    if (submittingRef.current) return
    submittingRef.current = true
    setSubmitting(true)
    const numeric = new Set(['studentCount', 'totalUnits', 'overallUnits', 'minSessionUnits', 'maxSessionUnits', 'preferredSessionUnits', 'semesterId', 'cohortId', 'studyTypeId', 'lecturerId', 'roomId', 'weekday', 'sortOrder'])
    const submittedValues = category === 'time-windows'
      ? { ...values, sortOrder: values.sortOrder || String(values.kind === 'dated' ? 0 : weeklySortOrder(Number(values.weekday), values.startTime)) }
      : values
    const payload: AcademicEditorValues = Object.fromEntries(Object.entries(submittedValues).filter(([, value]) => value !== '').map(([key, value]) => [key, numeric.has(key) ? Number(value) : value]))
    if (category === 'time-windows') {
      Object.assign(payload, values.kind === 'dated'
        ? { kind: 'dated', date: values.date, weekday: null, isIntensive: values.isIntensive === 'true' }
        : { kind: 'weekly', date: null, isIntensive: false })
    }
    try {
      await onSubmit(payload)
    } catch (reason) {
      if (reason instanceof AcademicCatalogApiError) {
        if (reason.errors.some(item=>item.code === 'DUPLICATE_TIME_WINDOW')) {
          setProblems([{key:'duplicate-time-window',tone:'blocking',title:'Zeitfenster bereits vorhanden',details:[
            'Ein Zeitfenster derselben Art mit gleicher Studienform, gleichem Datum beziehungsweise Wochentag und gleichen Zeiten besteht bereits.',
            'Das gilt auch für archivierte Einträge. Eine andere Intensivwoche-Markierung hebt den Konflikt nicht auf.',
            'Ihre Eingaben bleiben erhalten. Ändern Sie Studienform, Datum beziehungsweise Wochentag oder Zeiten; alternativ können Sie abbrechen und den bestehenden Eintrag bearbeiten.',
          ],action:{label:'Eingaben anpassen',onClick:()=>formRef.current?.querySelector<HTMLElement>('[name=studyTypeId]')?.focus()}}])
          return
        }
        const fieldProblems = reason.errors.flatMap((item, index) => {
          const fieldName = item.field ? aliases[item.field] ?? item.field : null
          const definition = fieldName ? fieldDefinitions[fieldName] : undefined
          if (!definition) return []
          const problem = fieldProblem(definition.id, definition.label, definition.expectation)
          return [{ ...problem, key: `${problem.key}-${item.code}-${index}` }]
        })
        if (fieldProblems.length > 0) {
          setProblems(fieldProblems)
          queueMicrotask(() => {
            const ids = new Set(fieldProblems.map(problem=>problem.fieldId))
            const first = [...(formRef.current?.querySelectorAll<HTMLElement>('input,select,button') ?? [])].find(element=>ids.has(element.id) && !element.hasAttribute('disabled'))
            first?.focus()
          })
          return
        }
        const category = reason.status === 409 ? 'stale' : reason.status === 403 ? 'permission' : reason.status === 0 ? 'connectivity' : 'unexpected'
        setProblems([operationProblem(category, { action: 'Speichern des Datensatzes', item: values.name.trim() || undefined, inputPreserved: true, outcomeUnknown: category === 'connectivity' || category === 'unexpected' })])
        return
      }
      setProblems([operationProblem('unexpected', { action: 'Speichern des Datensatzes', item: values.name.trim() || undefined, inputPreserved: true, outcomeUnknown: true })])
    } finally { submittingRef.current = false; setSubmitting(false) }
  }
  const missingLecturers = category === 'courses' && includeCourseResources && (options.lecturers?.length ?? 0) === 0
  const missingRooms = category === 'courses' && includeCourseResources && (options.rooms?.length ?? 0) === 0
  return <form ref={formRef} className="catalog-editor" onSubmit={submit}>
    {category !== 'time-windows' && input('name', 'Name')}
    {category === 'semesters' && <>{input('startDate', 'Beginn', 'date')}{input('endDate', 'Ende', 'date')}</>}
    {category === 'cohorts' && input('studentCount', 'Anzahl Studierende', 'number')}
    {category === 'courses' && <>{input('totalUnits', 'Lehreinheiten', 'number')}{input('overallUnits', 'Total Einheiten', 'number')}<p>Lehreinheiten werden geplant. Total Einheiten umfassen auch Online- und Selbstlerneinheiten; beim Anlegen wird ein leeres Feld mit den Lehreinheiten vorbelegt.</p>{input('minSessionUnits', 'Minimale Einheiten je Termin', 'number')}{input('maxSessionUnits', 'Maximale Einheiten je Termin', 'number')}{input('preferredSessionUnits', 'Bevorzugte LE pro Termin (optional)', 'number')}<p>Leer: Mittelwert aus Minimum und Maximum. Halbe Werte bevorzugen die beiden benachbarten ganzen LE gleich; Termine bleiben ganzzahlig.</p>{select('semesterId', 'Semester', options.semesters ?? [])}{select('cohortId', term('cohort.fieldLabel'), options.cohorts ?? [])}{select('studyTypeId', 'Studienform', options.studyTypes ?? [])}{includeCourseResources && <>{select('lecturerId', term('lecturer.fieldLabel'), options.lecturers ?? [])}{select('roomId', term('room.fieldLabel'), options.rooms ?? [])}</>}</>}
    {category === 'time-windows' && <><label className="catalog-field" htmlFor="academic-kind"><span>Art</span><select id="academic-kind" name="kind" value={values.kind} disabled={lockKind} onChange={(event) => set('kind', event.target.value)}><option value="weekly">Wöchentlich</option><option value="dated">Einmaliges Datum</option></select></label>{select('studyTypeId', 'Studienform', options.studyTypes ?? [])}{values.kind === 'dated' ? <>{input('date', 'Datum', 'date')}<label htmlFor="academic-isIntensive"><input id="academic-isIntensive" name="isIntensive" type="checkbox" aria-invalid={fieldState('isIntensive').invalid || undefined} aria-describedby={fieldState('isIntensive').describedBy} checked={values.isIntensive === 'true'} onChange={(event) => set('isIntensive', String(event.target.checked))} />Intensivwoche</label></> : <label className="catalog-field" htmlFor={fieldState('weekday').id}><span>Wochentag</span><select id={fieldState('weekday').id} name="weekday" value={values.weekday} aria-invalid={fieldState('weekday').invalid || undefined} aria-describedby={fieldState('weekday').describedBy} onChange={(event) => set('weekday', event.target.value)} required>{WEEKDAY_NAMES.map((name, weekday) => <option key={name} value={weekday}>{name}</option>)}</select></label>}{input('startTime', 'Beginn', 'time')}{input('endTime', 'Ende', 'time')}</>}
    {missingLecturers && <p role="alert" className="inline-error">Es ist keine {term('lecturer.singular')} verfügbar. Legen Sie die benötigte Ressource an, bevor Sie eine {term('course.singular')} erstellen.</p>}
    {missingRooms && <p role="alert" className="inline-error">Es ist kein {term('room.singular')} verfügbar. Legen Sie die benötigte Ressource an, bevor Sie eine {term('course.singular')} erstellen.</p>}
    <ActionableProblemList problems={problems} className="catalog-editor-problems" />
    <button type="submit" disabled={submitting || missingLecturers || missingRooms}>{submitLabel}</button>
  </form>
}
