import type {
  DraftSchedule,
  DraftScheduleContext,
  DraftSession,
  UpdateDraftSessionRequest,
} from '../api/draftSchedule'
import type { PlanningOptions, RoomOption } from '../api/planningOptions'
import type { LecturerRecord, ResourceCandidate } from '../api/resourceCatalog'

export type EditableDraftSessionRequest = Omit<UpdateDraftSessionRequest, 'scheduleRevisionId'>

export type EditableResource = {
  id: number
  name: string
  referenceCode?: string
  capacity?: number | null
}

export type TeachingSessionEditModel = DraftSession & {
  draftScheduleId: number
  context: DraftScheduleContext
  eligibleLecturers: EditableResource[]
  eligibleRooms: EditableResource[]
}

export function buildTeachingSessionEditModels(
  schedules: DraftSchedule[],
  rooms: RoomOption[],
  lecturers: LecturerRecord[],
  courseResources: PlanningOptions['courseResources'],
): TeachingSessionEditModel[] {
  return schedules.flatMap((schedule) =>
    schedule.sessions.map((session) => {
      const configuration = courseResources.find((item) => item.courseId === schedule.courseId)
      const listedRoom = rooms.find((item) => item.id === session.roomId)
      const listedLecturer = lecturers.find((item) => item.id === session.lecturerId)
      const currentLecturer = listedLecturer
        ? { id: listedLecturer.id, name: listedLecturer.name, referenceCode: listedLecturer.referenceCode }
        : session.lecturer
      const currentRoom = listedRoom
        ? {
            id: listedRoom.id,
            name: listedRoom.name,
            referenceCode: 'referenceCode' in listedRoom ? String(listedRoom.referenceCode) : '',
            capacity: listedRoom.capacity,
          }
        : session.room
      return {
        ...session,
        lecturer: currentLecturer,
        room: currentRoom,
        draftScheduleId: schedule.draftScheduleId,
        context: schedule.context,
        eligibleLecturers: configuration
          ? editableCandidates(configuration.eligibleLecturers, currentLecturer)
          : lecturers
              .filter((item) => item.isActive || item.id === session.lecturerId)
              .map((item) => ({ ...item })),
        eligibleRooms: configuration
          ? editableCandidates(configuration.eligibleRooms, currentRoom)
          : rooms
              .filter((item) => item.capacity >= schedule.context.cohortSize || item.id === session.roomId)
              .map((item) => ({
                ...item,
                referenceCode: 'referenceCode' in item ? String(item.referenceCode) : '',
              })),
      }
    }),
  )
}

function editableCandidates(
  candidates: ResourceCandidate[],
  current: EditableResource,
): EditableResource[] {
  const options = candidates
    .filter((candidate) => candidate.id === current.id || (candidate.isEligible && candidate.isUsable))
    .map((candidate) => ({
      id: candidate.id,
      name: candidate.name,
      referenceCode: candidate.referenceCode,
      capacity: candidate.capacity,
    }))
  return options.some((option) => option.id === current.id) ? options : [current, ...options]
}

export function createTeachingSessionDraft(
  session: TeachingSessionEditModel,
): EditableDraftSessionRequest {
  return {
    date: session.date,
    startTime: session.startTime,
    endTime: session.endTime,
    lecturerId: session.lecturerId,
    roomId: session.roomId,
  }
}

export function teachingDraftsEqual(
  left: EditableDraftSessionRequest,
  right: EditableDraftSessionRequest,
): boolean {
  return left.date === right.date
    && left.startTime === right.startTime
    && left.endTime === right.endTime
    && left.lecturerId === right.lecturerId
    && left.roomId === right.roomId
}

export function resourceLabel(resource: { name: string; referenceCode?: string | null }): string {
  return resource.referenceCode ? `${resource.name} · ${resource.referenceCode}` : resource.name
}

export function derivedLengthLabel(startTime: string, endTime: string): string {
  const [startHour, startMinute] = startTime.split(':').map(Number)
  const [endHour, endMinute] = endTime.split(':').map(Number)
  if ([startHour, startMinute, endHour, endMinute].some((value) => Number.isNaN(value))) {
    return 'Invalid'
  }
  const minutes = endHour * 60 + endMinute - (startHour * 60 + startMinute)
  if (minutes <= 0) return 'Invalid'
  if (minutes < 60) return `${minutes} min`
  const hours = Math.floor(minutes / 60)
  const remainder = minutes % 60
  return remainder === 0 ? `${hours} h` : `${hours} h ${remainder} min`
}
