from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OptimizationStatus(StrEnum):
    COMPLETE = "complete"
    IMPROVED_PARTIAL = "improved_partial"
    UNCHANGED = "unchanged"
    FAILED = "failed"
    STALE = "stale"


class BlockingReasonCode(StrEnum):
    LECTURER_OCCUPIED = "LECTURER_OCCUPIED"
    ROOM_OCCUPIED = "ROOM_OCCUPIED"
    COHORT_OCCUPIED = "COHORT_OCCUPIED"
    LECTURER_UNAVAILABLE = "LECTURER_UNAVAILABLE"
    ROOM_UNAVAILABLE = "ROOM_UNAVAILABLE"
    NO_ELIGIBLE_LECTURER = "NO_ELIGIBLE_LECTURER"
    NO_ELIGIBLE_ROOM = "NO_ELIGIBLE_ROOM"
    INSUFFICIENT_ROOM_CAPACITY = "INSUFFICIENT_ROOM_CAPACITY"
    UNAVAILABLE_DATE = "UNAVAILABLE_DATE"
    NO_ALLOWED_DATE_OR_WINDOW = "NO_ALLOWED_DATE_OR_WINDOW"
    COURSE_CONSTRAINT = "COURSE_CONSTRAINT"
    SELECTED_COURSE_COMPETITION = "SELECTED_COURSE_COMPETITION"
    INVALID_PLANNING_INPUT = "INVALID_PLANNING_INPUT"
    STALE_PLANNING_INPUT = "STALE_PLANNING_INPUT"


class OperationError(BaseModel):
    code: str
    message: str


class BlockingReason(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: BlockingReasonCode
    message: str
    related_count: int = Field(default=1, alias="relatedCount", ge=1)


class ArrangementImprovement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    added_units: int = Field(alias="addedUnits", ge=0)
    reduced_conflicts: int = Field(alias="reducedConflicts", ge=0)
    reduced_lecturer_changes: int = Field(alias="reducedLecturerChanges", ge=0)
    reduced_room_changes: int = Field(alias="reducedRoomChanges", ge=0)


class OptimizationPreparationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    course_ids: list[int] = Field(alias="courseIds")
    unavailable_dates: list[date] = Field(default_factory=list, alias="unavailableDates")


class PreparedOptimizationCourse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course_name: str | None = Field(alias="courseName")
    available: bool
    draft_schedule_id: int | None = Field(alias="draftScheduleId")
    draft_revision: int | None = Field(alias="draftRevision")
    scheduled_units: int = Field(alias="scheduledUnits", ge=0)
    remaining_units: int = Field(alias="remainingUnits", ge=0)
    replacement_required: bool = Field(alias="replacementRequired")
    input_snapshot_token: str = Field(alias="inputSnapshotToken", min_length=1)


class OptimizationPreparationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    unavailable_dates: list[date] = Field(alias="unavailableDates")
    shared_snapshot_token: str = Field(alias="sharedSnapshotToken")
    courses: list[PreparedOptimizationCourse]
    replacement_course_ids: list[int] = Field(alias="replacementCourseIds")


class PreparedOptimizationCourseInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    course_id: int = Field(alias="courseId", ge=1)
    expected_draft_schedule_id: int | None = Field(alias="expectedDraftScheduleId")
    expected_draft_revision: int | None = Field(alias="expectedDraftRevision", ge=1)
    input_snapshot_token: str = Field(alias="inputSnapshotToken", min_length=1)

    @model_validator(mode="after")
    def matching_draft_identity(self):
        if (self.expected_draft_schedule_id is None) != (self.expected_draft_revision is None):
            raise ValueError("Draft Schedule ID and revision must both be present or both be null.")
        return self


class OptimizationGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    unavailable_dates: list[date] = Field(alias="unavailableDates")
    shared_snapshot_token: str = Field(alias="sharedSnapshotToken", min_length=1)
    replacement_confirmed: bool = Field(alias="replacementConfirmed")
    courses: list[PreparedOptimizationCourseInput]


class CourseOptimizationOutcome(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course_name: str | None = Field(alias="courseName")
    status: OptimizationStatus
    draft_schedule_id: int | None = Field(alias="draftScheduleId")
    draft_revision: int | None = Field(alias="draftRevision")
    scheduled_units: int = Field(alias="scheduledUnits", ge=0)
    remaining_units: int = Field(alias="remainingUnits", ge=0)
    saved: bool
    improvement: ArrangementImprovement | None
    reasons: list[BlockingReason]
    errors: list[OperationError]


class OptimizationSummary(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total: int = Field(ge=1, le=20)
    complete: int = Field(ge=0)
    improved_partial: int = Field(alias="improvedPartial", ge=0)
    unchanged: int = Field(ge=0)
    failed: int = Field(ge=0)
    stale: int = Field(ge=0)
    scheduled_units: int = Field(alias="scheduledUnits", ge=0)
    remaining_units: int = Field(alias="remainingUnits", ge=0)
    elapsed_milliseconds: int = Field(alias="elapsedMilliseconds", ge=0, le=60000)
    optimal_for_prepared_snapshot: bool = Field(alias="optimalForPreparedSnapshot")


class OptimizationGenerationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    summary: OptimizationSummary
    outcomes: list[CourseOptimizationOutcome]


class ReplacementConfirmationRequired(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: Literal["REPLACEMENT_CONFIRMATION_REQUIRED"] = "REPLACEMENT_CONFIRMATION_REQUIRED"
    message: str
    replacement_course_ids: list[int] = Field(alias="replacementCourseIds")


class RequestFailureResponse(BaseModel):
    errors: list[OperationError]


class OptimizationOperationFailure(BaseModel):
    code: Literal[
        "OPTIMAL_RESULT_NOT_PROVEN",
        "OPTIMIZATION_MODEL_INVALID",
        "OPTIMIZATION_OPERATION_FAILED",
    ]
    message: str
    saved: Literal[False] = False
