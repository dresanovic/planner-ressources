import { useCallback, useEffect, useState } from 'react'
import {
  createCohort, createCourse, createSemester, createStudyType, createTimeWindow,
  deleteAcademicRecord, setAcademicLifecycle,
  listCohorts, listCourses, listSemesters, listStudyTypes, listTimeWindows,
  updateCohort, updateCourse, updateSemester, updateStudyType, updateTimeWindow,
  type CatalogAudit, type CatalogPage, type UsageSummary,
} from '../api/academicCatalog'
import { getPlanningOptions } from '../api/planningOptions'
import { AcademicCatalogList } from '../components/AcademicCatalogList'
import { AcademicRecordEditor, type AcademicCategory } from '../components/AcademicRecordEditor'
import { ProtectedDeleteDialog } from '../components/ProtectedDeleteDialog'
import { WEEKDAY_NAMES } from '../utils/weekdays'

const categories: Array<{ id: AcademicCategory; label: string; singular: string }> = [
  { id: 'semesters', label: 'Semesters', singular: 'semester' },
  { id: 'cohorts', label: 'Cohorts', singular: 'cohort' },
  { id: 'courses', label: 'Courses', singular: 'course' },
  { id: 'study-types', label: 'Study types', singular: 'study type' },
  { id: 'time-windows', label: 'Time windows', singular: 'time window' },
]
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

export function AcademicDataPage({ onCatalogChanged }: { onCatalogChanged: () => void }) {
  const [category, setCategory] = useState<AcademicCategory>('semesters')
  const [records, setRecords] = useState<DisplayRecord[]>([])
  const [options, setOptions] = useState<Options>(emptyOptions)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState('')
  const [status, setStatus] = useState<CatalogStatus>('all')
  const [selected, setSelected] = useState<DisplayRecord | null>(null)
  const [deleting, setDeleting] = useState<DisplayRecord | null>(null)
  const [editorGeneration, setEditorGeneration] = useState(0)

  const load = useCallback(async (selected: AcademicCategory) => {
    setLoading(true)
    try {
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
        setOptions({ semesters, cohorts, studyTypes, lecturers: planning.lecturers, rooms: planning.rooms })
      }
    } finally { setLoading(false) }
  }, [status])

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
    if (category === 'semesters') await updateSemester(selected.id, { ...(value as { name: string; startDate: string; endDate: string }), expectedRevision })
    if (category === 'cohorts') await updateCohort(selected.id, { ...(value as { name: string; studentCount: number }), expectedRevision })
    if (category === 'study-types') await updateStudyType(selected.id, { ...(value as { name: string }), expectedRevision })
    if (category === 'courses') await updateCourse(selected.id, { ...(value as Parameters<typeof createCourse>[0]), expectedRevision })
    if (category === 'time-windows') await updateTimeWindow(selected.id, { ...(value as Parameters<typeof createTimeWindow>[1]), expectedRevision })
    setSelected(null); await load(category); setMessage(`${current.singular} updated.`); onCatalogChanged()
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

  function editValues(record: DisplayRecord): Record<string, string | number> {
    if (category === 'semesters') return { name: record.name, startDate: record.startDate as string, endDate: record.endDate as string }
    if (category === 'cohorts') return { name: record.name, studentCount: record.studentCount as number }
    if (category === 'study-types') return { name: record.name }
    if (category === 'courses') return { name: record.name, totalUnits: record.totalUnits as number, minSessionUnits: record.minSessionUnits as number, maxSessionUnits: record.maxSessionUnits as number, semesterId: (record.semester as Option | null)?.id ?? '', cohortId: (record.cohort as Option).id, studyTypeId: (record.studyType as Option).id, lecturerId: (record.lecturer as Option).id, roomId: (record.room as Option).id }
    return { studyTypeId: record.studyTypeId as number, weekday: record.weekday as number, startTime: record.startTime as string, endTime: record.endTime as string }
  }

  const current = categories.find((item) => item.id === category)!
  return <main className="planner-shell"><aside className="sidebar"><div className="brand-mark">RP</div><nav aria-label="Academic categories">{categories.map((item) => <button className={category === item.id ? 'active' : ''} key={item.id} onClick={() => { setCategory(item.id); setSelected(null) }}>{item.label}</button>)}</nav></aside><section className="workbench"><header className="page-header"><div><p className="eyebrow">Planner administration</p><h1>Academic Data</h1></div><label className="catalog-field">Show<select value={status} onChange={(event) => setStatus(event.target.value as typeof status)}><option value="all">All records</option><option value="active">Active</option><option value="inactive">Inactive</option></select></label></header>{message && <p role="status">{message}</p>}<div className="catalog-grid"><section className="planner-panel"><h2>{current.label}</h2>{loading ? <p>Loading…</p> : <AcademicCatalogList records={records} emptyLabel={`No ${current.label.toLowerCase()} yet`} onEdit={(record) => setSelected(record as DisplayRecord)} onDelete={(record) => setDeleting(record as DisplayRecord)} onLifecycle={(record) => void lifecycle(record as DisplayRecord)} />}</section><section className="planner-panel"><h2>{selected ? 'Edit' : 'Create'} {current.singular}</h2>{selected?.nameRepairRequired === true && <p role="alert">This legacy name conflicts with another record. Enter a unique name to complete repair.</p>}{category === 'courses' && selected && selected.semester == null && <p role="alert">Assign a Semester to complete repair before saving this Course.</p>}<AcademicRecordEditor key={`${category}-${selected?.id ?? 'new'}-${selected?.revision ?? 0}-${editorGeneration}`} category={category} options={options} initialValues={selected ? editValues(selected) : {}} submitLabel={selected ? 'Save changes' : 'Create'} onSubmit={save} />{selected && <button type="button" className="secondary-button" onClick={() => setSelected(null)}>Cancel edit</button>}</section></div></section>{deleting && <ProtectedDeleteDialog name={deleting.name} usage={deleting.usage} canArchive={deleting.isActive} onClose={() => setDeleting(null)} onArchive={() => void lifecycle(deleting).then((changed) => { if (changed) setDeleting(null) })} onDelete={() => void remove(deleting)} />}</main>
}
