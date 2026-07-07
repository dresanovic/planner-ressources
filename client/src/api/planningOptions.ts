import type { PlanningEntity } from './draftSchedule'

export type CourseOption = {
  id: number
  name: string
  totalUnits: number
  minSessionUnits: number
  maxSessionUnits: number
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

export type PlanningOptions = {
  courses: CourseOption[]
  semesters: SemesterOption[]
  timeWindows: TimeWindowOption[]
}

const API_BASE = import.meta.env.VITE_API_BASE_URL ?? ''

export async function getPlanningOptions(): Promise<PlanningOptions> {
  const response = await fetch(`${API_BASE}/api/planning-options`)
  if (!response.ok) {
    throw new Error('Could not load planning options.')
  }
  return response.json()
}
