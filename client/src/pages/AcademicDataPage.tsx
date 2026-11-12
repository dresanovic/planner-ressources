import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import {
  createCohort, createCourse, createSemester, createCohortCalendar, createTimeWindow,
  deleteAcademicRecord, setAcademicLifecycle,
  listCohorts, listCourses, listSemesters, listCohortCalendars, listTimeWindows,
  updateCohort, updateCourse, updateSemester, updateCohortCalendar, updateTimeWindow,
  type CatalogAudit, type CatalogPage, type UsageSummary,
} from '../api/academicCatalog'
import { getPlanningOptions } from '../api/planningOptions'
import {
  createLecturer, createRoom, getResourceUsage, listLecturers, listRooms,
  reactivateResource, removeResource, updateLecturer, updateRoom,
  createUnavailability, deleteUnavailability, listUnavailability, updateUnavailability,
  getCourseResourceConfiguration, updateCourseResourceEligibility,
  type LecturerInput, type ResourceRecord, type ResourceType, type ResourceUsageAssessment, type RoomInput,
  type UnavailabilityInput, type UnavailabilityPeriod,
  type CourseResourceConfiguration, type CourseResourceEligibilityUpdate,
} from '../api/resourceCatalog'
import { AcademicCatalogList } from '../components/AcademicCatalogList'
import { AcademicRecordEditor, type AcademicCategory, type AcademicEditorValues } from '../components/AcademicRecordEditor'
import { ProtectedDeleteDialog } from '../components/ProtectedDeleteDialog'
import { ResourceCatalogList } from '../components/ResourceCatalogList'
import { ResourceEditor } from '../components/ResourceEditor'
import { ResourceRemovalDialog } from '../components/ResourceRemovalDialog'
import { ResourceAvailabilityEditor } from '../components/ResourceAvailabilityEditor'
import { CourseResourceEligibilityEditor } from '../components/CourseResourceEligibilityEditor'
import { ACADEMIC_DATA_CATEGORIES, type AcademicDataCategory } from '../components/ApplicationNavigation'
import { WEEKDAY_NAMES } from '../utils/weekdays'
import { HolidayAdministration } from '../components/HolidayAdministration'
import { label } from '../config/terminology'

type PageCategory = AcademicDataCategory
const categories: ReadonlyArray<{ id: PageCategory; label: string; singular: string }> = ACADEMIC_DATA_CATEGORIES
type DisplayRecord = CatalogAudit & { id: number; name: string; usage: UsageSummary; [key: string]: unknown }
type Option = { id: number; name: string }
type Options = { semesters: Option[]; cohorts: Option[]; cohortCalendars: Option[]; lecturers: Option[]; rooms: Option[] }
const emptyOptions: Options = { semesters: [], cohorts: [], cohortCalendars: [], lecturers: [], rooms: [] }
export type CourseListFilters = { semesterId: number | null; cohortId: number | null }
const unfilteredCourses: CourseListFilters = { semesterId: null, cohortId: null }

type CatalogStatus = 'all' | 'active' | 'inactive'

async function loadAllPages<T>(request: (page: number, pageSize: number) => Promise<CatalogPage<T>>): Promise<T[]> {
  const pageSize = 200
  const first = await request(1, pageSize)
  const items = [...first.items]
  for (let page = 2; items.length < first.total; page += 1) {
    const next = await request(page, pageSize)
    items.push(...next.items)
    if (next.items.length === 0) break
  }
  return items
}

async function loadAllResourcePages<T>(request: (page: number, pageSize: number) => Promise<CatalogPage<T>>): Promise<T[]> {
  return loadAllPages(request)
}

