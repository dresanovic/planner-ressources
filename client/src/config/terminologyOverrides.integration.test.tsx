import { act } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { plannerLecturerReviewOverviewFixture, publicLecturerReviewFixture } from '../test/lecturerReviewFixtures'
import { terminologyDefaults } from '../test/terminologyDefaults'
import { loadedCalendarWorkspaceFixture } from '../test/calendarWorkspaceFixtures'

const overrides = {
  ...terminologyDefaults,
  'course.singular': 'Modul ✨',
  'course.plural': 'Module ✨',
  'course.navigation': 'Modulnavigation ✨',
  'course.fieldLabel': 'Modulauswahl ✨',
  'lecturer.singular': 'Lehrkraft ✨',
  'lecturer.plural': 'Lehrkräfte ✨',
  'lecturer.navigation': 'Lehrkraftnavigation ✨',
  'lecturer.fieldLabel': 'Lehrkraftauswahl ✨',
  'cohort.singular': 'Lerngruppe ✨',
  'cohort.fieldLabel': 'Lerngruppenauswahl ✨',
  'room.singular': 'Lernort ✨',
  'room.fieldLabel': 'Lernortauswahl ✨',
  'schedule.navigation': 'Belegungsplan ✨',
  'schedule.heading': 'Belegungsplanung ✨',
  'academicData.navigation': 'Grunddaten ✨',
  'academicData.heading': 'Grunddatenverwaltung ✨',
}

afterEach(() => {
  document.body.innerHTML = ''
  vi.doUnmock('../api/lecturerReview')
  vi.doUnmock('../api/holidayCalendar')
})

async function initializeOverrides() {
  vi.resetModules()
  const terminology = await import('./terminology')
  terminology.initializeTerminology({ labels: overrides })
}

