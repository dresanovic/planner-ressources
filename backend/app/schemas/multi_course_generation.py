from enum import StrEnum
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, model_validator


class BatchOperationKind(StrEnum):
    INITIAL = "initial"
    RETRY = "retry"


class BatchPreparationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    schedule_revision_id: int = Field(alias="scheduleRevisionId", ge=1)
    operation_kind: BatchOperationKind = Field(alias="operationKind")
    course_ids: list[int] = Field(alias="courseIds")


class PreparedCourseSnapshot(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course_name: str | None = Field(alias="courseName")
    available: bool
    draft_schedule_id: int | None = Field(alias="draftScheduleId")
    draft_revision: int | None = Field(alias="draftRevision")
    replacement_required: bool = Field(alias="replacementRequired")


class BatchPreparationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    schedule_revision_id: int | None = Field(alias="scheduleRevisionId")
    operation_kind: BatchOperationKind = Field(alias="operationKind")
    courses: list[PreparedCourseSnapshot]
    replacement_course_ids: list[int] = Field(alias="replacementCourseIds")


class PreparedCourseInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    course_id: int = Field(alias="courseId", ge=1)
    expected_draft_schedule_id: int | None = Field(alias="expectedDraftScheduleId")
    expected_draft_revision: int | None = Field(alias="expectedDraftRevision", ge=1)


class BatchGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    schedule_revision_id: int = Field(alias="scheduleRevisionId", ge=1)
    operation_kind: BatchOperationKind = Field(alias="operationKind")
    replacement_confirmed: bool = Field(alias="replacementConfirmed")
    courses: list[PreparedCourseInput]


class CourseGenerationFailure(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str
    message: str
    holiday_date: date | None = Field(default=None, alias="holidayDate")
    holiday_name: str | None = Field(default=None, alias="holidayName")

    @model_validator(mode="after")
    def validate_holiday_evidence(self) -> "CourseGenerationFailure":
        is_holiday = self.code == "INSTITUTION_HOLIDAY"
        has_both = self.holiday_date is not None and self.holiday_name is not None
        has_either = self.holiday_date is not None or self.holiday_name is not None
        if is_holiday and not has_both:
            raise ValueError("Institution holiday failures require holiday date and name.")
        if not is_holiday and has_either:
            raise ValueError("Holiday evidence is only valid for institution holiday failures.")
        return self


class CourseGenerationOutcome(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course_name: str | None = Field(alias="courseName")
    status: str
    draft_schedule_id: int | None = Field(alias="draftScheduleId")
    draft_revision: int | None = Field(alias="draftRevision")
    errors: list[CourseGenerationFailure]


class BatchGenerationSummary(BaseModel):
    total: int
    succeeded: int
    failed: int


class BatchGenerationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    operation_kind: BatchOperationKind = Field(alias="operationKind")
    summary: BatchGenerationSummary
    outcomes: list[CourseGenerationOutcome]


class BatchRequestFailure(BaseModel):
    code: str
    message: str


class BatchRequestFailureResponse(BaseModel):
    errors: list[BatchRequestFailure]


class ReplacementConfirmationRequiredResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    code: str = "REPLACEMENT_CONFIRMATION_REQUIRED"
    message: str
    replacement_course_ids: list[int] = Field(alias="replacementCourseIds")


class BatchOperationFailureResponse(BaseModel):
    code: str = "BATCH_OPERATION_FAILED"
    message: str
