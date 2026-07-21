from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ExamModel(BaseModel):
    model_config = ConfigDict(alias_generator=lambda value: value.split("_")[0] + "".join(part.title() for part in value.split("_")[1:]), populate_by_name=True, extra="forbid")


class OperationError(ExamModel):
    code: str
    message: str
    field: str | None = None


class ErrorResponse(ExamModel):
    errors: list[OperationError]


class ExamConfigurationInput(ExamModel):
    identifier: str
    duration_minutes: int
    recommended_start_override: date | None
    recommended_end_override: date | None
    required_capacity: int
    exam_type: str
    responsible_lecturer_id: int


class SaveExamConfigurationRequest(ExamModel):
    semester_id: int = Field(ge=1)
    enabled: bool
    expected_revision: int | None = Field(ge=1)
    configuration: ExamConfigurationInput | None


class ExamConfiguration(ExamModel):
    id: int
    revision: int
    identifier: str
    duration_minutes: int
    recommended_start_override: date | None
    recommended_end_override: date | None
    required_capacity: int
    exam_type: str
    responsible_lecturer_id: int
    configuration_consumed: bool
    recommended_start_date: date | None
    recommended_end_date: date | None
    recommendation_was_overridden: bool


class FinalTeachingAnchor(ExamModel):
    date: date
    end_time: str
    teaching_session_id: int


class GenerationEligibility(ExamModel):
    eligible: bool
    code: str | None
    message: str | None


class ResourceReference(ExamModel):
    id: int
    name: str
    reference_code: str | None = None


class RoomReference(ResourceReference):
    capacity: int


class ExamIssue(ExamModel):
    code: str
    message: str
    related_date: date | None = None
    related_resource: ResourceReference | None = None
    related_session_id: int | None = None
    holiday_name: str | None = None


class ExamSessionResponse(ExamModel):
    id: int
    revision: int
    course_id: int
    semester_id: int
    configuration_identifier: str
    exam_type: str
    duration_minutes: int
    required_capacity: int
    recommended_start_date: date
    recommended_end_date: date
    recommendation_was_overridden: bool
    outside_recommended_window: bool
    final_teaching_anchor: FinalTeachingAnchor
    date: date
    start_time: str
    end_time: str
    lecturer: ResourceReference
    cohort: ResourceReference
    room: RoomReference
    lifecycle_status: Literal["active", "past"]
    source: Literal["generated", "manual"]
    validity_issues: list[ExamIssue]
    input_snapshot_token: str


class ExamCoursePlanningState(ExamModel):
    course_id: int
    course_name: str
    semester_id: int
    cohort_id: int
    cohort_name: str
    enabled: bool
    configuration: ExamConfiguration | None
    final_teaching_anchor: FinalTeachingAnchor | None
    active_exam: ExamSessionResponse | None
    past_exams: list[ExamSessionResponse]
    generation_eligibility: GenerationEligibility
    input_snapshot_token: str


class ExamPlanningOverview(ExamModel):
    semester_id: int
    institution_today: date
    courses: list[ExamCoursePlanningState]


class ExamGenerationPreparationRequest(ExamModel):
    semester_id: int = Field(ge=1)
    schedule_revision_id: int = Field(ge=1)
    course_ids: list[int] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_courses(self):
        if len(set(self.course_ids)) != len(self.course_ids) or any(value < 1 for value in self.course_ids):
            raise ValueError("courseIds must be unique.")
        return self


class PreparedExamCourse(ExamModel):
    course_id: int
    course_name: str
    configuration_id: int | None
    configuration_revision: int | None
    input_snapshot_token: str
    eligibility: GenerationEligibility


class ExamGenerationPreparation(ExamModel):
    semester_id: int
    schedule_revision_id: int | None
    institution_today: date
    shared_snapshot_token: str
    courses: list[PreparedExamCourse]


class PreparedExamCourseInput(ExamModel):
    course_id: int = Field(ge=1)
    configuration_id: int | None
    configuration_revision: int | None
    input_snapshot_token: str


class GenerateExamsRequest(ExamModel):
    semester_id: int = Field(ge=1)
    schedule_revision_id: int = Field(ge=1)
    institution_today: date
    shared_snapshot_token: str
    courses: list[PreparedExamCourseInput] = Field(min_length=1, max_length=100)

    @model_validator(mode="after")
    def unique_courses(self):
        if len({item.course_id for item in self.courses}) != len(self.courses):
            raise ValueError("courses must contain unique courseIds.")
        return self


class ExamGenerationOutcome(ExamModel):
    course_id: int
    course_name: str
    configuration_id: int | None
    configuration_identifier: str | None
    status: Literal["scheduled", "failed", "stale", "skipped_active", "skipped_disabled"]
    saved: bool
    exam: ExamSessionResponse | None
    reasons: list[ExamIssue]


class ExamGenerationSummary(ExamModel):
    total: int
    scheduled: int
    failed: int
    stale: int
    skipped_active: int
    skipped_disabled: int
    elapsed_milliseconds: int
    optimal_for_prepared_snapshot: bool


class ExamGenerationResult(ExamModel):
    semester_id: int
    summary: ExamGenerationSummary
    outcomes: list[ExamGenerationOutcome]


class CreateManualExamRequest(ExamModel):
    semester_id: int = Field(ge=1)
    schedule_revision_id: int = Field(ge=1)
    date: date
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    lecturer_id: int = Field(ge=1)
    room_id: int = Field(ge=1)
    expected_configuration_revision: int = Field(ge=1)
    input_snapshot_token: str


class UpdateExamRequest(ExamModel):
    schedule_revision_id: int = Field(ge=1)
    date: date
    start_time: str = Field(pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    lecturer_id: int = Field(ge=1)
    room_id: int = Field(ge=1)
    expected_exam_revision: int = Field(ge=1)
    input_snapshot_token: str


class DeleteExamRequest(ExamModel):
    schedule_revision_id: int = Field(ge=1)
    confirmed: Literal[True]
    expected_exam_revision: int = Field(ge=1)
    input_snapshot_token: str


class DeleteExamResponse(ExamModel):
    deleted_exam_id: int
    deleted_lifecycle_status: Literal["active", "past"]
    consequence: Literal["configuration_enabled_unscheduled", "historical_exam_only"]
    state: ExamCoursePlanningState