describe('customer terminology propagation', () => {
  it('renders non-default Unicode terms across shell, administration, schedule, exam, and planner coordination surfaces', async () => {
    await initializeOverrides()
    vi.doMock('../api/holidayCalendar', async () => ({
      ...(await vi.importActual<typeof import('../api/holidayCalendar')>('../api/holidayCalendar')),
      listHolidays: vi.fn().mockResolvedValue([]), createHoliday: vi.fn(), updateHoliday: vi.fn(), deleteHoliday: vi.fn(),
    }))
    const [{ ApplicationNavigation }, { AcademicRecordEditor }, { ResourceEditor }, { ScheduleContextHeader }, { ExamGenerationPanel }, { LecturerReviewManagement }, { ResourceRemovalDialog }, { CalendarPlanningWorkspace }, { ScheduleOccurrenceList }, { HolidayAdministration }, { DraftSchedulePanel }] = await Promise.all([
      import('../components/ApplicationNavigation'),
      import('../components/AcademicRecordEditor'),
      import('../components/ResourceEditor'),
      import('../components/ScheduleContextHeader'),
      import('../components/ExamGenerationPanel'),
      import('../components/LecturerReviewManagement'),
      import('../components/ResourceRemovalDialog'),
      import('../components/CalendarPlanningWorkspace'),
      import('../components/ScheduleOccurrenceList'),
      import('../components/HolidayAdministration'),
      import('../components/DraftSchedulePanel'),
    ])
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => root.render(<>
      <ApplicationNavigation
        view="schedule" selectedCategory="courses" selectedScheduleDestination="calendar"
        scheduleExpanded academicExpanded navigationOpen={false} navigationPinned
        onToggleAcademic={() => undefined} onToggleSchedule={() => undefined}
        onSelectScheduleDestination={() => undefined} onSelectCategory={() => undefined}
        onNavigationOpenChange={() => undefined} onNavigationPinnedChange={() => undefined}
      />
      <AcademicRecordEditor
        category="courses"
        options={{ semesters: [{ id: 1, name: 'Semester A' }], cohorts: [{ id: 2, name: 'Dynamische Kohorte' }], studyTypes: [{ id: 3, name: 'Dynamische Studienform' }], lecturers: [{ id: 4, name: 'Dynamische Person' }], rooms: [{ id: 5, name: 'Dynamischer Raum' }] }}
        onSubmit={async () => undefined}
      />
      <ResourceEditor resourceType="lecturers" onSubmit={async () => undefined} onCancel={() => undefined} />
      <ScheduleContextHeader
        destination="calendar" semesterId={1} semesters={[{ id: 1, label: 'Semester A' }]}
        revisionId={2} revisions={[{ id: 2, label: 'Revision A' }]}
        courseId={3} courses={[{ id: 3, label: 'Dynamischer Modulname' }]}
        onSemesterChange={() => undefined} onRevisionChange={() => undefined} onCourseChange={() => undefined}
      />
      <ExamGenerationPanel semesterId={1} courses={[]} disabled={false} onChanged={() => undefined} />
      <LecturerReviewManagement overview={plannerLecturerReviewOverviewFixture()} busy={false} onIssue={async () => { throw new Error('not used') }} />
      <CalendarPlanningWorkspace
        workspace={loadedCalendarWorkspaceFixture()}
        loading={false}
        onRetry={() => undefined}
        listContent={<ScheduleOccurrenceList workspace={loadedCalendarWorkspaceFixture()} onSelectOccurrence={() => undefined} />}
      />
      <ResourceRemovalDialog
        resourceName="Dynamische Ressource"
        assessment={{
          resourceId: 4, revision: 1, disposition: 'inactivate',
          activeCourses: [{ id: 3, name: 'Dynamischer Modulname' }],
          inactiveCourses: [],
          sessionUsage: { draftSessionCount: 1, draftScheduleCount: 1 },
          examUsage: { examSessionCount: 0, currentConfigurationCount: 0 },
        } as never}
        onClose={() => undefined}
        onConfirm={() => undefined}
      />
      <HolidayAdministration onChanged={() => undefined} />
      <DraftSchedulePanel schedules={[]} exams={[{
        id: 99, revision: 1, courseId: 99, semesterId: 1, configurationIdentifier: 'Klausur', examType: 'Schriftlich', durationMinutes: 90, requiredCapacity: 20,
        recommendedStartDate: '2026-10-01', recommendedEndDate: '2026-10-15', recommendationWasOverridden: false, outsideRecommendedWindow: false,
        finalTeachingAnchor: { date: '2026-09-30', endTime: '12:00', teachingSessionId: 1 }, date: '2026-10-02', startTime: '09:00', endTime: '10:30',
        lecturer: { id: 1, name: 'Dynamische Person', referenceCode: 'L1' }, cohort: { id: 2, name: 'Dynamische Kohorte', referenceCode: null }, room: { id: 3, name: 'Dynamischer Raum', referenceCode: 'R1', capacity: 30 },
        lifecycleStatus: 'active', source: 'manual', validityIssues: [], inputSnapshotToken: 'token',
      }]} />
    </>))

    for (const expected of [
      'Belegungsplan ✨', 'Grunddaten ✨', 'Modulnavigation ✨', 'Lehrkraftnavigation ✨',
      'Modulauswahl ✨', 'Lehrkraftauswahl ✨', 'Lerngruppenauswahl ✨', 'Lernortauswahl ✨',
      'Belegungsplanung ✨', 'Module ✨', 'Lehrkräfte ✨',
      'Aktive Module ✨',
      'Grunddatenverwaltung ✨', 'Modul ✨ #99',
    ]) expect(document.body.textContent).toContain(expected)
    expect(document.body.textContent).toContain('Dynamischer Modulname')
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).not.toContain('Course #99')
    expect(document.querySelector('[aria-current="page"]')?.textContent).toContain('Kalender')
    await act(async () => root.unmount())
  })

  it('uses the same overrides on the loaded accountless review without changing dynamic record names', async () => {
    await initializeOverrides()
    const review = publicLecturerReviewFixture()
    vi.doMock('../api/lecturerReview', async () => ({
      ...(await vi.importActual<typeof import('../api/lecturerReview')>('../api/lecturerReview')),
      getPublicLecturerReview: vi.fn().mockResolvedValue(review),
      submitPublicLecturerFeedback: vi.fn(),
    }))
    const { LecturerReviewPage } = await import('../pages/LecturerReviewPage')
    const root = createRoot(document.body.appendChild(document.createElement('div')))
    await act(async () => {
      root.render(<LecturerReviewPage secret="FS022TerminologyOverrideCanary1111111111111" />)
      await Promise.resolve()
      await Promise.resolve()
    })

    expect(document.body.textContent).toContain('Lehrkraft ✨')
    expect(document.body.textContent).toContain('Modulauswahl ✨')
    expect(document.body.textContent).toContain('Lernortauswahl ✨')
    expect(document.body.textContent).toContain('Dr Ada Lecturer')
    expect(document.body.textContent).toContain('Algorithms')
    expect(document.body.textContent).not.toContain('course.singular')
    await act(async () => root.unmount())
  })
})