export function AcademicDataPage({ category, onCatalogChanged, courseFilters = unfilteredCourses, onCourseFiltersChange }: { category: AcademicDataCategory; onCatalogChanged: () => void; courseFilters?: CourseListFilters; onCourseFiltersChange?: (filters: CourseListFilters) => void }) {
  const [records, setRecords] = useState<DisplayRecord[]>([])
  const [options, setOptions] = useState<Options>(emptyOptions)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [loadFailed, setLoadFailed] = useState(false)
  const courseFilterRef = useRef<HTMLSelectElement>(null)
  const focusedCourseAction = useRef<HTMLElement | null>(null)
  useLayoutEffect(() => {
    if (focusedCourseAction.current && !focusedCourseAction.current.isConnected && document.activeElement === document.body) { courseFilterRef.current?.focus(); focusedCourseAction.current = null }
  })
  const [status, setStatus] = useState<CatalogStatus>('all')
  const [resourceStatus, setResourceStatus] = useState<CatalogStatus>('active')
  const [selected, setSelected] = useState<DisplayRecord | null>(null)
  const [copyValues, setCopyValues] = useState<AcademicEditorValues | null>(null)
  const editorOrigin = useRef<HTMLElement | null>(null)
  const [deleting, setDeleting] = useState<DisplayRecord | null>(null)
  const [editorGeneration, setEditorGeneration] = useState(0)
  const [resourceRecords, setResourceRecords] = useState<ResourceRecord[]>([])
  const [selectedResource, setSelectedResource] = useState<ResourceRecord | null>(null)
  const [resourceQuery, setResourceQuery] = useState('')
  const [removingResource, setRemovingResource] = useState<{ record: ResourceRecord; assessment: ResourceUsageAssessment } | null>(null)
  const [availabilityPeriods, setAvailabilityPeriods] = useState<UnavailabilityPeriod[]>([])
  const [courseResources, setCourseResources] = useState<CourseResourceConfiguration | null>(null)
  const eligibilityRequestId = useRef(0)
  const availabilityRequestId = useRef(0)
  const selectedResourceKey = useRef('')
  const [renderedCategory, setRenderedCategory] = useState(category)
  const catalogLoadEpoch = useRef(0)

  const load = useCallback(async (selected: PageCategory) => {
    const epoch = ++catalogLoadEpoch.current
    const publishRecords = (value: DisplayRecord[]) => { if (catalogLoadEpoch.current === epoch) setRecords(value) }
    const publishResources = (value: ResourceRecord[]) => { if (catalogLoadEpoch.current === epoch) setResourceRecords(value) }
    const publishOptions = (value: Options) => { if (catalogLoadEpoch.current === epoch) setOptions(value) }
    setLoading(true)
    setLoadFailed(false)
    try {
      if (selected === 'lecturers') {
        publishResources(await loadAllResourcePages((page, pageSize) => listLecturers({ status: resourceStatus, query: resourceQuery, page, pageSize })))
        return
      }
      if (selected === 'rooms') {
        publishResources(await loadAllResourcePages((page, pageSize) => listRooms({ status: resourceStatus, query: resourceQuery, page, pageSize })))
        return
      }
      if (selected === 'semesters') publishRecords(await loadAllPages((page, pageSize) => listSemesters(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'cohorts') publishRecords(await loadAllPages((page, pageSize) => listCohorts(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'courses') publishRecords(await loadAllPages((page, pageSize) => listCourses(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'cohort-calendars') publishRecords(await loadAllPages((page, pageSize) => listCohortCalendars(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'time-windows') {
        const types = await loadAllPages((page, pageSize) => listCohortCalendars('all', page, pageSize))
        const typeNames = new Map(types.map((type) => [type.id, type.name]))
        const windows = (await Promise.all(types.map((type) => listTimeWindows(type.id)))).flat()
          .filter((window) => status === 'all' || window.isActive === (status === 'active'))
          .sort((left, right) => Number(left.kind === 'dated') - Number(right.kind === 'dated') || (left.kind === 'dated' ? left.date : String(left.weekday)).localeCompare(right.kind === 'dated' ? right.date : String(right.weekday)) || left.startTime.localeCompare(right.startTime) || left.endTime.localeCompare(right.endTime) || (typeNames.get(left.cohortCalendarId) ?? '').localeCompare(typeNames.get(right.cohortCalendarId) ?? '') || left.sortOrder - right.sortOrder || left.id - right.id)
        publishRecords(windows.map((window) => ({ ...window, name: `${typeNames.get(window.cohortCalendarId) ?? 'Unbekannte Kohortenkalender'} · ${window.kind === 'dated' ? `Einmalig: ${window.date.split('-').reverse().join('.')} · ${window.isIntensive ? 'Intensivwoche' : 'Nicht intensiv'}` : `Wöchentlich: ${WEEKDAY_NAMES[window.weekday] ?? 'Unbekannter Wochentag'}`}, ${window.startTime}–${window.endTime}` })))
      }
      if (selected === 'courses' || selected === 'time-windows' || selected === 'cohort-calendars') {
        const [semesters, cohorts, cohortCalendars, planning] = await Promise.all([
          loadAllPages((page, pageSize) => listSemesters('all', page, pageSize)),
          loadAllPages((page, pageSize) => listCohorts('all', page, pageSize)),
          loadAllPages((page, pageSize) => listCohortCalendars('all', page, pageSize)),
          getPlanningOptions(),
        ])
        publishOptions({
          semesters,
          cohorts,
          cohortCalendars: cohortCalendars.filter((type) => type.isActive),
          lecturers: planning.lecturers.filter((resource) => resource.isActive),
          rooms: planning.rooms.filter((resource) => resource.isActive),
        })
      }
    } catch (error) { if (catalogLoadEpoch.current === epoch) setLoadFailed(true); throw error } finally { if (catalogLoadEpoch.current === epoch) setLoading(false) }
  }, [resourceQuery, resourceStatus, status])

  if (renderedCategory !== category) {
    setRenderedCategory(category)
    setCopyValues(null)
    setSelected(null)
    setSelectedResource(null)
    setAvailabilityPeriods([])
    setCourseResources(null)
    setMessage('')
  }

  useLayoutEffect(() => {
    eligibilityRequestId.current += 1
    availabilityRequestId.current += 1
    selectedResourceKey.current = ''
  }, [category])

  useEffect(() => {
    let current = true
    void (async () => { try { await load(category) } catch { if (current) setMessage('Die akademischen Stammdaten konnten nicht geladen werden. Prüfen Sie die Verbindung und laden Sie die Seite erneut.') } })()
    return () => { current = false }
  }, [category, load])

  async function refreshAcknowledgedMutation(success: string) {
    setMessage(success)
    try { await load(category) }
    catch { setMessage(`${success} Die Liste ist nicht aktuell und konnte nicht neu geladen werden. Wählen Sie „Liste erneut laden“.`) }
  }

  async function create(value: AcademicEditorValues) {
    if (category === 'semesters') await createSemester(value as { name: string; startDate: string; endDate: string })
    if (category === 'cohorts') await createCohort(value as { name: string; studentCount: number })
    if (category === 'cohort-calendars') await createCohortCalendar(value as Parameters<typeof createCohortCalendar>[0])
    if (category === 'courses') await createCourse(value as Parameters<typeof createCourse>[0])
    if (category === 'time-windows') {
      const { cohortCalendarId, ...window } = value
      await createTimeWindow(Number(cohortCalendarId), window as Parameters<typeof createTimeWindow>[1])
    }
    onCatalogChanged()
    setCopyValues(null)
    setEditorGeneration((value) => value + 1)
    await refreshAcknowledgedMutation(`${categories.find((item) => item.id === category)?.singular ?? 'Datensatz'} erstellt.`)
  }

  async function save(value: AcademicEditorValues) {
    if (!selected) return create(value)
    const expectedRevision = selected.revision
    let outcomeMessage = `${current.singular} aktualisiert.`
    if (category === 'semesters') await updateSemester(selected.id, { ...(value as { name: string; startDate: string; endDate: string }), expectedRevision })
    if (category === 'cohorts') {
      const result = await updateCohort(selected.id, { ...(value as { name: string; studentCount: number }), expectedRevision })
      const removed = result?.capacityImpact?.removedRelationships ?? []
      const unavailableCourses = result?.capacityImpact?.coursesWithoutRooms ?? []
      if (removed.length > 0) {
        const unavailable = unavailableCourses.length > 0
          ? ` ${label('course.plural')} ohne geeigneten nutzbaren ${label('room.singular')}: ${unavailableCourses.map((course) => course.name).join(', ')}.`
          : ''
        outcomeMessage = `${current.singular} aktualisiert. ${removed.length} wegen zu geringer Kapazität ungültige Raumzuordnung${removed.length === 1 ? '' : 'en'} entfernt.${unavailable}`
      }
    }
    if (category === 'cohort-calendars') await updateCohortCalendar(selected.id, { ...(value as Parameters<typeof createCohortCalendar>[0]), expectedRevision })
    if (category === 'courses') await updateCourse(selected.id, { ...(value as Omit<Parameters<typeof createCourse>[0], 'lecturerId' | 'roomId'>), expectedRevision })
    if (category === 'time-windows') await updateTimeWindow(selected.id, { ...(value as Parameters<typeof createTimeWindow>[1]), expectedRevision })
    onCatalogChanged(); setSelected(null); await refreshAcknowledgedMutation(outcomeMessage)
  }

  async function lifecycle(record: DisplayRecord): Promise<boolean> {
    try {
      await setAcademicLifecycle(category, record.id, record.isActive ? 'archive' : 'reactivate', record.revision)
      onCatalogChanged(); await refreshAcknowledgedMutation(record.isActive ? 'Datensatz archiviert.' : 'Datensatz reaktiviert.')
      return true
    } catch {
      setMessage(`Der Status von „${record.name}“ konnte nicht geändert werden. Laden Sie den aktuellen Stand neu und versuchen Sie es danach erneut.`)
      return false
    }
  }

  async function remove(record: DisplayRecord) {
    try {
      await deleteAcademicRecord(category, record.id, record.revision)
      onCatalogChanged(); setDeleting(null); await refreshAcknowledgedMutation('Datensatz dauerhaft gelöscht.')
    } catch {
      setMessage(`„${record.name}“ konnte nicht gelöscht werden. Prüfen Sie, ob der Datensatz noch verwendet wird, und laden Sie den aktuellen Stand neu.`)
    }
  }

  async function refreshResources() {
    try {
      await load(category)
      setMessage('Ressourcen aktualisiert.')
    } catch {
      setMessage('Die Ressourcen konnten nicht aktualisiert werden. Die ausgewählte Ressource und der zuletzt bekannte Inhalt bleiben erhalten.')
    }
  }

  async function selectResource(record: ResourceRecord) {
    setSelectedResource(record)
    if (category !== 'lecturers' && category !== 'rooms') return
    const key = `${category}:${record.id}`
    const requestId = ++availabilityRequestId.current
    selectedResourceKey.current = key
    setAvailabilityPeriods([])
    try {
      const periods = await listUnavailability(category, record.id)
      if (availabilityRequestId.current === requestId && selectedResourceKey.current === key) setAvailabilityPeriods(periods)
    } catch {
      if (availabilityRequestId.current === requestId && selectedResourceKey.current === key) setMessage('Die Ressourcenverfügbarkeit konnte nicht aktualisiert werden. Die ausgewählte Ressource bleibt erhalten.')
    }
  }

  async function refreshAvailability(resourceType: ResourceType, resourceId: number) {
    const key = `${resourceType}:${resourceId}`
    const requestId = ++availabilityRequestId.current
    const periods = await listUnavailability(resourceType, resourceId)
    if (availabilityRequestId.current !== requestId || selectedResourceKey.current !== key) return false
    setAvailabilityPeriods(periods)
    return true
  }

  function clearSelectedResource() {
    availabilityRequestId.current += 1
    selectedResourceKey.current = ''
    setSelectedResource(null)
    setAvailabilityPeriods([])
  }

  async function addUnavailablePeriod(input: UnavailabilityInput) {
    if (!selectedResource || (category !== 'lecturers' && category !== 'rooms')) return
    const resourceType = category
    const resourceId = selectedResource.id
    await createUnavailability(resourceType, resourceId, input)
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Nichtverfügbarkeitszeitraum hinzugefügt.')
  }

  async function changeUnavailablePeriod(periodId: number, input: UnavailabilityInput & { expectedRevision: number }) {
    if (!selectedResource || (category !== 'lecturers' && category !== 'rooms')) return
    const resourceType = category
    const resourceId = selectedResource.id
    await updateUnavailability(resourceType, resourceId, periodId, input)
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Nichtverfügbarkeitszeitraum aktualisiert.')
  }

  async function removeUnavailablePeriod(period: UnavailabilityPeriod) {
    if (!selectedResource || (category !== 'lecturers' && category !== 'rooms')) return
    const resourceType = category
    const resourceId = selectedResource.id
    await deleteUnavailability(resourceType, resourceId, period.id, period.revision)
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Nichtverfügbarkeitszeitraum gelöscht.')
  }

  async function saveResource(input: LecturerInput | RoomInput) {
    if (category !== 'lecturers' && category !== 'rooms') return
    if (selectedResource) {
      if (category === 'lecturers') await updateLecturer(selectedResource.id, { ...(input as LecturerInput), expectedRevision: selectedResource.revision })
      else await updateRoom(selectedResource.id, { ...(input as RoomInput), expectedRevision: selectedResource.revision })
    } else if (category === 'lecturers') await createLecturer(input as LecturerInput)
    else await createRoom(input as RoomInput)
    clearSelectedResource()
    try {
      await load(category)
      setMessage(`${label(category === 'lecturers' ? 'lecturer.singular' : 'room.singular')} gespeichert.`)
    } catch {
      setMessage('Die Ressource wurde gespeichert, aber die Liste konnte nicht aktualisiert werden. Der zuletzt bekannte Inhalt bleibt sichtbar.')
    }
    onCatalogChanged()
  }

  async function prepareResourceRemoval(record: ResourceRecord) {
    if (category !== 'lecturers' && category !== 'rooms') return
    try {
      setRemovingResource({ record, assessment: await getResourceUsage(category, record.id) })
    } catch {
      setMessage(`Die Verwendung von „${record.name}“ konnte nicht geprüft werden. Laden Sie die Ressourcen neu und versuchen Sie es erneut.`)
    }
  }

  async function confirmResourceRemoval() {
    if (!removingResource || (category !== 'lecturers' && category !== 'rooms')) return
    try {
      const result = await removeResource(category, removingResource.record.id, removingResource.assessment.revision)
      setRemovingResource(null)
      clearSelectedResource()
      if (result.outcome === 'deleted') {
        const cleaned = result.removedInactiveCourseLinks.length
        setMessage(`Ressource dauerhaft gelöscht${cleaned ? `; ${cleaned} ${cleaned === 1 ? `inaktive Zuordnung zu einer ${label('course.singular')} entfernt` : `inaktive Zuordnungen zu ${label('course.plural')} entfernt`}` : ''}.`)
      } else {
        const courses = result.activeCourses.map((course) => course.name).join(', ')
        const courseReason = result.activeCourses.length > 0
          ? `${result.activeCourses.length} aktive ${result.activeCourses.length === 1 ? label('course.singular') : label('course.plural')}${courses ? `: ${courses}` : ''}`
          : ''
        const sessionReason = result.sessionUsage.draftSessionCount > 0
          ? `${result.sessionUsage.draftSessionCount} gespeicherte Termine in ${result.sessionUsage.draftScheduleCount} ${result.sessionUsage.draftScheduleCount === 1 ? 'Planung' : 'Planungen'}`
          : ''
        setMessage(`Ressource inaktiv gesetzt, weil sie noch verwendet wird: ${[courseReason, sessionReason].filter(Boolean).join('; ')}.`)
      }
      await load(category)
      onCatalogChanged()
    } catch {
      setMessage(`„${removingResource.record.name}“ konnte nicht entfernt werden. Laden Sie den aktuellen Stand neu und prüfen Sie die bestehenden Zuordnungen.`)
    }
  }

  async function reactivate(record: ResourceRecord) {
    if (category !== 'lecturers' && category !== 'rooms') return
    try {
      const result = await reactivateResource(category, record.id, record.revision)
      const unusable = result.unusableRelationships.length
      setMessage(`Ressource reaktiviert${unusable ? `; ${unusable} ${unusable === 1 ? 'Zuordnung bleibt' : 'Zuordnungen bleiben'} nicht nutzbar` : ''}.`)
      await load(category)
      onCatalogChanged()
    } catch {
      setMessage(`„${record.name}“ konnte nicht reaktiviert werden. Laden Sie den aktuellen Stand neu und prüfen Sie den Datensatz.`)
    }
  }

  async function selectAcademicRecord(record: DisplayRecord) {
    editorOrigin.current = document.activeElement as HTMLElement
    setCopyValues(null)
    setSelected(record)
    if (category !== 'courses') return
    const requestId = ++eligibilityRequestId.current
    setCourseResources((current) => current?.courseId === record.id ? current : null)
    try {
      const configuration = await getCourseResourceConfiguration(record.id)
      if (eligibilityRequestId.current === requestId) setCourseResources(configuration)
    } catch {
      if (eligibilityRequestId.current === requestId) setMessage(`Die Ressourceneignung für die ausgewählte ${label('course.singular')} konnte nicht aktualisiert werden. Auswahl und Kontrollkästchen bleiben erhalten.`)
    }
  }

  async function saveCourseResources(input: CourseResourceEligibilityUpdate) {
    if (!selected || courseResources?.courseId !== selected.id) return
    const courseId = selected.id
    const requestId = eligibilityRequestId.current
    const saved = await updateCourseResourceEligibility(courseId, input)
    onCatalogChanged()
    if (eligibilityRequestId.current !== requestId) return
    setCourseResources((current) => current?.courseId === courseId ? saved : current)
    setSelected((current) => current?.id === courseId ? { ...current, revision: saved.courseRevision } : current)
    setMessage(`Ressourceneignung für ${label('course.singular')} gespeichert.`)
  }

  function copyWindow(record: DisplayRecord, origin: HTMLButtonElement) {
    editorOrigin.current = origin
    setSelected(null)
    setCopyValues(editValues(record))
    setEditorGeneration(value=>value+1)
  }

  function cancelAcademicEditor() {
    setSelected(null);setCopyValues(null)
    queueMicrotask(() => {
      const origin=editorOrigin.current
      if (origin?.isConnected) origin.focus()
      else document.getElementById('academic-list-heading')?.focus()
    })
  }

  function editValues(record: DisplayRecord): AcademicEditorValues {
    if (category === 'semesters') return { name: record.name, startDate: record.startDate as string, endDate: record.endDate as string }
    if (category === 'cohorts') return { name: record.name, studentCount: record.studentCount as number }
    if (category === 'cohort-calendars') return { cohortId: record.cohortId as number, semesterId: record.semesterId as number, startDate: record.startDate as string, endDate: record.endDate as string }
    if (category === 'courses') return { name: record.name, totalUnits: record.totalUnits as number, overallUnits: (record.overallUnits ?? record.totalUnits) as number, minSessionUnits: record.minSessionUnits as number, maxSessionUnits: record.maxSessionUnits as number, preferredSessionUnits: (record.preferredSessionUnits as number | null) ?? '', semesterId: (record.semester as Option | null)?.id ?? '', cohortId: (record.cohort as Option).id }
    return { kind: (record.kind as string) ?? 'weekly', date: (record.date as string) ?? '', isIntensive: Boolean(record.isIntensive), sortOrder: (record.sortOrder as number) ?? 0, cohortCalendarId: record.cohortCalendarId as number, weekday: record.weekday as number | null, startTime: record.startTime as string, endTime: record.endTime as string }
  }

  const semesterRecords = records.filter((record) => courseFilters.semesterId == null || (record.semester as Option | null)?.id === courseFilters.semesterId)
  const visibleRecords = category === 'courses' ? semesterRecords.filter((record) => courseFilters.cohortId == null || (record.cohort as Option | null)?.id === courseFilters.cohortId) : records
  const semesterContext = courseFilters.semesterId == null ? 'Alle Semester' : options.semesters.find((item) => item.id === courseFilters.semesterId)?.name ?? `Semester #${courseFilters.semesterId} — nicht verfügbar`
  const cohortContext = courseFilters.cohortId == null ? 'Alle Kohorten' : options.cohorts.find((item) => item.id === courseFilters.cohortId)?.name ?? `Kohorte #${courseFilters.cohortId} — nicht verfügbar`
  const current = categories.find((item) => item.id === category)!
  if (category === 'holidays') return <HolidayAdministration onChanged={onCatalogChanged} />
  if (category === 'lecturers' || category === 'rooms') return <>
    <section className="workbench">
      <header className="page-header"><div><p className="eyebrow">Planungsverwaltung</p><h1>{label('academicData.heading')}</h1></div><label className="catalog-field">Anzeigen<select value={resourceStatus} onChange={(event) => setResourceStatus(event.target.value as typeof resourceStatus)}><option value="all">Alle Datensätze</option><option value="active">Aktiv</option><option value="inactive">Inaktiv</option></select></label></header>
      {message && <p role="status">{message}</p>}
      <div className="resource-toolbar"><label className="catalog-field">Nach Name oder Code suchen<input type="search" value={resourceQuery} onChange={(event) => setResourceQuery(event.target.value)} /></label><button type="button" className="secondary-button" onClick={() => void refreshResources()}>Aktualisieren</button></div>
      <div className="catalog-grid">
        <section className="planner-panel"><h2 id="academic-list-heading" tabIndex={-1}>{current.label}</h2>{loading ? <p>Wird geladen…</p> : <ResourceCatalogList resourceType={category} records={resourceRecords} onSelect={(record) => void selectResource(record)} onRemove={(record) => void prepareResourceRemoval(record)} onReactivate={(record) => void reactivate(record)} />}</section>
        <section className="planner-panel"><h2>{selectedResource ? 'Bearbeiten:' : 'Erstellen:'} {current.singular}</h2><ResourceEditor key={`${category}-${selectedResource?.id ?? 'new'}-${selectedResource?.revision ?? 0}`} resourceType={category} initial={selectedResource} onSubmit={saveResource} onCancel={clearSelectedResource} />{selectedResource && <ResourceAvailabilityEditor periods={availabilityPeriods} onCreate={addUnavailablePeriod} onUpdate={changeUnavailablePeriod} onDelete={removeUnavailablePeriod} />}</section>
      </div>
    </section>
    {removingResource && <ResourceRemovalDialog resourceName={`${removingResource.record.name} · ${removingResource.record.referenceCode}`} assessment={removingResource.assessment} onClose={() => setRemovingResource(null)} onConfirm={() => void confirmResourceRemoval()} />}
  </>
  return <><section className="workbench"><header className="page-header"><div><p className="eyebrow">Planungsverwaltung</p><h1>{label('academicData.heading')}</h1></div><label className="catalog-field">Anzeigen<select value={status} onChange={(event) => setStatus(event.target.value as typeof status)}><option value="all">Alle Datensätze</option><option value="active">Aktiv</option><option value="inactive">Inaktiv</option></select></label></header>{message && <p role="status">{message}</p>}{loadFailed && <p role="alert">Die Liste ist nicht aktuell. <button type="button" onClick={() => void load(category).then(() => setMessage('Liste aktualisiert.')).catch(() => setMessage('Die Liste konnte nicht neu geladen werden. Prüfen Sie die Verbindung.'))}>Liste erneut laden</button></p>}{category === 'courses' && <div className="course-list-filters">
    <label>Semester filtern<select aria-label="Semester filtern" value={courseFilters.semesterId ?? ''} onChange={(event) => onCourseFiltersChange?.({ semesterId: event.target.value === '' ? null : Number(event.target.value), cohortId: null })}>
      <option value="">Alle Semester</option>
      {courseFilters.semesterId != null && !options.semesters.some((item) => item.id === courseFilters.semesterId) && <option value={courseFilters.semesterId}>{semesterContext}</option>}
      {options.semesters.map((item) => <option key={item.id} value={item.id}>{item.name}</option>)}
    </select></label>
    <label>Kohorte filtern<select ref={courseFilterRef} aria-label="Kohorte filtern" value={courseFilters.cohortId ?? ''} onChange={(event) => onCourseFiltersChange?.({ ...courseFilters, cohortId: event.target.value === '' ? null : Number(event.target.value) })}>
      <option value="">Alle Kohorten</option>
      {courseFilters.cohortId != null && !options.cohorts.some((item) => item.id === courseFilters.cohortId) && <option value={courseFilters.cohortId}>{cohortContext}</option>}
      {options.cohorts.map((item) => <option key={item.id} value={item.id}>{item.name} · #{item.id}</option>)}
    </select></label>
    <button type="button" className="secondary-button" onClick={() => onCourseFiltersChange?.({ ...courseFilters, cohortId: null })}>Kohortenfilter zurücksetzen</button>
    <p role="status">{semesterContext} · {cohortContext} · {loading ? 'Wird geladen…' : loadFailed ? 'Stammdaten konnten nicht geladen werden. Laden Sie die Seite erneut.' : `${visibleRecords.length} Treffer`}</p>
  </div>}<div className={category === 'courses' ? 'catalog-grid course-catalog-grid' : 'catalog-grid'} onFocusCapture={(event) => { focusedCourseAction.current = category === 'courses' && event.target.closest('.catalog-list') ? event.target as HTMLElement : null }}><section className="planner-panel"><h2 id="academic-list-heading" tabIndex={-1}>{current.label}</h2>{loading ? <p>Wird geladen…</p> : loadFailed && category === 'courses' ? <p role="alert">Stammdaten konnten nicht geladen werden. Laden Sie die Seite erneut.</p> : <AcademicCatalogList onCopy={category === 'time-windows' ? (record,origin)=>copyWindow(record as DisplayRecord,origin) : undefined} groupBy={category === 'time-windows' ? (record) => (record as DisplayRecord).kind === 'dated' ? 'Einmalige Datumsfenster' : 'Wöchentliche Zeitfenster' : undefined} records={visibleRecords} renderMetadata={category === 'courses' ? (record) => {
    const course = record as DisplayRecord
    return <small className="course-record-metadata">{(course.cohort as Option | null)?.name ?? 'Keine Kohorte'} · {(course.semester as Option | null)?.name ?? 'Ohne Semester'} · #{course.id}</small>
  } : category === 'time-windows' ? (record) => <small className="window-overlap-note">{(record as DisplayRecord).overlapNotice as string | null}</small> : undefined} emptyLabel={category === 'courses' ? (semesterRecords.length === 0 ? 'Keine Lehrveranstaltungen in diesem Semester / Status.' : 'Keine Treffer. Setzen Sie den Kohortenfilter zurück.') : `Noch keine ${current.label}`} onEdit={(record) => void selectAcademicRecord(record as DisplayRecord)} onDelete={(record) => setDeleting(record as DisplayRecord)} onLifecycle={(record) => void lifecycle(record as DisplayRecord)} />}</section><section className="planner-panel"><h2>{copyValues ? 'Ungespeicherte Kopie:' : selected ? 'Bearbeiten:' : 'Erstellen:'} {current.singular}</h2>{selected?.nameRepairRequired === true && <p role="alert">Dieser übernommene Name steht im Konflikt mit einem anderen Datensatz. Geben Sie einen eindeutigen Namen ein.</p>}{category === 'courses' && selected && selected.semester == null && <p role="alert">Ordnen Sie vor dem Speichern dieser {label('course.singular')} ein Semester zu.</p>}<AcademicRecordEditor key={`${category}-${selected?.id ?? 'new'}-${selected?.revision ?? 0}-${editorGeneration}`} category={category as AcademicCategory} options={options} initialValues={selected ? editValues(selected) : copyValues ?? {}} submitLabel={selected ? 'Änderungen speichern' : copyValues ? 'Kopie speichern' : 'Erstellen'} includeCourseResources={!selected} lockKind={Boolean(selected || copyValues)} onSubmit={save} />{(selected || copyValues) && <button type="button" className="secondary-button" onClick={cancelAcademicEditor}>{copyValues ? 'Kopie verwerfen' : 'Bearbeitung abbrechen'}</button>}{category === 'courses' && selected && courseResources?.courseId === selected.id && <CourseResourceEligibilityEditor key={`${courseResources.courseId}-${courseResources.courseRevision}`} configuration={courseResources} onSave={saveCourseResources} onCancel={() => void selectAcademicRecord(selected)} />}</section></div></section>{deleting && <ProtectedDeleteDialog name={deleting.name} usage={deleting.usage} canArchive={deleting.isActive} onClose={() => setDeleting(null)} onArchive={() => void lifecycle(deleting).then((changed) => { if (changed) setDeleting(null) })} onDelete={() => void remove(deleting)} />}</>
}
