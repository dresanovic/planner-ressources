export type ResourceRecordFixture = {
  id: number
  name: string
  referenceCode: string
  isActive: boolean
  revision: number
  capacity?: number
}

export type UnavailabilityFixture =
  | {
      id: number
      resourceType: 'lecturer' | 'room'
      resourceId: number
      kind: 'recurring'
      weekdays: number[]
      startTime: string
      endTime: string
      revision: number
    }
  | {
      id: number
      resourceType: 'lecturer' | 'room'
      resourceId: number
      kind: 'dated'
      startDate: string
      startTime: string
      endDate: string
      endTime: string
      revision: number
    }

export type ResourceCandidateFixture = ResourceRecordFixture & {
  kind: 'lecturer' | 'room'
  isEligible: boolean
  isUsable: boolean
  reasons: Array<'RESOURCE_INACTIVE' | 'ROOM_CAPACITY_INSUFFICIENT'>
}

export const duplicateNameLecturersFixture: ResourceRecordFixture[] = [
  { id: 1, name: 'Alex Morgan', referenceCode: 'LECT-A', isActive: true, revision: 1 },
  { id: 2, name: 'Alex Morgan', referenceCode: 'LECT-B', isActive: true, revision: 1 },
]

export const activeRoomFixture: ResourceRecordFixture = {
  id: 1,
  name: 'Room 101',
  referenceCode: 'ROOM-101',
  capacity: 40,
  isActive: true,
  revision: 1,
}

export const inactiveRoomFixture: ResourceRecordFixture = {
  ...activeRoomFixture,
  id: 2,
  referenceCode: 'ROOM-OLD',
  isActive: false,
}

export const unavailabilityFixture: UnavailabilityFixture[] = [
  {
    id: 1,
    resourceType: 'lecturer',
    resourceId: 1,
    kind: 'recurring',
    weekdays: [0, 2],
    startTime: '09:00',
    endTime: '11:00',
    revision: 1,
  },
  {
    id: 2,
    resourceType: 'room',
    resourceId: 1,
    kind: 'dated',
    startDate: '2026-10-12',
    startTime: '15:00',
    endDate: '2026-10-13',
    endTime: '10:00',
    revision: 1,
  },
]

export const courseResourceConfigurationFixture = {
  courseId: 1,
  courseRevision: 1,
  cohortSize: 30,
  eligibleLecturerIds: [1, 2],
  eligibleRoomIds: [1, 3],
  lecturerCandidates: duplicateNameLecturersFixture.map((resource) => ({
    ...resource,
    kind: 'lecturer' as const,
    isEligible: true,
    isUsable: true,
    reasons: [],
    unavailabilityPeriods: [],
    courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 },
  })),
  roomCandidates: [activeRoomFixture, inactiveRoomFixture].map((resource) => ({
    ...resource,
    kind: 'room' as const,
    isEligible: resource.id === 1,
    isUsable: resource.isActive,
    reasons: resource.isActive ? [] : ['RESOURCE_INACTIVE' as const],
    unavailabilityPeriods: [],
    courseSessionUsage: { draftSessionCount: 0, draftScheduleCount: 0 },
  })),
  preferences: { minimizeLecturerChanges: true, minimizeRoomChanges: true },
}

export const deletedResourceOutcomeFixture = {
  outcome: 'deleted' as const,
  resourceId: 3,
  removedInactiveCourseLinks: [{ id: 9, name: 'Archived Planning' }],
}

export const inactivatedResourceOutcomeFixture = {
  outcome: 'inactivated' as const,
  resource: { ...activeRoomFixture, isActive: false, revision: 2 },
  activeCourses: [{ id: 1, name: 'Planning 101' }],
  sessionUsage: { draftSessionCount: 2, draftScheduleCount: 1 },
}
