from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Literal
from uuid import UUID
import unicodedata

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(part.capitalize() for part in tail)


class LecturerReviewModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra="forbid",
        use_enum_values=True,
    )


class RevisionState(StrEnum):
    DRAFT = "draft"
    READY_FOR_REVIEW = "ready_for_review"
    PUBLISHED = "published"
    ABANDONED = "abandoned"
    SUPERSEDED = "superseded"


class LinkStatus(StrEnum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REVOKED = "revoked"
    REPLACED = "replaced"
    REVISION_ENDED = "revision_ended"


class FeedbackAvailability(StrEnum):
    COMPLETE = "complete"
    PARTIAL = "partial"
    UNAVAILABLE = "unavailable"


class FeedbackKind(StrEnum):
    REVISION_COMMENT = "revision_comment"
    SESSION_COMMENT = "session_comment"
    IMPOSSIBLE_SESSION = "impossible_session"


class SessionKind(StrEnum):
    TEACHING = "teaching"
    EXAM = "exam"


class FeedbackOutcome(StrEnum):
    CREATED = "created"
    ALREADY_ACCEPTED = "already_accepted"


class IssueLinkInput(LecturerReviewModel):
    lecturer_id: int = Field(ge=1)
    duration_days: Literal[1, 2, 3] = 3


class ReplaceLinkInput(LecturerReviewModel):
    duration_days: Literal[1, 2, 3] = 3


class RevisionSummary(LecturerReviewModel):
    id: int = Field(ge=1)
    semester_id: int = Field(ge=1)
    semester_name: str = Field(min_length=1)
    label: str = Field(min_length=1)
    state: RevisionState


class CourseIdentity(LecturerReviewModel):
    source_course_id: int = Field(ge=1)
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)


class LecturerAssignmentSummary(LecturerReviewModel):
    lecturer_id: int = Field(ge=1)
    lecturer_name: str = Field(min_length=1)
    session_count: int = Field(ge=0)
    courses: list[CourseIdentity]
    initial_issue_allowed: bool


class LinkSummary(LecturerReviewModel):
    id: int = Field(ge=1)
    revision_id: int = Field(ge=1)
    lecturer_id: int = Field(ge=1)
    intended_lecturer_name: str = Field(min_length=1)
    duration_days: Literal[1, 2, 3]
    issued_at: datetime
    expires_at: datetime
    time_zone: str = Field(min_length=1)
    status: LinkStatus
    ended_at: datetime | None = None
    replace_allowed: bool


class PlannerSessionNavigation(LecturerReviewModel):
    revision_id: int = Field(ge=1)
    occurrence_ref: str = Field(pattern=r"^(teaching|exam):[1-9][0-9]*$")


class SessionContext(LecturerReviewModel):
    session_ref: str = Field(pattern=r"^(teaching|exam):[1-9][0-9]*$")
    session_kind: SessionKind
    source_session_id: int = Field(ge=1)
    session_type: str = Field(min_length=1)
    course_source_id: int = Field(ge=1)
    course_code: str = Field(min_length=1)
    course_title: str = Field(min_length=1)
    date: date
    start_time: str = Field(min_length=1)
    end_time: str = Field(min_length=1)
    time_zone: str = Field(min_length=1)
    room_name: str = Field(min_length=1)
    cohort_name: str = Field(min_length=1)
    study_type: str | None = None
    teaching_units: int | None = Field(default=None, ge=1)
    exam_duration_minutes: int | None = Field(default=None, ge=1)


class PlannerFeedbackItem(LecturerReviewModel):
    id: int = Field(ge=1)
    intended_lecturer_id: int = Field(ge=1)
    intended_lecturer_name: str = Field(min_length=1)
    attribution: str = Field(min_length=1)
    kind: FeedbackKind
    comment: str | None = Field(default=None, max_length=2000)
    session_context: SessionContext | None = None
    submitted_at: datetime
    time_zone: str = Field(min_length=1)

    @model_validator(mode="after")
    def kind_matches_captured_context(self):
        if self.kind == FeedbackKind.REVISION_COMMENT:
            if self.session_context is not None:
                raise ValueError("Revision feedback cannot contain session context.")
        elif self.session_context is None:
            raise ValueError("Session feedback requires captured session context.")
        return self


