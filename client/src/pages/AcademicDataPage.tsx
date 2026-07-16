import { useCallback, useEffect, useLayoutEffect, useRef, useState } from 'react'
import {
  createCohort, createCourse, createSemester, createStudyType, createTimeWindow,
  deleteAcademicRecord, setAcademicLifecycle,
  listCohorts, listCourses, listSemesters, listStudyTypes, listTimeWindows,
  updateCohort, updateCourse, updateSemester, updateStudyType, updateTimeWindow,
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
import { AcademicRecordEditor, type AcademicCategory } from '../components/AcademicRecordEditor'
import { ProtectedDeleteDialog } from '../components/ProtectedDeleteDialog'
import { ResourceCatalogList } from '../components/ResourceCatalogList'
import { ResourceEditor } from '../components/ResourceEditor'
import { ResourceRemovalDialog } from '../components/ResourceRemovalDialog'
import { ResourceAvailabilityEditor } from '../components/ResourceAvailabilityEditor'
import { CourseResourceEligibilityEditor } from '../components/CourseResourceEligibilityEditor'
import { ACADEMIC_DATA_CATEGORIES, type AcademicDataCategory } from '../components/ApplicationNavigation'
import { WEEKDAY_NAMES } from '../utils/weekdays'

type PageCategory = AcademicDataCategory
const categories: ReadonlyArray<{ id: PageCategory; label: string; singular: string }> = ACADEMIC_DATA_CATEGORIES
type DisplayRecord = CatalogAudit & { id: number; name: string; usage: UsageSummary; [key: string]: unknown }
type Option = { id: number; name: string }
type Options = { semesters: Option[]; cohorts: Option[]; studyTypes: Option[]; lecturers: Option[]; rooms: Option[] }
const emptyOptions: Options = { semesters: [], cohorts: [], studyTypes: [], lecturers: [], rooms: [] }
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

export function AcademicDataPage({ category, onCatalogChanged }: { category: AcademicDataCategory; onCatalogChanged: () => void }) {
  const [records, setRecords] = useState<DisplayRecord[]>([])
  const [options, setOptions] = useState<Options>(emptyOptions)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<CatalogStatus>('all')
  const [resourceStatus, setResourceStatus] = useState<CatalogStatus>('active')
  const [selected, setSelected] = useState<DisplayRecord | null>(null)
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

  const load = useCallback(async (selected: PageCategory) => {
    setLoading(true)
    try {
      if (selected === 'lecturers') {
        setResourceRecords(await loadAllResourcePages((page, pageSize) => listLecturers({ status: resourceStatus, query: resourceQuery, page, pageSize })))
        return
      }
      if (selected === 'rooms') {
        setResourceRecords(await loadAllResourcePages((page, pageSize) => listRooms({ status: resourceStatus, query: resourceQuery, page, pageSize })))
        return
      }
      if (selected === 'semesters') setRecords(await loadAllPages((page, pageSize) => listSemesters(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'cohorts') setRecords(await loadAllPages((page, pageSize) => listCohorts(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'courses') setRecords(await loadAllPages((page, pageSize) => listCourses(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'study-types') setRecords(await loadAllPages((page, pageSize) => listStudyTypes(status, page, pageSize)) as DisplayRecord[])
      if (selected === 'time-windows') {
        const types = await loadAllPages((page, pageSize) => listStudyTypes('all', page, pageSize))
        const typeNames = new Map(types.map((type) => [type.id, type.name]))
        const windows = (await Promise.all(types.map((type) => listTimeWindows(type.id)))).flat()
          .filter((window) => status === 'all' || window.isActive === (status === 'active'))
          .sort((left, right) => (typeNames.get(left.studyTypeId) ?? '').localeCompare(typeNames.get(right.studyTypeId) ?? '') || left.weekday - right.weekday || left.startTime.localeCompare(right.startTime))
        setRecords(windows.map((window) => ({ ...window, name: `${typeNames.get(window.studyTypeId) ?? 'Unknown Study Type'} · ${WEEKDAY_NAMES[window.weekday] ?? 'Unknown day'}, ${window.startTime}–${window.endTime}` })))
      }
      if (selected === 'courses' || selected === 'time-windows') {
        const [semesters, cohorts, studyTypes, planning] = await Promise.all([
          loadAllPages((page, pageSize) => listSemesters('all', page, pageSize)),
          loadAllPages((page, pageSize) => listCohorts('all', page, pageSize)),
          loadAllPages((page, pageSize) => listStudyTypes('all', page, pageSize)),
          getPlanningOptions(),
        ])
        setOptions({
          semesters,
          cohorts,
          studyTypes,
          lecturers: planning.lecturers.filter((resource) => resource.isActive),
          rooms: planning.rooms.filter((resource) => resource.isActive),
        })
      }
    } finally { setLoading(false) }
  }, [resourceQuery, resourceStatus, status])

  if (renderedCategory !== category) {
    setRenderedCategory(category)
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
    void (async () => { try { await load(category) } catch { if (current) setMessage('Could not load academic data.') } })()
    return () => { current = false }
  }, [category, load])

  async function create(value: Record<string, string | number>) {
    if (category === 'semesters') await createSemester(value as { name: string; startDate: string; endDate: string })
    if (category === 'cohorts') await createCohort(value as { name: string; studentCount: number })
    if (category === 'study-types') await createStudyType(value as { name: string })
    if (category === 'courses') await createCourse(value as Parameters<typeof createCourse>[0])
    if (category === 'time-windows') {
      const { studyTypeId, ...window } = value
      await createTimeWindow(Number(studyTypeId), window as Parameters<typeof createTimeWindow>[1])
    }
    await load(category)
    setEditorGeneration((value) => value + 1)
    setMessage(`${categories.find((item) => item.id === category)?.singular ?? 'Record'} created.`)
    onCatalogChanged()
  }

  async function save(value: Record<string, string | number>) {
    if (!selected) return create(value)
    const expectedRevision = selected.revision
    let outcomeMessage = `${current.singular} updated.`
    if (category === 'semesters') await updateSemester(selected.id, { ...(value as { name: string; startDate: string; endDate: string }), expectedRevision })
    if (category === 'cohorts') {
      const result = await updateCohort(selected.id, { ...(value as { name: string; studentCount: number }), expectedRevision })
      const removed = result?.capacityImpact?.removedRelationships ?? []
      const unavailableCourses = result?.capacityImpact?.coursesWithoutRooms ?? []
      if (removed.length > 0) {
        const unavailable = unavailableCourses.length > 0
          ? ` Courses without a usable eligible room: ${unavailableCourses.map((course) => course.name).join(', ')}.`
          : ''
        outcomeMessage = `${current.singular} updated. Removed ${removed.length} newly insufficient room relationship${removed.length === 1 ? '' : 's'}.${unavailable}`
      }
    }
    if (category === 'study-types') await updateStudyType(selected.id, { ...(value as { name: string }), expectedRevision })
    if (category === 'courses') await updateCourse(selected.id, { ...(value as Omit<Parameters<typeof createCourse>[0], 'lecturerId' | 'roomId'>), expectedRevision })
    if (category === 'time-windows') await updateTimeWindow(selected.id, { ...(value as Parameters<typeof createTimeWindow>[1]), expectedRevision })
    setSelected(null); await load(category); setMessage(outcomeMessage); onCatalogChanged()
  }

  async function lifecycle(record: DisplayRecord): Promise<boolean> {
    try {
      await setAcademicLifecycle(category, record.id, record.isActive ? 'archive' : 'reactivate', record.revision)
      await load(category); setMessage(record.isActive ? 'Record archived.' : 'Record reactivated.'); onCatalogChanged()
      return true
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Could not change this record status.')
      return false
    }
  }

  async function remove(record: DisplayRecord) {
    try {
      await deleteAcademicRecord(category, record.id, record.revision)
      setDeleting(null); await load(category); setMessage('Record permanently deleted.'); onCatalogChanged()
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Could not delete this record.')
    }
  }

  async function refreshResources() {
    try {
      await load(category)
      setMessage('Resources refreshed.')
    } catch {
      setMessage('Could not refresh resources. The selected resource and last-known content were retained.')
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
      if (availabilityRequestId.current === requestId && selectedResourceKey.current === key) setMessage('Could not refresh resource availability. The selected resource was retained.')
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
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Unavailable period added.')
  }

  async function changeUnavailablePeriod(periodId: number, input: UnavailabilityInput & { expectedRevision: number }) {
    if (!selectedResource || (category !== 'lecturers' && category !== 'rooms')) return
    const resourceType = category
    const resourceId = selectedResource.id
    await updateUnavailability(resourceType, resourceId, periodId, input)
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Unavailable period updated.')
  }

  async function removeUnavailablePeriod(period: UnavailabilityPeriod) {
    if (!selectedResource || (category !== 'lecturers' && category !== 'rooms')) return
    const resourceType = category
    const resourceId = selectedResource.id
    await deleteUnavailability(resourceType, resourceId, period.id, period.revision)
    if (await refreshAvailability(resourceType, resourceId)) setMessage('Unavailable period deleted.')
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
      setMessage(`${category === 'lecturers' ? 'Lecturer' : 'Room'} saved.`)
    } catch {
      setMessage('The resource was saved, but the list could not be refreshed. Last-known content was retained.')
    }
    onCatalogChanged()
  }

  async function prepareResourceRemoval(record: ResourceRecord) {
    if (category !== 'lecturers' && category !== 'rooms') return
    try {
      setRemovingResource({ record, assessment: await getResourceUsage(category, record.id) })
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Could not assess resource usage.')
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
        setMessage(`Resource permanently deleted${cleaned ? `; ${cleaned} inactive course link${cleaned === 1 ? '' : 's'} removed` : ''}.`)
      } else {
        const courses = result.activeCourses.map((course) => course.name).join(', ')
        const courseReason = result.activeCourses.length > 0
          ? `${result.activeCourses.length} active course${result.activeCourses.length === 1 ? '' : 's'}${courses ? `: ${courses}` : ''}`
          : ''
        const sessionReason = result.sessionUsage.draftSessionCount > 0
          ? `${result.sessionUsage.draftSessionCount} saved session${result.sessionUsage.draftSessionCount === 1 ? '' : 's'} across ${result.sessionUsage.draftScheduleCount} schedule${result.sessionUsage.draftScheduleCount === 1 ? '' : 's'}`
          : ''
        setMessage(`Resource placed inactive because it is used by ${[courseReason, sessionReason].filter(Boolean).join(' and ')}.`)
      }
      await load(category)
      onCatalogChanged()
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Could not remove this resource.')
    }
  }

  async function reactivate(record: ResourceRecord) {
    if (category !== 'lecturers' && category !== 'rooms') return
    try {
      const result = await reactivateResource(category, record.id, record.revision)
      const unusable = result.unusableRelationships.length
      setMessage(`Resource reactivated${unusable ? `; ${unusable} relationship${unusable === 1 ? ' remains' : 's remain'} unusable` : ''}.`)
      await load(category)
      onCatalogChanged()
    } catch (reason) {
      setMessage(reason instanceof Error ? reason.message : 'Could not reactivate this resource.')
    }
  }

  async function selectAcademicRecord(record: DisplayRecord) {
    setSelected(record)
    if (category !== 'courses') return
    const requestId = ++eligibilityRequestId.current
    setCourseResources((current) => current?.courseId === record.id ? current : null)
    try {
      const configuration = await getCourseResourceConfiguration(record.id)
      if (eligibilityRequestId.current === requestId) setCourseResources(configuration)
    } catch {
      if (eligibilityRequestId.current === requestId) setMessage('Could not refresh Course eligibility. The selected Course and current checkbox state were retained.')
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
    setMessage('Course resource eligibility saved.')
  }

  function editValues(record: DisplayRecord): Record<string, string | number> {
    if (category === 'semesters') return { name: record.name, startDate: record.startDate as string, endDate: record.endDate as string }
    if (category === 'cohorts') return { name: record.name, studentCount: record.studentCount as number }
    if (category === 'study-types') return { name: record.name }
    if (category === 'courses') return { name: record.name, totalUnits: record.totalUnits as number, minSessionUnits: record.minSessionUnits as number, maxSessionUnits: record.maxSessionUnits as number, semesterId: (record.semester as Option | null)?.id ?? '', cohortId: (record.cohort as Option).id, studyTypeId: (record.studyType as Option).id }
    return { studyTypeId: record.studyTypeId as number, weekday: record.weekday as number, startTime: record.startTime as string, endTime: record.endTime as string }
  }

  const current = categories.find((item) => item.id === category)!
  if (category === 'lecturers' || category === 'rooms') return <>
    <section className="workbench">
      <header className="page-header"><div><p className="eyebrow">Planner administration</p><h1>Academic Data</h1></div><label className="catalog-field">Show<select value={resourceStatus} onChange={(event) => setResourceStatus(event.target.value as typeof resourceStatus)}><option value="all">All records</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label></header>
      {message && <p role="status">{message}</p>}
      <div className="resource-toolbar"><label className="catalog-field">Search by name or code<input type="search" value={resourceQuery} onChange={(event) => setResourceQuery(event.target.value)} /></label><button type="button" className="secondary-button" onClick={() => void refreshResources()}>Refresh</button></div>
      <div className="catalog-grid">
        <section className="planner-panel"><h2>{current.label}</h2>{loading ? <p>Loading…</p> : <ResourceCatalogList resourceType={category} records={resourceRecords} onSelect={(record) => void selectResource(record)} onRemove={(record) => void prepareResourceRemoval(record)} onReactivate={(record) => void reactivate(record)} />}</section>
        <section className="planner-panel"><h2>{selectedResource ? 'Edit' : 'Create'} {current.singular}</h2><ResourceEditor key={`${category}-${selectedResource?.id ?? 'new'}-${selectedResource?.revision ?? 0}`} resourceType={category} initial={selectedResource} onSubmit={saveResource} onCancel={clearSelectedResource} />{selectedResource && <ResourceAvailabilityEditor periods={availabilityPeriods} onCreate={addUnavailablePeriod} onUpdate={changeUnavailablePeriod} onDelete={removeUnavailablePeriod} />}</section>
      </div>
    </section>
    {removingResource && <ResourceRemovalDialog resourceName={`${removingResource.record.name} · ${removingResource.record.referenceCode}`} assessment={removingResource.assessment} onClose={() => setRemovingResource(null)} onConfirm={() => void confirmResourceRemoval()} />}
  </>
  return <><section className="workbench"><header className="page-header"><div><p className="eyebrow">Planner administration</p><h1>Academic Data</h1></div><label className="catalog-field">Show<select value={status} onChange={(event) => setStatus(event.target.value as typeof status)}><option value="all">All records</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label></header>{message && <p role="status">{message}</p>}<div className="catalog-grid"><section className="planner-panel"><h2>{current.label}</h2>{loading ? <p>Loading…</p> : <AcademicCatalogList records={records} emptyLabel={`No ${current.label.toLowerCase()} yet`} onEdit={(record) => void selectAcademicRecord(record as DisplayRecord)} onDelete={(record) => setDeleting(record as DisplayRecord)} onLifecycle={(record) => void lifecycle(record as DisplayRecord)} />}</section><section className="planner-panel"><h2>{selected ? 'Edit' : 'Create'} {current.singular}</h2>{selected?.nameRepairRequired === true && <p role="alert">This legacy name conflicts with another record. Enter a unique name to complete repair.</p>}{category === 'courses' && selected && selected.semester == null && <p role="alert">Assign a Semester to complete repair before saving this Course.</p>}<AcademicRecordEditor key={`${category}-${selected?.id ?? 'new'}-${selected?.revision ?? 0}-${editorGeneration}`} category={category as AcademicCategory} options={options} initialValues={selected ? editValues(selected) : {}} submitLabel={selected ? 'Save changes' : 'Create'} includeCourseResources={!selected} onSubmit={save} />{selected && <button type="button" className="secondary-button" onClick={() => setSelected(null)}>Cancel edit</button>}{category === 'courses' && selected && courseResources?.courseId === selected.id && <CourseResourceEligibilityEditor key={`${courseResources.courseId}-${courseResources.courseRevision}`} configuration={courseResources} onSave={saveCourseResources} onCancel={() => void selectAcademicRecord(selected)} />}</section></div></section>{deleting && <ProtectedDeleteDialog name={deleting.name} usage={deleting.usage} canArchive={deleting.isActive} onClose={() => setDeleting(null)} onArchive={() => void lifecycle(deleting).then((changed) => { if (changed) setDeleting(null) })} onDelete={() => void remove(deleting)} />}</>
}
