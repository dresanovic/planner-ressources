import type { CourseOption } from '../../api/planningOptions'
import type { CourseRecord } from '../../api/academicCatalog'

export const targetCohort = { id: 101, name: 'MA IT & Wirtschaftsinformatik – 2. Semester' }
export const otherCohort = { id: 102, name: targetCohort.name }
export const emptyCohort = { id: 103, name: 'Ohne Lehrveranstaltungen' }
export const courseListSemester = { id: 1, name: '2027 S', startDate: '2027-02-01', endDate: '2027-07-31' }
export const generationCatalog: CourseOption[] = Array.from({ length: 94 }, (_, index) => ({
  id: index + 1, name: index < 2 ? 'Gleichnamige Lehrveranstaltung' : `Lehrveranstaltung ${index + 1}`,
  semesterId: 1, cohort: index < 11 ? targetCohort : otherCohort,
  totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
  lecturer: null, room: null, studyType: { id: 1, name: 'Vollzeit' },
  availability: { available: index !== 93, reasons: index === 93 ? ['COURSE_UNAVAILABLE'] : [] },
}))
export const administrationCatalog: CourseRecord[] = generationCatalog.map((course) => ({
  ...course, semester: courseListSemester, isActive: true, revision: 1, nameRepairRequired: false,
  availability: course.availability!,
  usage: { recordId: course.id, revision: 1, canDelete: true, dependentRecords: [], savedSchedules: { type: 'draft_schedule', count: 0 }, blockers: [] },
}))
export const legacyCourse: CourseRecord = { ...administrationCatalog[0], id: 1001, name: 'Legacy ohne Semester', semester: null }
export const otherSemesterCourse: CourseRecord = { ...administrationCatalog[0], id: 1002, semester: { id: 2, name: '2027 W' } }
export const laterPageCourses: CourseRecord[] = Array.from({ length: 110 }, (_, index) => ({ ...administrationCatalog[12], id: 2000 + index }))
