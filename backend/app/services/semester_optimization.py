from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass, field, replace
from datetime import date, datetime, time, timedelta
from time import monotonic
from typing import Iterable, Sequence

from ortools.sat.python import cp_model

from app.services.resource_rules import resource_is_unavailable
from app.services.schedule_generation import (
    GeneratedSession,
    PlanningPeriodPlan,
    ResourceCandidatePlan,
    TimeWindowPlan,
    session_duration_minutes,
)


REASON_MESSAGES = {
    "LECTURER_OCCUPIED": "Eligible lecturers are occupied by fixed semester sessions.",
    "ROOM_OCCUPIED": "Eligible rooms are occupied by fixed semester sessions.",
    "COHORT_OCCUPIED": "The cohort is occupied by fixed semester sessions.",
    "LECTURER_UNAVAILABLE": "Eligible lecturers are unavailable in otherwise allowed slots.",
    "ROOM_UNAVAILABLE": "Eligible rooms are unavailable in otherwise allowed slots.",
    "NO_ELIGIBLE_LECTURER": "The course has no active eligible lecturer.",
    "NO_ELIGIBLE_ROOM": "The course has no active eligible room.",
    "INSUFFICIENT_ROOM_CAPACITY": "No eligible active room has sufficient cohort capacity.",
    "UNAVAILABLE_DATE": "Planner-supplied unavailable dates removed otherwise allowed dates.",
    "NO_ALLOWED_DATE_OR_WINDOW": "No date and allowed teaching window can host a session.",
    "COURSE_CONSTRAINT": "The course planning constraints prevent additional placement.",
    "SELECTED_COURSE_COMPETITION": "Other selected courses use the same limited semester capacity.",
    "INVALID_PLANNING_INPUT": "The course planning input is invalid or incomplete.",
}


class OptimalResultNotProven(RuntimeError):
    pass


class OptimizationModelInvalid(RuntimeError):
    pass


@dataclass(frozen=True)
class FixedSession:
    course_id: int
    cohort_id: int
    lecturer_id: int
    room_id: int
    date: date
    start_time: time
    end_time: time


@dataclass(frozen=True)
class CurrentSession(FixedSession):
    units: int
    time_window_id: int | None = None
    constraint_window_index: int = 0


@dataclass(frozen=True)
class OptimizationCourse:
    course_id: int
    course_name: str | None
    total_units: int
    min_session_units: int
    max_session_units: int
    cohort_id: int
    cohort_size: int
    planning_period: PlanningPeriodPlan
    windows: tuple[TimeWindowPlan, ...]
    lecturers: tuple[ResourceCandidatePlan, ...]
    rooms: tuple[ResourceCandidatePlan, ...]
    current_sessions: tuple[CurrentSession, ...] = ()


@dataclass(frozen=True)
class TemporalCandidate:
    candidate_id: int
    course_id: int
    cohort_id: int
    date: date
    start_time: time
    end_time: time
    units: int
    time_window_id: int | None
    constraint_window_index: int
    lecturer_ids: tuple[int, ...]
    room_ids: tuple[int, ...]
    canonical_rank: int


@dataclass(frozen=True)
class BlockingEvidence:
    code: str
    count: int
    message: str


@dataclass(frozen=True)
class CandidateSet:
    candidates: tuple[TemporalCandidate, ...]
    evidence: tuple[BlockingEvidence, ...]


@dataclass(frozen=True)
class CourseOptimization:
    course_id: int
    sessions: tuple[GeneratedSession, ...]
    retained_current: bool
    scheduled_units: int
    lecturer_changes: int
    room_changes: int
    evidence: tuple[BlockingEvidence, ...]


@dataclass(frozen=True)
class SemesterOptimizationResult:
    courses: tuple[CourseOptimization, ...]
    total_units: int
    conflicts: int
    lecturer_changes: int
    room_changes: int
    retained_drafts: int
    elapsed_milliseconds: int
    optimal: bool = True


@dataclass
class _CourseVariables:
    course: OptimizationCourse
    candidate_set: CandidateSet
    temporal: dict[int, cp_model.IntVar] = field(default_factory=dict)
    lecturer: dict[tuple[int, int], cp_model.IntVar] = field(default_factory=dict)
    room: dict[tuple[int, int], cp_model.IntVar] = field(default_factory=dict)
    retain: cp_model.IntVar | None = None
    lecturer_changes: list[cp_model.IntVar] = field(default_factory=list)
    room_changes: list[cp_model.IntVar] = field(default_factory=list)


