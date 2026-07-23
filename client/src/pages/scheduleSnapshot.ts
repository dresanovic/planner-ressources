import type { DraftSchedule, RelatedSession, ValidationAlert } from '../api/draftSchedule'
import type { ExamIssue, ExamSession } from '../api/examScheduling'
import type { CapturedIssue, ScheduleRevisionContent } from '../api/scheduleLifecycle'

export function snapshotSchedules(content: ScheduleRevisionContent): DraftSchedule[] {
  const relatedSessions = new Map<number, RelatedSession>()
  for (const course of content.snapshot.courses) {
    for (const session of course.teachingSessions) {
      relatedSessions.set(session.sourceSessionId, {
        sessionId: session.sourceSessionId,
        draftScheduleId: -course.sourceCourseId,
        courseId: course.sourceCourseId,
        courseName: course.name,
        date: session.date,
        startTime: session.startTime,
        endTime: session.endTime,
        cohortName: course.cohort.name,
        lecturerName: session.lecturer.name,
        roomName: session.room.name,
      })
    }
  }
  return content.snapshot.courses.filter((course) => course.draftStatus != null || course.teachingSessions.length > 0).map((course) => ({
    draftScheduleId: -course.sourceCourseId,
    revision: content.revision.revisionVersion,
    courseId: course.sourceCourseId,
    semesterId: content.revision.semesterId,
    context: { course: { id: course.sourceCourseId, name: course.name }, cohort: { id: course.cohort.sourceId, name: course.cohort.name }, cohortSize: course.cohort.size, lecturer: { id: course.teachingSessions[0]?.lecturer.sourceId ?? 0, name: course.teachingSessions[0]?.lecturer.name ?? 'Captured lecturer' }, room: { id: course.teachingSessions[0]?.room.sourceId ?? 0, name: course.teachingSessions[0]?.room.name ?? 'Captured room' }, studyType: { id: course.studyType.sourceId, name: course.studyType.name } },
    sessions: course.teachingSessions.map((session) => ({ id: session.sourceSessionId, date: session.date, startTime: session.startTime, endTime: session.endTime, units: session.units, courseId: course.sourceCourseId, lecturerId: session.lecturer.sourceId, lecturerName: session.lecturer.name, lecturerReferenceCode: session.lecturer.referenceCode, cohortId: course.cohort.sourceId, roomId: session.room.sourceId, roomName: session.room.name, roomReferenceCode: session.room.referenceCode, studyTypeId: course.studyType.sourceId, timeWindowId: session.timeWindowId, constraintWindowIndex: session.constraintWindowIndex, validationAlerts: session.validationAlerts.map((issue) => capturedValidationAlert(issue, relatedSessions)), lecturer: { id: session.lecturer.sourceId, name: session.lecturer.name, referenceCode: session.lecturer.referenceCode }, room: { id: session.room.sourceId, name: session.room.name, referenceCode: session.room.referenceCode } })),
  }))
}

export function snapshotExams(content: ScheduleRevisionContent): ExamSession[] {
  return content.snapshot.examSessions.map((exam) => ({ id: exam.sourceExamId, revision: content.revision.revisionVersion, courseId: exam.course.sourceId, semesterId: content.revision.semesterId, configurationIdentifier: exam.configurationIdentifier, examType: exam.examType, durationMinutes: exam.durationMinutes, requiredCapacity: exam.requiredCapacity, recommendedStartDate: exam.recommendedStartDate, recommendedEndDate: exam.recommendedEndDate, recommendationWasOverridden: exam.recommendationWasOverridden, outsideRecommendedWindow: exam.outsideRecommendedWindow, finalTeachingAnchor: { date: exam.finalTeachingDate, endTime: exam.finalTeachingEndTime, teachingSessionId: exam.finalTeachingSessionId }, date: exam.examDate, startTime: exam.startTime, endTime: exam.endTime, lecturer: { id: exam.lecturer.sourceId, name: exam.lecturer.name, referenceCode: exam.lecturer.referenceCode }, cohort: { id: exam.cohort.sourceId, name: exam.cohort.name, referenceCode: null }, room: { id: exam.room.sourceId, name: exam.room.name, referenceCode: exam.room.referenceCode, capacity: exam.room.capacity ?? 0 }, lifecycleStatus: 'active', source: exam.source, validityIssues: exam.validityIssues.map(capturedExamIssue), inputSnapshotToken: '' }))
}

export function snapshotExamCourseNames(content: ScheduleRevisionContent): Record<number, string> {
  return Object.fromEntries(
    content.snapshot.examSessions.map((exam) => [
      exam.course.sourceId,
      exam.course.name,
    ]),
  )
}

function capturedValidationAlert(issue: CapturedIssue, sessions: Map<number, RelatedSession>): ValidationAlert {
  const ids = Array.isArray(issue.details.relatedSessionIds) ? issue.details.relatedSessionIds : []
  return {
    code: issue.code as ValidationAlert['code'],
    message: issue.message,
    relatedSessions: ids.map(Number).map((id) => sessions.get(id)).filter((item): item is RelatedSession => item != null),
    holidayDate: typeof issue.details.holidayDate === 'string' ? issue.details.holidayDate : null,
    holidayName: typeof issue.details.holidayName === 'string' ? issue.details.holidayName : null,
  }
}

function capturedExamIssue(issue: CapturedIssue): ExamIssue {
  const resource = issue.details.relatedResource
  return {
    code: issue.code,
    message: issue.message,
    relatedDate: typeof issue.details.relatedDate === 'string' ? issue.details.relatedDate : null,
    relatedResource: resource != null && typeof resource === 'object'
      ? { id: Number((resource as Record<string, unknown>).id), name: String((resource as Record<string, unknown>).name), referenceCode: typeof (resource as Record<string, unknown>).referenceCode === 'string' ? String((resource as Record<string, unknown>).referenceCode) : null }
      : null,
    relatedSessionId: typeof issue.details.relatedSessionId === 'number' ? issue.details.relatedSessionId : null,
    holidayName: typeof issue.details.holidayName === 'string' ? issue.details.holidayName : null,
  }
}