class PlannerFeedbackGroup(LecturerReviewModel):
    group_ref: str = Field(min_length=1)
    level: Literal["revision", "session"]
    session_context: SessionContext | None = None
    current_navigation: PlannerSessionNavigation | None = None
    impossible_flag_count: int = Field(ge=0)
    items: list[PlannerFeedbackItem]

    @model_validator(mode="after")
    def level_matches_session_fields(self):
        if self.level == "revision" and (
            self.session_context is not None or self.current_navigation is not None
        ):
            raise ValueError("Revision feedback groups cannot contain session fields.")
        if self.level == "session" and self.session_context is None:
            raise ValueError("Session feedback groups require captured session context.")
        return self


class PlannerReviewOverview(LecturerReviewModel):
    revision: RevisionSummary
    lecturers: list[LecturerAssignmentSummary]
    links: list[LinkSummary]
    feedback_availability: FeedbackAvailability
    total_feedback_count: int | None = Field(default=None, ge=0)
    impossible_flag_count: int | None = Field(default=None, ge=0)
    feedback_groups: list[PlannerFeedbackGroup]

    @model_validator(mode="after")
    def counts_match_availability(self):
        counts = (self.total_feedback_count, self.impossible_flag_count)
        if self.feedback_availability == FeedbackAvailability.COMPLETE:
            if any(value is None for value in counts):
                raise ValueError("Complete feedback requires both exact counts.")
        elif any(value is not None for value in counts):
            raise ValueError("Partial or unavailable feedback cannot expose exact counts.")
        return self


class IssuedLinkResult(LecturerReviewModel):
    secret: str = Field(pattern=r"^[A-Za-z0-9_-]{43}$")
    issued_link: LinkSummary
    overview: PlannerReviewOverview


class PublicSession(LecturerReviewModel):
    session_ref: str = Field(pattern=r"^(teaching|exam):[1-9][0-9]*$")
    session_kind: SessionKind
    source_session_id: int = Field(ge=1)
    course_ref: str = Field(pattern=r"^course:[1-9][0-9]*$")
    session_type: str = Field(min_length=1)
    date: date
    start_time: str = Field(min_length=1)
    end_time: str = Field(min_length=1)
    time_zone: str = Field(min_length=1)
    room_name: str = Field(min_length=1)
    room_ref: str = Field(pattern=r"^room:[1-9][0-9]*$")
    cohort_name: str = Field(min_length=1)
    teaching_units: int | None = Field(default=None, ge=1)
    exam_duration_minutes: int | None = Field(default=None, ge=1)
    validation_finding_refs: list[str]


class PublicCourse(LecturerReviewModel):
    source_course_id: int = Field(ge=1)
    course_ref: str = Field(pattern=r"^course:[1-9][0-9]*$")
    code: str = Field(min_length=1)
    title: str = Field(min_length=1)
    cohort_name: str = Field(min_length=1)
    study_type: str = Field(min_length=1)
    sessions: list[PublicSession]


class PublicValidationFinding(LecturerReviewModel):
    finding_ref: str = Field(min_length=1)
    category: Literal[
        "lecturer_conflict",
        "room_conflict",
        "cohort_conflict",
        "room_capacity",
        "holiday",
        "exam_validity",
        "other",
    ]
    message: str = Field(min_length=1)
    affected_session_refs: list[str]


class PublicFacetValue(LecturerReviewModel):
    value: str = Field(min_length=1)
    label: str = Field(min_length=1)