def canonical_minute(value: date, at: time) -> int:
    return value.toordinal() * 1440 + at.hour * 60 + at.minute


def intervals_overlap(
    first_date: date,
    first_start: time,
    first_end: time,
    second_date: date,
    second_start: time,
    second_end: time,
) -> bool:
    return first_date == second_date and first_start < second_end and second_start < first_end


def generate_candidates(
    course: OptimizationCourse,
    fixed_sessions: Sequence[FixedSession],
    unavailable_dates: frozenset[date],
) -> CandidateSet:
    counts: Counter[str] = Counter()
    candidates: list[TemporalCandidate] = []
    active_lecturers = tuple(sorted((item for item in course.lecturers if item.active), key=lambda item: (item.normalized_code, item.id)))
    active_rooms = tuple(sorted((item for item in course.rooms if item.active), key=lambda item: (item.normalized_code, item.id)))
    capacity_rooms = tuple(item for item in active_rooms if (item.capacity or 0) >= course.cohort_size)

    if not active_lecturers:
        counts["NO_ELIGIBLE_LECTURER"] += 1
    if not active_rooms:
        counts["NO_ELIGIBLE_ROOM"] += 1
    elif not capacity_rooms:
        counts["INSUFFICIENT_ROOM_CAPACITY"] += 1
    if course.min_session_units <= 0 or course.max_session_units < course.min_session_units:
        counts["INVALID_PLANNING_INPUT"] += 1
    if course.planning_period.start_date > course.planning_period.end_date or not course.windows:
        counts["NO_ALLOWED_DATE_OR_WINDOW"] += 1

    if counts.get("INVALID_PLANNING_INPUT") or not active_lecturers or not capacity_rooms:
        return CandidateSet((), _evidence(counts))

    ordered_windows = sorted(
        course.windows,
        key=lambda item: (item.weekday, item.start_time, item.end_time, item.sort_order, item.id or 0),
    )
    cursor = course.planning_period.start_date
    raw: list[tuple] = []
    permitted_temporal_slot_found = False
    while cursor <= course.planning_period.end_date:
        matching = [window for window in ordered_windows if window.weekday == cursor.weekday()]
        if cursor in unavailable_dates:
            if matching:
                counts["UNAVAILABLE_DATE"] += 1
            cursor += timedelta(days=1)
            continue
        for window in matching:
            for units in range(course.min_session_units, course.max_session_units + 1):
                end_dt = datetime.combine(cursor, window.start_time) + timedelta(minutes=session_duration_minutes(units))
                end_time = end_dt.time()
                if end_dt.date() != cursor or end_time > window.end_time:
                    counts["COURSE_CONSTRAINT"] += 1
                    continue
                permitted_temporal_slot_found = True
                cohort_blocked = any(
                    fixed.cohort_id == course.cohort_id
                    and intervals_overlap(cursor, window.start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
                    for fixed in fixed_sessions
                )
                if cohort_blocked:
                    counts["COHORT_OCCUPIED"] += 1
                lecturers = []
                for lecturer in active_lecturers:
                    if resource_is_unavailable(lecturer.unavailable_periods, cursor, window.start_time, end_time):
                        counts["LECTURER_UNAVAILABLE"] += 1
                        continue
                    if any(
                        fixed.lecturer_id == lecturer.id
                        and intervals_overlap(cursor, window.start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
                        for fixed in fixed_sessions
                    ):
                        counts["LECTURER_OCCUPIED"] += 1
                        continue
                    lecturers.append(lecturer.id)
                rooms = []
                for room in capacity_rooms:
                    if resource_is_unavailable(room.unavailable_periods, cursor, window.start_time, end_time):
                        counts["ROOM_UNAVAILABLE"] += 1
                        continue
                    if any(
                        fixed.room_id == room.id
                        and intervals_overlap(cursor, window.start_time, end_time, fixed.date, fixed.start_time, fixed.end_time)
                        for fixed in fixed_sessions
                    ):
                        counts["ROOM_OCCUPIED"] += 1
                        continue
                    rooms.append(room.id)
                if not cohort_blocked and lecturers and rooms:
                    raw.append((cursor, window.start_time, end_time, units, window, tuple(lecturers), tuple(rooms)))
        cursor += timedelta(days=1)

    if not raw and not permitted_temporal_slot_found:
        counts["NO_ALLOWED_DATE_OR_WINDOW"] += 1
    for rank, item in enumerate(sorted(raw, key=lambda value: (value[0], value[1], value[3], value[4].sort_order, value[5], value[6]))):
        session_date, start, end, units, window, lecturers, rooms = item
        candidates.append(TemporalCandidate(
            candidate_id=rank,
            course_id=course.course_id,
            cohort_id=course.cohort_id,
            date=session_date,
            start_time=start,
            end_time=end,
            units=units,
            time_window_id=window.id,
            constraint_window_index=window.constraint_window_index,
            lecturer_ids=lecturers,
            room_ids=rooms,
            canonical_rank=rank + 1,
        ))
    return CandidateSet(tuple(candidates), _evidence(counts))


def _evidence(counts: Counter[str]) -> tuple[BlockingEvidence, ...]:
    return tuple(
        BlockingEvidence(code, count, REASON_MESSAGES[code])
        for code, count in sorted(counts.items())
        if count > 0 and code in REASON_MESSAGES
    )


def optimize_semester(
    courses: Sequence[OptimizationCourse],
    fixed_sessions: Sequence[FixedSession],
    unavailable_dates: Iterable[date] = (),
    *,
    deadline_seconds: float = 60.0,
) -> SemesterOptimizationResult:
    started = monotonic()
    unavailable = frozenset(unavailable_dates)
    model = cp_model.CpModel()
    course_vars: dict[int, _CourseVariables] = {}
    all_temporal: list[tuple[TemporalCandidate, cp_model.IntVar]] = []
    lecturer_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)
    room_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)

    for course in sorted(courses, key=lambda item: item.course_id):
        candidate_set = generate_candidates(course, fixed_sessions, unavailable)
        variables = _CourseVariables(course=course, candidate_set=candidate_set)
        course_vars[course.course_id] = variables
        by_date: dict[date, list[cp_model.IntVar]] = defaultdict(list)
        for candidate in candidate_set.candidates:
            selected = model.new_bool_var(f"course_{course.course_id}_candidate_{candidate.candidate_id}")
            variables.temporal[candidate.candidate_id] = selected
            all_temporal.append((candidate, selected))
            by_date[candidate.date].append(selected)
            lecturer_vars = []
            for lecturer_id in candidate.lecturer_ids:
                assigned = model.new_bool_var(f"candidate_{course.course_id}_{candidate.candidate_id}_lecturer_{lecturer_id}")
                variables.lecturer[(candidate.candidate_id, lecturer_id)] = assigned
                lecturer_assignments[lecturer_id].append((candidate, assigned))
                lecturer_vars.append(assigned)
            room_vars = []
            for room_id in candidate.room_ids:
                assigned = model.new_bool_var(f"candidate_{course.course_id}_{candidate.candidate_id}_room_{room_id}")
                variables.room[(candidate.candidate_id, room_id)] = assigned
                room_assignments[room_id].append((candidate, assigned))
                room_vars.append(assigned)
            model.add(sum(lecturer_vars) == selected)
            model.add(sum(room_vars) == selected)
        for date_vars in by_date.values():
            model.add(sum(date_vars) <= 1)

        generated_units = sum(
            candidate.units * variables.temporal[candidate.candidate_id]
            for candidate in candidate_set.candidates
        )
        model.add(generated_units <= course.total_units)
        if course.current_sessions:
            retain = model.new_bool_var(f"course_{course.course_id}_retain_current")
            variables.retain = retain
            if variables.temporal:
                model.add(sum(variables.temporal.values()) <= len(variables.temporal) * (1 - retain))
            current_units = sum(session.units for session in course.current_sessions)
            if current_units > course.total_units:
                model.add(retain == 1)
            else:
                model.add(generated_units >= current_units * (1 - retain))
        _add_continuity(model, variables, lecturer=True)
        _add_continuity(model, variables, lecturer=False)

    _add_selected_conflict_constraints(model, all_temporal, lecturer_assignments, room_assignments)
    conflict_terms = _add_retained_alternatives(model, course_vars, fixed_sessions)

    total_units_terms = []
    lecturer_change_terms = []
    room_change_terms = []
    retain_terms = []
    canonical_temporal_terms = []
    canonical_resource_terms = []
    for variables in course_vars.values():
        for candidate in variables.candidate_set.candidates:
            selected = variables.temporal[candidate.candidate_id]
            total_units_terms.append(candidate.units * selected)
            canonical_temporal_terms.append(
                (len(variables.candidate_set.candidates) - candidate.canonical_rank + 1) * selected
            )
            canonical_resource_terms.extend(
                (rank + 1) * variables.lecturer[(candidate.candidate_id, lecturer_id)]
                for rank, lecturer_id in enumerate(candidate.lecturer_ids)
            )
            canonical_resource_terms.extend(
                (rank + 1) * variables.room[(candidate.candidate_id, room_id)]
                for rank, room_id in enumerate(candidate.room_ids)
            )
        lecturer_change_terms.extend(variables.lecturer_changes)
        room_change_terms.extend(variables.room_changes)
        if variables.retain is not None:
            current_units = sum(session.units for session in variables.course.current_sessions)
            total_units_terms.append(current_units * variables.retain)
            lecturer_change_terms.append(_count_current_changes(variables.course.current_sessions, "lecturer_id") * variables.retain)
            room_change_terms.append(_count_current_changes(variables.course.current_sessions, "room_id") * variables.retain)
            retain_terms.append(variables.retain)

    objectives = [
        ("max", sum(total_units_terms)),
        ("min", sum(conflict_terms)),
        ("min", sum(lecturer_change_terms)),
        ("min", sum(room_change_terms)),
        ("max", sum(retain_terms)),
        ("max", sum(canonical_temporal_terms)),
        ("min", sum(canonical_resource_terms)),
    ]
    solver: cp_model.CpSolver | None = None
    tracked_vars = [var for variables in course_vars.values() for var in (
        list(variables.temporal.values()) + list(variables.lecturer.values()) + list(variables.room.values()) + ([variables.retain] if variables.retain is not None else [])
    )]
    objective_values: list[int] = []
    for direction, expression in objectives:
        elapsed = monotonic() - started
        remaining = deadline_seconds - elapsed
        if remaining <= 0:
            raise OptimalResultNotProven("The optimization deadline elapsed before every comparison stage was proven optimal.")
        model.clear_objective()
        if direction == "max":
            model.maximize(expression)
        else:
            model.minimize(expression)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = remaining
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0
        solver.parameters.cp_model_presolve = True
        status = solver.solve(model)
        if status == cp_model.MODEL_INVALID:
            raise OptimizationModelInvalid("The semester optimization model is invalid.")
        if status != cp_model.OPTIMAL:
            raise OptimalResultNotProven("A fully optimal semester result was not proven within the operation deadline.")
        value = int(round(solver.objective_value))
        objective_values.append(value)
        model.add(expression == value)
        model.clear_hints()
        for variable in tracked_vars:
            model.add_hint(variable, solver.value(variable))

    assert solver is not None
    results: list[CourseOptimization] = []
    for course_id, variables in sorted(course_vars.items()):
        retained = variables.retain is not None and bool(solver.value(variables.retain))
        sessions: list[GeneratedSession] = []
        if retained:
            sessions = [
                GeneratedSession(
                    date=item.date,
                    start_time=item.start_time,
                    end_time=item.end_time,
                    units=item.units,
                    time_window_id=item.time_window_id,
                    constraint_window_index=item.constraint_window_index,
                    lecturer_id=item.lecturer_id,
                    room_id=item.room_id,
                )
                for item in sorted(variables.course.current_sessions, key=lambda session: (session.date, session.start_time, session.lecturer_id, session.room_id))
            ]
        else:
            for candidate in variables.candidate_set.candidates:
                if not solver.value(variables.temporal[candidate.candidate_id]):
                    continue
                lecturer_id = next(item for item in candidate.lecturer_ids if solver.value(variables.lecturer[(candidate.candidate_id, item)]))
                room_id = next(item for item in candidate.room_ids if solver.value(variables.room[(candidate.candidate_id, item)]))
                sessions.append(GeneratedSession(
                    date=candidate.date,
                    start_time=candidate.start_time,
                    end_time=candidate.end_time,
                    units=candidate.units,
                    time_window_id=candidate.time_window_id,
                    constraint_window_index=candidate.constraint_window_index,
                    lecturer_id=lecturer_id,
                    room_id=room_id,
                ))
        sessions.sort(key=lambda item: (item.date, item.start_time, item.lecturer_id or 0, item.room_id or 0))
        evidence = list(variables.candidate_set.evidence)
        scheduled = sum(item.units for item in sessions)
        results.append(CourseOptimization(
            course_id=course_id,
            sessions=tuple(sessions),
            retained_current=retained,
            scheduled_units=scheduled,
            lecturer_changes=_count_generated_changes(sessions, "lecturer_id"),
            room_changes=_count_generated_changes(sessions, "room_id"),
            evidence=tuple(_deduplicate_evidence(evidence)),
        ))
    result_by_course = {item.course_id: item for item in results}
    for index, course_result in enumerate(results):
        variables = course_vars[course_result.course_id]
        if course_result.scheduled_units >= variables.course.total_units:
            continue
        evidence = list(course_result.evidence)
        competing = any(
            candidate.course_id == course_result.course_id
            and any(
                other_id != course_result.course_id
                and any(
                    intervals_overlap(candidate.date, candidate.start_time, candidate.end_time, session.date, session.start_time, session.end_time)
                    and (
                        candidate.cohort_id == course_vars[other_id].course.cohort_id
                        or session.lecturer_id in candidate.lecturer_ids
                        or session.room_id in candidate.room_ids
                    )
                    for session in other_result.sessions
                )
                for other_id, other_result in result_by_course.items()
            )
            for candidate in variables.candidate_set.candidates
        )
        if competing:
            evidence.append(BlockingEvidence(
                "SELECTED_COURSE_COMPETITION",
                1,
                REASON_MESSAGES["SELECTED_COURSE_COMPETITION"],
            ))
        if not evidence:
            evidence.append(BlockingEvidence(
                "COURSE_CONSTRAINT",
                1,
                REASON_MESSAGES["COURSE_CONSTRAINT"],
            ))
        results[index] = replace(
            course_result,
            evidence=tuple(_deduplicate_evidence(evidence)),
        )
    return SemesterOptimizationResult(
        courses=tuple(results),
        total_units=objective_values[0],
        conflicts=objective_values[1],
        lecturer_changes=objective_values[2],
        room_changes=objective_values[3],
        retained_drafts=objective_values[4],
        elapsed_milliseconds=min(int((monotonic() - started) * 1000), 60000),
    )


