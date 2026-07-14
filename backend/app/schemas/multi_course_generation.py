from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class BatchOperationKind(StrEnum):
    INITIAL = "initial"
    RETRY = "retry"


class BatchPreparationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
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
    operation_kind: BatchOperationKind = Field(alias="operationKind")
    replacement_confirmed: bool = Field(alias="replacementConfirmed")
    courses: list[PreparedCourseInput]


class CourseGenerationFailure(BaseModel):
    code: str
    message: str


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
