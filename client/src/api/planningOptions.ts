import type { PlanningEntity } from './draftSchedule'
import type { Availability } from './academicCatalog'

export type CourseOption = {
  id: number
  name: string
  totalUnits: number
  minSessionUnits: number
  maxSessionUnits: number
  semesterId?: number
  availability?: Availability
  lecturer: PlanningEntity
  cohort: PlanningEntity
  room: PlanningEntity
  studyType: PlanningEntity
}

export type SemesterOption = {
  id: number
  name: string
  startDate: string
  endDate: string
}

export type TimeWindowOption = {
  id: number
  studyTypeId: number
  weekday: number
  startTime: string
  endTime: string
  sortOrder: number
}

export type RoomOption = {
  id: number
  name: string
  capacity: number
}

export type PlanningOptions = {
  courses: CourseOption[]
  semesters: SemesterOption[]
  timeWindows: TimeWindowOption[]
  rooms: RoomOption[]
  lecturers: PlanningEntity[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function getPlanningOptions(semesterId?: number): Promise<PlanningOptions> {
  const query = semesterId == null ? '' : `?semesterId=${semesterId}`
  const response = await fetch(`${API_BASE}/api/planning-options${query}`)
  if (!response.ok) {
    throw new Error('Could not load planning options.')
  }
  return response.json()
}
