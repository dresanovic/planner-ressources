from __future__ import annotations
from app.services.schedule_generation import window_applies, window_has_occurrence, format_clock

import hashlib
import json
from dataclasses import dataclass, replace, asdict
from collections import Counter
from datetime import date, datetime, timedelta
from time import monotonic

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Course,
    DraftSchedule,
    ExamSession,
    Lecturer,
    ResourceUnavailabilityPeriod,
    Room,
    ScheduleRevision,
    Semester,
)
from app.schemas.conflict_aware_generation import (
    ArrangementImprovement,
    BlockingReason,
    BlockingReasonCode,
    CourseRegenerationComparison,
    CourseOptimizationOutcome,
    CoverageFacts,
    OperationError,
    OptimizationDecisionRequiredResult,
    OptimizationGenerationRequest,
    OptimizationGenerationResult,
    OptimizationPreparationResponse,
    OptimizationStatus,
    OptimizationSummary,
    PreparedOptimizationCourse,
    PreparedOptimizationCourseInput,
    RegenerationComparison,
    ResolvedWarning,
    CandidateProof, ObjectiveProof, objective_keys,
)
from app.services.academic_catalog import planning_eligibility_reasons
from app.services.draft_schedule_repository import (
    GenerationConstraints,
    get_draft_schedule,
    list_draft_schedules_by_semester,
    load_course_plan,
    load_generation_constraints,
    load_semester_plan,
    load_time_windows,
    replace_draft_schedule,
)
from app.services.draft_schedule_validation import collect_validation_alerts
from app.services.schedule_generation import CoursePlan, SemesterPlan
from app.services.schedule_generation import session_duration_minutes
from app.services.exam_scheduling import institution_today
from app.services.holiday_calendar import HolidayReference, holiday_snapshot
from app.services.semester_optimization import (
    CourseOptimization,
    intensive_arrangement,
    CurrentSession,
    FixedSession,
    NoGeneratedAlternative,
    OptimalResultNotProven,
    OptimizationCourse,
    SemesterOptimizationResult,
    intervals_overlap,
    optimize_semester,
    valid_unit_upper_bound,
)
from app.services.schedule_lifecycle import claim_active_working_revision
from app.services.optimization_config import load_optimization_policy
from app.services.resource_rules import resource_is_unavailable


OPERATION_DEADLINE_SECONDS = 60.0
POST_SOLVE_RESERVE_SECONDS = 5.0


class SemesterNotFoundError(ValueError):
    pass