def _add_selected_conflict_constraints(model, all_temporal, lecturer_assignments, room_assignments):
    for index, (first, first_var) in enumerate(all_temporal):
        for second, second_var in all_temporal[index + 1:]:
            if first.course_id == second.course_id or not intervals_overlap(first.date, first.start_time, first.end_time, second.date, second.start_time, second.end_time):
                continue
            if first.cohort_id == second.cohort_id:
                model.add(first_var + second_var <= 1)
    for assignments in (lecturer_assignments, room_assignments):
        for items in assignments.values():
            for index, (first, first_var) in enumerate(items):
                for second, second_var in items[index + 1:]:
                    if first.course_id != second.course_id and intervals_overlap(first.date, first.start_time, first.end_time, second.date, second.start_time, second.end_time):
                        model.add(first_var + second_var <= 1)


def _add_retained_alternatives(model, course_vars, fixed_sessions):
    conflict_terms = []
    retained = [item for item in course_vars.values() if item.retain is not None]
    for variables in retained:
        assert variables.retain is not None
        fixed_conflicts = 0
        for current in variables.course.current_sessions:
            for fixed in fixed_sessions:
                if not intervals_overlap(current.date, current.start_time, current.end_time, fixed.date, fixed.start_time, fixed.end_time):
                    continue
                fixed_conflicts += int(current.lecturer_id == fixed.lecturer_id)
                fixed_conflicts += int(current.room_id == fixed.room_id)
                fixed_conflicts += int(current.cohort_id == fixed.cohort_id)
        if fixed_conflicts:
            conflict_terms.append(fixed_conflicts * variables.retain)
        for other in course_vars.values():
            if other.course.course_id == variables.course.course_id:
                continue
            for current in variables.course.current_sessions:
                for candidate in other.candidate_set.candidates:
                    if not intervals_overlap(current.date, current.start_time, current.end_time, candidate.date, candidate.start_time, candidate.end_time):
                        continue
                    if current.cohort_id == candidate.cohort_id:
                        model.add(variables.retain + other.temporal[candidate.candidate_id] <= 1)
                    for lecturer_id in candidate.lecturer_ids:
                        if current.lecturer_id == lecturer_id:
                            model.add(variables.retain + other.lecturer[(candidate.candidate_id, lecturer_id)] <= 1)
                    for room_id in candidate.room_ids:
                        if current.room_id == room_id:
                            model.add(variables.retain + other.room[(candidate.candidate_id, room_id)] <= 1)
    for index, first in enumerate(retained):
        for second in retained[index + 1:]:
            pair_count = 0
            for one in first.course.current_sessions:
                for two in second.course.current_sessions:
                    if intervals_overlap(one.date, one.start_time, one.end_time, two.date, two.start_time, two.end_time):
                        pair_count += int(one.lecturer_id == two.lecturer_id)
                        pair_count += int(one.room_id == two.room_id)
                        pair_count += int(one.cohort_id == two.cohort_id)
            if pair_count:
                pair = model.new_bool_var(f"retain_conflict_{first.course.course_id}_{second.course.course_id}")
                model.add(pair <= first.retain)
                model.add(pair <= second.retain)
                model.add(pair >= first.retain + second.retain - 1)
                conflict_terms.append(pair_count * pair)
    return conflict_terms


