from datetime import date
from math import isfinite
from enum import StrEnum
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, UUID4, model_validator

from app.schemas.draft_schedule import GenerationConstraintsResponse


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
    ACTIVE_EXAM_BOUNDARY = "ACTIVE_EXAM_BOUNDARY"
    STUDY_TYPE_WINDOW_UNAVAILABLE = "STUDY_TYPE_WINDOW_UNAVAILABLE"
    LECTURER_UNAVAILABLE = "LECTURER_UNAVAILABLE"
    ROOM_UNAVAILABLE = "ROOM_UNAVAILABLE"
    NO_ELIGIBLE_LECTURER = "NO_ELIGIBLE_LECTURER"
    NO_ELIGIBLE_ROOM = "NO_ELIGIBLE_ROOM"
    INSUFFICIENT_ROOM_CAPACITY = "INSUFFICIENT_ROOM_CAPACITY"
    UNAVAILABLE_DATE = "UNAVAILABLE_DATE"
    INSTITUTION_HOLIDAY = "INSTITUTION_HOLIDAY"
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
    holiday_date: date | None = Field(default=None, alias="holidayDate")
    holiday_name: str | None = Field(default=None, alias="holidayName")
    source_kind: Literal["teaching_session", "active_exam"] | None = Field(
        default=None, alias="sourceKind"
    )
    source_id: int | None = Field(default=None, alias="sourceId", ge=1)

    @model_validator(mode="after")
    def validate_holiday_evidence(self) -> "BlockingReason":
        is_holiday = self.code == BlockingReasonCode.INSTITUTION_HOLIDAY
        has_both = self.holiday_date is not None and self.holiday_name is not None
        has_either = self.holiday_date is not None or self.holiday_name is not None
        if is_holiday and not has_both:
            raise ValueError("Institution holiday reasons require holiday date and name.")
        if not is_holiday and has_either:
            raise ValueError("Holiday evidence is only valid for institution holiday reasons.")
        if (self.source_kind is None) != (self.source_id is None):
            raise ValueError("Protected source kind and ID must be provided together.")
        return self


class ArrangementImprovement(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    added_units: int = Field(alias="addedUnits", ge=0)
    reduced_conflicts: int = Field(alias="reducedConflicts", ge=0)
    reduced_lecturer_changes: int = Field(alias="reducedLecturerChanges", ge=0)
    reduced_room_changes: int = Field(alias="reducedRoomChanges", ge=0)


class OptimizationPreparationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    schedule_revision_id: int = Field(alias="scheduleRevisionId", ge=1)
    course_ids: list[int] = Field(alias="courseIds")
    unavailable_dates: list[date] = Field(default_factory=list, alias="unavailableDates")


class PreparedOptimizationCourse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    course_name: str | None = Field(alias="courseName")
    available: bool
    unavailable_reasons: list[BlockingReason] = Field(
        default_factory=list, alias="unavailableReasons"
    )
    draft_schedule_id: int | None = Field(alias="draftScheduleId")
    draft_revision: int | None = Field(alias="draftRevision")
    scheduled_units: int = Field(alias="scheduledUnits", ge=0)
    remaining_units: int = Field(alias="remainingUnits", ge=0)
    replacement_required: bool = Field(alias="replacementRequired")
    effective_constraints: GenerationConstraintsResponse = Field(alias="effectiveConstraints")
    input_snapshot_token: str = Field(alias="inputSnapshotToken", min_length=1)


class OptimizationPreparationResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    schedule_revision_id: int | None = Field(alias="scheduleRevisionId")
    unavailable_dates: list[date] = Field(alias="unavailableDates")
    shared_snapshot_token: str = Field(alias="sharedSnapshotToken")
    courses: list[PreparedOptimizationCourse]
    replacement_course_ids: list[int] = Field(alias="replacementCourseIds")
    budget_policy: "OptimizationBudgetPolicy" = Field(alias="budgetPolicy")
    algorithm: Literal['standard', 'cohort', 'lecturer', 'standard_optimized'] = 'standard'
    strategy_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='strategyProfile')
    strategy_settings: dict = Field(default_factory=dict, alias='strategySettings')


class PreparedOptimizationCourseInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    course_id: int = Field(alias="courseId", ge=1)
    expected_draft_schedule_id: int | None = Field(default=None, alias="expectedDraftScheduleId")
    expected_draft_revision: int | None = Field(default=None, alias="expectedDraftRevision", ge=1)
    input_snapshot_token: str = Field(alias="inputSnapshotToken", min_length=1)

    @model_validator(mode="after")
    def matching_draft_identity(self):
        if (self.expected_draft_schedule_id is None) != (self.expected_draft_revision is None):
            raise ValueError("Draft Schedule ID and revision must both be present or both be null.")
        return self


class OptimizationGenerationRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    semester_id: int = Field(alias="semesterId", ge=1)
    schedule_revision_id: int = Field(alias="scheduleRevisionId", ge=1)
    unavailable_dates: list[date] = Field(alias="unavailableDates")
    shared_snapshot_token: str = Field(alias="sharedSnapshotToken", min_length=1)
    courses: list[PreparedOptimizationCourseInput]


class AcceptRegenerationRequest(OptimizationGenerationRequest):
    candidate_fingerprint: str = Field(
        alias="candidateFingerprint", pattern=r"^[0-9a-f]{64}$"
    )


class IntensiveRational(BaseModel):
    numerator: int = Field(ge=0, strict=True)
    denominator: Literal[2700000000] = 2700000000


