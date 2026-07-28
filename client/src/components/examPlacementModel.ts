import type {
  CreateManualExamRequest,
  ExamConfiguration,
  ExamSession,
  UpdateExamRequest,
} from '../api/examScheduling'

export type ExamPlacementInput =
  | Omit<CreateManualExamRequest, 'scheduleRevisionId'>
  | Omit<UpdateExamRequest, 'scheduleRevisionId'>

export type ExamPlacementDraft = {
  day: string
  startTime: string
  lecturerId: number
  roomId: number
}

type Option = { id: number; name: string; capacity?: number }

export function createExamPlacementDraft({
  exam,
  configuration,
  lecturers,
  rooms,
}: {
  exam?: ExamSession
  configuration?: ExamConfiguration
  lecturers: Option[]
  rooms: Option[]
}): ExamPlacementDraft {
  return {
    day: exam?.date ?? '',
    startTime: exam?.startTime ?? '09:00',
    lecturerId: exam?.lecturer.id ?? configuration?.responsibleLecturerId ?? lecturers[0]?.id ?? 0,
    roomId: exam?.room.id ?? rooms[0]?.id ?? 0,
  }
}

export function examPlacementDraftsEqual(left: ExamPlacementDraft, right: ExamPlacementDraft) {
  return left.day === right.day
    && left.startTime === right.startTime
    && left.lecturerId === right.lecturerId
    && left.roomId === right.roomId
}
