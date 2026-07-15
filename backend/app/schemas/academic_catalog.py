from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class CatalogErrorResponseItem(BaseModel):
    code: str
    message: str
    field: str | None = None
    meta: dict[str, Any] | None = None


class CatalogErrorEnvelope(BaseModel):
    errors: list[CatalogErrorResponseItem]


class AvailabilityResponse(BaseModel):
    available: bool
    reasons: list[str]


class LifecycleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    expected_revision: int = Field(alias="expectedRevision", ge=1)


class UsageCountResponse(BaseModel):
    type: str
    count: int


class BlockerResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    kind: str
    type: str
    count: int
    message: str
    prerequisite_action: str | None = Field(default=None, alias="prerequisiteAction")


class UsageSummaryResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    record_id: int = Field(alias="recordId")
    revision: int
    can_delete: bool = Field(alias="canDelete")
    dependent_records: list[UsageCountResponse] = Field(alias="dependentRecords")
    saved_schedules: UsageCountResponse = Field(alias="savedSchedules")
    blockers: list[BlockerResponse]


class EntitySummaryResponse(BaseModel):
    id: int
    name: str


class SemesterInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")


class SemesterUpdate(SemesterInput):
    expected_revision: int = Field(alias="expectedRevision")


class CohortInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    student_count: int = Field(alias="studentCount")


class CohortUpdate(CohortInput):
    expected_revision: int = Field(alias="expectedRevision")


class StudyTypeInput(BaseModel):
    name: str


class StudyTypeUpdate(StudyTypeInput):
    model_config = ConfigDict(populate_by_name=True)
    expected_revision: int = Field(alias="expectedRevision")


class TimeWindowInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    weekday: int
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    sort_order: int = Field(alias="sortOrder")


class TimeWindowUpdate(TimeWindowInput):
    expected_revision: int = Field(alias="expectedRevision")


class CourseDetailsInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    total_units: int = Field(alias="totalUnits")
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    semester_id: int = Field(alias="semesterId")
    cohort_id: int = Field(alias="cohortId")
    study_type_id: int = Field(alias="studyTypeId")


class CourseInput(CourseDetailsInput):
    lecturer_id: int = Field(alias="lecturerId")
    room_id: int = Field(alias="roomId")


class CourseUpdate(CourseDetailsInput):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    expected_revision: int = Field(alias="expectedRevision")


class SemesterResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    name_repair_required: bool = Field(alias="nameRepairRequired")
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")
    is_active: bool = Field(alias="isActive")
    revision: int
    usage: UsageSummaryResponse


class CohortResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    name_repair_required: bool = Field(alias="nameRepairRequired")
    student_count: int = Field(alias="studentCount")
    is_active: bool = Field(alias="isActive")
    revision: int
    usage: UsageSummaryResponse


class RemovedRoomRelationship(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    course_id: int = Field(alias="courseId")
    room_id: int = Field(alias="roomId")
    course_revision: int = Field(alias="courseRevision")


class CohortCapacityImpact(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    removed_relationships: list[RemovedRoomRelationship] = Field(alias="removedRelationships")
    courses_without_rooms: list[EntitySummaryResponse] = Field(alias="coursesWithoutRooms")


class CohortMutationResult(CohortResponse):
    model_config = ConfigDict(populate_by_name=True)
    cohort: CohortResponse
    capacity_impact: CohortCapacityImpact = Field(alias="capacityImpact")


class TimeWindowResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    study_type_id: int = Field(alias="studyTypeId")
    weekday: int
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    sort_order: int = Field(alias="sortOrder")
    is_active: bool = Field(alias="isActive")
    revision: int
    availability: AvailabilityResponse
    usage: UsageSummaryResponse


class StudyTypeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    name_repair_required: bool = Field(alias="nameRepairRequired")
    time_windows: list[TimeWindowResponse] = Field(alias="timeWindows")
    is_active: bool = Field(alias="isActive")
    revision: int
    usage: UsageSummaryResponse


class CourseResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    id: int
    name: str
    name_repair_required: bool = Field(alias="nameRepairRequired")
    total_units: int = Field(alias="totalUnits")
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    semester: EntitySummaryResponse | None
    cohort: EntitySummaryResponse
    study_type: EntitySummaryResponse = Field(alias="studyType")
    lecturer: EntitySummaryResponse | None
    room: EntitySummaryResponse | None
    is_active: bool = Field(alias="isActive")
    revision: int
    availability: AvailabilityResponse
    usage: UsageSummaryResponse


class PageResponse(BaseModel):
    page: int
    page_size: int = Field(alias="pageSize")
    total: int
    items: list[Any]