class IntensiveCohortDate(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    cohort_id: int = Field(alias='cohortId')
    date: date
    distinct_course_ids: list[int] = Field(alias='distinctCourseIds')
    distinct_lv_count: int = Field(alias='distinctLvCount',ge=1)
    variety_contribution: int = Field(alias='varietyContribution',ge=0)

    @model_validator(mode='after')
    def exact_counts(self):
        if self.distinct_course_ids != sorted(set(self.distinct_course_ids)) or self.distinct_lv_count != len(self.distinct_course_ids) or self.variety_contribution != max(0,self.distinct_lv_count-1):
            raise ValueError('Variety must count distinct courses once per cohort/date')
        return self


class IntensiveFacts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    total_units: int = Field(alias='totalUnits',ge=0)
    intensive_le: IntensiveRational = Field(alias='intensiveLe')
    daily_variety: int = Field(alias='dailyVariety',ge=0)
    cohort_dates: list[IntensiveCohortDate] = Field(alias='cohortDates')
    prepared_snapshot_token: str = Field(alias='preparedSnapshotToken',pattern=r'^[0-9a-f]{64}$')
    candidate_fingerprint: str = Field(alias='candidateFingerprint',pattern=r'^[0-9a-f]{64}$')

    @model_validator(mode='after')
    def exact_total(self):
        pairs = [(row.date,row.cohort_id) for row in self.cohort_dates]
        if pairs != sorted(set(pairs)) or self.daily_variety != sum(row.variety_contribution for row in self.cohort_dates):
            raise ValueError('Variety facts must be ordered, unique and sum to their total')
        return self


class CoverageFacts(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    required_units: int = Field(alias="requiredUnits", ge=0)
    scheduled_units: int = Field(alias="scheduledUnits", ge=0)
    remaining_units: int = Field(alias="remainingUnits", ge=0)
    status: Literal["complete", "partial"]
    intensive_facts: IntensiveFacts | None = Field(default=None,alias='intensiveFacts')

    @model_validator(mode='after')
    def reconciled_units(self):
        # Historical/current manual plans may already exceed the requirement.
        # Generated candidates are independently rejected for overallocation.
        if self.remaining_units != max(0, self.required_units - self.scheduled_units):
            raise ValueError('Required units must equal scheduled plus remaining units')
        if (self.status == 'complete') != (self.remaining_units == 0):
            raise ValueError('Coverage status must describe remaining units')
        return self


class ResolvedWarning(BaseModel):
    code: str
    count: int = Field(ge=1)


class LecturerPortionFacts(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    lecturer_id: int = Field(alias='lecturerId', ge=1)
    lecturer_code: str = Field(alias='lecturerCode')
    sequence_index: int = Field(alias='sequenceIndex', ge=0)
    source: Literal['derived', 'explicit']
    required_units: int = Field(alias='requiredUnits', ge=0, strict=True)
    scheduled_units: int = Field(alias='scheduledUnits', ge=0, strict=True)
    remaining_units: int = Field(alias='remainingUnits', ge=0, strict=True)
    reason_code: str | None = Field(default=None, alias='reasonCode')
    reason: str | None = None

    @model_validator(mode='after')
    def reconciled(self):
        if self.required_units != self.scheduled_units + self.remaining_units:
            raise ValueError('Portion totals must reconcile')
        if self.remaining_units and (not self.reason_code or not self.reason):
            raise ValueError('Unfilled portions require a blocker or uncertainty')
        return self


class CourseRegenerationComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId", ge=1)
    course_name: str | None = Field(alias="courseName")
    current: CoverageFacts
    generated: CoverageFacts
    resolved_current_warnings: list[ResolvedWarning] = Field(
        alias="resolvedCurrentWarnings"
    )
    remaining_reasons: list[BlockingReason] = Field(alias="remainingReasons")
    lecturer_portions: list[LecturerPortionFacts] = Field(default_factory=list, alias='lecturerPortions')

    @model_validator(mode='after')
    def ordered_portions(self):
        rows = self.lecturer_portions
        if rows:
            if [r.sequence_index for r in rows] != list(range(len(rows))) or len({r.lecturer_id for r in rows}) != len(rows):
                raise ValueError('Portions must have unique identities in sequence order')
            order = [(r.lecturer_code.strip().casefold(), r.lecturer_id) for r in rows]
            if order != sorted(order) or sum(r.required_units for r in rows) != self.generated.required_units or sum(r.scheduled_units for r in rows) != self.generated.scheduled_units:
                raise ValueError('Portion order and totals must describe the selected course')
        return self


class RegenerationComparison(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    selected_course_ids: list[int] = Field(alias="selectedCourseIds")
    current: CoverageFacts
    generated: CoverageFacts
    courses: list[CourseRegenerationComparison]
    replaces_all_selected_sessions: Literal[True] = Field(
        default=True, alias="replacesAllSelectedSessions"
    )
    may_replace_planner_edits: Literal[True] = Field(
        default=True, alias="mayReplacePlannerEdits"
    )

    @model_validator(mode='after')
    def complete_selected_scope(self):
        if self.selected_course_ids != sorted(set(self.selected_course_ids)) or [c.course_id for c in self.courses] != self.selected_course_ids:
            raise ValueError('Comparison must contain every selected course exactly once in order')
        for name in ('current', 'generated'):
            total = getattr(self, name)
            if total.required_units != sum(getattr(c, name).required_units for c in self.courses) or total.scheduled_units != sum(getattr(c, name).scheduled_units for c in self.courses):
                raise ValueError('Selection and course coverage must reconcile')
        return self


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
    lecturer_portions: list[LecturerPortionFacts] = Field(default_factory=list, alias='lecturerPortions')


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
    elapsed_milliseconds: int = Field(alias="elapsedMilliseconds", ge=0)
    optimal_for_prepared_snapshot: bool = Field(alias="optimalForPreparedSnapshot")


class OptimizationGenerationResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["direct_saved"] = "direct_saved"
    semester_id: int = Field(alias="semesterId")
    summary: OptimizationSummary
    outcomes: list[CourseOptimizationOutcome]
    proof: "CandidateProof | None" = None
    intensive_facts: IntensiveFacts | None = Field(default=None,alias='intensiveFacts')
    algorithm: Literal['standard', 'cohort', 'lecturer', 'standard_optimized'] = 'standard'
    strategy_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='strategyProfile')
    strategy_settings: dict = Field(default_factory=dict, alias='strategySettings')
    termination: Literal['standard_completed', 'standard_optimized_completed', 'heuristic_completed', 'repair_limit', 'deadline', 'cancelled', 'failed'] | None = None


class OptimizationDecisionRequiredResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    mode: Literal["decision_required"] = "decision_required"
    saved: Literal[False] = False
    candidate_fingerprint: str = Field(
        alias="candidateFingerprint", pattern=r"^[0-9a-f]{64}$"
    )
    prepared_evidence: OptimizationGenerationRequest = Field(alias="preparedEvidence")
    comparison: RegenerationComparison
    proof: "CandidateProof | None" = None
    has_saved_sessions: bool = Field(default=True, alias="hasSavedSessions")
    algorithm: Literal['standard', 'cohort', 'lecturer', 'standard_optimized'] = 'standard'
    strategy_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='strategyProfile')
    strategy_settings: dict = Field(default_factory=dict, alias='strategySettings')


class RequestFailureResponse(BaseModel):
    errors: list[OperationError]


class OptimizationOperationFailure(BaseModel):
    code: Literal[
        "OPTIMAL_RESULT_NOT_PROVEN",
        "OPTIMIZATION_MODEL_INVALID",
        "OPTIMIZATION_OPERATION_FAILED",
        "NO_VALID_ALTERNATIVE",
    ]
    message: str
    saved: Literal[False] = False


class OptimizationBudgetPolicy(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    active_algorithm: Literal['standard', 'cohort', 'lecturer', 'standard_optimized'] = Field(default='standard', alias='activeAlgorithm')
    strategy_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='strategyProfile')
    strategy_settings: dict = Field(default_factory=dict, alias='strategySettings')
    default_seconds: int = Field(alias="defaultSeconds", gt=0, strict=True)
    ceiling_seconds: int = Field(alias="ceilingSeconds", gt=0, strict=True)
    policy_fingerprint: str = Field(alias="policyFingerprint", pattern=r"^[0-9a-f]{64}$")

    @model_validator(mode="after")
    def consistent_budget(self):
        if self.default_seconds > self.ceiling_seconds:
            raise ValueError("Default exceeds the configured ceiling")
        return self


OBJECTIVE_KEYS = ('total_units', 'intensive_teaching_time', 'daily_variety', 'conflicts', 'schedule_shape', 'lecturer_changes',
    'room_changes', 'retained_drafts', 'canonical_temporal', 'canonical_resource')
HEURISTIC_OBJECTIVE_KEYS = ('total_units', 'intensive_teaching_time', 'daily_variety',
    'preferred_size_deviation', 'course_rhythm_penalty', 'owner_balance_penalty',
    'extra_cohort_day_rooms', 'course_room_changes')


OPTIMIZED_OBJECTIVE_KEYS = OBJECTIVE_KEYS[:4] + ('weekly_spread',) + OBJECTIVE_KEYS[4:]


def objective_keys(profile):
    return {'standard-v1': OBJECTIVE_KEYS, 'heuristic-v1': HEURISTIC_OBJECTIVE_KEYS,
        'standard-optimized-v1': OPTIMIZED_OBJECTIVE_KEYS}[profile]


class ObjectiveProof(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    objective_key: str = Field(alias='objectiveKey')
    direction: Literal['max','min']
    proof_status: Literal['proven','unfinished','not_attempted','conditional'] = Field(alias='proofStatus')
    value: int | float | None
    prepared_snapshot_token: str = Field(alias='preparedSnapshotToken', pattern=r'^[0-9a-f]{64}$')
    candidate_fingerprint: str = Field(alias='candidateFingerprint', pattern=r'^[0-9a-f]{64}$')
    condition: dict[str,int] | None = None


class CandidateProof(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra='forbid')
    objective_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='objectiveProfile')
    prepared_snapshot_token: str = Field(alias='preparedSnapshotToken', pattern=r'^[0-9a-f]{64}$')
    candidate_fingerprint: str = Field(alias='candidateFingerprint', pattern=r'^[0-9a-f]{64}$')
    selected_course_ids: list[int] = Field(alias='selectedCourseIds')
    required_units: int = Field(alias='requiredUnits',ge=0)
    scheduled_units: int = Field(alias='scheduledUnits',ge=0)
    coverage_proven: bool = Field(alias='coverageProven')
    preferences_proven: bool = Field(alias='preferencesProven')
    objectives: list[ObjectiveProof]
    unit_upper_bound: int | None = Field(alias='unitUpperBound',ge=0)
    additional_possible_units: int | None = Field(alias='additionalPossibleUnits',ge=0)
    gap_known: bool = Field(alias='gapKnown')

    @model_validator(mode='after')
    def matching_proof(self):
        keys = objective_keys(self.objective_profile)
        if tuple(o.objective_key for o in self.objectives) != keys:
            raise ValueError('Objective priorities must be complete and ordered')
        preceding_proven=True
        for index, item in enumerate(self.objectives):
            expected_direction = 'max' if item.objective_key in ('total_units','intensive_teaching_time','daily_variety','retained_drafts') else 'min'
            if item.direction != expected_direction:
                raise ValueError('Objective direction must match its priority')
            if item.prepared_snapshot_token != self.prepared_snapshot_token or item.candidate_fingerprint != self.candidate_fingerprint:
                raise ValueError('Objective evidence must describe this candidate and prepared problem')
            if item.proof_status == 'proven' and not preceding_proven:
                raise ValueError('Full-priority proof requires every preceding priority proven')
            if item.value is not None and not isfinite(item.value):
                raise ValueError('Objective values must be finite')
            if self.objective_profile == 'heuristic-v1' and index > 0 and item.proof_status in ('proven', 'conditional'):
                raise ValueError('Heuristics cannot prove preferences')
            if item.proof_status == 'conditional' and (not item.condition or not set(item.condition).issubset(keys[:index])):
                raise ValueError('Conditional proof must identify earlier fixed objectives')
            preceding_proven = preceding_proven and item.proof_status == 'proven'
        if self.coverage_proven != (self.objectives[0].proof_status == 'proven') or self.preferences_proven != preceding_proven:
            raise ValueError('Coverage and preference flags must match objective evidence')
        if self.objective_profile == 'heuristic-v1' and self.coverage_proven and self.scheduled_units != self.required_units:
            raise ValueError('Heuristic coverage proof requires complete demand equality')
        if self.objectives[0].value is not None and self.objectives[0].value != self.scheduled_units:
            raise ValueError('Coverage evidence must match scheduled units')
        if (not self.selected_course_ids or self.selected_course_ids != sorted(set(self.selected_course_ids))
                or self.scheduled_units > self.required_units):
            raise ValueError('Invalid selection or coverage totals')
        if self.gap_known != (self.unit_upper_bound is not None) or (self.additional_possible_units is None) != (self.unit_upper_bound is None):
            raise ValueError('Unknown bounds require unknown gaps')
        if self.unit_upper_bound is not None and (self.unit_upper_bound < self.scheduled_units or self.additional_possible_units != self.unit_upper_bound-self.scheduled_units):
            raise ValueError('Bound gap must describe this candidate')
        return self


class OptimizationOperationStart(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    operation_id: UUID4 = Field(alias="operationId")
    context_secret: str = Field(alias="contextSecret", pattern=r"^[0-9a-f]{64}$", repr=False)
    policy_fingerprint: str = Field(alias="policyFingerprint", pattern=r"^[0-9a-f]{64}$")
    preparation: OptimizationGenerationRequest

    @model_validator(mode="after")
    def distinct_selection(self):
        ids = [course.course_id for course in self.preparation.courses]
        if not 1 <= len(ids) <= 20 or len(ids) != len(set(ids)):
            raise ValueError("Select 1–20 distinct courses")
        return self


class OptimizationOperationDecision(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    context_secret: str = Field(alias="contextSecret", pattern=r"^[0-9a-f]{64}$", repr=False)
    candidate_fingerprint: str = Field(alias="candidateFingerprint", pattern=r"^[0-9a-f]{64}$")


class OptimizationOperationContinue(OptimizationOperationDecision):
    continuation_id: UUID4 = Field(alias="continuationId")


class OptimizationOperationCancel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    context_secret: str | None = Field(default=None, alias="contextSecret", pattern=r"^[0-9a-f]{64}$", repr=False)
    reason: Literal["cancel", "navigation", "dismiss", "retry", "context_lost"] = "cancel"


OperationPhase = Literal[
    "preparing", "optimizing", "checking", "ready_to_save", "awaiting_decision",
    "saving", "saved", "cancelled", "timeout_no_candidate", "failed", "stale", "interrupted",
]


class OptimizationOperationStatus(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")
    operation_id: UUID = Field(alias="operationId")
    semester_id: int = Field(alias="semesterId", ge=1)
    schedule_revision_id: int = Field(alias="scheduleRevisionId", ge=1)
    selected_course_ids: list[int] = Field(alias="selectedCourseIds", min_length=1, max_length=20)
    selection_count: int = Field(alias="selectionCount", ge=1, le=20)
    phase: OperationPhase
    budget_seconds: int = Field(alias="budgetSeconds", gt=0)
    elapsed_milliseconds: int = Field(alias="elapsedMilliseconds", ge=0)
    budget_exhausted: bool = Field(alias="budgetExhausted")
    current_objective_key: str | None = Field(default=None, alias="currentObjectiveKey")
    saved: bool = False
    can_accept: bool = Field(default=False, alias="canAccept")
    can_finalize: bool = Field(default=False, alias="canFinalize")
    review: OptimizationDecisionRequiredResult | None = None
    result: OptimizationGenerationResult | None = None
    errors: list[OperationError] = Field(default_factory=list)
    terminal_code: str | None = Field(default=None, alias="terminalCode")
    algorithm: Literal['standard', 'cohort', 'lecturer', 'standard_optimized'] = 'standard'
    strategy_profile: Literal['standard-v1', 'heuristic-v1', 'standard-optimized-v1'] = Field(default='standard-v1', alias='strategyProfile')
    strategy_settings: dict = Field(default_factory=dict, alias='strategySettings')
    termination: Literal['standard_completed', 'standard_optimized_completed', 'heuristic_completed', 'repair_limit', 'deadline', 'cancelled', 'failed'] | None = None

    @model_validator(mode="after")
    def consistent_state(self):
        if self.phase in ('preparing', 'optimizing', 'checking') and self.termination is not None:
            raise ValueError('Active search has no terminal cause')
        if self.strategy_profile != ({'standard': 'standard-v1', 'standard_optimized': 'standard-optimized-v1'}.get(self.algorithm, 'heuristic-v1')):
            raise ValueError('Algorithm and profile must match')
        if self.algorithm != 'standard' and (self.can_finalize or self.phase == 'ready_to_save'):
            raise ValueError('Heuristic results require explicit acceptance')
        if self.selection_count != len(self.selected_course_ids) or len(set(self.selected_course_ids)) != self.selection_count or any(i <= 0 for i in self.selected_course_ids):
            raise ValueError("Invalid selected course identity")
        if self.saved != (self.phase == "saved") or (self.result is not None) != self.saved:
            raise ValueError("Only a committed saved operation has a result")
        if self.can_accept and (self.phase != "awaiting_decision" or self.review is None):
            raise ValueError("Acceptance requires live reviewed candidate")
        if self.can_finalize and (self.phase != "ready_to_save" or self.review is None):
            raise ValueError("Finalization requires live checked candidate")
        if self.review is not None and self.phase not in ("awaiting_decision", "ready_to_save"):
            raise ValueError("Only live decision phases expose review")
        if self.review is not None and self.review.comparison.generated.scheduled_units <= 0:
            raise ValueError('A whole-zero selection has no usable review')
        return self
