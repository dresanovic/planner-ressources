from __future__ import annotations

from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


def _camel(value: str) -> str:
    head, *tail = value.split("_")
    return head + "".join(item.capitalize() for item in tail)


class WorkspaceModel(BaseModel):
    model_config = ConfigDict(
        alias_generator=_camel,
        populate_by_name=True,
        extra="forbid",
    )


class SemesterReference(WorkspaceModel):
    semester_id: int = Field(ge=1)
    name: str
    start_date: date
    end_date: date


class RevisionSelector(WorkspaceModel):
    revision_id: int = Field(ge=1)
    revision_number: int = Field(ge=1)
    lifecycle_state: Literal["draft", "ready_for_review", "published"]
    designation: Literal["active_working", "current_published"]


class RevisionContext(RevisionSelector):
    read_only: bool
    content_source: Literal["active_working", "captured_published"]
    validation_basis: Literal["current"] = "current"
    snapshot_schema_version: Literal[1, 2] | None


class AvailableContexts(WorkspaceModel):
    active_working: RevisionSelector | None
    current_published: RevisionSelector | None


class SectionStatus(WorkspaceModel):
    availability: Literal["available", "partial", "unavailable"]
    reason: str | None = None
    coverage: str | None = None


class SectionStatuses(WorkspaceModel):
    courses: SectionStatus
    occurrences: SectionStatus
    holidays: SectionStatus
    validation_findings: SectionStatus
    planning_outcomes: SectionStatus
    summary: SectionStatus


class WorkspaceCourse(WorkspaceModel):
    course_ref: str
    course_id: int = Field(ge=1)
    code: str
    name: str
    cohort: str
    lecturer_refs: list[str]
    study_type: str
    planning_eligible: bool
    total_teaching_units: int = Field(ge=0)
    scheduled_teaching_units: int = Field(ge=0)
    remaining_teaching_units: int = Field(ge=0)
    remaining_instructional_minutes: int = Field(ge=0, multiple_of=45)
    occurrence_refs: list[str]
    finding_refs: list[str]
    outcome_refs: list[str]
    needs_review_reason_refs: list[str]


class OccurrenceBase(WorkspaceModel):
    occurrence_ref: str
    course_ref: str
    date: date
    start_time: str
    end_time: str
    cohort: str
    lecturer_refs: list[str]
    room_ref: str
    finding_refs: list[str]


class TeachingOccurrence(OccurrenceBase):
    kind: Literal["teaching"]
    teaching_units: int = Field(ge=1)
    source: str


class ExamValidityContext(WorkspaceModel):
    configuration_identifier: str
    configuration_revision: int = Field(ge=0)
    final_teaching_date: date
    final_teaching_end_time: str
    source: str
    captured_issues: list[Any] | None = None


class ExamRecommendationContext(WorkspaceModel):
    recommended_start_date: date
    recommended_end_date: date
    recommendation_was_overridden: bool
    outside_recommended_window: bool


class ExamOccurrence(OccurrenceBase):
    kind: Literal["exam"]
    exam_type: str
    duration_minutes: int = Field(ge=1)
    required_capacity: int = Field(ge=0)
    assigned_room_name: str
    current_room_capacity: int | None = Field(default=None, ge=0)
    validity_context: ExamValidityContext
    recommendation_context: ExamRecommendationContext | None = None


class Holiday(WorkspaceModel):
    holiday_ref: str
    date: date
    name: str


class ConflictFindingDetails(WorkspaceModel):
    kind: Literal["conflict"]
    conflict_type: Literal["lecturer", "room", "cohort"]
    occurrence_refs: list[str] = Field(min_length=2)
    subject_ref: str


class CapacityFindingDetails(WorkspaceModel):
    kind: Literal["capacity"]
    occurrence_ref: str
    required_capacity: int = Field(ge=0)
    room_ref: str
    room_name: str
    current_capacity: int = Field(ge=0)


class HolidayFindingDetails(WorkspaceModel):
    kind: Literal["holiday"]
    holiday_ref: str
    holiday_date: date
    holiday_name: str
    occurrence_refs: list[str] = Field(min_length=1)


class ExamValidityFindingDetails(WorkspaceModel):
    kind: Literal["exam_validity"]
    exam_occurrence_ref: str
    issue_code: str
    supporting_values: dict[str, str | int | bool]


class OtherFindingDetails(WorkspaceModel):
    kind: Literal["other"]
    issue_code: str
    occurrence_refs: list[str] = Field(min_length=1)
    room_ref: str | None = None
    subject_ref: str | None = None


class ValidationFinding(WorkspaceModel):
    finding_ref: str
    category: Literal[
        "lecturer_conflict",
        "room_conflict",
        "cohort_conflict",
        "room_capacity",
        "holiday",
        "exam_validity",
        "other",
    ]
    validation_basis: Literal["current"] = "current"
    affected_course_refs: list[str]
    affected_occurrence_refs: list[str]
    details: (
        ConflictFindingDetails
        | CapacityFindingDetails
        | HolidayFindingDetails
        | ExamValidityFindingDetails
        | OtherFindingDetails
    ) = Field(discriminator="kind")

    @model_validator(mode="after")
    def category_matches_details(self):
        expected = {
            "lecturer_conflict": "conflict",
            "room_conflict": "conflict",
            "cohort_conflict": "conflict",
            "room_capacity": "capacity",
            "holiday": "holiday",
            "exam_validity": "exam_validity",
            "other": "other",
        }[self.category]
        if self.details.kind != expected:
            raise ValueError("Finding category and detail kind must match.")
        if isinstance(self.details, ConflictFindingDetails):
            if self.category != f"{self.details.conflict_type}_conflict":
                raise ValueError("Conflict category and type must match.")
        return self


