import { describe, expect, it } from 'vitest'

import calendarWorkspaceSource from '../components/CalendarPlanningWorkspace.tsx?raw'
import draftScheduleSource from '../components/DraftSchedulePanel.tsx?raw'
import lifecycleSource from '../components/ScheduleLifecyclePanel.tsx?raw'
import courseScheduleSource from './CourseSchedulePage.tsx?raw'
import lecturerReviewSource from './LecturerReviewPage.tsx?raw'
import academicDataSource from './AcademicDataPage.tsx?raw'
import academicRecordSource from '../components/AcademicRecordEditor.tsx?raw'
import resourceAvailabilitySource from '../components/ResourceAvailabilityEditor.tsx?raw'
import resourceRemovalSource from '../components/ResourceRemovalDialog.tsx?raw'
import scheduleOccurrenceSource from '../components/ScheduleOccurrenceList.tsx?raw'
import examManualSource from '../components/ExamManualSessionEditor.tsx?raw'
import teachingEditorSource from '../components/TeachingSessionEditor.tsx?raw'
import holidayAdministrationSource from '../components/HolidayAdministration.tsx?raw'

describe('planner German and terminology migration', () => {
  it('does not reintroduce the reviewed English interface copy', () => {
    const source = [
      courseScheduleSource, calendarWorkspaceSource, draftScheduleSource,
      lifecycleSource, lecturerReviewSource, academicDataSource,
      academicRecordSource, resourceAvailabilitySource, resourceRemovalSource,
      scheduleOccurrenceSource, examManualSource, teachingEditorSource,
      holidayAdministrationSource,
    ].join('\n')
    for (const forbidden of [
      'Scheduled units',
      'Remaining units',
      'Session preference',
      'Current publication',
      'Active working revision',
      'Lecturer coordination',
      'Retry refresh',
      'Place exam manually',
      'Add Draft Session',
      'Generation constraints',
      'No Draft Schedules',
      'Calendar workspace unavailable',
      'Current warnings',
      'Submit session comment',
      'Submit revision comment',
      'Discard unsent feedback?',
      'The review could not be reached',
      'No sessions match the active filters',
      "replaceAll('_', ' ')",
      'Could not load academic data.',
      'Resource permanently deleted',
      'Resource placed inactive',
      'Resource reactivated',
      'Unavailable periods',
      'No unavailable periods.',
      'Recurring weekly',
      'Save unavailable period',
      'Remove {resourceName}',
      'Active courses',
      'Schedule sessions',
      'current warning',
      '<dt>Lifecycle</dt>',
      '<dt>Source</dt>',
      '<dt>Duration</dt>',
      '<dt>Capacity</dt>',
      '<dt>Configuration</dt>',
      "label: 'another course'",
      "label: 'session detail'",
      '>Versions</h2>',
      ".join(' ')",
      'Course #',
    ]) expect(source).not.toContain(forbidden)
  })

  it('uses catalog lookups for configurable planner domain labels', () => {
    expect(courseScheduleSource).toContain("label('course.singular')")
    expect(courseScheduleSource).toContain("label('lecturer.singular')")
    expect(courseScheduleSource).toContain("label('cohort.singular')")
    expect(courseScheduleSource).toContain("label('room.singular')")
    expect(calendarWorkspaceSource).toContain("label('course.fieldLabel')")
    expect(draftScheduleSource).toContain("label('lecturer.tableHeading')")
    expect(academicDataSource).toContain("label('academicData.heading')")
    expect(resourceRemovalSource).toContain("label('course.plural')")
    expect(scheduleOccurrenceSource).toContain('Prüfungstermin')
    expect(holidayAdministrationSource).toContain("label('academicData.heading')")
    expect(calendarWorkspaceSource).not.toContain(".join('; ')")
  })
})