class PublicFilterFacets(LecturerReviewModel):
    courses: list[PublicFacetValue]
    cohorts: list[PublicFacetValue]
    rooms: list[PublicFacetValue]
    study_types: list[PublicFacetValue]
    session_types: list[PublicFacetValue]
    lifecycle_contexts: list[PublicFacetValue] = Field(max_length=1)
    validation_categories: list[PublicFacetValue]


class PublicFeedbackItem(LecturerReviewModel):
    id: int = Field(ge=1)
    kind: FeedbackKind
    session_ref: str | None = Field(
        default=None,
        pattern=r"^(teaching|exam):[1-9][0-9]*$",
    )
    comment: str | None = Field(default=None, max_length=2000)
    submitted_at: datetime
    time_zone: str = Field(min_length=1)


class PublicReview(LecturerReviewModel):
    intended_lecturer: str = Field(min_length=1)
    identity_disclaimer: str = Field(min_length=1)
    revision: RevisionSummary
    access_expires_at: datetime
    time_zone: str = Field(min_length=1)
    semester_start_date: date
    semester_end_date: date
    validation_availability: FeedbackAvailability
    validation_findings: list[PublicValidationFinding]
    filter_facets: PublicFilterFacets
    courses: list[PublicCourse]
    submitted_feedback: list[PublicFeedbackItem]


class FeedbackInput(LecturerReviewModel):
    client_submission_id: UUID
    kind: FeedbackKind
    session_ref: str | None = Field(
        default=None,
        pattern=r"^(teaching|exam):[1-9][0-9]*$",
    )
    comment: str | None = None

    @field_validator("comment")
    @classmethod
    def trim_visible_comment(cls, value: str | None) -> str | None:
        if value is None:
            return None
        trimmed = value.strip()
        if len(trimmed) > 2000:
            raise ValueError("A provided comment cannot exceed 2000 characters.")
        if not any(
            unicodedata.category(character)[0] in {"L", "N", "P", "S"}
            for character in trimmed
        ):
            raise ValueError("A provided comment must contain visible text.")
        return trimmed

    @model_validator(mode="after")
    def kind_matches_fields(self):
        if self.kind == FeedbackKind.REVISION_COMMENT:
            if self.session_ref is not None or self.comment is None:
                raise ValueError(
                    "Revision comments require comment and prohibit sessionRef."
                )
        elif self.kind == FeedbackKind.SESSION_COMMENT:
            if self.session_ref is None or self.comment is None:
                raise ValueError(
                    "Session comments require both sessionRef and comment."
                )
        elif self.session_ref is None:
            raise ValueError("Impossible-session feedback requires sessionRef.")
        return self


class FeedbackResult(LecturerReviewModel):
    outcome: FeedbackOutcome
    item: PublicFeedbackItem


class PlannerError(LecturerReviewModel):
    code: str = Field(min_length=1)
    message: str = Field(min_length=1)


class PublicUnavailableError(LecturerReviewModel):
    code: Literal["REVIEW_UNAVAILABLE"] = "REVIEW_UNAVAILABLE"
    message: Literal[
        "This review is unavailable. Contact the planner for a new link."
    ] = "This review is unavailable. Contact the planner for a new link."


class PublicThrottledError(LecturerReviewModel):
    code: Literal[
        "REVIEW_TEMPORARILY_UNAVAILABLE"
    ] = "REVIEW_TEMPORARILY_UNAVAILABLE"
    message: Literal[
        "This review is temporarily unavailable. Try again later."
    ] = "This review is temporarily unavailable. Try again later."


class PublicRefreshRequiredError(LecturerReviewModel):
    code: Literal["REVIEW_REFRESH_REQUIRED"] = "REVIEW_REFRESH_REQUIRED"
    message: Literal[
        "The schedule changed. Reload the browser page or reopen the link before submitting feedback."
    ] = "The schedule changed. Reload the browser page or reopen the link before submitting feedback."


class PublicValidationError(LecturerReviewModel):
    code: Literal["INVALID_FEEDBACK"] = "INVALID_FEEDBACK"
    message: str = Field(min_length=1)
