import { act, useState, type ComponentProps, type ComponentType } from 'react'
import { createRoot } from 'react-dom/client'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

const mocks = vi.hoisted(() => ({
  getPlanningOptions: vi.fn(),
  getGenerationConstraints: vi.fn(),
  getDraftSchedules: vi.fn(),
  generateDraftSchedule: vi.fn(),
  clearGenerationConstraints: vi.fn(),
  saveGenerationConstraints: vi.fn(),
  updateDraftSession: vi.fn(),
  createManualDraftSession: vi.fn(),
  deleteDraftSession: vi.fn(),
  clearCourseDraft: vi.fn(),
  prepare: vi.fn(),
  generateBatch: vi.fn(),
  acceptBatch: vi.fn(),
  getExamPlanningOverview: vi.fn(),
  saveExamConfiguration: vi.fn(),
  createManualExam: vi.fn(),
  updateExam: vi.fn(),
  deleteExam: vi.fn(),
  getScheduleLifecycle: vi.fn(),
  createWorkingRevision: vi.fn(),
  prepareSchedulePublication: vi.fn(),
  transitionScheduleRevision: vi.fn(),
  getScheduleRevision: vi.fn(),
  getCalendarWorkspace: vi.fn(),
  getLecturerReviewOverview: vi.fn(),
  issueLecturerReviewLink: vi.fn(),
  revokeLecturerReviewLink: vi.fn(),
  replaceLecturerReviewLink: vi.fn(),
}))

vi.mock('../api/planningOptions', () => ({ getPlanningOptions: mocks.getPlanningOptions }))
vi.mock('../api/draftSchedule', () => ({
  getGenerationConstraints: mocks.getGenerationConstraints,
  getDraftSchedules: mocks.getDraftSchedules,
  generateDraftSchedule: mocks.generateDraftSchedule,
  clearGenerationConstraints: mocks.clearGenerationConstraints,
  saveGenerationConstraints: mocks.saveGenerationConstraints,
  updateDraftSession: mocks.updateDraftSession,
  createManualDraftSession: mocks.createManualDraftSession,
  deleteDraftSession: mocks.deleteDraftSession,
  clearCourseDraft: mocks.clearCourseDraft,
}))
vi.mock('../api/conflictAwareGeneration', () => ({
  prepareConflictAwareGeneration: mocks.prepare,
  generateConflictAwareSchedules: mocks.generateBatch,
  acceptConflictAwareSchedules: mocks.acceptBatch,
}))
vi.mock('../api/examScheduling', () => ({
  getExamPlanningOverview: mocks.getExamPlanningOverview,
  saveExamConfiguration: mocks.saveExamConfiguration,
  createManualExam: mocks.createManualExam,
  updateExam: mocks.updateExam,
  deleteExam: mocks.deleteExam,
}))
vi.mock('../api/scheduleLifecycle', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/scheduleLifecycle')>()),
  getScheduleLifecycle: mocks.getScheduleLifecycle,
  createWorkingRevision: mocks.createWorkingRevision,
  prepareSchedulePublication: mocks.prepareSchedulePublication,
  transitionScheduleRevision: mocks.transitionScheduleRevision,
  getScheduleRevision: mocks.getScheduleRevision,
}))
vi.mock('../api/calendarWorkspace', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/calendarWorkspace')>()),
  getCalendarWorkspace: mocks.getCalendarWorkspace,
}))
vi.mock('../api/lecturerReview', async (importOriginal) => ({
  ...(await importOriginal<typeof import('../api/lecturerReview')>()),
  getLecturerReviewOverview: mocks.getLecturerReviewOverview,
  issueLecturerReviewLink: mocks.issueLecturerReviewLink,
  revokeLecturerReviewLink: mocks.revokeLecturerReviewLink,
  replaceLecturerReviewLink: mocks.replaceLecturerReviewLink,
}))

import { CourseSchedulePage } from './CourseSchedulePage'
import type { ScheduleDestination } from '../components/ApplicationNavigation'
import type { IssuedLecturerReviewLink } from '../api/lecturerReview'
import { calendarWorkspaceMatchesSelection } from './calendarWorkspaceSelection'
import { draftScheduleFixture, generationConstraintsFixture } from '../test/draftScheduleFixtures'
import { lifecycleOverviewFixture, snapshotFixture } from '../test/lifecycleFixtures'
import { loadedCalendarWorkspaceFixture, noRevisionWorkspaceFixture } from '../test/calendarWorkspaceFixtures'
import { issuedLecturerReviewLinkFixture, plannerLecturerReviewOverviewFixture } from '../test/lecturerReviewFixtures'
import { decisionRequiredGenerationFixture, directSavedGenerationFixture, optimizationPreparationFixture } from '../test/optimizationFixtures'

function deferred<Value>() {
  let resolve!: (value: Value) => void
  let reject!: (reason?: unknown) => void
  const promise = new Promise<Value>((resolvePromise, rejectPromise) => {
    resolve = resolvePromise
    reject = rejectPromise
  })
  return { promise, resolve, reject }
}

const entity = (id: number, name: string) => ({ id, name })
const options = {
  courses: [1, 2].map((id) => ({
    id, name: `Course ${id}`, totalUnits: 8, minSessionUnits: 2, maxSessionUnits: 4, cohortSize: 30,
    lecturer: entity(id, `L${id}`), cohort: entity(id, `C${id}`), room: entity(id, `R${id}`), studyType: entity(1, 'Full-time'),
  })),
  semesters: [{ id: 1, name: 'Fall 2026', startDate: '2026-09-07', endDate: '2026-12-20' }],
  timeWindows: [],
  cohorts: [{ id: 1, name: 'C1', studentCount: 30 }, { id: 2, name: 'C2', studentCount: 30 }],
  rooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', capacity: 40, isActive: true, revision: 1 }],
  lecturers: [
    { id: 1, name: 'L1', referenceCode: 'LEC-001', isActive: true, revision: 1 },
    { id: 2, name: 'L2', referenceCode: 'LEC-002', isActive: true, revision: 1 },
  ],
  courseResources: [],
}
const examOverview = {
  semesterId: 1,
  institutionToday: '2026-07-20',
  courses: [1, 2].map((courseId) => ({
    courseId,
    courseName: `Course ${courseId}`,
    semesterId: 1,
    cohortId: courseId,
    cohortName: `C${courseId}`,
    enabled: false,
    configuration: null,
    finalTeachingAnchor: null,
    activeExam: null,
    pastExams: [],
    generationEligibility: { eligible: false, code: 'DISABLED', message: 'Exam planning is disabled.' },
    inputSnapshotToken: `exam-course-${courseId}`,
  })),
}

function publishedLifecycleOverview() {
  const base = lifecycleOverviewFixture()
  const published = {
    ...base.activeWorkingRevision!,
    revisionId: 12,
    revisionNumber: 2,
    state: 'published' as const,
    isActiveWorking: false,
    isCurrentPublication: true,
    publishedAt: '2026-07-21T10:00:00Z',
    allowedActions: {
      markReady: false,
      returnToDraft: false,
      preparePublication: false,
      abandon: false,
      restore: false,
      editSchedule: false,
    },
  }
  return {
    ...base,
    activeWorkingRevision: null,
    currentPublication: published,
    revisions: [published],
    allowedActions: { createWorkingRevision: true },
  }
}

function publishedCalendarWorkspace() {
  const workspace = loadedCalendarWorkspaceFixture()
  const selector = {
    revisionId: 12,
    revisionNumber: 2,
    lifecycleState: 'published' as const,
    designation: 'current_published' as const,
  }
  return {
    ...workspace,
    availableContexts: {
      activeWorking: null,
      currentPublished: selector,
    },
    selectedRevision: {
      ...selector,
      readOnly: true,
      contentSource: 'captured_published' as const,
      validationBasis: 'current' as const,
      snapshotSchemaVersion: 2 as const,
    },
    workspaceToken: 'semester:1:revision:12:published:2',
  }
}

function lifecycleWithWorkingAndPublished() {
  const working = lifecycleOverviewFixture().activeWorkingRevision!
  const published = {
    ...working,
    revisionId: 12,
    revisionNumber: 2,
    state: 'published' as const,
    isActiveWorking: false,
    isCurrentPublication: true,
    publishedAt: '2026-07-21T10:00:00Z',
    allowedActions: {
      markReady: false,
      returnToDraft: false,
      preparePublication: false,
      abandon: false,
      restore: false,
      editSchedule: false,
    },
  }
  return {
    ...lifecycleOverviewFixture(),
    activeWorkingRevision: working,
    currentPublication: published,
    revisions: [working, published],
  }
}

function workingCalendarWithPublishedAvailable() {
  const workspace = loadedCalendarWorkspaceFixture()
  return {
    ...workspace,
    availableContexts: {
      ...workspace.availableContexts,
      currentPublished: {
        revisionId: 12,
        revisionNumber: 2,
        lifecycleState: 'published' as const,
        designation: 'current_published' as const,
      },
    },
  }
}

function publishedCalendarWithWorkingAvailable() {
  const workspace = publishedCalendarWorkspace()
  return {
    ...workspace,
    availableContexts: {
      activeWorking: {
        revisionId: 11,
        revisionNumber: 1,
        lifecycleState: 'draft' as const,
        designation: 'active_working' as const,
      },
      currentPublished: workspace.availableContexts.currentPublished,
    },
  }
}

