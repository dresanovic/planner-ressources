from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, replace
from datetime import date
from time import monotonic

from sqlalchemy import update
from sqlalchemy.orm import Session

from app.models.planning import Course, DraftSchedule, Semester
from app.schemas.conflict_aware_generation import (
    ArrangementImprovement,
    BlockingReason,
    BlockingReasonCode,
    CourseOptimizationOutcome,
    OperationError,
    OptimizationGenerationResult,
    OptimizationPreparationResponse,
    OptimizationStatus,
    OptimizationSummary,
    PreparedOptimizationCourse,
    PreparedOptimizationCourseInput,
)
from app.services.academic_catalog import planning_eligibility_reasons
from app.services.draft_schedule_repository import (
    GenerationConstraints,
    get_draft_schedule,
    list_draft_schedules_by_semester,
    load_course_plan,
    load_generation_constraints,
    load_semester_plan,
    replace_draft_schedule,
    save_generation_constraints,
)
from app.services.schedule_generation import CoursePlan, SemesterPlan
from app.services.holiday_calendar import HolidayReference, holiday_snapshot
from app.services.semester_optimization import (
    CourseOptimization,
    CurrentSession,
    FixedSession,
    OptimalResultNotProven,
    OptimizationCourse,
    SemesterOptimizationResult,
    intervals_overlap,
    optimize_semester,
)
from app.services.schedule_lifecycle import claim_active_working_revision


OPERATION_DEADLINE_SECONDS = 60.0
POST_SOLVE_RESERVE_SECONDS = 5.0


class SemesterNotFoundError(ValueError):
    pass


