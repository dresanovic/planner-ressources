const emptyFacets = {
  courses: [],
  cohorts: [],
  lecturers: [],
  rooms: [],
  studyTypes: [],
  sessionTypes: [],
  lifecycleContexts: [],
  validationCategories: [],
}

const notApplicable = {
  availability: 'not_applicable' as const,
  scope: 'no_revision' as const,
  contributorRefs: [],
  notApplicableReason: 'No lifecycle revision exists for this semester.',
}

export function noRevisionWorkspaceFixture() {
  return {
    semester: {
      semesterId: 1,
      name: 'Fall 2026',
      startDate: '2026-09-01',
      endDate: '2026-12-20',
    },
    workspaceState: 'no_revision' as const,
    selectedRevision: null,
    availableContexts: { activeWorking: null, currentPublished: null },
    workspaceToken: 'no-revision-1',
    sectionStatus: {
      courses: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
      occurrences: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
      holidays: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
      validationFindings: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
      planningOutcomes: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
      summary: { availability: 'unavailable' as const, reason: 'No schedule revision exists.' },
    },
    courses: [],
    occurrences: [],
    holidays: [],
    validationFindings: [],
    planningOutcomes: [],
    summary: {
      unscheduledWork: { ...notApplicable },
      conflicts: { ...notApplicable },
      capacityIssues: { ...notApplicable },
      planningFailures: { ...notApplicable },
      needsReview: { ...notApplicable },
    },
    filterFacets: { ...emptyFacets },
  }
}