def _add_continuity(model, variables: _CourseVariables, *, lecturer: bool):
    candidates = variables.candidate_set.candidates
    if not candidates:
        return
    resource_ids = sorted({resource_id for candidate in candidates for resource_id in (candidate.lecturer_ids if lecturer else candidate.room_ids)})
    resource_index = {resource_id: index + 1 for index, resource_id in enumerate(resource_ids)}
    by_date: dict[date, list[TemporalCandidate]] = defaultdict(list)
    for candidate in candidates:
        by_date[candidate.date].append(candidate)
    previous_seen = None
    previous_value = None
    changes = variables.lecturer_changes if lecturer else variables.room_changes
    assignments = variables.lecturer if lecturer else variables.room
    for date_index, (session_date, date_candidates) in enumerate(sorted(by_date.items())):
        has_session = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_has_{date_index}")
        temporal_vars = [variables.temporal[item.candidate_id] for item in date_candidates]
        model.add(has_session == sum(temporal_vars))
        current_value = model.new_int_var(0, len(resource_ids), f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_value_{date_index}")
        resource_terms = []
        for candidate in date_candidates:
            for resource_id in (candidate.lecturer_ids if lecturer else candidate.room_ids):
                resource_terms.append(resource_index[resource_id] * assignments[(candidate.candidate_id, resource_id)])
        model.add(current_value == sum(resource_terms))
        seen = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_seen_{date_index}")
        last_value = model.new_int_var(0, len(resource_ids), f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_last_{date_index}")
        if previous_seen is None:
            model.add(seen == has_session)
            model.add(last_value == current_value)
        else:
            model.add(seen >= previous_seen)
            model.add(seen >= has_session)
            model.add(seen <= previous_seen + has_session)
            model.add(last_value == current_value).only_enforce_if(has_session)
            model.add(last_value == previous_value).only_enforce_if(has_session.Not())
            change = model.new_bool_var(f"course_{variables.course.course_id}_{'lecturer' if lecturer else 'room'}_change_{date_index}")
            model.add(change <= has_session)
            model.add(change <= previous_seen)
            model.add(current_value != previous_value).only_enforce_if([has_session, previous_seen, change])
            model.add(current_value == previous_value).only_enforce_if([has_session, previous_seen, change.Not()])
            changes.append(change)
        previous_seen = seen
        previous_value = last_value


def _count_current_changes(sessions: Sequence[CurrentSession], field_name: str) -> int:
    ordered = sorted(sessions, key=lambda item: (item.date, item.start_time))
    return sum(getattr(first, field_name) != getattr(second, field_name) for first, second in zip(ordered, ordered[1:]))


def _count_generated_changes(sessions: Sequence[GeneratedSession], field_name: str) -> int:
    ordered = sorted(sessions, key=lambda item: (item.date, item.start_time))
    return sum(getattr(first, field_name) != getattr(second, field_name) for first, second in zip(ordered, ordered[1:]))


def _deduplicate_evidence(items: Sequence[BlockingEvidence]) -> list[BlockingEvidence]:
    combined: dict[str, BlockingEvidence] = {}
    for item in items:
        existing = combined.get(item.code)
        combined[item.code] = BlockingEvidence(item.code, item.count + (existing.count if existing else 0), item.message)
    return [combined[code] for code in sorted(combined)]