class InvalidOptimizationSelection(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


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
    prepared = []
    replacement_ids = []
    for item in loaded.courses:
        scheduled = sum(session.units for session in item.draft.sessions) if item.draft else 0
        replacement = item.draft is not None
        if replacement:
            replacement_ids.append(item.course.id)
        prepared.append(PreparedOptimizationCourse(
            courseId=item.course.id,
            courseName=item.course.name,
            available=_course_available(db, item.course, semester_id),
            draftScheduleId=item.draft.id if item.draft else None,
            draftRevision=item.draft.revision if item.draft else None,
            scheduledUnits=scheduled,
            remainingUnits=max(item.course.total_units - scheduled, 0),
            replacementRequired=replacement,
            inputSnapshotToken=item.input_snapshot_token,
        ))
    return OptimizationPreparationResponse(
        semesterId=semester_id,
        scheduleRevisionId=schedule_revision_id,
        unavailableDates=list(loaded.unavailable_dates),
        sharedSnapshotToken=loaded.shared_snapshot_token,
        courses=prepared,
        replacementCourseIds=replacement_ids,
    )


def generate_optimization(
    db: Session,
    semester_id: int,
    prepared_courses: list[PreparedOptimizationCourseInput],
    unavailable_dates,
    shared_snapshot_token: str,
    schedule_revision_id: int | None = None,
) -> OptimizationGenerationResult:
    started = monotonic()
    deadline = started + OPERATION_DEADLINE_SECONDS
    course_ids = [item.course_id for item in prepared_courses]
    _validate_selection(course_ids)
    loaded = load_operation(
        db, semester_id, course_ids, unavailable_dates, schedule_revision_id
    )
    supplied = {item.course_id: item for item in prepared_courses}
    stale_ids: set[int] = set()
    for item in loaded.courses:
        expected = supplied[item.course.id]
        current_id = item.draft.id if item.draft else None
        current_revision = item.draft.revision if item.draft else None
        if (
            expected.input_snapshot_token != item.input_snapshot_token
            or expected.expected_draft_schedule_id != current_id
            or expected.expected_draft_revision != current_revision
        ):
            stale_ids.add(item.course.id)
    # A changed preparation cannot be reconstructed from opaque fingerprints.
    # Require a fresh operation rather than silently optimizing refreshed input.
    if stale_ids or shared_snapshot_token != loaded.shared_snapshot_token:
        stale_ids.update(course_ids)

    availability = {
        item.course.id: _course_available(db, item.course, semester_id)
        for item in loaded.courses
    }
    eligible = [
        item for item in loaded.courses
        if item.course.id not in stale_ids and availability[item.course.id]
    ]
    unavailable_ids = {
        item.course.id for item in loaded.courses
        if item.course.id not in stale_ids and not availability[item.course.id]
    }
    solve_occupancy = list(loaded.fixed_sessions)
    for item in loaded.courses:
        if item.course.id in unavailable_ids and item.draft is not None:
            solve_occupancy.extend(_draft_as_fixed(item.draft))
    solution = _empty_solution()
    optimal_for_prepared_snapshot = False
    if eligible:
        remaining_seconds = deadline - monotonic() - POST_SOLVE_RESERVE_SECONDS
        if remaining_seconds <= 0:
            raise OptimalResultNotProven("The optimization deadline elapsed before solving could begin.")
        solution = optimize_semester(
            [item.optimization for item in eligible],
            solve_occupancy,
            loaded.unavailable_dates,
            holidays=loaded.holidays,
            deadline_seconds=remaining_seconds,
        )
        optimal_for_prepared_snapshot = True
    solved = {item.course_id: item for item in solution.courses}

    if eligible:
        _require_time_remaining(deadline, "The optimization deadline elapsed before final input validation.")
        # Establish the physical write transaction before the final reload. This
        # both closes SQLite's validation-to-write race and keeps later SAVEPOINTs
        # under the operation-level rollback boundary.
        if schedule_revision_id is None:
            db.execute(update(Semester).where(Semester.id == semester_id).values(id=Semester.id))
        else:
            claim_active_working_revision(
                db, semester_id, schedule_revision_id
            )
    # The final result must always describe current persisted state. This also
    # covers stale or unavailable selections for which no solver run occurs.
    db.expire_all()
    refreshed = load_operation(
        db, semester_id, course_ids, unavailable_dates, schedule_revision_id
    )
    refreshed_by_id = {item.course.id: item for item in refreshed.courses}
    original_by_id = {item.course.id: item for item in loaded.courses}
    if refreshed.semester_snapshot_token != loaded.semester_snapshot_token:
        stale_ids.update(course_ids)
    for course_id in course_ids:
        if refreshed_by_id[course_id].input_snapshot_token != original_by_id[course_id].input_snapshot_token:
            stale_ids.add(course_id)
    unavailable_ids.difference_update(stale_ids)

    improvements: dict[int, ArrangementImprovement] = {}
    planned_save_ids: set[int] = set()
    for course_id, course_solution in solved.items():
        if course_id in stale_ids or course_id in unavailable_ids:
            continue
        improvement = _candidate_improvement(original_by_id[course_id], course_solution, loaded)
        if improvement is not None:
            improvements[course_id] = improvement
            planned_save_ids.add(course_id)

    preserved_occupancy = list(refreshed.fixed_sessions)
    preserved_ids = stale_ids | unavailable_ids | (set(solved) - planned_save_ids)
    for course_id in preserved_ids:
        item = refreshed_by_id[course_id]
        if item.draft is not None:
            preserved_occupancy.extend(_draft_as_fixed(item.draft))

    # A newly preserved draft can invalidate another exact result. Repeat until
    # every remaining candidate is valid against the complete preserved state.
    while True:
        newly_stale = set()
        for course_id in sorted(planned_save_ids - stale_ids):
            item = refreshed_by_id[course_id]
            if not _exact_sessions_valid(solved[course_id].sessions, item.course.cohort_id, preserved_occupancy):
                newly_stale.add(course_id)
        if not newly_stale:
            break
        stale_ids.update(newly_stale)
        for course_id in newly_stale:
            item = refreshed_by_id[course_id]
            if item.draft is not None:
                preserved_occupancy.extend(_draft_as_fixed(item.draft))
    planned_save_ids.difference_update(stale_ids)

    saved_ids: set[int] = set()
    save_errors: dict[int, tuple[str, str]] = {}
    components, component_dependencies = _save_plan(planned_save_ids, solved, refreshed_by_id)
    pending_components = set(range(len(components)))
    failed_components: set[int] = set()
    while pending_components:
        ready = sorted(
            (
                component_id for component_id in pending_components
                if not (component_dependencies[component_id] & pending_components)
            ),
            key=lambda component_id: min(components[component_id]),
        )
        if not ready:
            raise RuntimeError("The condensed save-dependency graph must be acyclic.")
        for component_id in ready:
            component = components[component_id]
            if component_dependencies[component_id] & failed_components:
                failed_components.add(component_id)
                for course_id in component:
                    save_errors[course_id] = (
                        "DEPENDENT_RESULT_INVALIDATED",
                        "This exact result depended on a course whose previous draft was preserved after a save failure.",
                    )
                pending_components.remove(component_id)
                continue
            _require_time_remaining(deadline, "The optimization deadline elapsed before all result groups could be saved.")
            try:
                with db.begin_nested():
                    for course_id in sorted(component):
                        item = refreshed_by_id[course_id]
                        replace_draft_schedule(
                            db,
                            item.plan,
                            semester_id,
                            list(solved[course_id].sessions),
                            existing_draft=item.draft,
                            reload=False,
                        )
                        if not item.constraints.is_custom:
                            save_generation_constraints(
                                db,
                                item.plan,
                                refreshed.semester,
                                item.constraints.planning_period,
                                item.constraints.allowed_windows,
                                existing_set=None,
                                reload=False,
                            )
                    db.flush()
            except Exception:
                failed_components.add(component_id)
                for course_id in component:
                    save_errors[course_id] = (
                        "COURSE_SAVE_FAILED",
                        "This atomic result group could not be saved; its previous drafts and constraints were preserved.",
                    )
                db.expire_all()
            else:
                saved_ids.update(component)
            pending_components.remove(component_id)

    outcomes: list[CourseOptimizationOutcome] = []
    for item in loaded.courses:
        if item.course.id in stale_ids:
            current_item = replace(refreshed_by_id[item.course.id], draft=get_draft_schedule(db, item.course.id, semester_id))
            outcomes.append(_stale_outcome(current_item))
            continue
        if item.course.id in unavailable_ids:
            current_item = replace(refreshed_by_id[item.course.id], draft=get_draft_schedule(db, item.course.id, semester_id))
            outcomes.append(_failed_outcome(current_item, "INVALID_PLANNING_INPUT", "The course is not available for planning in this semester."))
            continue
        if item.course.id in save_errors:
            current_item = replace(refreshed_by_id[item.course.id], draft=get_draft_schedule(db, item.course.id, semester_id))
            code, message = save_errors[item.course.id]
            outcomes.append(_failed_outcome(
                current_item,
                code,
                message,
            ))
            continue
        course_solution = solved[item.course.id]
        baseline_units = sum(session.units for session in item.draft.sessions) if item.draft else 0
        saved = item.course.id in saved_ids
        final_draft = get_draft_schedule(db, item.course.id, semester_id) if saved else item.draft
        status = (
            OptimizationStatus.COMPLETE
            if saved and course_solution.scheduled_units >= item.course.total_units
            else OptimizationStatus.IMPROVED_PARTIAL
            if saved
            else OptimizationStatus.UNCHANGED
        )
        improvement = improvements.get(item.course.id) if saved else None
        scheduled = sum(session.units for session in final_draft.sessions) if saved and final_draft is not None else baseline_units
        outcomes.append(CourseOptimizationOutcome(
            courseId=item.course.id,
            courseName=item.course.name,
            status=status,
            draftScheduleId=final_draft.id if final_draft else None,
            draftRevision=final_draft.revision if final_draft else None,
            scheduledUnits=scheduled,
            remainingUnits=max(item.course.total_units - scheduled, 0),
            saved=saved,
            improvement=improvement,
            reasons=[
                BlockingReason(
                    code=BlockingReasonCode(reason.code),
                    message=reason.message,
                    relatedCount=reason.count,
                    holidayDate=reason.holiday_date,
                    holidayName=reason.holiday_name,
                )
                for reason in course_solution.evidence
                if scheduled < item.course.total_units
            ],
            errors=[],
        ))

    outcomes.sort(key=lambda outcome: outcome.course_id)
    counts = {status: sum(outcome.status == status for outcome in outcomes) for status in OptimizationStatus}
    elapsed_seconds = monotonic() - started
    if started + elapsed_seconds > deadline:
        raise OptimalResultNotProven("The optimization operation exceeded its 60-second deadline before completion.")
    elapsed = int(elapsed_seconds * 1000)
    return OptimizationGenerationResult(
        semesterId=semester_id,
        summary=OptimizationSummary(
            total=len(outcomes),
            complete=counts[OptimizationStatus.COMPLETE],
            improvedPartial=counts[OptimizationStatus.IMPROVED_PARTIAL],
            unchanged=counts[OptimizationStatus.UNCHANGED],
            failed=counts[OptimizationStatus.FAILED],
            stale=counts[OptimizationStatus.STALE],
            scheduledUnits=sum(item.scheduled_units for item in outcomes),
            remainingUnits=sum(item.remaining_units for item in outcomes),
            elapsedMilliseconds=elapsed,
            optimalForPreparedSnapshot=optimal_for_prepared_snapshot,
        ),
        outcomes=outcomes,
    )


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
    canonical_dates = canonical_unavailable_dates(unavailable_dates)
    holidays = holiday_snapshot(db, semester.start_date, semester.end_date)
    drafts = list_draft_schedules_by_semester(db, semester_id)
    selected_ids = set(course_ids)
    fixed_sessions = tuple(
        FixedSession(
            course_id=draft.course_id,
            cohort_id=session.cohort_id,
            lecturer_id=session.lecturer_id,
            room_id=session.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
        )
        for draft in drafts if draft.course_id not in selected_ids
        for session in draft.sessions
    )
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
        optimization = OptimizationCourse(
            course_id=course.id,
            course_name=course.name,
            total_units=course.total_units,
            min_session_units=course.min_session_units,
            max_session_units=course.max_session_units,
            cohort_id=course.cohort_id,
            cohort_size=plan.cohort_size,
            planning_period=constraints.planning_period,
            windows=tuple(constraints.allowed_windows),
            lecturers=tuple(plan.lecturer_candidates),
            rooms=tuple(plan.room_candidates),
            current_sessions=current,
        )
        relevant_fixed = [
            session for session in fixed_sessions
            if session.cohort_id == course.cohort_id
            or session.lecturer_id in {lecturer.id for lecturer in plan.lecturer_candidates}
            or session.room_id in {room.id for room in plan.room_candidates}
        ]
        token = _fingerprint({
            "scheduleRevisionId": schedule_revision_id,
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
        "scheduleRevisionId": schedule_revision_id,
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


def _course_payload(course, plan, constraints):
    return {
        "id": course.id,
        "revision": course.revision,
        "active": course.is_active,
        "semester": course.current_semester_id,
        "units": [course.total_units, course.min_session_units, course.max_session_units],
        "cohort": [course.cohort_id, plan.cohort_size, course.cohort.is_active],
        "studyType": [course.study_type_id, course.study_type.is_active],
        "lecturers": [[item.id, item.normalized_code, item.active, _period_payload(item.unavailable_periods)] for item in plan.lecturer_candidates],
        "rooms": [[item.id, item.normalized_code, item.active, item.capacity, _period_payload(item.unavailable_periods)] for item in plan.room_candidates],
        "constraints": {
            "custom": constraints.is_custom,
            "revision": constraints.revision,
            "period": [constraints.planning_period.start_date.isoformat(), constraints.planning_period.end_date.isoformat()],
            "windows": [[item.id, item.weekday, item.start_time.isoformat(), item.end_time.isoformat(), item.sort_order] for item in constraints.allowed_windows],
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
    return [item.course_id, item.cohort_id, item.lecturer_id, item.room_id, item.date.isoformat(), item.start_time.isoformat(), item.end_time.isoformat()]


def _fixed_sort_key(item):
    return (item.date, item.start_time, item.end_time, item.course_id, item.lecturer_id, item.room_id)


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