export function loadedCalendarWorkspaceFixture() {
  const revision = {
    revisionId: 11,
    revisionNumber: 1,
    lifecycleState: 'draft' as const,
    designation: 'active_working' as const,
    readOnly: false,
    contentSource: 'active_working' as const,
    validationBasis: 'current' as const,
    snapshotSchemaVersion: null,
  }
  return {
    semester: {
      semesterId: 1,
      name: 'Fall 2026',
      startDate: '2026-09-01',
      endDate: '2026-12-20',
    },
    workspaceState: 'loaded' as const,
    selectedRevision: revision,
    availableContexts: {
      activeWorking: {
        revisionId: 11,
        revisionNumber: 1,
        lifecycleState: 'draft' as const,
        designation: 'active_working' as const,
      },
      currentPublished: null,
    },
    workspaceToken: 'working-11-v1',
    sectionStatus: {
      courses: { availability: 'available' as const },
      occurrences: { availability: 'available' as const },
      holidays: { availability: 'available' as const },
      validationFindings: { availability: 'available' as const },
      planningOutcomes: {
        availability: 'partial' as const,
        coverage: '1 of 2 eligible courses covered',
      },
      summary: { availability: 'available' as const },
    },
    courses: [
      {
        courseRef: 'course:1',
        courseId: 1,
        code: 'C-001',
        name: 'Algorithms',
        cohort: 'CS-26',
        lecturerRefs: ['lecturer:1'],
        studyType: 'Full-time',
        planningEligible: true,
        totalTeachingUnits: 4,
        scheduledTeachingUnits: 2,
        remainingTeachingUnits: 2,
        remainingInstructionalMinutes: 90,
        occurrenceRefs: ['teaching:1', 'exam:1'],
        findingRefs: [],
        outcomeRefs: [],
        needsReviewReasonRefs: ['remaining:course:1'],
      },
    ],
    occurrences: [
      {
        occurrenceRef: 'teaching:1',
        kind: 'teaching' as const,
        courseRef: 'course:1',
        date: '2026-10-05',
        startTime: '09:00',
        endTime: '10:40',
        cohort: 'CS-26',
        lecturerRefs: ['lecturer:1'],
        roomRef: 'room:1',
        findingRefs: [],
        teachingUnits: 2,
        source: 'generated',
      },
      {
        occurrenceRef: 'exam:1',
        kind: 'exam' as const,
        courseRef: 'course:1',
        date: '2026-12-10',
        startTime: '09:00',
        endTime: '11:00',
        cohort: 'CS-26',
        lecturerRefs: ['lecturer:1'],
        roomRef: 'room:1',
        findingRefs: [],
        examType: 'Written',
        durationMinutes: 120,
        requiredCapacity: 30,
        assignedRoomName: 'Auditorium 1',
        currentRoomCapacity: 40,
        validityContext: {
          configurationIdentifier: 'FINAL',
          configurationRevision: 2,
          finalTeachingDate: '2026-12-01',
          finalTeachingEndTime: '12:00',
          source: 'manual',
        },
        recommendationContext: {
          recommendedStartDate: '2026-12-08',
          recommendedEndDate: '2026-12-15',
          recommendationWasOverridden: true,
          outsideRecommendedWindow: false,
        },
      },
    ],
    holidays: [
      { holidayRef: 'holiday:1', date: '2026-10-26', name: 'National Holiday' },
    ],
    validationFindings: [],
    planningOutcomes: [],
    summary: {
      unscheduledWork: {
        availability: 'available' as const,
        scope: 'complete_revision' as const,
        remainingTeachingUnits: 2,
        remainingInstructionalMinutes: 90,
        contributingCourseCount: 1,
        contributorRefs: ['course:1'],
      },
      conflicts: {
        availability: 'available' as const,
        scope: 'complete_revision' as const,
        distinctFindingCount: 0,
        countByType: { lecturer: 0, room: 0, cohort: 0 },
        contributorRefs: [],
      },
      capacityIssues: {
        availability: 'available' as const,
        scope: 'complete_revision' as const,
        affectedOccurrenceCount: 0,
        contributorRefs: [],
      },
      planningFailures: {
        availability: 'partial' as const,
        scope: 'complete_revision' as const,
        coverage: {
          eligibleCourseCount: 2,
          coveredCourseCount: 1,
          coverageComplete: false,
        },
        failedOutcomeCount: 0,
        staleOutcomeCount: 0,
        unchangedOutcomeCount: 0,
        contributorRefs: [],
      },
      needsReview: {
        availability: 'available' as const,
        scope: 'complete_revision' as const,
        distinctCourseCount: 1,
        contributorRefs: ['course:1'],
      },
    },
    filterFacets: {
      ...emptyFacets,
      courses: [{ value: 'course:1', label: 'Algorithms' }],
      cohorts: [{ value: 'CS-26', label: 'CS-26' }],
      sessionTypes: [
        { value: 'teaching', label: 'Teaching' },
        { value: 'exam', label: 'Exam' },
      ],
      lifecycleContexts: [
        { value: 'active_working', label: 'Working' },
        { value: 'draft', label: 'Draft' },
      ],
    },
  }
}

export function partialCalendarWorkspaceFixture() {
  const value = loadedCalendarWorkspaceFixture()
  return {
    ...value,
    sectionStatus: {
      ...value.sectionStatus,
      validationFindings: {
        availability: 'unavailable' as const,
        reason: 'Current resource data could not be loaded.',
      },
    },
    summary: {
      ...value.summary,
      conflicts: {
        availability: 'unavailable' as const,
        scope: 'complete_revision' as const,
        contributorRefs: [],
        unavailableReason: 'Current validation is unavailable.',
      },
    },
  }
}

export function publishedCalendarWorkspaceFixture() {
  const value = loadedCalendarWorkspaceFixture()
  return {
    ...value,
    selectedRevision: {
      ...value.selectedRevision,
      revisionId: 9,
      revisionNumber: 1,
      lifecycleState: 'published' as const,
      designation: 'current_published' as const,
      readOnly: true,
      contentSource: 'captured_published' as const,
      snapshotSchemaVersion: 2,
    },
    availableContexts: {
      activeWorking: null,
      currentPublished: {
        revisionId: 9,
        revisionNumber: 1,
        lifecycleState: 'published' as const,
        designation: 'current_published' as const,
      },
    },
    workspaceToken: 'published-9-v2',
  }
}

export function calendarWorkspaceFailureFixture() {
  return {
    detail: 'The calendar workspace could not be loaded.',
    retryable: true,
  }
}
