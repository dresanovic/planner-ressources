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


class CohortCalendarInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cohort_id: int = Field(alias="cohortId", ge=1)
    semester_id: int = Field(alias="semesterId", ge=1)
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")


class CohortCalendarUpdate(CohortCalendarInput):
    model_config = ConfigDict(populate_by_name=True)
    expected_revision: int = Field(alias="expectedRevision")


class TimeWindowInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    # Preserve raw values so the service can aggregate every detected field
    # correction into the catalog's German error envelope (including parsing).
    kind: Any = "weekly"
    weekday: Any = None
    date: Any = None
    is_intensive: Any = Field(default=False, alias="isIntensive")
    start_time: Any = Field(default=None, alias="startTime")
    end_time: Any = Field(default=None, alias="endTime")
    sort_order: Any = Field(default=0, alias="sortOrder")


class TimeWindowUpdate(TimeWindowInput):
    expected_revision: int = Field(alias="expectedRevision")
    cohort_calendar_id: Any = Field(default=None, alias="cohortCalendarId")


class CourseDetailsInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    name: str
    total_units: int = Field(alias="totalUnits")
    overall_units: int | None = Field(default=None, alias="overallUnits", ge=1)
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    preferred_session_units: float | None = Field(default=None, alias="preferredSessionUnits", strict=True, allow_inf_nan=False, multiple_of=0.5)
    semester_id: int = Field(alias="semesterId")
    cohort_id: int = Field(alias="cohortId")


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
    cohort_calendar_id: int = Field(alias="cohortCalendarId")
    kind: str
    weekday: int | None
    date: date | None
    is_intensive: bool = Field(alias="isIntensive")
    overlap_notice: str | None = Field(alias="overlapNotice")
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    sort_order: int = Field(alias="sortOrder")
    is_active: bool = Field(alias="isActive")
    revision: int
    availability: AvailabilityResponse
    usage: UsageSummaryResponse


class CohortCalendarResponse(CohortCalendarInput):
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
    overall_units: int = Field(alias="overallUnits")
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    preferred_session_units: float | None = Field(default=None, alias="preferredSessionUnits")
    semester: EntitySummaryResponse | None
    cohort: EntitySummaryResponse
    cohort_calendar: EntitySummaryResponse | None = Field(alias="cohortCalendar")
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