class InvalidOptimizationSelection(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StaleOptimizationCandidate(RuntimeError):
    pass


class CandidateNotReproducible(RuntimeError):
    pass


class InvalidExactCandidate(ValueError):
    pass


def validate_exact_candidate(courses, fixed_sessions, unavailable_dates, holidays, candidates, *, algorithm='standard'):
    """Check detached exact assignments independently of solver status, without writes."""
    expected = {course.course_id: course for course in courses}
    ids = [candidate.course_id for candidate in candidates]
    if len(ids) != len(set(ids)) or set(ids) != set(expected):
        raise InvalidExactCandidate("Candidate must represent every selected course exactly once")
    occupancy = list(fixed_sessions)
    unavailable = frozenset(unavailable_dates)
    for candidate in candidates:
        course = expected[candidate.course_id]
        total = sum(session.units for session in candidate.sessions)
        if total != candidate.scheduled_units or total > course.total_units or total < 0:
            raise InvalidExactCandidate("Invalid course unit total")
        dates = set()
        lecturers = {item.id: item for item in course.lecturers if item.active}
        rooms = {item.id: item for item in course.rooms if item.active and (item.capacity or 0) >= course.cohort_size}
        for session in candidate.sessions:
            if (not isinstance(session.units, int) or isinstance(session.units, bool)
                or not course.min_session_units <= session.units <= course.max_session_units):
                raise InvalidExactCandidate("Invalid session units")
            if (session.date in dates or session.date in unavailable or session.date in holidays
                or not course.planning_period.start_date <= session.date <= course.planning_period.end_date):
                raise InvalidExactCandidate("Invalid teaching date")
            dates.add(session.date)
            start = datetime.combine(session.date, session.start_time)
            end = datetime.combine(session.date, session.end_time)
            if end - start != timedelta(minutes=session_duration_minutes(session.units)):
                raise InvalidExactCandidate("Session duration does not match units and breaks")
            if course.latest_teaching_end is not None and end > course.latest_teaching_end:
                raise InvalidExactCandidate("Teaching extends beyond active same-course exam")
            if not any(
                window_applies(window, session.date)
                and window.start_time <= session.start_time < session.end_time <= window.end_time
                and window.id == session.time_window_id
                and window.constraint_window_index == session.constraint_window_index
                for window in course.windows
            ):
                raise InvalidExactCandidate("Session is outside its allowed teaching window")
            for resource, resource_id in ((lecturers, session.lecturer_id), (rooms, session.room_id)):
                item = resource.get(resource_id)
                if item is None or resource_is_unavailable(item.unavailable_periods, session.date, session.start_time, session.end_time):
                    raise InvalidExactCandidate("Ineligible, inactive, unavailable or insufficient resource")
            if not _exact_sessions_valid((session,), course.cohort_id, occupancy):
                raise InvalidExactCandidate("Candidate overlaps selected or protected occupancy")
            occupancy.append(FixedSession(course.course_id, course.cohort_id,
                session.lecturer_id, session.room_id, session.date, session.start_time, session.end_time))
        if algorithm == 'lecturer':
            from app.services.teaching_preferences import derive_portions
            portions = derive_portions(course, course.explicit_lecturer_portions)
            predecessor_complete = True
            predecessor_end = None
            for portion in portions:
                sessions = tuple(s for s in candidate.sessions if s.lecturer_id == portion.lecturer_id)
                units = sum(s.units for s in sessions)
                if units > portion.required_units:
                    raise InvalidExactCandidate('Lecturer portion was transferred or overallocated')
                if sessions and not predecessor_complete:
                    raise InvalidExactCandidate('Incomplete lecturer predecessor was bypassed')
                if sessions and predecessor_end is not None and min(datetime.combine(s.date, s.start_time) for s in sessions) < predecessor_end:
                    raise InvalidExactCandidate('Lecturer portions alternate or reverse authoritative code order')
                predecessor_complete = predecessor_complete and units == portion.required_units
                if sessions:
                    predecessor_end = max(datetime.combine(s.date, s.end_time) for s in sessions)


@dataclass(frozen=True)
class LoadedCourse:
    course: Course
    plan: CoursePlan
    constraints: GenerationConstraints
    draft: DraftSchedule | None
    optimization: OptimizationCourse
    input_snapshot_token: str


@dataclass(frozen=True)
class LoadedOperation:
    semester: SemesterPlan
    unavailable_dates: tuple[date, ...]
    holidays: dict[date, HolidayReference]
    semester_snapshot_token: str
    shared_snapshot_token: str
    courses: tuple[LoadedCourse, ...]
    fixed_sessions: tuple[FixedSession, ...]


def canonical_unavailable_dates(values) -> tuple[date, ...]:
    parsed = (date.fromisoformat(value) if isinstance(value, str) else value for value in values)
    return tuple(sorted(set(parsed)))


def prepare_optimization(
    db: Session,
    semester_id: int,
    course_ids: list[int],
    unavailable_dates,
    schedule_revision_id: int | None = None,
) -> OptimizationPreparationResponse:
    _validate_selection(course_ids)
    budget_policy = load_optimization_policy()
    loaded = load_operation(
        db, semester_id, course_ids, unavailable_dates, schedule_revision_id
    )
    mismatched = next(
        (item for item in loaded.courses if item.course.current_semester_id != semester_id),
        None,
    )
    if mismatched is not None:
        raise InvalidOptimizationSelection(
            "COURSE_SEMESTER_MISMATCH",
            f"Course {mismatched.course.id} is not assigned to the selected semester.",
        )
    for item in loaded.courses:
        unavailable = _unavailable_selection_error(db, item, semester_id)
        if unavailable is not None:
            raise unavailable
    prepared = []
    replacement_ids = []
    for item in loaded.courses:
        scheduled = sum(session.units for session in item.draft.sessions) if item.draft else 0
        replacement = item.draft is not None and bool(item.draft.sessions)
        if replacement:
            replacement_ids.append(item.course.id)
        window_unavailable = not _windows_host_minimum_session(item)
        prepared.append(PreparedOptimizationCourse(
            courseId=item.course.id,
            courseName=item.course.name,
            available=_course_available(db, item.course, semester_id) and not window_unavailable,
            unavailableReasons=(
                [BlockingReason(
                    code=BlockingReasonCode.STUDY_TYPE_WINDOW_UNAVAILABLE,
                    message="The current study type has no active teaching window long enough for the minimum session.",
                    relatedCount=1,
                )]
                if window_unavailable
                else []
            ),
            draftScheduleId=item.draft.id if item.draft else None,
            draftRevision=item.draft.revision if item.draft else None,
            scheduledUnits=scheduled,
            remainingUnits=max(item.course.total_units - scheduled, 0),
            replacementRequired=replacement,
            effectiveConstraints=_constraints_response(item.constraints),
            inputSnapshotToken=item.input_snapshot_token,
        ))
    return OptimizationPreparationResponse(
        semesterId=semester_id,
        scheduleRevisionId=schedule_revision_id,
        unavailableDates=list(loaded.unavailable_dates),
        sharedSnapshotToken=loaded.shared_snapshot_token,
        courses=prepared,
        replacementCourseIds=replacement_ids,
        budgetPolicy=budget_policy,
        algorithm=budget_policy.active_algorithm,
        strategyProfile=budget_policy.strategy_profile,
        strategySettings=dict(budget_policy.strategy_settings),
    )


def generate_optimization(
    db: Session,
    semester_id: int,
    prepared_courses: list[PreparedOptimizationCourseInput],
    unavailable_dates,
    shared_snapshot_token: str,
    schedule_revision_id: int | None = None,
) -> OptimizationGenerationResult | OptimizationDecisionRequiredResult:
    raise InvalidOptimizationSelection('OPERATION_API_REQUIRED', 'Bitte den aktuellen Optimierungslauf verwenden.')


def accept_optimization(
    db: Session,
    semester_id: int,
    prepared_courses: list[PreparedOptimizationCourseInput],
    unavailable_dates,
    shared_snapshot_token: str,
    schedule_revision_id: int,
    expected_candidate_fingerprint: str,
) -> OptimizationGenerationResult:
    raise InvalidOptimizationSelection('OPERATION_API_REQUIRED', 'Bitte den aktuellen Optimierungslauf verwenden.')




def load_operation(
    db: Session,
    semester_id: int,
    course_ids: list[int],
    unavailable_dates,
    schedule_revision_id: int | None = None,
) -> LoadedOperation:
    semester_record = db.get(Semester, semester_id)
    if semester_record is None:
        raise SemesterNotFoundError("Semester not found.")
    semester = load_semester_plan(db, semester_id)
    schedule_revision = (
        db.get(ScheduleRevision, schedule_revision_id)
        if schedule_revision_id is not None
        else None
    )
    lifecycle_payload = [
        schedule_revision_id,
        schedule_revision.state if schedule_revision is not None else None,
        schedule_revision.row_version if schedule_revision is not None else None,
    ]
    canonical_dates = canonical_unavailable_dates(unavailable_dates)
    holidays = holiday_snapshot(db, semester.start_date, semester.end_date)
    drafts = list_draft_schedules_by_semester(db, semester_id)
    selected_ids = set(course_ids)
    protected_teaching = tuple(
        FixedSession(
            course_id=draft.course_id,
            cohort_id=session.cohort_id,
            lecturer_id=session.lecturer_id,
            room_id=session.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            source_kind="teaching_session",
            source_id=session.id,
            units=session.units,
            study_type_id=db.get(Course,draft.course_id).study_type_id,
            marked_windows=tuple(load_time_windows(db,db.get(Course,draft.course_id).study_type_id)),
        )
        for draft in drafts if draft.course_id not in selected_ids
        for session in draft.sessions
    )
    active_exams = tuple(
        db.scalars(
            select(ExamSession)
            .where(
                ExamSession.semester_id == semester_id,
                ExamSession.exam_date >= institution_today(),
            )
            .order_by(ExamSession.exam_date, ExamSession.start_time, ExamSession.id)
        )
    )
    protected_exams = tuple(
        FixedSession(
            course_id=exam.course_id,
            cohort_id=exam.cohort_id,
            lecturer_id=exam.lecturer_id,
            room_id=exam.room_id,
            date=exam.exam_date,
            start_time=exam.start_time,
            end_time=exam.end_time,
            source_kind="active_exam",
            source_id=exam.id,
        )
        for exam in active_exams
    )
    fixed_sessions = protected_teaching + protected_exams
    loaded_courses: list[LoadedCourse] = []
    for course_id in sorted(course_ids):
        course = db.get(Course, course_id)
        if course is None:
            raise InvalidOptimizationSelection("COURSE_NOT_FOUND", f"Course {course_id} was not found.")
        plan = load_course_plan(db, course_id)
        constraints = load_generation_constraints(db, plan, semester)
        draft = next((item for item in drafts if item.course_id == course_id), None)
        current = tuple(
            CurrentSession(
                course_id=course_id,
                cohort_id=session.cohort_id,
                lecturer_id=session.lecturer_id,
                room_id=session.room_id,
                date=session.date,
                start_time=session.start_time,
                end_time=session.end_time,
                units=session.units,
                time_window_id=session.time_window_id,
                constraint_window_index=session.constraint_window_index,
            )
            for session in (draft.sessions if draft else [])
        )
        course_exams = [exam for exam in active_exams if exam.course_id == course_id]
        earliest_exam = min(
            course_exams,
            key=lambda exam: (exam.exam_date, exam.start_time, exam.id),
            default=None,
        )
        optimization = OptimizationCourse(
            course_id=course.id,
            course_name=course.name,
            total_units=course.total_units,
            min_session_units=course.min_session_units,
            max_session_units=course.max_session_units,
            preferred_session_units=course.preferred_session_units,
            cohort_id=course.cohort_id,
            cohort_size=plan.cohort_size,
            planning_period=constraints.planning_period,
            windows=tuple(constraints.allowed_windows),
            lecturers=tuple(plan.lecturer_candidates),
            rooms=tuple(plan.room_candidates),
            current_sessions=current,
            latest_teaching_end=(
                datetime.combine(earliest_exam.exam_date, earliest_exam.start_time)
                if earliest_exam is not None
                else None
            ),
            latest_teaching_source_id=earliest_exam.id if earliest_exam is not None else None,
        )
        relevant_fixed = [
            session for session in fixed_sessions
            if session.cohort_id == course.cohort_id
            or session.lecturer_id in {lecturer.id for lecturer in plan.lecturer_candidates}
            or session.room_id in {room.id for room in plan.room_candidates}
        ]
        token = _fingerprint({
            "scheduleRevision": lifecycle_payload,
            "course": _course_payload(course, plan, constraints),
            "draft": _draft_payload(draft),
            "occupancy": [_fixed_payload(item) for item in sorted(relevant_fixed, key=_fixed_sort_key)],
            "unavailableDates": [value.isoformat() for value in canonical_dates],
            "institutionHolidays": [
                [holiday_id, day.isoformat(), name, revision]
                for holiday_id, day, name, revision in holidays.entries
            ],
        })
        loaded_courses.append(LoadedCourse(course, plan, constraints, draft, optimization, token))
    semester_payload = [
        semester.id,
        semester.start_date.isoformat(),
        semester.end_date.isoformat(),
        semester_record.revision,
        semester_record.is_active,
    ]
    semester_token = _fingerprint(semester_payload)
    shared_token = _fingerprint({
        "scheduleRevision": lifecycle_payload,
        "semester": semester_payload,
        "unavailableDates": [value.isoformat() for value in canonical_dates],
        "institutionHolidays": [
            [holiday_id, day.isoformat(), name, revision]
            for holiday_id, day, name, revision in holidays.entries
        ],
        "courses": [[item.course.id, item.input_snapshot_token] for item in loaded_courses],
    })
    return LoadedOperation(
        semester,
        canonical_dates,
        holidays.by_date,
        semester_token,
        shared_token,
        tuple(loaded_courses),
        fixed_sessions,
    )


def _decision_required_result(
    db: Session,
    loaded: LoadedOperation,
    solution: SemesterOptimizationResult,
    prepared_courses: list[PreparedOptimizationCourseInput],
    shared_snapshot_token: str,
    schedule_revision_id: int,
    *, algorithm='standard', strategy_profile='standard-v1', strategy_settings=None, policy_fingerprint=None,
) -> OptimizationDecisionRequiredResult:
    actual = intensive_arrangement([c.optimization for c in loaded.courses],loaded.fixed_sessions,
                                  {c.course_id:c.sessions for c in solution.courses})
    if actual is not None and (solution.intensive_teaching_time,solution.daily_variety) != (actual[1],actual[2]):
        raise InvalidExactCandidate('Intensive objective facts do not match the actual arrangement')
    solved = {item.course_id: item for item in solution.courses}
    warning_counts = _current_warning_counts(db, loaded)
    course_comparisons: list[CourseRegenerationComparison] = []
    current_total = 0
    generated_total = 0
    required_total = 0
    for item in loaded.courses:
        course_solution = solved[item.course.id]
        required = item.course.total_units
        current_units = (
            sum(session.units for session in item.draft.sessions)
            if item.draft is not None
            else 0
        )
        generated_units = course_solution.scheduled_units
        required_total += required
        current_total += current_units
        generated_total += generated_units
        course_comparisons.append(
            CourseRegenerationComparison(
                courseId=item.course.id,
                courseName=item.course.name,
                current=_coverage(required, current_units),
                generated=_coverage(required, generated_units),
                resolvedCurrentWarnings=warning_counts.get(item.course.id, []),
                remainingReasons=[
                    BlockingReason(
                        code=BlockingReasonCode(reason.code),
                        message=reason.message,
                        relatedCount=reason.count,
                        holidayDate=reason.holiday_date,
                        holidayName=reason.holiday_name,
                        sourceKind=reason.source_kind,
                        sourceId=reason.source_id,
                    )
                    for reason in course_solution.evidence
                    if generated_units < required
                ],
                lecturerPortions=lecturer_portion_facts(item.optimization, course_solution.sessions) if algorithm == 'lecturer' else [],
            )
        )
    identity = {'algorithm': algorithm, 'profile': strategy_profile, 'settings': strategy_settings or {}, 'policy': policy_fingerprint}
    if algorithm == 'lecturer':
        from app.services.teaching_preferences import derive_portions
        identity['portions'] = {c.course.id: [asdict(p) for p in derive_portions(c.optimization, c.optimization.explicit_lecturer_portions)] for c in loaded.courses}
    fingerprint = _fingerprint({'assignments': candidate_fingerprint(solution, {item.course.id: item.course.cohort_id for item in loaded.courses}), 'strategy': identity})
    scope = _fingerprint({'shared': shared_snapshot_token,
        'courses': [item.model_dump(mode='json', by_alias=True) for item in sorted(prepared_courses, key=lambda c:c.course_id)], 'strategy': identity})
    objective_by_key = {item.objective_key: item for item in solution.objectives}
    objectives = [ObjectiveProof(objectiveKey=key, direction='max' if key in ('total_units','intensive_teaching_time','daily_variety','retained_drafts') else 'min',
        proofStatus=objective_by_key[key].proof_status if key in objective_by_key else 'not_attempted',
        value=objective_by_key[key].value if key in objective_by_key else None,
        candidateFingerprint=fingerprint, preparedSnapshotToken=scope,
        condition={earlier: objective_by_key[earlier].value for earlier in objective_keys(strategy_profile)[:index]}
            if key in objective_by_key and objective_by_key[key].proof_status == 'conditional' else None)
        for index, key in enumerate(objective_keys(strategy_profile))]
    coverage_proven = objectives[0].proof_status == 'proven'
    upper = generated_total if coverage_proven else valid_unit_upper_bound(generated_total, required_total, solution.unit_upper_bound)
    proof = CandidateProof(preparedSnapshotToken=scope, candidateFingerprint=fingerprint,
        objectiveProfile=strategy_profile,
        selectedCourseIds=[item.course.id for item in loaded.courses], requiredUnits=required_total, scheduledUnits=generated_total,
        coverageProven=coverage_proven, preferencesProven=all(o.proof_status == 'proven' for o in objectives),
        objectives=objectives, unitUpperBound=upper, additionalPossibleUnits=upper-generated_total if upper is not None else None,
        gapKnown=upper is not None)
    return OptimizationDecisionRequiredResult(
        algorithm=algorithm, strategyProfile=strategy_profile, strategySettings=strategy_settings or {},
        proof=proof,
        hasSavedSessions=any(item.draft and item.draft.sessions for item in loaded.courses),
        candidateFingerprint=fingerprint,
        preparedEvidence=OptimizationGenerationRequest(
            semesterId=loaded.semester.id,
            scheduleRevisionId=schedule_revision_id,
            unavailableDates=list(loaded.unavailable_dates),
            sharedSnapshotToken=shared_snapshot_token,
            courses=prepared_courses,
        ),
        comparison=RegenerationComparison(
            selectedCourseIds=[item.course.id for item in loaded.courses],
            current=_coverage(required_total, current_total, _arrangement_facts(loaded,
                {c.course.id:c.optimization.current_sessions for c in loaded.courses},scope,
                _fingerprint({'current':[_draft_payload(c.draft) for c in loaded.courses]}))),
            generated=_coverage(required_total, generated_total, _arrangement_facts(loaded,
                {c.course_id:c.sessions for c in solution.courses},scope,fingerprint)),
            courses=course_comparisons,
        ),
    )


def lecturer_portion_facts(course, sessions):
    from app.services.teaching_preferences import derive_portions
    rows = []
    predecessor_complete = True
    for portion in derive_portions(course, course.explicit_lecturer_portions):
        scheduled = sum(s.units for s in sessions if s.lecturer_id == portion.lecturer_id)
        remaining = portion.required_units - scheduled
        blocked = remaining and not predecessor_complete
        rows.append(dict(lecturerId=portion.lecturer_id, lecturerCode=portion.lecturer_code,
            sequenceIndex=portion.sequence_index, source=portion.source, requiredUnits=portion.required_units,
            scheduledUnits=scheduled, remainingUnits=remaining,
            reasonCode=('PREDECESSOR_INCOMPLETE' if blocked else 'SEARCH_UNCERTAIN') if remaining else None,
            reason=('Vorheriger Lehrpersonenanteil ist noch nicht vollständig geplant.' if blocked else
                    'Weitere zulässige Termine sind durch die begrenzte Suche nicht nachgewiesen.') if remaining else None))
        predecessor_complete = predecessor_complete and remaining == 0
    return rows


def _arrangement_facts(loaded, sessions, scope, fingerprint):
    facts = intensive_arrangement([c.optimization for c in loaded.courses],loaded.fixed_sessions,sessions)
    if facts is None:
        return None
    total,ticks,variety,rows = facts
    return dict(totalUnits=total,intensiveLe=dict(numerator=ticks,denominator=2700000000),
                dailyVariety=variety,cohortDates=rows,preparedSnapshotToken=scope,candidateFingerprint=fingerprint)


def _coverage(required_units: int, scheduled_units: int, intensive_facts=None) -> CoverageFacts:
    return CoverageFacts(
        intensiveFacts=intensive_facts,
        requiredUnits=required_units,
        scheduledUnits=scheduled_units,
        remainingUnits=max(required_units - scheduled_units, 0),
        status="complete" if scheduled_units >= required_units else "partial",
    )


def _current_warning_counts(
    db: Session,
    loaded: LoadedOperation,
) -> dict[int, list[ResolvedWarning]]:
    drafts = list_draft_schedules_by_semester(db, loaded.semester.id)
    if not drafts:
        return {}
    rooms_by_id = {item.id: item for item in db.scalars(select(Room))}
    lecturers_by_id = {item.id: item for item in db.scalars(select(Lecturer))}
    periods = db.scalars(
        select(ResourceUnavailabilityPeriod).options(
            selectinload(ResourceUnavailabilityPeriod.weekdays)
        )
    )
    unavailability_by_resource = {}
    for period in periods:
        key = (
            ("lecturer", period.lecturer_id)
            if period.lecturer_id is not None
            else ("room", period.room_id)
        )
        unavailability_by_resource.setdefault(key, []).append(period)
    constraints_by_course_id = {
        item.course.id: item.constraints for item in loaded.courses
    }
    study_windows_by_study_type_id = {
        draft.study_type_id_snapshot: load_time_windows(
            db, draft.study_type_id_snapshot
        )
        for draft in drafts
    }
    alerts = collect_validation_alerts(
        drafts,
        rooms_by_id=rooms_by_id,
        lecturers_by_id=lecturers_by_id,
        constraints_by_course_id=constraints_by_course_id,
        study_windows_by_study_type_id=study_windows_by_study_type_id,
        unavailability_by_resource=unavailability_by_resource,
        eligible_lecturer_ids_by_course={
            draft.course_id: {
                link.lecturer_id for link in draft.course.eligible_lecturers
            }
            for draft in drafts
        },
        eligible_room_ids_by_course={
            draft.course_id: {link.room_id for link in draft.course.eligible_rooms}
            for draft in drafts
        },
        active_lecturer_ids={
            item.id for item in lecturers_by_id.values() if item.is_active
        },
        active_room_ids={item.id for item in rooms_by_id.values() if item.is_active},
        current_cohort_sizes_by_course={
            draft.course_id: draft.course.cohort.student_count for draft in drafts
        },
        holidays_by_date=loaded.holidays,
    )
    selected_ids = {item.course.id for item in loaded.courses}
    counts: dict[int, Counter[str]] = {
        course_id: Counter() for course_id in selected_ids
    }
    for draft in drafts:
        if draft.course_id not in selected_ids:
            continue
        for session in draft.sessions:
            counts[draft.course_id].update(
                alert.code.value for alert in alerts.get(session.id, [])
            )
    return {
        course_id: [
            ResolvedWarning(code=code, count=count)
            for code, count in sorted(course_counts.items())
        ]
        for course_id, course_counts in counts.items()
    }


def _validate_selection(course_ids: list[int]) -> None:
    if not 1 <= len(course_ids) <= 20:
        raise InvalidOptimizationSelection("INVALID_OPTIMIZATION_SIZE", "Semester optimization requires 1-20 courses.")
    if len(set(course_ids)) != len(course_ids):
        raise InvalidOptimizationSelection("DUPLICATE_COURSE_SELECTION", "Select each course only once.")


def _course_available(db: Session, course: Course, semester_id: int) -> bool:
    solver_explainable_reasons = {
        "MISSING_ACTIVE_TIME_WINDOW",
        "NO_ACTIVE_ELIGIBLE_LECTURER",
        "NO_USABLE_ELIGIBLE_ROOM",
    }
    return not (
        set(planning_eligibility_reasons(db, course, semester_id))
        - solver_explainable_reasons
    )


def _unavailable_selection_error(
    db: Session,
    item: LoadedCourse,
    semester_id: int,
) -> InvalidOptimizationSelection | None:
    solver_explainable_reasons = {
        "MISSING_ACTIVE_TIME_WINDOW",
        "NO_ACTIVE_ELIGIBLE_LECTURER",
        "NO_USABLE_ELIGIBLE_ROOM",
    }
    hard_reasons = [
        reason
        for reason in planning_eligibility_reasons(db, item.course, semester_id)
        if reason not in solver_explainable_reasons
    ]
    if hard_reasons:
        reason = hard_reasons[0]
        return InvalidOptimizationSelection(
            reason,
            f"Course {item.course.id} is unavailable for automatic generation ({reason}).",
        )
    if not _windows_host_minimum_session(item):
        return InvalidOptimizationSelection(
            "STUDY_TYPE_WINDOW_UNAVAILABLE",
            f"Course {item.course.id}'s current study type has no active teaching window long enough for the minimum session.",
        )
    return None


def _windows_host_minimum_session(item: LoadedCourse) -> bool:
    required = timedelta(minutes=session_duration_minutes(item.course.min_session_units))
    return any(
        datetime.combine(date.min, window.end_time)
        - datetime.combine(date.min, window.start_time)
        >= required and window_has_occurrence(window, item.constraints.planning_period)
        for window in item.constraints.allowed_windows
    )


def _constraints_response(constraints: GenerationConstraints):
    from app.schemas.draft_schedule import (
        AllowedTeachingWindowResponse,
        GenerationConstraintsResponse,
        PlanningPeriodResponse,
        StudyTypeSummaryResponse,
    )

    return GenerationConstraintsResponse(
        courseId=constraints.course_id,
        semesterId=constraints.semester_id,
        isCustom=constraints.is_custom,
        revision=constraints.revision,
        planningPeriod=PlanningPeriodResponse(
            startDate=constraints.planning_period.start_date,
            endDate=constraints.planning_period.end_date,
        ),
        studyType=StudyTypeSummaryResponse(
            id=constraints.study_type_id,
            name=constraints.study_type_name,
        ),
        allowedTeachingWindows=[
            AllowedTeachingWindowResponse(
                weekday=window.weekday,
                kind=window.kind, date=window.date, is_intensive=window.is_intensive,
                startTime=format_clock(window.start_time),
                endTime=format_clock(window.end_time),
                sourceTimeWindowId=window.id,
            )
            for window in constraints.allowed_windows
        ],
    )


def _candidate_improvement(
    item: LoadedCourse,
    course_solution: CourseOptimization,
    operation: LoadedOperation,
) -> ArrangementImprovement | None:
    if course_solution.retained_current or course_solution.scheduled_units <= 0:
        return None
    baseline_units = sum(session.units for session in item.draft.sessions) if item.draft else 0
    if course_solution.scheduled_units < baseline_units:
        return None
    added_units = max(course_solution.scheduled_units - baseline_units, 0)
    old_lecturer_changes = _draft_changes(item.draft, "lecturer_id")
    old_room_changes = _draft_changes(item.draft, "room_id")
    comparison_occupancy = operation.fixed_sessions + tuple(
        FixedSession(
            course_id=other.course.id,
            cohort_id=session.cohort_id,
            lecturer_id=session.lecturer_id,
            room_id=session.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
        )
        for other in operation.courses
        if other.course.id != item.course.id and other.draft is not None
        for session in other.draft.sessions
    )
    baseline_conflicts = _draft_conflicts(item.draft, comparison_occupancy)
    reduced_lecturer = max(old_lecturer_changes - course_solution.lecturer_changes, 0)
    reduced_room = max(old_room_changes - course_solution.room_changes, 0)
    if item.draft is not None and added_units == 0:
        current_arrangement = (baseline_conflicts, old_lecturer_changes, old_room_changes)
        candidate_arrangement = (0, course_solution.lecturer_changes, course_solution.room_changes)
        if candidate_arrangement >= current_arrangement:
            return None
    return ArrangementImprovement(
        addedUnits=added_units,
        reducedConflicts=baseline_conflicts,
        reducedLecturerChanges=reduced_lecturer,
        reducedRoomChanges=reduced_room,
    )


def _save_plan(
    planned_ids: set[int],
    solved: dict[int, CourseOptimization],
    loaded_by_id: dict[int, LoadedCourse],
) -> tuple[list[set[int]], dict[int, set[int]]]:
    dependencies = {course_id: set() for course_id in planned_ids}
    ordered = sorted(planned_ids)
    for index, first_id in enumerate(ordered):
        for second_id in ordered[index + 1:]:
            first = loaded_by_id[first_id]
            second = loaded_by_id[second_id]
            first_depends_on_second = second.draft is not None and not _exact_sessions_valid(
                solved[first_id].sessions,
                first.course.cohort_id,
                _draft_as_fixed(second.draft),
            )
            second_depends_on_first = first.draft is not None and not _exact_sessions_valid(
                solved[second_id].sessions,
                second.course.cohort_id,
                _draft_as_fixed(first.draft),
            )
            if first_depends_on_second:
                dependencies[first_id].add(second_id)
            if second_depends_on_first:
                dependencies[second_id].add(first_id)

    components = _strongly_connected_components(dependencies)
    component_by_course = {
        course_id: component_id
        for component_id, component in enumerate(components)
        for course_id in component
    }
    component_dependencies = {component_id: set() for component_id in range(len(components))}
    for course_id, prerequisites in dependencies.items():
        component_id = component_by_course[course_id]
        component_dependencies[component_id].update(
            component_by_course[prerequisite]
            for prerequisite in prerequisites
            if component_by_course[prerequisite] != component_id
        )
    return components, component_dependencies


def _strongly_connected_components(graph: dict[int, set[int]]) -> list[set[int]]:
    next_index = 0
    indices: dict[int, int] = {}
    low_links: dict[int, int] = {}
    stack: list[int] = []
    on_stack: set[int] = set()
    components: list[set[int]] = []

    def visit(node: int) -> None:
        nonlocal next_index
        indices[node] = next_index
        low_links[node] = next_index
        next_index += 1
        stack.append(node)
        on_stack.add(node)
        for prerequisite in sorted(graph[node]):
            if prerequisite not in indices:
                visit(prerequisite)
                low_links[node] = min(low_links[node], low_links[prerequisite])
            elif prerequisite in on_stack:
                low_links[node] = min(low_links[node], indices[prerequisite])
        if low_links[node] != indices[node]:
            return
        component = set()
        while True:
            member = stack.pop()
            on_stack.remove(member)
            component.add(member)
            if member == node:
                break
        components.append(component)

    for node in sorted(graph):
        if node not in indices:
            visit(node)
    components.sort(key=min)
    return components


def _require_time_remaining(deadline: float, message: str) -> None:
    if monotonic() >= deadline:
        raise OptimalResultNotProven(message)


def _fingerprint(payload) -> str:
    serialized = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def candidate_fingerprint(
    solution: SemesterOptimizationResult,
    cohort_ids: dict[int, int],
) -> str:
    """Identify only the exact generated joint sessions shown to the planner."""
    payload = []
    for course in sorted(solution.courses, key=lambda item: item.course_id):
        cohort_id = cohort_ids[course.course_id]
        sessions = [
            [
                session.date.isoformat(),
                session.start_time.isoformat(),
                session.end_time.isoformat(),
                session.units,
                session.lecturer_id,
                session.room_id,
                cohort_id,
                session.time_window_id,
                session.constraint_window_index,
            ]
            for session in sorted(
                course.sessions,
                key=lambda item: (
                    item.date,
                    item.start_time,
                    item.end_time,
                    item.units,
                    item.lecturer_id or -1,
                    item.room_id or -1,
                    item.time_window_id or -1,
                    item.constraint_window_index,
                ),
            )
        ]
        payload.append([course.course_id, sessions])
    return _fingerprint(payload)


def _course_payload(course, plan, constraints):
    return {
        "id": course.id,
        "revision": course.revision,
        "active": course.is_active,
        "semester": course.current_semester_id,
        "units": [course.total_units, course.min_session_units, course.max_session_units, course.preferred_session_units],
        "cohort": [course.cohort_id, plan.cohort_size, course.cohort.is_active],
        "studyType": [course.study_type_id, course.study_type.is_active],
        "lecturers": [[item.id, item.normalized_code, item.active, _period_payload(item.unavailable_periods)] for item in plan.lecturer_candidates],
        "rooms": [[item.id, item.normalized_code, item.active, item.capacity, _period_payload(item.unavailable_periods)] for item in plan.room_candidates],
        "constraints": {
            "custom": constraints.is_custom,
            "revision": constraints.revision,
            "period": [constraints.planning_period.start_date.isoformat(), constraints.planning_period.end_date.isoformat()],
            "windows": [[item.id, item.kind, item.date.isoformat() if item.date else None, item.is_intensive, item.revision, item.weekday, item.start_time.isoformat(), item.end_time.isoformat(), item.sort_order] for item in constraints.allowed_windows],
        },
    }


def _period_payload(periods):
    return sorted([
        [item.id, item.revision, item.kind, item.start_date.isoformat() if item.start_date else None, item.end_date.isoformat() if item.end_date else None, item.start_time.isoformat(), item.end_time.isoformat(), sorted(day.weekday for day in item.weekdays)]
        for item in periods
    ])


def _draft_payload(draft):
    if draft is None:
        return None
    return {
        "id": draft.id,
        "revision": draft.revision,
        "sessions": [[item.id, item.date.isoformat(), item.start_time.isoformat(), item.end_time.isoformat(), item.units, item.lecturer_id, item.room_id, item.cohort_id] for item in draft.sessions],
    }


def _fixed_payload(item):
    return [item.source_kind, item.source_id, item.course_id, item.cohort_id, item.lecturer_id, item.room_id, item.date.isoformat(), item.start_time.isoformat(), item.end_time.isoformat(),item.units,item.study_type_id,
        [[w.id,w.kind,w.weekday,w.date.isoformat() if w.date else None,w.start_time.isoformat(),w.end_time.isoformat(),w.is_intensive,w.revision] for w in item.marked_windows]]


def _fixed_sort_key(item):
    return (item.date, item.start_time, item.end_time, item.source_kind, item.source_id or 0, item.course_id, item.lecturer_id, item.room_id)


def _draft_changes(draft, attribute):
    if draft is None:
        return 0
    sessions = sorted(draft.sessions, key=lambda item: (item.date, item.start_time))
    return sum(getattr(one, attribute) != getattr(two, attribute) for one, two in zip(sessions, sessions[1:]))


def _draft_conflicts(draft, fixed_sessions):
    if draft is None:
        return 0
    conflicts = 0
    for session in draft.sessions:
        for fixed in fixed_sessions:
            if not intervals_overlap(session.date, session.start_time, session.end_time, fixed.date, fixed.start_time, fixed.end_time):
                continue
            conflicts += int(session.lecturer_id == fixed.lecturer_id)
            conflicts += int(session.room_id == fixed.room_id)
            conflicts += int(session.cohort_id == fixed.cohort_id)
    return conflicts


def _draft_as_fixed(draft):
    return [
        FixedSession(
            course_id=draft.course_id,
            cohort_id=session.cohort_id,
            lecturer_id=session.lecturer_id,
            room_id=session.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            source_kind="teaching_session",
            source_id=session.id,
            units=session.units,
        )
        for session in draft.sessions
    ]


def _exact_sessions_valid(sessions, cohort_id, occupancy):
    for session in sessions:
        for fixed in occupancy:
            if not intervals_overlap(session.date, session.start_time, session.end_time, fixed.date, fixed.start_time, fixed.end_time):
                continue
            if cohort_id == fixed.cohort_id or session.lecturer_id == fixed.lecturer_id or session.room_id == fixed.room_id:
                return False
    return True


def _stale_outcome(item):
    scheduled = sum(session.units for session in item.draft.sessions) if item.draft else 0
    return CourseOptimizationOutcome(
        courseId=item.course.id,
        courseName=item.course.name,
        status=OptimizationStatus.STALE,
        draftScheduleId=item.draft.id if item.draft else None,
        draftRevision=item.draft.revision if item.draft else None,
        scheduledUnits=scheduled,
        remainingUnits=max(item.course.total_units - scheduled, 0),
        saved=False,
        improvement=None,
        reasons=[BlockingReason(code=BlockingReasonCode.STALE_PLANNING_INPUT, message="Planning inputs changed after preparation. Refresh and confirm again.", relatedCount=1)],
        errors=[],
    )


def _failed_outcome(item, code, message):
    scheduled = sum(session.units for session in item.draft.sessions) if item.draft else 0
    return CourseOptimizationOutcome(
        courseId=item.course.id,
        courseName=item.course.name,
        status=OptimizationStatus.FAILED,
        draftScheduleId=item.draft.id if item.draft else None,
        draftRevision=item.draft.revision if item.draft else None,
        scheduledUnits=scheduled,
        remainingUnits=max(item.course.total_units - scheduled, 0),
        saved=False,
        improvement=None,
        reasons=[],
        errors=[OperationError(code=code, message=message)],
    )


def _empty_solution():
    return SemesterOptimizationResult((), 0, 0, 0, 0, 0, 0)