function lecturerReviewOverviewForRevision(
  revisionId: number,
  occurrenceRef = 'exam:1',
) {
  const overview = plannerLecturerReviewOverviewFixture()
  const sessionGroup = overview.feedbackGroups.find(
    (group) => group.level === 'session',
  )!
  return {
    ...overview,
    revision: {
      ...overview.revision,
      id: revisionId,
      label: revisionId === 12 ? 'Published R2' : 'Working R1',
      state: revisionId === 12 ? 'published' as const : 'draft' as const,
    },
    totalFeedbackCount: sessionGroup.items.length,
    impossibleFlagCount: sessionGroup.impossibleFlagCount,
    feedbackGroups: [{
      ...sessionGroup,
      groupRef: occurrenceRef,
      sessionContext: sessionGroup.sessionContext && {
        ...sessionGroup.sessionContext,
        sessionRef: occurrenceRef,
        sourceSessionId: Number(occurrenceRef.split(':')[1]),
      },
      currentNavigation: { revisionId, occurrenceRef },
    }],
  }
}

beforeEach(() => {
  Object.values(mocks).forEach((mock) => mock.mockReset())
  mocks.getPlanningOptions.mockResolvedValue(options)
  mocks.getGenerationConstraints.mockResolvedValue(generationConstraintsFixture)
  mocks.getDraftSchedules.mockResolvedValue([])
  mocks.getExamPlanningOverview.mockResolvedValue(examOverview)
  mocks.getScheduleLifecycle.mockResolvedValue(lifecycleOverviewFixture())
  mocks.getCalendarWorkspace.mockResolvedValue(loadedCalendarWorkspaceFixture())
  mocks.getLecturerReviewOverview.mockImplementation((revisionId: number) =>
    Promise.resolve(lecturerReviewOverviewForRevision(revisionId)),
  )
  mocks.issueLecturerReviewLink.mockResolvedValue(issuedLecturerReviewLinkFixture())
})

afterEach(() => { document.body.innerHTML = '' })

