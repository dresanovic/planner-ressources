from typing import Annotated, Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class ResourceErrorResponseItem(BaseModel):
    code: str
    message: str
    field: str | None = None
    meta: dict[str, Any] | None = None


class ResourceErrorEnvelope(BaseModel):
    errors: list[ResourceErrorResponseItem]


class LecturerCreate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    reference_code: str = Field(alias="referenceCode")


class LecturerUpdate(LecturerCreate):
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class RoomCreate(LecturerCreate):
    capacity: int


class RoomUpdate(RoomCreate):
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class RevisionCommand(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class LecturerRecord(BaseModel):
    model_config = ConfigDict(populate_by_name=True, from_attributes=True)
    id: int
    name: str
    reference_code: str = Field(alias="referenceCode")
    is_active: bool = Field(alias="isActive")
    revision: int


class RoomRecord(LecturerRecord):
    capacity: int


class LecturerList(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    items: list[LecturerRecord]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int


class RoomList(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    items: list[RoomRecord]
    page: int
    page_size: int = Field(alias="pageSize")
    total: int


class CourseIdentity(BaseModel):
    id: int
    name: str


class SessionUsage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    draft_session_count: int = Field(alias="draftSessionCount")
    draft_schedule_count: int = Field(alias="draftScheduleCount")


class ExamUsage(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    exam_session_count: int = Field(alias="examSessionCount")
    current_configuration_count: int = Field(alias="currentConfigurationCount")


class ResourceUsageAssessment(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    resource_id: int = Field(alias="resourceId")
    revision: int
    disposition: Literal["delete", "inactivate"]
    active_courses: list[CourseIdentity] = Field(alias="activeCourses")
    inactive_courses: list[CourseIdentity] = Field(alias="inactiveCourses")
    session_usage: SessionUsage = Field(alias="sessionUsage")
    exam_usage: ExamUsage = Field(alias="examUsage")


class RelationshipStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    course: CourseIdentity
    resource_id: int = Field(alias="resourceId")
    usable: bool
    reasons: list[str]


class DeletedResourceResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    outcome: Literal["deleted"]
    resource_id: int = Field(alias="resourceId")
    removed_inactive_course_links: list[CourseIdentity] = Field(alias="removedInactiveCourseLinks")


class InactivatedLecturerResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    outcome: Literal["inactivated"]
    resource: LecturerRecord
    active_courses: list[CourseIdentity] = Field(alias="activeCourses")
    session_usage: SessionUsage = Field(alias="sessionUsage")
    exam_usage: ExamUsage = Field(alias="examUsage")


class InactivatedRoomResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    outcome: Literal["inactivated"]
    resource: RoomRecord
    active_courses: list[CourseIdentity] = Field(alias="activeCourses")
    session_usage: SessionUsage = Field(alias="sessionUsage")
    exam_usage: ExamUsage = Field(alias="examUsage")


LecturerRemovalResult = Annotated[
    DeletedResourceResult | InactivatedLecturerResult,
    Field(discriminator="outcome"),
]
RoomRemovalResult = Annotated[
    DeletedResourceResult | InactivatedRoomResult,
    Field(discriminator="outcome"),
]


class LecturerReactivationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    resource: LecturerRecord
    restored_relationships: list[CourseIdentity] = Field(alias="restoredRelationships")
    unusable_relationships: list[RelationshipStatus] = Field(alias="unusableRelationships")


class RoomReactivationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    resource: RoomRecord
    restored_relationships: list[CourseIdentity] = Field(alias="restoredRelationships")
    unusable_relationships: list[RelationshipStatus] = Field(alias="unusableRelationships")


class RoomMutationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    room: RoomRecord
    affected_relationships: list[RelationshipStatus] = Field(alias="affectedRelationships")


class RecurringUnavailabilityInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    kind: Literal["recurring"]
    weekdays: list[int]
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")


class DatedUnavailabilityInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    kind: Literal["dated"]
    start_date: str = Field(alias="startDate")
    start_time: str = Field(alias="startTime")
    end_date: str = Field(alias="endDate")
    end_time: str = Field(alias="endTime")


class RecurringUnavailabilityUpdate(RecurringUnavailabilityInput):
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class DatedUnavailabilityUpdate(DatedUnavailabilityInput):
    expected_revision: int = Field(alias="expectedRevision", ge=1)


UnavailabilityCreate = Annotated[RecurringUnavailabilityInput | DatedUnavailabilityInput, Field(discriminator="kind")]
UnavailabilityUpdate = Annotated[RecurringUnavailabilityUpdate | DatedUnavailabilityUpdate, Field(discriminator="kind")]


class RecurringUnavailability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    resource_type: Literal["lecturer", "room"] = Field(alias="resourceType")
    resource_id: int = Field(alias="resourceId")
    kind: Literal["recurring"]
    weekdays: list[int]
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    revision: int


class DatedUnavailability(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    resource_type: Literal["lecturer", "room"] = Field(alias="resourceType")
    resource_id: int = Field(alias="resourceId")
    kind: Literal["dated"]
    start_date: str = Field(alias="startDate")
    start_time: str = Field(alias="startTime")
    end_date: str = Field(alias="endDate")
    end_time: str = Field(alias="endTime")
    revision: int


UnavailabilityRecord = Annotated[RecurringUnavailability | DatedUnavailability, Field(discriminator="kind")]


class ResourceCandidate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    reference_code: str = Field(alias="referenceCode")
    kind: Literal["lecturer", "room"]
    capacity: int | None = None
    is_active: bool = Field(alias="isActive")
    is_eligible: bool = Field(alias="isEligible")
    is_usable: bool = Field(alias="isUsable")
    reasons: list[str]


class CourseResourceCandidate(ResourceCandidate):
    unavailability_periods: list[UnavailabilityRecord] = Field(alias="unavailabilityPeriods")
    course_session_usage: SessionUsage = Field(alias="courseSessionUsage")


class AssignmentPreferences(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    minimize_lecturer_changes: Literal[True] = Field(alias="minimizeLecturerChanges")
    minimize_room_changes: Literal[True] = Field(alias="minimizeRoomChanges")


class CourseResourceConfiguration(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    course_id: int = Field(alias="courseId")
    course_revision: int = Field(alias="courseRevision")
    cohort_size: int = Field(alias="cohortSize")
    eligible_lecturer_ids: list[int] = Field(alias="eligibleLecturerIds")
    eligible_room_ids: list[int] = Field(alias="eligibleRoomIds")
    lecturer_candidates: list[CourseResourceCandidate] = Field(alias="lecturerCandidates")
    room_candidates: list[CourseResourceCandidate] = Field(alias="roomCandidates")
    preferences: AssignmentPreferences


class CourseResourceEligibilityUpdate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    expected_revision: int = Field(alias="expectedRevision", ge=1)
    lecturer_ids: list[int] = Field(alias="lecturerIds")
    room_ids: list[int] = Field(alias="roomIds")