class RetainedPlanningOutcome(WorkspaceModel):
    outcome_ref: str
    revision_id: int = Field(ge=1)
    course_ref: str
    operation_kind: Literal[
        "single_course_generation",
        "multi_course_generation",
        "semester_optimization",
        "exam_generation",
    ]
    classification: Literal["successful", "failed", "stale", "unchanged", "skipped"]
    source_status: str
    reasons: list[dict[str, Any]]
    completed_at: datetime


class PlanningOutcomeCoverage(WorkspaceModel):
    eligible_course_count: int = Field(ge=0)
    covered_course_count: int = Field(ge=0)
    coverage_complete: bool


class MetricSummary(WorkspaceModel):
    availability: Literal["available", "partial", "unavailable", "not_applicable"]
    scope: Literal["complete_revision", "no_revision"]
    contributor_refs: list[str]
    remaining_teaching_units: int | None = Field(default=None, ge=0)
    remaining_instructional_minutes: int | None = Field(
        default=None, ge=0, multiple_of=45
    )
    contributing_course_count: int | None = Field(default=None, ge=0)
    distinct_finding_count: int | None = Field(default=None, ge=0)
    count_by_type: dict[str, int] | None = None
    affected_occurrence_count: int | None = Field(default=None, ge=0)
    coverage: PlanningOutcomeCoverage | None = None
    failed_outcome_count: int | None = Field(default=None, ge=0)
    stale_outcome_count: int | None = Field(default=None, ge=0)
    unchanged_outcome_count: int | None = Field(default=None, ge=0)
    distinct_course_count: int | None = Field(default=None, ge=0)
    unavailable_reason: str | None = None
    not_applicable_reason: str | None = None

    @model_validator(mode="after")
    def reason_matches_availability(self):
        if self.availability == "unavailable" and not self.unavailable_reason:
            raise ValueError("Unavailable metrics require an unavailable reason.")
        if self.availability == "not_applicable" and not self.not_applicable_reason:
            raise ValueError("Not-applicable metrics require a reason.")
        value_fields = (
            self.remaining_teaching_units,
            self.remaining_instructional_minutes,
            self.contributing_course_count,
            self.distinct_finding_count,
            self.count_by_type,
            self.affected_occurrence_count,
            self.failed_outcome_count,
            self.stale_outcome_count,
            self.unchanged_outcome_count,
            self.distinct_course_count,
        )
        if self.availability in {"unavailable", "not_applicable"} and any(
            value is not None for value in value_fields
        ):
            raise ValueError(
                "Unavailable and not-applicable metrics cannot expose numeric values."
            )
        return self


class WorkspaceSummary(WorkspaceModel):
    unscheduled_work: MetricSummary
    conflicts: MetricSummary
    capacity_issues: MetricSummary
    planning_failures: MetricSummary
    needs_review: MetricSummary

    @model_validator(mode="after")
    def available_metrics_have_named_values(self):
        required = {
            "unscheduled_work": (
                "remaining_teaching_units",
                "remaining_instructional_minutes",
                "contributing_course_count",
            ),
            "conflicts": ("distinct_finding_count", "count_by_type"),
            "capacity_issues": ("affected_occurrence_count",),
            "planning_failures": (
                "coverage",
                "failed_outcome_count",
                "stale_outcome_count",
                "unchanged_outcome_count",
            ),
            "needs_review": ("distinct_course_count",),
        }
        for metric_name, field_names in required.items():
            metric = getattr(self, metric_name)
            if metric.availability not in {"available", "partial"}:
                continue
            if any(getattr(metric, field_name) is None for field_name in field_names):
                raise ValueError(
                    f"{metric_name} requires its named values when available or partial."
                )
        return self


class FacetValue(WorkspaceModel):
    value: str
    label: str


class FilterFacets(WorkspaceModel):
    courses: list[FacetValue]
    cohorts: list[FacetValue]
    lecturers: list[FacetValue]
    rooms: list[FacetValue]
    study_types: list[FacetValue]
    session_types: list[FacetValue]
    lifecycle_contexts: list[FacetValue]
    validation_categories: list[FacetValue]


class WorkspaceResponseBase(WorkspaceModel):
    semester: SemesterReference
    available_contexts: AvailableContexts
    workspace_token: str = Field(min_length=1)
    section_status: SectionStatuses
    courses: list[WorkspaceCourse]
    occurrences: list[TeachingOccurrence | ExamOccurrence]
    holidays: list[Holiday]
    validation_findings: list[ValidationFinding]
    planning_outcomes: list[RetainedPlanningOutcome]
    summary: WorkspaceSummary
    filter_facets: FilterFacets


class LoadedCalendarWorkspaceResponse(WorkspaceResponseBase):
    workspace_state: Literal["loaded"]
    selected_revision: RevisionContext


class NoRevisionCalendarWorkspaceResponse(WorkspaceResponseBase):
    workspace_state: Literal["no_revision"]
    selected_revision: None

    @model_validator(mode="after")
    def revision_owned_sections_are_empty(self):
        if any(
            (
                self.courses,
                self.occurrences,
                self.holidays,
                self.validation_findings,
                self.planning_outcomes,
            )
        ):
            raise ValueError("No-revision workspaces cannot contain revision-owned data.")
        return self


CalendarWorkspaceResponse = (
    LoadedCalendarWorkspaceResponse | NoRevisionCalendarWorkspaceResponse
)


class WorkspaceProblem(WorkspaceModel):
    detail: str