async function renderPage(destination: ScheduleDestination = 'calendar') {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => {
    root.render(<CourseSchedulePage catalogRevision={0} destination={destination} />)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
  return root
}

type NavigableCourseSchedulePageProps =
  ComponentProps<typeof CourseSchedulePage> & {
    onScheduleDestinationChange?: (
      destination: ScheduleDestination,
    ) => void
  }

const NavigableCourseSchedulePage =
  CourseSchedulePage as ComponentType<NavigableCourseSchedulePageProps>

function CourseScheduleNavigationHarness() {
  const [destination, setDestination] =
    useState<ScheduleDestination>('calendar')
  return (
    <>
      <button type="button" onClick={() => setDestination('reviews')}>
        Show lecturer reviews
      </button>
      <NavigableCourseSchedulePage
        catalogRevision={0}
        destination={destination}
        onScheduleDestinationChange={setDestination}
      />
    </>
  )
}

async function renderNavigationHarness() {
  const root = createRoot(document.body.appendChild(document.createElement('div')))
  await act(async () => {
    root.render(<CourseScheduleNavigationHarness />)
    await new Promise((resolve) => setTimeout(resolve, 0))
  })
  return root
}

function button(label: string) {
  return [...document.querySelectorAll('button')].find((item) => item.textContent === label)
}

function summaryValue(label: string) {
  const term = [...document.querySelectorAll('dt')].find((item) => item.textContent === label)
  return term?.parentElement?.querySelector('dd')?.textContent
}

describe('CourseSchedulePage multi-course mode', () => {
  it('exposes exactly one focused Schedule workspace for each controlled destination', async () => {
    const root = await renderPage('versions')
    expect(document.querySelector<HTMLElement>('.versions-workspace-region')?.hidden).toBe(false)
    expect(document.querySelector<HTMLElement>('.calendar-workspace-region')?.hidden).toBe(true)
    expect(document.querySelector<HTMLElement>('.exams-workspace-region')?.hidden).toBe(true)
    await act(async () => root.render(<CourseSchedulePage catalogRevision={0} destination="exams" />))
    expect(document.querySelector<HTMLElement>('.versions-workspace-region')?.hidden).toBe(true)
    expect(document.querySelector<HTMLElement>('.calendar-workspace-region')?.hidden).toBe(true)
    expect(document.querySelector<HTMLElement>('.exams-workspace-region')?.hidden).toBe(false)
    await act(async () => root.render(<CourseSchedulePage catalogRevision={0} destination="calendar" />))
    expect(document.querySelector<HTMLElement>('.calendar-workspace-region')?.hidden).toBe(false)
    expect(document.querySelectorAll('.calendar-workspace')).not.toHaveLength(0)
  })

  it('preserves the selected schedule revision when opening Lecturer coordination', async () => {
    const lifecycle = lifecycleWithWorkingAndPublished()
    mocks.getScheduleLifecycle.mockResolvedValue(lifecycle)
    mocks.getScheduleRevision.mockResolvedValue({
      revision: lifecycle.currentPublication,
      contentSource: 'captured_snapshot',
      snapshot: snapshotFixture(),
    })
    mocks.getCalendarWorkspace.mockImplementation((_semesterId, revisionId) =>
      Promise.resolve(
        revisionId === 12
          ? publishedCalendarWithWorkingAvailable()
          : workingCalendarWithPublishedAvailable(),
      ),
    )
    const root = await renderPage()

    await act(async () => {
      button('Veröffentlichung R2')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    await act(async () => {
      root.render(
        <CourseSchedulePage catalogRevision={0} destination="reviews" />,
      )
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    const revisionSelect =
      [...document.querySelectorAll<HTMLSelectElement>(
        '.schedule-context-field select',
      )][1]
    expect(revisionSelect.value).toBe('12')
    expect(mocks.getLecturerReviewOverview).toHaveBeenLastCalledWith(12)
    expect(
      document.querySelector<HTMLElement>('.lecturer-reviews-region')?.hidden,
    ).toBe(false)
    expect(document.body.textContent).toContain('Veröffentlichung R2')
  })

  it('never renders coordination data from the previously selected revision', async () => {
    const lifecycle = lifecycleWithWorkingAndPublished()
    const publishedRequest = deferred<ReturnType<typeof lecturerReviewOverviewForRevision>>()
    mocks.getScheduleLifecycle.mockResolvedValue(lifecycle)
    mocks.getScheduleRevision.mockResolvedValue({
      revision: lifecycle.currentPublication,
      contentSource: 'captured_snapshot',
      snapshot: snapshotFixture(),
    })
    mocks.getLecturerReviewOverview.mockImplementation((revisionId: number) =>
      revisionId === 12
        ? publishedRequest.promise
        : Promise.resolve(lecturerReviewOverviewForRevision(revisionId)),
    )
    await renderPage('reviews')
    expect(document.querySelector('.lecturer-review-management')?.textContent)
      .toContain('Could this session start at 10:00?')

    await act(async () => {
      const revisionSelect = [...document.querySelectorAll<HTMLSelectElement>(
        '.schedule-context-field select',
      )][1]
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')
        ?.set?.call(revisionSelect, '12')
      revisionSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await Promise.resolve()
    })

    expect(document.querySelector('.lecturer-review-management')).toBeNull()
    expect(document.body.textContent).toContain('Abstimmung mit Lehrende wird geladen')

    await act(async () => {
      publishedRequest.resolve(lecturerReviewOverviewForRevision(12))
      await publishedRequest.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('.lecturer-review-management')?.textContent)
      .toContain('Published R2')
  })

  it('ignores a completed coordination mutation after the selected revision changes', async () => {
    const lifecycle = lifecycleWithWorkingAndPublished()
    const issueRequest = deferred<IssuedLecturerReviewLink>()
    const issued = issuedLecturerReviewLinkFixture()
    mocks.getScheduleLifecycle.mockResolvedValue(lifecycle)
    mocks.getScheduleRevision.mockResolvedValue({
      revision: lifecycle.currentPublication,
      contentSource: 'captured_snapshot',
      snapshot: snapshotFixture(),
    })
    mocks.issueLecturerReviewLink.mockReturnValueOnce(issueRequest.promise)
    await renderPage('reviews')

    await act(async () => {
      const lecturer = document.querySelector<HTMLSelectElement>(
        '#lecturer-review-lecturer',
      )!
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')
        ?.set?.call(lecturer, '8')
      lecturer.dispatchEvent(new Event('change', { bubbles: true }))
      await Promise.resolve()
    })
    await act(async () => {
      button('Issue review link')?.click()
      await Promise.resolve()
    })

    await act(async () => {
      const revisionSelect = [...document.querySelectorAll<HTMLSelectElement>(
        '.schedule-context-field select',
      )][1]
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')
        ?.set?.call(revisionSelect, '12')
      revisionSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('.lecturer-review-management')?.textContent)
      .toContain('Published R2')

    await act(async () => {
      issueRequest.resolve({
        ...issued,
        issuedLink: { ...issued.issuedLink, revisionId: 11 },
        overview: lecturerReviewOverviewForRevision(11),
      })
      await issueRequest.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('.lecturer-review-management')?.textContent)
      .toContain('Published R2')
    expect(document.body.textContent).not.toContain('Abstimmung mit Lehrende wird geladen')
    expect(document.body.textContent).not.toContain(issued.secret)
    expect(document.body.textContent).not.toContain(
      'Review link issued. Copy it now',
    )
  })

  it('guards a feedback session jump and then opens its authoritative Calendar occurrence', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    await renderNavigationHarness()
    const calendarDate =
      document.querySelector<HTMLInputElement>(
        '#calendar-anchor-date',
      )!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
        ?.set?.call(calendarDate, '05.10.2026')
      calendarDate.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      [...document.querySelectorAll<HTMLButtonElement>(
        '.calendar-occurrence',
      )]
        .find((item) => item.textContent?.includes('Lehrtermin'))
        ?.click()
    })
    await act(async () => button('Termin bearbeiten')?.click())
    const editorDate =
      document.querySelector<HTMLInputElement>(
        '.session-pane input[inputmode="numeric"]',
      )!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')
        ?.set?.call(editorDate, '06.10.2026')
      editorDate.dispatchEvent(new Event('input', { bubbles: true }))
      editorDate.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      button('Show lecturer reviews')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => button('Aktuellen Termin öffnen')?.click())

    expect(document.body.textContent).toContain('Ungespeicherte Änderungen verwerfen?')
    expect(
      document.querySelector<HTMLElement>('.lecturer-reviews-region')?.hidden,
    ).toBe(false)
    await act(async () => button('Weiter bearbeiten')?.click())
    expect(
      document.querySelector<HTMLElement>('.lecturer-reviews-region')?.hidden,
    ).toBe(false)

    await act(async () => button('Aktuellen Termin öffnen')?.click())
    await act(async () => {
      document.querySelector<HTMLButtonElement>('.discard-changes-dialog .destructive-button')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(
      document.querySelector<HTMLElement>('.calendar-workspace-region')?.hidden,
    ).toBe(false)
    expect(
      [...document.querySelectorAll<HTMLSelectElement>(
        '.schedule-context-field select',
      )][1].value,
    ).toBe('11')
    expect(document.querySelector('.session-pane')?.textContent)
      .toContain('Prüfungstermin')
    expect(
      document.querySelector<HTMLButtonElement>(
        '[data-occurrence-ref="exam:1"]',
      )?.getAttribute('aria-pressed'),
    ).toBe('true')
  })

  it('announces and focuses Calendar results when a feedback target no longer exists', async () => {
    mocks.getLecturerReviewOverview.mockResolvedValue(
      lecturerReviewOverviewForRevision(11, 'exam:999'),
    )
    await renderNavigationHarness()
    await act(async () => {
      button('Show lecturer reviews')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => {
      button('Aktuellen Termin öffnen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('.session-pane')).toBeNull()
    expect(document.querySelector('.calendar-navigation-status')?.textContent)
      .toContain('Der aktuelle Termin ist in dieser Revision nicht mehr verfügbar.')
    expect(document.activeElement?.hasAttribute('data-workspace-results-heading'))
      .toBe(true)
  })

  it('hides Planning inputs independently without hiding the compact context', async () => {
    await renderPage()
    expect(document.querySelector<HTMLElement>('#planning-inputs')?.hidden).toBe(false)
    await act(async () => button('Planungseingaben ausblenden')?.click())
    expect(document.querySelector<HTMLElement>('#planning-inputs')?.hidden).toBe(true)
    expect(document.querySelector('[aria-label="Terminplanung – Kontext"]')).not.toBeNull()
    expect(document.querySelector('.planner-grid')?.getAttribute('data-planning-inputs-visible')).toBe('false')
    await act(async () => button('Planungseingaben anzeigen')?.click())
    expect(document.querySelector<HTMLElement>('#planning-inputs')?.hidden).toBe(false)
  })

  it('identifies a retained course that is not assigned to the newly selected semester', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      courses: [
        { ...options.courses[0], semesterId: 1 },
        { ...options.courses[1], semesterId: 2 },
      ],
      semesters: [
        ...options.semesters,
        { id: 2, name: 'Spring 2027', startDate: '2027-02-15', endDate: '2027-06-30' },
      ],
    })
    await renderPage()
    await act(async () => button('Planungseingaben ausblenden')?.click())
    const contextSelects = document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')
    const semesterSelect = contextSelects[0]
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(semesterSelect, '2')
      semesterSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await Promise.resolve()
    })

    const courseSelect = document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')[2]
    expect(courseSelect.selectedOptions[0]?.textContent).toContain('dem ausgewählten Semester nicht zugeordnet')
    expect(document.querySelector<HTMLElement>('#planning-inputs')?.hidden).toBe(true)
  })

  it('loads the Working workspace by default and renders the adapted overview once', async () => {
    await renderPage()

    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1, 11)
    expect(document.body.textContent).toContain('Aktive Arbeitsrevision')
    expect(document.body.textContent?.match(/Lehrveranstaltungen/g)).toBeTruthy()
  })

  it('falls back coherently to Current Published when no Working revision exists', async () => {
    mocks.getScheduleLifecycle.mockResolvedValue(publishedLifecycleOverview())
    mocks.getScheduleRevision.mockResolvedValue({
      revision: publishedLifecycleOverview().currentPublication,
      snapshot: snapshotFixture(),
    })
    mocks.getCalendarWorkspace.mockResolvedValue(publishedCalendarWorkspace())

    await renderPage()
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1, 12)
    expect(document.body.textContent).toContain('Aktuelle Veröffentlichung')
    expect(document.body.textContent).toContain('Veröffentlichte Inhalte sind schreibgeschützt')
  })

  it('renders the no-revision workspace without inventing revision-owned records', async () => {
    const base = lifecycleOverviewFixture()
    mocks.getScheduleLifecycle.mockResolvedValue({
      ...base,
      activeWorkingRevision: null,
      currentPublication: null,
      revisions: [],
      allowedActions: { createWorkingRevision: true },
    })
    mocks.getCalendarWorkspace.mockResolvedValue(noRevisionWorkspaceFixture())

    await renderPage()
    await act(async () => { await new Promise((resolve) => setTimeout(resolve, 0)) })

    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1, undefined)
    expect(document.body.textContent).toContain('Es gibt noch keine Planungsrevision')
    expect(button('Entwurf starten')).toBeTruthy()
    const requirement = [...document.querySelectorAll('label')]
      .find((item) => item.textContent?.includes('ist eine Prüfung erforderlich'))
      ?.querySelector<HTMLInputElement>('input')
    expect(requirement?.disabled).toBe(false)
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(true)
    expect(document.body.textContent).toContain('Starten Sie vor dem Hinzufügen von Terminen einen Entwurf.')
  })

  it('requires complete lifecycle identity before accepting a cached calendar workspace', () => {
    const draft = lifecycleOverviewFixture().activeWorkingRevision!
    const workspace = loadedCalendarWorkspaceFixture()

    expect(calendarWorkspaceMatchesSelection(workspace, 1, draft)).toBe(true)
    expect(calendarWorkspaceMatchesSelection(workspace, 1, {
      ...draft,
      state: 'ready_for_review',
    })).toBe(false)
    expect(calendarWorkspaceMatchesSelection(workspace, 1, {
      ...draft,
      state: 'published',
      isActiveWorking: false,
      isCurrentPublication: true,
    })).toBe(false)
    expect(calendarWorkspaceMatchesSelection({
      ...workspace,
      selectedRevision: {
        ...workspace.selectedRevision,
        designation: 'current_published',
      },
    }, 1, draft)).toBe(false)
    expect(calendarWorkspaceMatchesSelection({
      ...workspace,
      selectedRevision: {
        ...workspace.selectedRevision,
        readOnly: true,
      },
    }, 1, draft)).toBe(false)
    expect(calendarWorkspaceMatchesSelection(workspace, 1, {
      ...draft,
      isActiveWorking: false,
      isCurrentPublication: false,
    })).toBe(false)
    expect(calendarWorkspaceMatchesSelection(workspace, 1, null)).toBe(false)
    expect(calendarWorkspaceMatchesSelection(noRevisionWorkspaceFixture(), 1, null)).toBe(true)
  })

  it('keeps the latest revision selection when workspace responses resolve out of order', async () => {
    const lifecycle = lifecycleWithWorkingAndPublished()
    const initialWorking = workingCalendarWithPublishedAvailable()
    const currentWorking = {
      ...workingCalendarWithPublishedAvailable(),
      workspaceToken: 'working-current',
      courses: workingCalendarWithPublishedAvailable().courses.map((course) => ({
        ...course,
        name: 'Current Working course',
      })),
      filterFacets: {
        ...workingCalendarWithPublishedAvailable().filterFacets,
        courses: [{ value: 'course:1', label: 'Current Working course' }],
      },
    }
    const stalePublished = {
      ...publishedCalendarWithWorkingAvailable(),
      workspaceToken: 'published-stale',
      courses: publishedCalendarWithWorkingAvailable().courses.map((course) => ({
        ...course,
        name: 'Stale Published course',
      })),
      filterFacets: {
        ...publishedCalendarWithWorkingAvailable().filterFacets,
        courses: [{ value: 'course:1', label: 'Stale Published course' }],
      },
    }
    const publishedRequest = deferred<typeof stalePublished>()
    const workingRequest = deferred<typeof currentWorking>()
    mocks.getScheduleLifecycle.mockResolvedValue(lifecycle)
    mocks.getScheduleRevision.mockResolvedValue({
      revision: lifecycle.currentPublication,
      contentSource: 'captured_snapshot',
      snapshot: snapshotFixture(),
    })
    mocks.getCalendarWorkspace.mockImplementation((_semesterId, revisionId) => {
      if (revisionId === 12) return publishedRequest.promise
      if (revisionId === 11) return workingRequest.promise
      return Promise.resolve(initialWorking)
    })

    await renderPage()
    await act(async () => {
      button('Veröffentlichung R2')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1, 12)
    await act(async () => {
      const revisionSelect = [...document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')][1]
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(revisionSelect, '11')
      revisionSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1, 11)
    await act(async () => {
      workingRequest.resolve(currentWorking)
      await workingRequest.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    await act(async () => {
      publishedRequest.resolve(stalePublished)
      await publishedRequest.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('Aktive Arbeitsrevision')
    expect(document.body.textContent).toContain('Current Working course')
    expect(document.body.textContent).not.toContain('Stale Published course')
  })

  it('replaces same-revision Draft identity with Ready for review after lifecycle refresh', async () => {
    const draft = lifecycleOverviewFixture()
    const readyRevision = {
      ...draft.activeWorkingRevision!,
      revisionVersion: 2,
      state: 'ready_for_review' as const,
      allowedActions: {
        ...draft.activeWorkingRevision!.allowedActions,
        markReady: false,
        returnToDraft: true,
      },
    }
    const ready = {
      ...draft,
      stateToken: 'state-ready',
      activeWorkingRevision: readyRevision,
      revisions: [readyRevision],
    }
    const readyWorkspace = {
      ...loadedCalendarWorkspaceFixture(),
      selectedRevision: {
        ...loadedCalendarWorkspaceFixture().selectedRevision,
        lifecycleState: 'ready_for_review' as const,
      },
      availableContexts: {
        ...loadedCalendarWorkspaceFixture().availableContexts,
        activeWorking: {
          ...loadedCalendarWorkspaceFixture().availableContexts.activeWorking!,
          lifecycleState: 'ready_for_review' as const,
        },
      },
      workspaceToken: 'working-ready-v2',
    }
    let readyPhase = false
    mocks.transitionScheduleRevision.mockImplementation(async () => {
      readyPhase = true
      return ready
    })
    mocks.getScheduleLifecycle.mockImplementation(async () => readyPhase ? ready : draft)
    mocks.getCalendarWorkspace.mockImplementation(async () => (
      readyPhase ? readyWorkspace : loadedCalendarWorkspaceFixture()
    ))

    await renderPage()
    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
      await Promise.resolve()
    })
    await act(async () => {
      document.querySelector<HTMLButtonElement>('.calendar-occurrence')?.click()
      await Promise.resolve()
    })
    const sessionType = [...document.querySelectorAll<HTMLSelectElement>('select')]
      .find((item) => item.previousElementSibling?.textContent === 'Terminart')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(sessionType, 'teaching')
      sessionType.dispatchEvent(new Event('change', { bubbles: true }))
      button('Liste')?.click()
      await Promise.resolve()
    })
    expect(document.querySelector('.session-pane')).not.toBeNull()
    expect(document.querySelector('.active-filter-status')).not.toBeNull()
    await act(async () => {
      button('Als prüfbereit markieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
      await new Promise((resolve) => setTimeout(resolve, 0))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('Bereit zur Prüfung (nicht freigegeben)')
    expect(document.body.textContent).toContain('Die Revision wurde als bereit zur Prüfung markiert.')
    expect(button('Liste')?.getAttribute('aria-pressed')).toBe('true')
    expect(document.querySelector('.session-pane')).not.toBeNull()
    expect(document.querySelector('.active-filter-status')).not.toBeNull()
  })

  it('edits teaching in the Calendar pane and retains the established deletion workflow', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    await renderPage()
    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Lehrtermin'))?.click()
    })
    await act(async () => button('Termin bearbeiten')?.click())
    expect(button('Speichern')).toBeTruthy()
    await act(async () => button('Abbrechen')?.click())
    expect(button('Woche')?.getAttribute('aria-pressed')).toBe('true')

    await act(async () => button('Woche')?.click())
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Lehrtermin'))?.click()
    })
    await act(async () => button('Mit Bestätigung löschen')?.click())
    expect(document.body.textContent).toContain('Diesen Entwurfstermin löschen?')
    expect(mocks.deleteDraftSession).not.toHaveBeenCalled()
    await act(async () => button('Abbrechen')?.click())
  })

  it('does not expose pane actions when editable schedule details failed to load', async () => {
    mocks.getDraftSchedules.mockRejectedValue(new Error('draft overview unavailable'))
    await renderPage()
    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Lehrtermin'))?.click()
    })

    expect(button('Termin bearbeiten')).toBeUndefined()
    expect(button('Mit Bestätigung löschen')).toBeUndefined()
    expect(document.querySelector('.session-pane')?.textContent)
      .toContain('Terminaktionen sind nicht verfügbar, weil die bearbeitbaren Planungsdetails nicht geladen werden konnten.')
  })

  it('leaves edit mode with an explanation when refreshed backing details disappear', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    const root = await renderPage()
    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Lehrtermin'))?.click()
    })
    await act(async () => button('Termin bearbeiten')?.click())
    expect(document.querySelector('.session-pane-editing')).not.toBeNull()

    mocks.getDraftSchedules.mockResolvedValue([])
    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={1} destination="calendar" />)
      await new Promise((resolve) => setTimeout(resolve, 0))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('.session-pane-editing')).toBeNull()
    expect(document.querySelector('.session-pane-detail')).not.toBeNull()
    expect(document.querySelector('.session-pane')?.textContent)
      .toContain('Die Bearbeitung wurde beendet, weil die bearbeitbaren Termindetails nicht mehr verfügbar sind.')
  })

  it('keeps dirty pane work by default and discards only after explicit confirmation', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    await renderPage()
    const calendarDate = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(calendarDate, '05.10.2026')
      calendarDate.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const occurrence = [...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
      .find((item) => item.textContent?.includes('Lehrtermin'))!
    await act(async () => occurrence.click())
    await act(async () => button('Termin bearbeiten')?.click())
    const editorDate = document.querySelector<HTMLInputElement>('.session-pane input[inputmode="numeric"]')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(editorDate, '06.10.2026')
      editorDate.dispatchEvent(new Event('input', { bubbles: true }))
      editorDate.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const close = document.querySelector<HTMLButtonElement>('[aria-label="Termindetails schließen"]')!
    await act(async () => close.click())
    expect(document.body.textContent).toContain('Ungespeicherte Änderungen verwerfen?')
    await act(async () => button('Weiter bearbeiten')?.click())
    expect(document.querySelector('.session-pane-editing')).not.toBeNull()
    expect(document.querySelector('.session-pane')?.contains(document.activeElement)).toBe(true)
    await act(async () => document.querySelector<HTMLButtonElement>('[aria-label="Termindetails schließen"]')?.click())
    await act(async () => document.querySelector<HTMLButtonElement>('.discard-changes-dialog .destructive-button')?.click())
    expect(document.querySelector('.session-pane')).toBeNull()
    expect(document.activeElement).toBe(occurrence)
  })

  it('ignores an older save refresh after the selected semester changes', async () => {
    const secondSemester = {
      id: 2,
      name: 'Spring 2027',
      startDate: '2027-02-15',
      endDate: '2027-06-30',
    }
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [...options.semesters, secondSemester],
    })
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.updateDraftSession.mockResolvedValue(draftScheduleFixture)
    await renderPage()

    const oldLifecycle = deferred<ReturnType<typeof lifecycleOverviewFixture>>()
    const oldCalendar = deferred<ReturnType<typeof loadedCalendarWorkspaceFixture>>()
    const oldDrafts = deferred<typeof draftScheduleFixture[]>()
    const oldExams = deferred<typeof examOverview>()
    const lifecycle2Base = lifecycleOverviewFixture()
    const revision2 = {
      ...lifecycle2Base.activeWorkingRevision!,
      revisionId: 22,
      semesterId: 2,
      revisionNumber: 4,
    }
    const lifecycle2 = {
      ...lifecycle2Base,
      semesterId: 2,
      semesterName: secondSemester.name,
      stateToken: 'state-2',
      activeWorkingRevision: revision2,
      revisions: [revision2],
    }
    const workspace2Base = loadedCalendarWorkspaceFixture()
    const workspace2 = {
      ...workspace2Base,
      semester: {
        semesterId: 2,
        name: secondSemester.name,
        startDate: secondSemester.startDate,
        endDate: secondSemester.endDate,
      },
      selectedRevision: {
        ...workspace2Base.selectedRevision,
        revisionId: 22,
        revisionNumber: 4,
      },
      availableContexts: {
        activeWorking: {
          ...workspace2Base.availableContexts.activeWorking!,
          revisionId: 22,
          revisionNumber: 4,
        },
        currentPublished: null,
      },
      workspaceToken: 'semester:2:revision:22',
      courses: [],
      occurrences: [],
    }
    const examOverview2 = { ...examOverview, semesterId: 2, courses: [] }
    mocks.getScheduleLifecycle.mockImplementation((semesterId: number) => (
      semesterId === 1 ? oldLifecycle.promise : Promise.resolve(lifecycle2)
    ))
    mocks.getCalendarWorkspace.mockImplementation((semesterId: number) => (
      semesterId === 1 ? oldCalendar.promise : Promise.resolve(workspace2)
    ))
    mocks.getDraftSchedules.mockImplementation((semesterId: number) => (
      semesterId === 1 ? oldDrafts.promise : Promise.resolve([])
    ))
    mocks.getExamPlanningOverview.mockImplementation((semesterId: number) => (
      semesterId === 1 ? oldExams.promise : Promise.resolve(examOverview2)
    ))
    mocks.getScheduleLifecycle.mockClear()
    mocks.getCalendarWorkspace.mockClear()
    mocks.getDraftSchedules.mockClear()
    mocks.getExamPlanningOverview.mockClear()

    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '05.10.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Lehrtermin'))?.click()
    })
    await act(async () => {
      button('Termin bearbeiten')?.click()
    })
    await act(async () => {
      button('Speichern')?.click()
      await Promise.resolve()
    })
    expect(mocks.updateDraftSession).toHaveBeenCalled()
    expect(mocks.getScheduleLifecycle).toHaveBeenCalledWith(1)
    expect(mocks.getCalendarWorkspace).toHaveBeenCalledWith(1)
    expect(mocks.getDraftSchedules).toHaveBeenCalledWith(1)
    expect(mocks.getExamPlanningOverview).toHaveBeenCalledWith(1)

    const semesterSelect = document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')[0]
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(semesterSelect, '2')
      semesterSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    await act(async () => {
      oldLifecycle.resolve(lifecycleOverviewFixture())
      oldCalendar.resolve(loadedCalendarWorkspaceFixture())
      oldDrafts.resolve([draftScheduleFixture])
      oldExams.resolve(examOverview)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(semesterSelect.value).toBe('2')
    expect(document.querySelector('[data-revision-id="22"]')).not.toBeNull()
    expect(document.querySelector('[data-revision-id="11"]')).toBeNull()
  })

  it('does not start a stale refresh when an older mutation resolves after a semester change', async () => {
    const mutation = deferred<{
      courseId: number
      semesterId: number
      scheduledUnits: number
      remainingUnits: number
      draftSchedule: typeof draftScheduleFixture
    }>()
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [
        ...options.semesters,
        { id: 2, name: 'Spring 2027', startDate: '2027-02-15', endDate: '2027-06-30' },
      ],
    })
    mocks.createManualDraftSession.mockReturnValue(mutation.promise)
    await renderPage()

    await act(async () => {
      button('Entwurfstermin hinzufügen')?.click()
      await Promise.resolve()
    })
    const semesterSelect = document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')[0]
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(semesterSelect, '2')
      semesterSelect.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    mocks.getScheduleLifecycle.mockClear()
    mocks.getCalendarWorkspace.mockClear()
    mocks.getDraftSchedules.mockClear()
    mocks.getExamPlanningOverview.mockClear()

    await act(async () => {
      mutation.resolve({
        courseId: 1,
        semesterId: 1,
        scheduledUnits: 2,
        remainingUnits: 6,
        draftSchedule: draftScheduleFixture,
      })
      await mutation.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(semesterSelect.value).toBe('2')
    expect(mocks.getScheduleLifecycle).not.toHaveBeenCalled()
    expect(mocks.getCalendarWorkspace).not.toHaveBeenCalled()
    expect(mocks.getDraftSchedules).not.toHaveBeenCalled()
    expect(mocks.getExamPlanningOverview).not.toHaveBeenCalled()
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(false)
  })

  it('focuses the committed context after discarding a dirty course change', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    await renderPage()
    const calendarDate = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(calendarDate, '05.10.2026')
      calendarDate.dispatchEvent(new Event('change', { bubbles: true }))
    })
    const occurrence = [...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
      .find((item) => item.textContent?.includes('Lehrtermin'))!
    await act(async () => occurrence.click())
    await act(async () => button('Termin bearbeiten')?.click())
    const editorDate = document.querySelector<HTMLInputElement>('.session-pane input[inputmode="numeric"]')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(editorDate, '06.10.2026')
      editorDate.dispatchEvent(new Event('input', { bubbles: true }))
      editorDate.dispatchEvent(new Event('change', { bubbles: true }))
    })

    const courseSelect = [...document.querySelectorAll<HTMLSelectElement>('.schedule-context-field select')][2]
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(courseSelect, '2')
      courseSelect.dispatchEvent(new Event('change', { bubbles: true }))
    })
    expect(document.body.textContent).toContain('Ungespeicherte Änderungen verwerfen?')
    await act(async () => {
      document.querySelector<HTMLButtonElement>('.discard-changes-dialog .destructive-button')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('.session-pane')).toBeNull()
    expect(courseSelect.value).toBe('2')
    expect(document.activeElement).toBe(document.querySelector('.schedule-context-surface h2'))
  })

  it('edits exams in the Calendar pane and retains the established deletion workflow', async () => {
    const activeExam = {
      id: 1,
      revision: 1,
      courseId: 1,
      semesterId: 1,
      configurationIdentifier: 'FINAL',
      examType: 'Written',
      durationMinutes: 120,
      requiredCapacity: 30,
      recommendedStartDate: '2026-12-08',
      recommendedEndDate: '2026-12-15',
      recommendationWasOverridden: true,
      outsideRecommendedWindow: false,
      finalTeachingAnchor: {
        date: '2026-12-01',
        endTime: '12:00',
        teachingSessionId: 1,
      },
      date: '2026-12-10',
      startTime: '09:00',
      endTime: '11:00',
      lecturer: { id: 1, name: 'Ada', referenceCode: 'L-1' },
      cohort: { id: 1, name: 'C1', referenceCode: null },
      room: {
        id: 3,
        name: 'Large room',
        referenceCode: 'ROOM-003',
        capacity: 40,
      },
      lifecycleStatus: 'active' as const,
      source: 'manual' as const,
      validityIssues: [],
      inputSnapshotToken: 'exam-token',
    }
    const configuration = {
      id: 10,
      revision: 1,
      identifier: 'FINAL',
      durationMinutes: 120,
      recommendedStartOverride: null,
      recommendedEndOverride: null,
      requiredCapacity: 30,
      examType: 'Written',
      responsibleLecturerId: 1,
      configurationConsumed: true,
      recommendedStartDate: '2026-12-08',
      recommendedEndDate: '2026-12-15',
      recommendationWasOverridden: true,
    }
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      lecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', isActive: true, revision: 1 }],
      courseResources: [{
        courseId: 1,
        eligibleLecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        eligibleRooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', kind: 'room', capacity: 40, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
      }],
    })
    mocks.getExamPlanningOverview.mockResolvedValue({
      ...examOverview,
      courses: examOverview.courses.map((course) => course.courseId === 1
        ? {
            ...course,
            enabled: true,
            configuration,
            finalTeachingAnchor: activeExam.finalTeachingAnchor,
            activeExam,
            generationEligibility: {
              eligible: false,
              code: 'ACTIVE_EXAM_EXISTS',
              message: 'An active exam already exists.',
            },
          }
        : course),
    })

    await renderPage()
    const dateInput = document.querySelector<HTMLInputElement>('#calendar-anchor-date')!
    await act(async () => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(dateInput, '10.12.2026')
      dateInput.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      ;[...document.querySelectorAll<HTMLButtonElement>('.calendar-occurrence')]
        .find((item) => item.textContent?.includes('Prüfungstermin'))?.click()
    })
    await act(async () => button('Termin bearbeiten')?.click())
    expect(document.body.textContent).toContain('Prüfungstermin korrigieren')
    await act(async () => button('Abbrechen')?.click())

    await act(async () => button('Mit Bestätigung löschen')?.click())
    expect(document.body.textContent).toContain('Prüfung löschen?')
    expect(mocks.deleteExam).not.toHaveBeenCalled()
    await act(async () => button('Abbrechen')?.click())
  })

  it('does not label live schedules as a publication while its snapshot is loading', async () => {
    const draft = lifecycleOverviewFixture().activeWorkingRevision!
    const published = {
      ...draft,
      state: 'published' as const,
      isActiveWorking: false,
      isCurrentPublication: true,
      publishedAt: draft.stateChangedAt,
      allowedActions: { markReady: false, returnToDraft: false, preparePublication: false, abandon: false, restore: false, editSchedule: false },
    }
    mocks.getScheduleLifecycle.mockResolvedValue({
      ...lifecycleOverviewFixture(),
      activeWorkingRevision: null,
      currentPublication: published,
      revisions: [published],
      allowedActions: { createWorkingRevision: true },
    })
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.getScheduleRevision.mockImplementation(() => new Promise(() => undefined))

    await renderPage()

    expect(document.body.textContent).toContain('Ausgewählte Revision wird geladen')
    expect(document.body.textContent).not.toContain('Ada Lovelace')
  })

  it('keeps live schedules hidden when a publication snapshot cannot be loaded', async () => {
    const draft = lifecycleOverviewFixture().activeWorkingRevision!
    const published = {
      ...draft,
      state: 'published' as const,
      isActiveWorking: false,
      isCurrentPublication: true,
      publishedAt: draft.stateChangedAt,
      allowedActions: { markReady: false, returnToDraft: false, preparePublication: false, abandon: false, restore: false, editSchedule: false },
    }
    mocks.getScheduleLifecycle.mockResolvedValue({
      ...lifecycleOverviewFixture(),
      activeWorkingRevision: null,
      currentPublication: published,
      revisions: [published],
      allowedActions: { createWorkingRevision: true },
    })
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.getScheduleRevision.mockRejectedValue({ errors: [{ message: 'Captured publication is unavailable.' }] })

    await renderPage()

    expect(document.body.textContent).toContain('ausgewählte Revision konnte nicht geladen werden')
    expect(document.body.textContent).not.toContain('Ada Lovelace')
    expect(document.body.textContent).not.toContain('Ausgewählte Revision wird geladen')
  })

  it('retries a failed publication snapshot without changing revisions', async () => {
    const draft = lifecycleOverviewFixture().activeWorkingRevision!
    const published = {
      ...draft,
      state: 'published' as const,
      isActiveWorking: false,
      isCurrentPublication: true,
      publishedAt: draft.stateChangedAt,
      allowedActions: { markReady: false, returnToDraft: false, preparePublication: false, abandon: false, restore: false, editSchedule: false },
    }
    mocks.getScheduleLifecycle.mockResolvedValue({
      ...lifecycleOverviewFixture(),
      activeWorkingRevision: null,
      currentPublication: published,
      revisions: [published],
      allowedActions: { createWorkingRevision: true },
    })
    mocks.getScheduleRevision
      .mockRejectedValueOnce({ errors: [{ message: 'Captured publication is unavailable.' }] })
      .mockResolvedValueOnce({ revision: published, contentSource: 'captured_snapshot', snapshot: snapshotFixture() })

    await renderPage()
    expect(document.body.textContent).toContain('ausgewählte Revision konnte nicht geladen werden')

    await act(async () => {
      button('Revision erneut laden')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(mocks.getScheduleRevision).toHaveBeenCalledTimes(2)
    expect(document.body.textContent).not.toContain('Captured publication is unavailable.')
    expect(document.body.textContent).toContain('Aktuelle Veröffentlichung')
  })

  it('blocks further exam writes when an authoritative post-save refresh fails', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      lecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', isActive: true, revision: 1 }],
      courseResources: [{
        courseId: 1,
        eligibleLecturers: [{ id: 1, name: 'Ada', referenceCode: 'L-1', kind: 'lecturer', capacity: null, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        eligibleRooms: [{ id: 3, name: 'Large room', referenceCode: 'ROOM-003', kind: 'room', capacity: 40, isActive: true, isEligible: true, isUsable: true, reasons: [] }],
        preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
      }],
    })
    const savedState = {
      ...examOverview.courses[0], enabled: true,
      configuration: { id: 10, revision: 1, identifier: 'Exam', durationMinutes: 90, recommendedStartOverride: null, recommendedEndOverride: null, requiredCapacity: 1, examType: 'Written', responsibleLecturerId: 1, configurationConsumed: false, recommendedStartDate: null, recommendedEndDate: null, recommendationWasOverridden: false },
      generationEligibility: { eligible: false, code: 'FINAL_TEACHING_SESSION_MISSING', message: 'Save teaching first.' },
    }
    mocks.saveExamConfiguration.mockResolvedValue(savedState)
    await renderPage()
    mocks.getExamPlanningOverview.mockRejectedValueOnce(new Error('refresh failed'))
    const requirement = [...document.querySelectorAll('label')].find((item) => item.textContent?.includes('ist eine Prüfung erforderlich'))?.querySelector<HTMLInputElement>('input')
    await act(async () => requirement?.click())
    await act(async () => { button('Prüfungsanforderung speichern')?.click(); await new Promise((resolve) => setTimeout(resolve, 0)) })
    expect(document.body.textContent).toContain('gespeichert, aber die Semesterübersicht konnte nicht aktualisiert werden')
    expect(requirement?.disabled).toBe(true)
    expect(button('Speichern…')).toBeUndefined()
    expect(button('Prüfungsanforderung speichern')?.disabled).toBe(true)
  })

  it('does not warn for disabled courses and explains an enabled course without a final teaching anchor', async () => {
    const root = await renderPage()
    expect(document.body.textContent).not.toContain('Noch kein letzter Lehrtermin gespeichert.')

    await act(async () => root.unmount())
    document.body.innerHTML = ''

    mocks.getExamPlanningOverview.mockResolvedValue({
      ...examOverview,
      courses: examOverview.courses.map((course) => course.courseId === 1 ? {
        ...course,
        enabled: true,
        configuration: {
          id: 10, revision: 1, identifier: 'Final exam', durationMinutes: 90,
          recommendedStartOverride: null, recommendedEndOverride: null,
          requiredCapacity: 30, examType: 'Written', responsibleLecturerId: 1,
          configurationConsumed: false, recommendedStartDate: null,
          recommendedEndDate: null, recommendationWasOverridden: false,
        },
        generationEligibility: { eligible: false, code: 'FINAL_TEACHING_SESSION_MISSING', message: 'A final teaching session is required.' },
      } : course),
    })
    await renderPage()
    expect(document.body.textContent).toContain('Noch kein letzter Lehrtermin gespeichert.')
    expect(document.body.textContent).toContain('automatische und manuelle Platzierung bleiben bis dahin blockiert')
  })

  it('renders scheduling content without page-owned or dead hash navigation', async () => {
    await renderPage()
    expect(document.querySelector('nav')).toBeNull()
    expect(document.querySelectorAll('a[href^="#"]')).toHaveLength(0)
    expect(document.body.textContent).not.toContain('Dashboard')
    expect(document.body.textContent).toContain('Ressourcenplanung')
  })

  it('keeps focused single-course constraints isolated while selecting and generating several courses', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, scheduleRevisionId: 11, unavailableDates: ['2026-10-26', '2026-11-02'], sharedSnapshotToken: 'shared', replacementCourseIds: [],
      courses: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: `course-${courseId}` })),
    })
    mocks.generateBatch.mockResolvedValue({
      mode: 'direct_saved',
      semesterId: 1, summary: { total: 2, complete: 2, improvedPartial: 0, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 16, remainingUnits: 0, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
      outcomes: [1, 2].map((courseId) => ({ courseId, courseName: `Course ${courseId}`, status: 'complete', draftScheduleId: courseId, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] })),
    })
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    const unavailableDates = document.querySelector<HTMLInputElement>('input[type="text"]')
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(unavailableDates, '02.11.2026, 26.10.2026, 26.10.2026')
      unavailableDates?.dispatchEvent(new Event('input', { bubbles: true }))
    })
    expect(document.body.textContent).toContain('2 ausgewählt')
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.prepare).toHaveBeenCalledWith(1, 11, [1, 2], ['2026-10-26', '2026-11-02'])
    expect(mocks.generateBatch).toHaveBeenCalledOnce()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).toContain('2 vollständig · 0 teilweise verbessert')
    expect(mocks.getGenerationConstraints).toHaveBeenCalledTimes(1)
  })

  it('shows course-specific blocking reasons when no valid alternative exists', async () => {
    mocks.prepare.mockResolvedValue(optimizationPreparationFixture)
    mocks.generateBatch.mockRejectedValue([{
      code: 'NO_VALID_ALTERNATIVE',
      message: 'Course 1: Founders Day removes the only allowed date.',
    }])
    await renderPage()
    act(() => document.querySelector<HTMLInputElement>('.multi-course-panel input[type="checkbox"]')?.click())

    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('Keine gültige Alternative')
    expect(document.body.textContent).toContain('Course 1: Founders Day')
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('shows each course draft status in several-course mode', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    await renderPage()

    act(() => button('Mehrere Lehrveranstaltungen')?.click())

    const statuses = [...document.querySelectorAll('.course-draft-status')].map((status) => status.textContent)
    expect(statuses).toEqual(['Entwurf · 8/8 Lehreinheiten', 'Kein Entwurf'])
  })

  it('clears the batch selection when the semester changes', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [...options.semesters, { id: 2, name: 'Spring 2027', startDate: '2027-02-01', endDate: '2027-06-20' }],
      courses: [
        { ...options.courses[0], semesterId: 1, availability: { available: true, reasons: [] } },
        { ...options.courses[1], semesterId: 2, availability: { available: true, reasons: [] } },
      ],
    })
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    act(() => document.querySelector<HTMLInputElement>('input[type="checkbox"]')?.click())
    expect(document.body.textContent).toContain('1 ausgewählt')

    const semesterSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')
    await act(async () => {
      if (semesterSelect) semesterSelect.value = '2'
      semesterSelect?.dispatchEvent(new Event('change', { bubbles: true }))
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('0 ausgewählt')
  })

  it('discards a post-generation replacement comparison without accepting it', async () => {
    mocks.prepare.mockResolvedValue({
      semesterId: 1, scheduleRevisionId: 11, unavailableDates: [], sharedSnapshotToken: 'shared', replacementCourseIds: [1],
      courses: [
        { courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: 5, draftRevision: 2, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, inputSnapshotToken: 'course-1' },
        { courseId: 2, courseName: 'Course 2', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-2' },
      ],
    })
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
    act(() => button('Abbrechen')?.click())
    expect(mocks.generateBatch).toHaveBeenCalledTimes(1)
    expect(mocks.acceptBatch).not.toHaveBeenCalled()
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('blocks schedule mutations while the generated comparison is open', async () => {
    const customConstraints = {
      ...generationConstraintsFixture,
      isCustom: true,
      revision: 3,
      planningPeriod: { startDate: '2026-09-14', endDate: '2026-12-10' },
    }
    mocks.getGenerationConstraints.mockResolvedValue(customConstraints)
    mocks.prepare.mockResolvedValue({
      semesterId: 1, scheduleRevisionId: 11, unavailableDates: [], sharedSnapshotToken: 'shared', replacementCourseIds: [1],
      courses: [{ courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: 5, draftRevision: 2, scheduledUnits: 4, remainingUnits: 4, replacementRequired: true, inputSnapshotToken: 'course-1' }],
    })
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    await renderPage()
    act(() => document.querySelector<HTMLInputElement>('.multi-course-panel input[type="checkbox"]')?.click())
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()

    const resetButton = button('Benutzerdefinierte Regeln zurücksetzen') as HTMLButtonElement
    expect(resetButton.disabled).toBe(true)
    act(() => resetButton.click())
    expect(mocks.clearGenerationConstraints).not.toHaveBeenCalled()
    const generate = document.querySelector<HTMLButtonElement>('.multi-course-panel .generate-button')
    expect(generate?.disabled).toBe(true)
    expect(generate?.textContent).toContain('optimieren')
    expect(generate?.textContent).not.toContain('werden optimiert')
    act(() => generate?.click())
    expect(mocks.prepare).toHaveBeenCalledTimes(1)
    act(() => button('Abbrechen')?.click())
    expect(document.querySelector('[role="dialog"]')).toBeNull()
  })

  it('blocks constraint reset while unified preparation is in flight', async () => {
    const customConstraints = {
      ...generationConstraintsFixture,
      isCustom: true,
      revision: 3,
      planningPeriod: { startDate: '2026-09-14', endDate: '2026-12-10' },
    }
    const preparation = deferred<{
      semesterId: number
      scheduleRevisionId: number
      unavailableDates: string[]
      sharedSnapshotToken: string
      replacementCourseIds: number[]
      courses: Array<{
        courseId: number
        courseName: string
        available: boolean
        draftScheduleId: number
        draftRevision: number
        scheduledUnits: number
        remainingUnits: number
        replacementRequired: boolean
        inputSnapshotToken: string
      }>
    }>()
    mocks.getGenerationConstraints.mockResolvedValue(customConstraints)
    mocks.prepare.mockReturnValue(preparation.promise)
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    await renderPage()
    act(() => document.querySelector<HTMLInputElement>('.multi-course-panel input[type="checkbox"]')?.click())

    act(() => button('Ausgewählte Lehrveranstaltungen optimieren')?.click())

    const resetButton = document.querySelector<HTMLButtonElement>('.generation-constraints .secondary-button')
    expect(resetButton?.disabled).toBe(true)
    act(() => resetButton?.click())
    expect(mocks.clearGenerationConstraints).not.toHaveBeenCalled()

    await act(async () => {
      preparation.resolve({
        semesterId: 1,
        scheduleRevisionId: 11,
        unavailableDates: [],
        sharedSnapshotToken: 'shared',
        replacementCourseIds: [1],
        courses: [{
          courseId: 1,
          courseName: 'Course 1',
          available: true,
          draftScheduleId: 5,
          draftRevision: 2,
          scheduledUnits: 4,
          remainingUnits: 4,
          replacementRequired: true,
          inputSnapshotToken: 'course-1',
        }],
      })
      await preparation.promise
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('[role="dialog"]')).not.toBeNull()
  })

  it('re-prepares failed and stale courses before retrying and refreshes each result', async () => {
    const preparation = {
      semesterId: 1, unavailableDates: [], sharedSnapshotToken: 'shared', replacementCourseIds: [],
      courses: [{ courseId: 1, courseName: 'Course 1', available: true, draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, replacementRequired: false, inputSnapshotToken: 'course-1' }],
    }
    mocks.prepare.mockResolvedValue(preparation)
    mocks.generateBatch
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 1, complete: 0, improvedPartial: 0, unchanged: 0, failed: 0, stale: 1, scheduledUnits: 0, remainingUnits: 8, elapsedMilliseconds: 100, optimalForPreparedSnapshot: false },
        outcomes: [{ courseId: 1, courseName: 'Course 1', status: 'stale', draftScheduleId: null, draftRevision: null, scheduledUnits: 0, remainingUnits: 8, saved: false, improvement: null, reasons: [{ code: 'STALE_PLANNING_INPUT', message: 'Refresh.', relatedCount: 1 }], errors: [] }],
      })
      .mockResolvedValueOnce({
        semesterId: 1,
        summary: { total: 1, complete: 1, improvedPartial: 0, unchanged: 0, failed: 0, stale: 0, scheduledUnits: 8, remainingUnits: 0, elapsedMilliseconds: 100, optimalForPreparedSnapshot: true },
        outcomes: [{ courseId: 1, courseName: 'Course 1', status: 'complete', draftScheduleId: 1, draftRevision: 1, scheduledUnits: 8, remainingUnits: 0, saved: true, improvement: { addedUnits: 8, reducedConflicts: 0, reducedLecturerChanges: 0, reducedRoomChanges: 0 }, reasons: [], errors: [] }],
      })
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    act(() => document.querySelector<HTMLInputElement>('input[type="checkbox"]')?.click())
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).toContain('1 veraltet')

    await act(async () => {
      button('Fehlgeschlagene oder veraltete Lehrveranstaltungen erneut versuchen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(mocks.prepare).toHaveBeenCalledTimes(2)
    expect(mocks.prepare).toHaveBeenLastCalledWith(1, 11, [1], [])
    expect(mocks.generateBatch).toHaveBeenCalledTimes(2)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(3)
    expect(document.body.textContent).toContain('1 vollständig')
  })

  it('accepts the complete comparison once and refreshes the saved result', async () => {
    mocks.prepare.mockResolvedValue(optimizationPreparationFixture)
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    mocks.acceptBatch.mockResolvedValue(directSavedGenerationFixture)
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()

    await act(async () => {
      button('Neu erzeugten Stundenplan übernehmen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.generateBatch).toHaveBeenCalledTimes(1)
    expect(mocks.acceptBatch).toHaveBeenCalledTimes(1)
    expect(mocks.acceptBatch).toHaveBeenCalledWith(decisionRequiredGenerationFixture)
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).toContain('1 vollständig')
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it.each([
    'STALE_PLANNING_INPUT',
    'stale_lifecycle_state',
    'revision_not_editable',
  ])('discards a candidate rejected with %s, refreshes current schedules, and preserves the selection', async (code) => {
    mocks.prepare.mockResolvedValue(optimizationPreparationFixture)
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    mocks.acceptBatch.mockRejectedValue([
      { code, message: 'Planning inputs changed.' },
    ])
    await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    await act(async () => {
      button('Neu erzeugten Stundenplan übernehmen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).toContain('2 ausgewählt')
    expect(document.body.textContent).toContain('nicht mehr aktuell')
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('discards the local candidate without an API call when navigating away', async () => {
    mocks.prepare.mockResolvedValue(optimizationPreparationFixture)
    mocks.generateBatch.mockResolvedValue(decisionRequiredGenerationFixture)
    const root = await renderPage()
    act(() => button('Mehrere Lehrveranstaltungen')?.click())
    const boxes = document.querySelectorAll<HTMLInputElement>('input[type="checkbox"]')
    act(() => { boxes[0].click(); boxes[1].click() })
    await act(async () => {
      button('Ausgewählte Lehrveranstaltungen optimieren')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).not.toBeNull()

    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={0} destination="versions" />)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(mocks.acceptBatch).not.toHaveBeenCalled()
  })
})

describe('CourseSchedulePage academic option compatibility', () => {
  it('filters by assigned semester and retains an invalid prior selection without substitution', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      semesters: [...options.semesters, { id: 2, name: 'Spring 2027', startDate: '2027-02-01', endDate: '2027-06-20' }],
      courses: [
        { ...options.courses[0], semesterId: 1, availability: { available: true, reasons: [] } },
        { ...options.courses[1], semesterId: 2, availability: { available: false, reasons: ['MISSING_ACTIVE_TIME_WINDOW'] } },
      ],
    })
    await renderPage()
    const selects = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    act(() => { selects[1].value = '2'; selects[1].dispatchEvent(new Event('change', { bubbles: true })) })
    expect(selects[0].value).toBe('1')
    expect(document.body.textContent).toContain('dem ausgewählten Semester nicht zugeordnet')
    expect(button('Erzeugen')).toBeUndefined()
    expect(document.querySelector('.multi-course-panel .generate-button')).not.toBeNull()
  })

  it('refreshes options without replacing a still-valid selected Course', async () => {
    const root = await renderPage()
    const courseSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')!
    act(() => { courseSelect.value = '2'; courseSelect.dispatchEvent(new Event('change', { bubbles: true })) })

    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={1} />)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(courseSelect.value).toBe('2')
    expect(mocks.getPlanningOptions).toHaveBeenCalledTimes(2)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('retains and flags a selected Course removed by a catalog refresh', async () => {
    const root = await renderPage()
    const courseSelect = document.querySelector<HTMLSelectElement>('.planning-selectors select')!
    act(() => { courseSelect.value = '2'; courseSelect.dispatchEvent(new Event('change', { bubbles: true })) })
    mocks.getPlanningOptions.mockResolvedValue({ ...options, courses: [options.courses[0]] })

    await act(async () => {
      root.render(<CourseSchedulePage catalogRevision={1} />)
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(courseSelect.value).toBe('2')
    expect(document.body.textContent).not.toContain('OPTION_NO_LONGER_AVAILABLE')
    expect(document.body.textContent).toContain('genaue Ursache ist nicht verfügbar')
    expect(button('Erzeugen')).toBeUndefined()
    expect(document.querySelector('.multi-course-panel .generate-button')).not.toBeNull()
  })
})

describe('CourseSchedulePage manual session creation', () => {
  it('keeps remaining units unavailable and creation disabled until the current overview loads', async () => {
    const partialDraft = { ...draftScheduleFixture, sessions: draftScheduleFixture.sessions.slice(0, 1) }
    let resolveOverview: (value: typeof partialDraft[]) => void = () => undefined
    mocks.getDraftSchedules.mockReturnValue(new Promise((resolve) => { resolveOverview = resolve }))

    await renderPage()

    expect(summaryValue('Geplante Lehreinheiten')).toBe('Wird geladen…')
    expect(summaryValue('Offene Lehreinheiten')).toBe('Wird geladen…')
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(true)

    await act(async () => {
      resolveOverview([partialDraft])
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(summaryValue('Geplante Lehreinheiten')).toBe('4')
    expect(summaryValue('Offene Lehreinheiten')).toBe('4')
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(false)
  })

  it('locks the selected planning context while a manual creation and refresh are pending', async () => {
    let resolveCreation: (value: { courseId: number; semesterId: number; scheduledUnits: number; remainingUnits: number; draftSchedule: null }) => void = () => undefined
    mocks.createManualDraftSession.mockReturnValue(new Promise((resolve) => { resolveCreation = resolve }))
    await renderPage()

    act(() => button('Entwurfstermin hinzufügen')?.click())

    const selectors = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    expect([...selectors].every((select) => select.disabled)).toBe(true)

    await act(async () => {
      resolveCreation({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: null })
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect([...selectors].every((select) => !select.disabled)).toBe(true)
  })

  it('shows selected-course progress, calculates an editable end time, and refreshes after save', async () => {
    mocks.createManualDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: null })
    await renderPage()

    expect(document.body.textContent).toContain('Geplante Lehreinheiten')
    expect(document.body.textContent).toContain('Offene Lehreinheiten')
    const start = document.querySelector<HTMLInputElement>('input[name="manual-start-time"]')!
    const end = document.querySelector<HTMLInputElement>('input[name="manual-end-time"]')!
    const units = document.querySelector<HTMLInputElement>('input[name="manual-units"]')!
    expect(start.value).toBe('08:00')
    expect(units.value).toBe('2')
    expect(end.value).toBe('09:40')

    act(() => {
      Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value')?.set?.call(end, '10:15')
      end.dispatchEvent(new Event('input', { bubbles: true }))
    })
    await act(async () => {
      button('Entwurfstermin hinzufügen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.createManualDraftSession).toHaveBeenCalledWith(1, expect.objectContaining({ endTime: '10:15', units: 2, roomId: 3 }))
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('defaults manual resources from the course and submits active lecturer and cohort overrides', async () => {
    mocks.getPlanningOptions.mockResolvedValue({
      ...options,
      courses: [{
        ...options.courses[0],
        lecturer: entity(1, 'Ada'),
        cohort: entity(1, 'Cohort 30'),
        cohortSize: 30,
        room: entity(3, 'Large room'),
      }],
      lecturers: [
        { id: 1, name: 'Ada', referenceCode: 'LEC-001', isActive: true, revision: 1 },
        { id: 2, name: 'Grace', referenceCode: 'LEC-002', isActive: true, revision: 1 },
      ],
      cohorts: [
        { id: 1, name: 'Cohort 30', studentCount: 30 },
        { id: 2, name: 'Cohort 20', studentCount: 20 },
      ],
      rooms: [
        { id: 3, name: 'Large room', referenceCode: 'ROOM-003', capacity: 40, isActive: true, revision: 1 },
        { id: 4, name: 'Small room', referenceCode: 'ROOM-004', capacity: 25, isActive: true, revision: 1 },
      ],
    })
    mocks.createManualDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: null })
    await renderPage()

    const lecturer = document.querySelector<HTMLSelectElement>('select[name="manual-lecturer"]')!
    const cohort = document.querySelector<HTMLSelectElement>('select[name="manual-cohort"]')!
    const room = document.querySelector<HTMLSelectElement>('select[name="manual-room"]')!
    expect(lecturer.value).toBe('1')
    expect(cohort.value).toBe('1')
    expect(room.value).toBe('3')
    expect([...room.options].map((item) => item.text)).not.toContain('Small room (25 Plätze)')

    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(lecturer, '2')
      lecturer.dispatchEvent(new Event('change', { bubbles: true }))
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(cohort, '2')
      cohort.dispatchEvent(new Event('change', { bubbles: true }))
    })
    expect([...room.options].map((item) => item.text)).toContain('Small room (25 Plätze)')
    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(room, '4')
      room.dispatchEvent(new Event('change', { bubbles: true }))
    })
    await act(async () => {
      button('Entwurfstermin hinzufügen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(mocks.createManualDraftSession).toHaveBeenCalledWith(1, expect.objectContaining({
      lecturerId: 2,
      cohortId: 2,
      roomId: 4,
    }))
  })

  it('resets inherited manual-resource defaults when the selected course changes', async () => {
    await renderPage()
    const courseSelector = document.querySelector<HTMLSelectElement>('.planning-selectors select')!

    expect(document.querySelector<HTMLSelectElement>('select[name="manual-lecturer"]')?.value).toBe('1')
    expect(document.querySelector<HTMLSelectElement>('select[name="manual-cohort"]')?.value).toBe('1')

    act(() => {
      Object.getOwnPropertyDescriptor(HTMLSelectElement.prototype, 'value')?.set?.call(
        courseSelector,
        '2',
      )
      courseSelector.dispatchEvent(new Event('change', { bubbles: true }))
    })

    expect(document.querySelector<HTMLSelectElement>('select[name="manual-lecturer"]')?.value).toBe('2')
    expect(document.querySelector<HTMLSelectElement>('select[name="manual-cohort"]')?.value).toBe('2')
  })

  it('reports a saved mutation whose overview refresh failed and blocks another write until retry succeeds', async () => {
    const partialDraft = { ...draftScheduleFixture, sessions: draftScheduleFixture.sessions.slice(0, 1) }
    let resolveRetry: (value: typeof partialDraft[]) => void = () => undefined
    const retry = new Promise<typeof partialDraft[]>((resolve) => { resolveRetry = resolve })
    mocks.getDraftSchedules
      .mockResolvedValueOnce([])
      .mockRejectedValueOnce(new Error('refresh failed'))
      .mockReturnValueOnce(retry)
    mocks.createManualDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 2, remainingUnits: 6, draftSchedule: partialDraft })
    await renderPage()

    await act(async () => {
      button('Entwurfstermin hinzufügen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('wurde gespeichert, aber die Übersicht konnte nicht aktualisiert werden')
    expect(document.body.textContent).toContain('Die Übersicht der Lehrveranstaltungen konnte nicht aktualisiert werden')
    const visibleMutationNotice = document.querySelector('.mutation-feedback')
    expect(visibleMutationNotice?.textContent).toContain('wurde gespeichert, aber die Übersicht konnte nicht aktualisiert werden')
    expect(visibleMutationNotice?.classList.contains('sr-only')).toBe(false)
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(true)

    await act(async () => {
      button('Übersicht erneut laden')?.click()
      await Promise.resolve()
    })
    const selectors = document.querySelectorAll<HTMLSelectElement>('.planning-selectors select')
    expect([...selectors].every((select) => select.disabled)).toBe(true)

    await act(async () => {
      resolveRetry([partialDraft])
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect((button('Entwurfstermin hinzufügen') as HTMLButtonElement).disabled).toBe(false)
    expect([...selectors].every((select) => !select.disabled)).toBe(true)
  })
})

describe('CourseSchedulePage single-session deletion', () => {
  it('cancels without writing, then confirms exact-scope deletion and refreshes', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 4, remainingUnits: 4, draftSchedule: null })
    await renderPage()
    const firstDelete = [...document.querySelectorAll('button')].find((item) => item.textContent === 'Löschen')!
    act(() => firstDelete.click())
    expect(document.body.textContent).toContain('Diesen Entwurfstermin löschen?')
    act(() => button('Abbrechen')?.click())
    expect(mocks.deleteDraftSession).not.toHaveBeenCalled()

    act(() => firstDelete.click())
    await act(async () => {
      button('Termin löschen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.deleteDraftSession).toHaveBeenCalledWith(1, 1, 1, 11)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('closes a stale confirmation, refreshes, and requires the action to be opened again', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Löschen')?.click())
    await act(async () => {
      button('Termin löschen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.body.textContent).not.toContain('Diesen Entwurfstermin löschen?')
    expect(document.body.textContent).toContain('zwischenzeitlich geändert')
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(2)
  })

  it('blocks renewed deletion when the stale-state refresh fails', async () => {
    mocks.getDraftSchedules
      .mockResolvedValueOnce([draftScheduleFixture])
      .mockRejectedValueOnce(new Error('refresh failed'))
      .mockResolvedValue([draftScheduleFixture])
    mocks.deleteDraftSession.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => [...document.querySelectorAll('button')].find((item) => item.textContent === 'Löschen')?.click())
    await act(async () => {
      button('Termin löschen')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })

    expect(document.body.textContent).toContain('aktuelle Stand konnte nicht geladen werden')
    const deleteActions = [...document.querySelectorAll<HTMLButtonElement>('button')].filter((item) => item.textContent === 'Löschen')
    expect(deleteActions.every((item) => item.disabled)).toBe(true)

    await act(async () => {
      button('Übersicht erneut laden')?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(deleteActions.every((item) => item.disabled)).toBe(false)
    expect(document.body.textContent).not.toContain('current state could not be refreshed')
  })
})

describe('CourseSchedulePage complete draft clearing', () => {
  it('disables clearing without a selected draft, then supports cancel and exact-scope confirm', async () => {
    await renderPage()
    expect((button('Lehrveranstaltung-Entwurf leeren') as HTMLButtonElement).disabled).toBe(true)
    document.body.innerHTML = ''

    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.clearCourseDraft.mockResolvedValue({ courseId: 1, semesterId: 1, scheduledUnits: 0, remainingUnits: 8, draftSchedule: null })
    await renderPage()
    act(() => button('Lehrveranstaltung-Entwurf leeren')?.click())
    expect(document.body.textContent).toContain('2 Termine werden gelöscht')
    act(() => button('Abbrechen')?.click())
    expect(mocks.clearCourseDraft).not.toHaveBeenCalled()

    act(() => button('Lehrveranstaltung-Entwurf leeren')?.click())
    const confirm = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')].at(-1)
    await act(async () => {
      confirm?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(mocks.clearCourseDraft).toHaveBeenCalledWith(1, 1, 1, 1, 11)
    expect(mocks.getDraftSchedules).toHaveBeenCalledTimes(3)
  })

  it('refreshes and requires renewed confirmation when complete clearing is stale', async () => {
    mocks.getDraftSchedules.mockResolvedValue([draftScheduleFixture])
    mocks.clearCourseDraft.mockRejectedValue([{ code: 'STALE_DRAFT', message: 'Draft changed.', currentRevision: 2 }])
    await renderPage()
    act(() => button('Lehrveranstaltung-Entwurf leeren')?.click())
    const dialogButtons = [...document.querySelectorAll<HTMLButtonElement>('[role="dialog"] button')]
    await act(async () => {
      dialogButtons.at(-1)?.click()
      await new Promise((resolve) => setTimeout(resolve, 0))
    })
    expect(document.querySelector('[role="dialog"]')).toBeNull()
    expect(document.body.textContent).toContain('Löschdialog erneut')
  })
})
