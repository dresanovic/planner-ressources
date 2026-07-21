from datetime import date, datetime, time
from enum import StrEnum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class LifecycleModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        use_enum_values=True,
    )


class LifecycleState(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ABANDONED = "abandoned"


class TransitionAction(StrEnum):
    MARK_READY = "mark_ready"
    RETURN_TO_DRAFT = "return_to_draft"
    PUBLISH = "publish"
    ABANDON = "abandon"
    RESTORE = "restore"


class LifecycleEventType(StrEnum):
    CREATED = "created"
    MARKED_READY = "marked_ready"
    RETURNED_TO_DRAFT = "returned_to_draft"
    PUBLISHED = "published"
    SUPERSEDED = "superseded"
    ABANDONED = "abandoned"
    RESTORED = "restored"


class CreateWorkingRevisionRequest(LifecycleModel):
    expected_state_token: str = Field(min_length=1)


class PreparePublicationRequest(LifecycleModel):
    expected_revision_version: int = Field(ge=1)
    expected_state_token: str = Field(min_length=1)


class TransitionRevisionRequest(LifecycleModel):
    action: TransitionAction
    expected_revision_version: int = Field(ge=1)
    expected_state_token: str = Field(min_length=1)
    confirmed: bool
    publication_token: str | None = None


class ScheduleRevisionEventResponse(LifecycleModel):
    event_sequence: int = Field(ge=1)
    event_type: LifecycleEventType
    from_state: LifecycleState | None
    to_state: LifecycleState
    occurred_at: datetime


class RevisionAllowedActions(LifecycleModel):
    mark_ready: bool
    return_to_draft: bool
    prepare_publication: bool
    abandon: bool
    restore: bool
    edit_schedule: bool


class ScheduleRevisionSummary(LifecycleModel):
    revision_id: int = Field(ge=1)
    semester_id: int = Field(ge=1)
    revision_number: int = Field(ge=1)
    revision_version: int = Field(ge=1)
    state: LifecycleState
    origin_revision_id: int | None
    is_active_working: bool
    is_current_publication: bool
    created_at: datetime
    state_changed_at: datetime
    published_at: datetime | None
    events: list[ScheduleRevisionEventResponse]
    allowed_actions: RevisionAllowedActions


class LifecycleAllowedActions(LifecycleModel):
    create_working_revision: bool


class ScheduleLifecycleOverview(LifecycleModel):
    semester_id: int = Field(ge=1)
    semester_name: str = Field(min_length=1)
    state_token: str = Field(min_length=1)
    active_working_revision: ScheduleRevisionSummary | None
    current_publication: ScheduleRevisionSummary | None
    revisions: list[ScheduleRevisionSummary]
    allowed_actions: LifecycleAllowedActions


class PublicationCondition(LifecycleModel):
    code: str
    message: str = Field(min_length=1)
    course_id: int | None
    session_kind: str | None
    source_session_id: int | None
    details: dict[str, Any]


class CapturedEntity(LifecycleModel):
    source_id: int = Field(ge=1)
    name: str = Field(min_length=1)


class CapturedCohort(CapturedEntity):
    size: int = Field(ge=0)


class CapturedResource(CapturedEntity):
    reference_code: str = Field(min_length=1)
    capacity: int | None = Field(default=None, ge=1)


class CapturedIssue(LifecycleModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)
    details: dict[str, Any] = Field(default_factory=dict)


class CapturedTeachingSession(LifecycleModel):
    source_session_id: int = Field(ge=1)
    date: date
    start_time: time
    end_time: time
    units: int = Field(ge=1)
    time_window_id: int | None
    constraint_window_index: int = Field(ge=0)
    lecturer: CapturedResource
    room: CapturedResource
    validation_alerts: list[CapturedIssue]


class CapturedCourseSchedule(LifecycleModel):
    source_course_id: int = Field(ge=1)
    name: str = Field(min_length=1)
    cohort: CapturedCohort
    study_type: CapturedEntity
    total_units: int = Field(ge=0)
    scheduled_units: int = Field(ge=0)
    remaining_units: int = Field(ge=0)
    draft_status: str | None
    teaching_sessions: list[CapturedTeachingSession]


class CapturedExamSession(LifecycleModel):
    source_exam_id: int = Field(ge=1)
    course: CapturedEntity
    cohort: CapturedEntity
    lecturer: CapturedResource
    room: CapturedResource
    exam_date: date
    start_time: time
    end_time: time
    source: str
    configuration_identifier: str = Field(min_length=1)
    configuration_revision: int = Field(ge=1)
    duration_minutes: int = Field(ge=1)
    exam_type: str = Field(min_length=1)
    required_capacity: int = Field(ge=1)
    recommended_start_date: date
    recommended_end_date: date
    recommendation_was_overridden: bool
    final_teaching_date: date
    final_teaching_end_time: time
    validity_issues: list[CapturedIssue]
    outside_recommended_window: bool


class CapturedSemester(LifecycleModel):
    source_id: int = Field(ge=1)
    name: str = Field(min_length=1)
    start_date: date
    end_date: date


class SemesterScheduleSnapshot(LifecycleModel):
    schema_version: int = Field(default=1, ge=1)
    captured_at: datetime
    semester: CapturedSemester
    courses: list[CapturedCourseSchedule]
    exam_sessions: list[CapturedExamSession]
    captured_conditions: list[PublicationCondition]


class PublicationPreparation(LifecycleModel):
    preparation_token: str = Field(min_length=1)
    prepared_at: datetime
    semester_id: int = Field(ge=1)
    semester_name: str = Field(min_length=1)
    target_revision: ScheduleRevisionSummary
    consequence: str
    current_publication: ScheduleRevisionSummary | None
    course_count: int = Field(ge=0)
    total_units: int = Field(ge=0)
    scheduled_units: int = Field(ge=0)
    remaining_units: int = Field(ge=0)
    conditions: list[PublicationCondition]


class ScheduleRevisionContent(LifecycleModel):
    revision: ScheduleRevisionSummary
    content_source: str
    snapshot: SemesterScheduleSnapshot


class LifecycleErrorItem(LifecycleModel):
    code: str
    message: str
    field: str | None = None
    meta: dict[str, Any] | None = None


class ErrorResponse(LifecycleModel):
    errors: list[LifecycleErrorItem]


class LifecycleConflictResponse(ErrorResponse):
    current_overview: ScheduleLifecycleOverview | None
