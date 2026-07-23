import { describe, expect, it } from 'vitest'

import type { ScheduleRevisionContent } from '../api/scheduleLifecycle'
import { lifecycleOverviewFixture, snapshotFixture } from '../test/lifecycleFixtures'
import { snapshotExamCourseNames, snapshotExams, snapshotSchedules } from './scheduleSnapshot'

function contentFixture(): ScheduleRevisionContent {
  const revision = {
    ...lifecycleOverviewFixture().activeWorkingRevision!,
    state: 'published' as const,
    isActiveWorking: false,
    isCurrentPublication: true,
  }
  return {
    revision,
    contentSource: 'captured_snapshot',
    snapshot: {
      ...snapshotFixture(),
      courses: [{
        sourceCourseId: 1,
        name: 'Captured course',
        cohort: { sourceId: 2, name: 'Captured cohort', size: 20 },
        studyType: { sourceId: 3, name: 'Full-time' },
        totalUnits: 2,
        scheduledUnits: 2,
        remainingUnits: 0,
        draftStatus: 'generated',
        teachingSessions: [{
          sourceSessionId: 10,
          date: '2026-09-07',
          startTime: '08:00',
          endTime: '09:30',
          units: 2,
          timeWindowId: 1,
          constraintWindowIndex: 0,
          lecturer: { sourceId: 4, name: 'Captured lecturer', referenceCode: 'L-4', capacity: null },
          room: { sourceId: 5, name: 'Captured room', referenceCode: 'R-5', capacity: 30 },
          validationAlerts: [{ code: 'INSTITUTION_HOLIDAY', message: 'Captured holiday conflict.', details: { relatedSessionIds: [10], holidayDate: '2026-09-07', holidayName: 'Holiday' } }],
        }],
      }],
      examSessions: [{
        sourceExamId: 20,
        course: { sourceId: 1, name: 'Captured course' },
        cohort: { sourceId: 2, name: 'Captured cohort' },
        lecturer: { sourceId: 4, name: 'Captured lecturer', referenceCode: 'L-4', capacity: null },
        room: { sourceId: 5, name: 'Captured room', referenceCode: 'R-5', capacity: 30 },
        examDate: '2026-12-10',
        startTime: '10:00',
        endTime: '11:30',
        source: 'manual',
        configurationIdentifier: 'FINAL',
        configurationRevision: 1,
        durationMinutes: 90,
        examType: 'Written',
        requiredCapacity: 20,
        recommendedStartDate: '2026-12-01',
        recommendedEndDate: '2026-12-08',
        recommendationWasOverridden: false,
        finalTeachingDate: '2026-11-30',
        finalTeachingEndTime: '11:30',
        finalTeachingSessionId: 10,
        validityIssues: [{ code: 'INSTITUTION_HOLIDAY', message: 'Captured exam issue.', details: { relatedDate: '2026-12-10', relatedSessionId: 20, holidayName: 'Exam holiday' } }],
        outsideRecommendedWindow: true,
      }],
    },
  }
}

describe('captured schedule snapshots', () => {
  it('retains captured teaching alerts and their related sessions', () => {
    const alert = snapshotSchedules(contentFixture())[0].sessions[0].validationAlerts[0]
    expect(alert.message).toBe('Captured holiday conflict.')
    expect(alert.holidayName).toBe('Holiday')
    expect(alert.relatedSessions[0]).toMatchObject({ sessionId: 10, courseName: 'Captured course' })
  })

  it('retains captured exam validity issues and final teaching identity', () => {
    const exam = snapshotExams(contentFixture())[0]
    expect(exam.finalTeachingAnchor.teachingSessionId).toBe(10)
    expect(exam.validityIssues[0]).toMatchObject({
      message: 'Captured exam issue.',
      relatedDate: '2026-12-10',
      relatedSessionId: 20,
      holidayName: 'Exam holiday',
    })
  })

  it('uses captured course names for historical exams', () => {
    expect(snapshotExamCourseNames(contentFixture())).toEqual({ 1: 'Captured course' })
  })
})
