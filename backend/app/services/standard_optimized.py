"""Standard-derived extension. Original search stays in semester_optimization.py.

Only model/search orchestration is copied; legality, candidates, continuity,
resource constraints and result types are shared with Standard.
"""
from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import replace
from datetime import date
from threading import Event, Thread
from time import monotonic
from typing import Iterable, Mapping, Sequence

from ortools.sat.python import cp_model
from app.services.holiday_calendar import HolidayReference
from app.services.semester_optimization import (
    OptimizationCourse, FixedSession, OptimizationSearchControl, SemesterOptimizationResult,
    TemporalCandidate, GeneratedSession, CourseOptimization, BlockingEvidence, ObjectiveEvidence,
    REASON_MESSAGES, NoGeneratedAlternative, OptimalResultNotProven, OptimizationCancelled,
    OptimizationModelInvalid, _CourseVariables, _candidate_start_times, generate_candidates,
    week_start, _current_sessions_respect_hard_constraints, _add_continuity,
    _add_selected_conflict_constraints, _add_retained_alternatives, weekly_concentration_cost,
    _count_current_changes, _cohort_day_room_penalties, _intensive_objectives,
    _count_generated_changes, _deduplicate_evidence, intervals_overlap, valid_unit_upper_bound,
    _construct_completion, intensive_arrangement, _time_ticks, CandidateSet,
)
from app.services.schedule_generation import intensive_instruction_ticks

STAGE_WEIGHTS = (35, 5, 5, 0, 40, 5, 2, 2, 2, 2, 2)


def stage_budget_seconds(remaining: float, stage: int) -> float:
    return remaining * STAGE_WEIGHTS[stage] / sum(STAGE_WEIGHTS[stage:])


def _weekly_spread(model, course_vars, control):
    """Cumulative LE deviation from even distribution over feasible teaching weeks.

    Empty/blocked weeks are excluded, and no date becomes a hard requirement.
    Generated demand remains the expression's scale, so partial candidates can
    also be distributed without pretending all requested teaching was placed.
    """
    penalties = []
    for course_id, variables in course_vars.items():
        control.check()
        by_week = defaultdict(list)
        for candidate in variables.candidate_set.candidates:
            control.check()
            by_week[week_start(candidate.date)].append(candidate.units * variables.temporal[candidate.candidate_id])
        current_units = sum(s.units for s in variables.course.current_sessions)
        if variables.retain is not None:
            for session in variables.course.current_sessions:
                by_week[week_start(session.date)].append(session.units * variables.retain)
        weeks = sorted(by_week)
        if len(weeks) < 2:
            continue
        total = sum(term for terms in by_week.values() for term in terms)
        bound = max(variables.course.total_units, current_units)
        cumulative = 0
        for index, week in enumerate(weeks[:-1], start=1):
            control.check()
            previous = cumulative
            cumulative = model.new_int_var(0, bound, f'spread_{course_id}_{index}_cumulative')
            model.add(cumulative == previous + sum(by_week[week]))
            deviation = model.new_int_var(0, bound * len(weeks), f'spread_{course_id}_{index}_deviation')
            model.add_abs_equality(deviation, len(weeks) * cumulative - index * total)
            penalties.append(deviation)
    return sum(penalties)


def optimize_semester(
    courses: Sequence[OptimizationCourse],
    fixed_sessions: Sequence[FixedSession],
    unavailable_dates: Iterable[date] = (),
    *,
    holidays: Mapping[date, HolidayReference] | None = None,
    deadline_seconds: float = 60.0,
    generated_only: bool = False,
    control: OptimizationSearchControl | None = None,
    allow_unproven: bool = False,
    incumbent: SemesterOptimizationResult | None = None,
) -> SemesterOptimizationResult:
    started = monotonic()
    control = control or OptimizationSearchControl(deadline=started + deadline_seconds)
    control.check()
    unavailable = frozenset(unavailable_dates)
    holidays = holidays or {}
    starts_by_date = {}
    def start_times_for_date(day):
        if day not in starts_by_date:
            starts_by_date[day] = _candidate_start_times(courses, fixed_sessions, day, control)
        return starts_by_date[day]
    candidate_sets = {}
    for course in sorted(courses, key=lambda item: item.course_id):
        control.check()
        candidate_sets[course.course_id] = generate_candidates(course, fixed_sessions,
            unavailable, holidays, control=control, start_times_for_date=start_times_for_date)
    # A solver hint is not an application incumbent. Preserve and publish the
    # independently checked construction before creating the expensive model.
    if incumbent is None and generated_only:
        incumbent = _starting_candidate(courses, fixed_sessions, candidate_sets, control,
            unavailable=unavailable, holidays=holidays, started=started)
        if incumbent is not None:
            if control.cancelled():
                raise OptimizationCancelled('Optimization cancelled')
            incumbent = replace(incumbent,
                elapsed_milliseconds=max(0, int((monotonic()-started)*1000)))
            if control.checkpoint is not None:
                control.checkpoint(incumbent)
    try:
        control.check()
        result = _optimize_model(courses, fixed_sessions, unavailable, holidays,
            generated_only, control, allow_unproven, incumbent, candidate_sets, started)
    except OptimalResultNotProven:
        if control.cancelled():
            raise OptimizationCancelled('Optimization cancelled')
        if not allow_unproven or incumbent is None:
            raise
        exhausted = control.clock() >= control.deadline
        result = replace(incumbent, optimal=False, search_exhausted=exhausted,
            termination='deadline' if exhausted else 'standard_optimized_completed')
    if control.cancelled():
        raise OptimizationCancelled('Optimization cancelled')
    return replace(result, elapsed_milliseconds=max(0, int((monotonic()-started)*1000)))


def _spread_dates(course, dates):
    """Visit intensive dates first, then interleave dates across feasible weeks."""
    by_week = defaultdict(list)
    intensive = set()
    for day, candidates in dates:
        by_week[week_start(day)].append(day)
        if any(intensive_instruction_ticks(c.date, c.start_time, c.end_time,
                c.units, course.windows) for c in candidates):
            intensive.add(day)
    weeks = sorted(by_week)
    bits = max(1, (len(weeks)-1).bit_length())
    ranks = {week:int(f'{index:0{bits}b}'[::-1], 2) for index,week in enumerate(weeks)}
    positions = {day:index for days in by_week.values() for index,day in enumerate(sorted(days))}
    return sorted(dates, key=lambda item: (item[0] not in intensive,
        positions[item[0]], ranks[week_start(item[0])], item[0]))


def _saved_selection(courses, candidate_sets, control, sessions=None):
    selected = {}
    for course in courses:
        control.check()
        by_signature = {(c.date,c.start_time,c.end_time,c.units,c.time_window_id,
            c.constraint_window_index):c for c in candidate_sets[course.course_id].candidates}
        seen = set()
        for session in course.current_sessions if sessions is None else sessions[course.course_id]:
            signature = (session.date,session.start_time,session.end_time,session.units,
                session.time_window_id,session.constraint_window_index)
            candidate = by_signature.get(signature)
            if (candidate is None or signature in seen
                    or session.lecturer_id not in candidate.lecturer_ids
                    or session.room_id not in candidate.room_ids):
                return None
            seen.add(signature)
            selected[course.course_id,candidate.candidate_id] = (session.lecturer_id,session.room_id)
    return selected


def _spread_selection(courses, candidate_sets, selected, control):
    """Relocate ordinary sessions without changing coverage or intensive presence."""
    selected = dict(selected)
    candidates = {(c.course_id,c.candidate_id):c for cs in candidate_sets.values() for c in cs.candidates}
    for course in courses:
        control.check()
        weeks = sorted({week_start(c.date) for c in candidate_sets[course.course_id].candidates})
        loads = Counter()
        keys = [key for key in selected if key[0] == course.course_id]
        for key in keys:
            c = candidates[key]
            loads[week_start(c.date)] += c.units
        total = sum(loads.values())
        def cost(values):
            cumulative = score = 0
            for index, week in enumerate(weeks[:-1],start=1):
                cumulative += values[week]
                score += abs(len(weeks)*cumulative-index*total)
            return score
        for key in keys:
            control.check()
            old = candidates[key]
            if intensive_instruction_ticks(old.date,old.start_time,old.end_time,old.units,course.windows):
                continue
            old_lecturer, old_room = selected.pop(key)
            occupied = defaultdict(list)
            used_dates = set()
            for other_key,(lecturer,room) in selected.items():
                c = candidates[other_key]
                if c.course_id == course.course_id:
                    used_dates.add(c.date)
                for kind,resource in (('cohort',c.cohort_id),('lecturer',lecturer),('room',room)):
                    occupied[kind,resource,c.date].append((c.start_time,c.end_time))
            def free(kind,resource,c):
                return all(c.end_time <= start or end <= c.start_time
                    for start,end in occupied[kind,resource,c.date])
            current_cost = cost(loads)
            move_costs = {}
            for week in weeks:
                updated = loads.copy()
                updated[week_start(old.date)] -= old.units
                updated[week] += old.units
                move_costs[week] = cost(updated)
            best = None
            best_key = None
            for candidate in candidate_sets[course.course_id].candidates:
                control.check()
                score = move_costs[week_start(candidate.date)]
                if (candidate.units != old.units or score >= current_cost
                        or candidate.date in used_dates
                        or intensive_instruction_ticks(candidate.date,candidate.start_time,
                            candidate.end_time,candidate.units,course.windows)
                        or not free('cohort',candidate.cohort_id,candidate)):
                    continue
                lecturer = next((r for r in sorted(candidate.lecturer_ids,key=lambda r:r != old_lecturer)
                    if free('lecturer',r,candidate)),None)
                room = next((r for r in sorted(candidate.room_ids,key=lambda r:r != old_room)
                    if free('room',r,candidate)),None)
                if lecturer is None or room is None:
                    continue
                rank = (score,lecturer != old_lecturer,room != old_room,candidate.canonical_rank,lecturer,room)
                if best_key is None or rank < best_key:
                    best_key, best = rank, (candidate,lecturer,room)
            if best is None:
                selected[key] = old_lecturer,old_room
            else:
                candidate,lecturer,room = best
                selected[course.course_id,candidate.candidate_id] = lecturer,room
                loads[week_start(old.date)] -= old.units
                loads[week_start(candidate.date)] += old.units
    return selected


def _starting_candidate(courses, fixed_sessions, candidate_sets, control, *, unavailable=(), holidays=None, started=None):
    from app.services.conflict_aware_generation import validate_exact_candidate, InvalidExactCandidate
    from app.services.optimization_incumbent import prefer_candidate
    started = monotonic() if started is None else started
    course_vars = {c.course_id: _CourseVariables(c, candidate_sets[c.course_id]) for c in courses}
    best = None
    def accept(selected):
        nonlocal best
        if not selected:
            return
        candidate = _evaluate_selection(courses, fixed_sessions, candidate_sets, selected, control)
        try:
            validate_exact_candidate(courses, fixed_sessions, unavailable, holidays or {},
                candidate.courses, algorithm='standard_optimized')
        except InvalidExactCandidate:
            return
        chosen = prefer_candidate(candidate, best)
        if chosen is candidate:
            best = replace(candidate,elapsed_milliseconds=max(0,int((monotonic()-started)*1000)))
            if control.cancelled():
                raise OptimizationCancelled('Optimization cancelled')
            if control.checkpoint is not None:
                control.checkpoint(best)
    try:
        # Evaluate lazily: an expensive later construction must not hide an
        # already validated saved/chronological proposal from the parent worker.
        for construct in (
                lambda: _saved_selection(courses,candidate_sets,control),
                lambda: _construct_completion(course_vars,control),
                lambda: _construct_completion(course_vars,control,date_order=_spread_dates)):
            control.check()
            accept(construct())
        if best is not None:
            selected = _saved_selection(courses,candidate_sets,control,
                sessions={c.course_id:c.sessions for c in best.courses})
            accept(_spread_selection(courses,candidate_sets,selected,control))
    except OptimalResultNotProven:
        if best is None:
            raise
    return best


def _evaluate_selection(courses, fixed_sessions, candidate_sets, selected, control):
    """Score saved/constructed assignments in exactly the model's objective units."""
    course_vars = {c.course_id: _CourseVariables(c, candidate_sets[c.course_id]) for c in courses}
    results = []
    spread = shape = temporal = resources = shape_bound = 0
    room_sets = defaultdict(set)
    for course_id, variables in sorted(course_vars.items()):
        control.check()
        course = variables.course
        sessions = []
        by_week = Counter()
        feasible_weeks = set()
        for candidate in variables.candidate_set.candidates:
            control.check()
            feasible_weeks.add(week_start(candidate.date))
            assignment = selected.get((course_id, candidate.candidate_id))
            if assignment is None:
                continue
            lecturer, room = assignment
            sessions.append(GeneratedSession(candidate.date, candidate.start_time,
                candidate.end_time, candidate.units, candidate.time_window_id,
                candidate.constraint_window_index, lecturer, room))
            by_week[week_start(candidate.date)] += candidate.units
            temporal += candidate.canonical_rank
            resources += candidate.lecturer_ids.index(lecturer)+1 + candidate.room_ids.index(room)+1
            room_sets[(course.cohort_id, candidate.date)].add(room)
        sessions.sort(key=lambda s: (s.date, s.start_time, s.lecturer_id, s.room_id))
        total = sum(s.units for s in sessions)
        cumulative = 0
        weeks = sorted(feasible_weeks)
        for index, week in enumerate(weeks[:-1], start=1):
            cumulative += by_week[week]
            spread += abs(len(weeks)*cumulative - index*total)
        shape_bound += (course.total_units // course.min_session_units
            if course.min_session_units > 0 else 0) * max(
                abs(2*course.min_session_units-course.preferred_size_twice),
                abs(2*course.max_session_units-course.preferred_size_twice))
        shape += sum(abs(2*s.units-course.preferred_size_twice) for s in sessions)
        results.append(CourseOptimization(course_id, tuple(sessions), False, total,
            _count_generated_changes(sessions, 'lecturer_id'),
            _count_generated_changes(sessions, 'room_id'), variables.candidate_set.evidence))
    total = sum(c.scheduled_units for c in results)
    if total <= 0:
        return None
    cohort_ids = {c.cohort_id for c in courses}
    for session in fixed_sessions:
        control.check()
        if session.cohort_id in cohort_ids:
            room_sets[(session.cohort_id, session.date)].add(session.room_id)
    intensive = intensive_arrangement(courses, fixed_sessions,
        {c.course_id:c.sessions for c in results}, control=control)
    ticks, variety = (intensive[1], intensive[2]) if intensive else (0, 0)
    lecturer_changes = sum(c.lecturer_changes for c in results)
    room_changes = (sum(c.room_changes for c in results)
        + sum(max(0, len(rooms)-1) for rooms in room_sets.values()))
    shape += (shape_bound+1)*sum(weekly_concentration_cost([s.date for s in c.sessions]) for c in results)
    values = [('total_units', 'max', total), ('intensive_teaching_time', 'max', ticks),
        ('daily_variety', 'max', variety), ('conflicts', 'min', 0),
        ('weekly_spread', 'min', spread), ('schedule_shape', 'min', shape),
        ('lecturer_changes', 'min', lecturer_changes), ('room_changes', 'min', room_changes),
        ('retained_drafts', 'max', 0), ('canonical_temporal', 'min', temporal),
        ('canonical_resource', 'min', resources)]
    upper = sum(c.total_units for c in courses)
    return SemesterOptimizationResult(courses=tuple(results), total_units=total,
        conflicts=0, lecturer_changes=lecturer_changes, room_changes=room_changes, retained_drafts=0,
        optimal=False, elapsed_milliseconds=0, intensive_teaching_time=ticks, daily_variety=variety,
        unit_upper_bound=upper, objectives=tuple(ObjectiveEvidence(key, direction,
            'proven' if key == 'total_units' and total == upper else
            'unfinished' if key == 'total_units' else 'not_attempted', value)
            for key, direction, value in values))


def _compact_day(model, variables, candidates, intervals, control):
    """One selected time and one assignment per resource on this course/date."""
    control.check()
    first = candidates[0]
    prefix = f'day_{first.course_id}_{first.date}'
    present = model.new_bool_var(prefix+'_present')
    model.add(present == sum(variables.temporal[c.candidate_id] for c in candidates))
    start = model.new_int_var(0, 86_400_000_000, prefix+'_start')
    end = model.new_int_var(0, 86_400_000_000, prefix+'_end')
    duration = model.new_int_var(0, 86_400_000_000, prefix+'_duration')
    model.add(start == sum(_time_ticks(c.start_time)*variables.temporal[c.candidate_id] for c in candidates))
    model.add(end == sum(_time_ticks(c.end_time)*variables.temporal[c.candidate_id] for c in candidates))
    model.add(duration == end-start)
    def interval(kind, resource_id, assigned):
        intervals[(kind,resource_id,first.date)].append(model.new_optional_interval_var(
            start, duration, end, assigned, f'{prefix}_{kind}_{resource_id}'))
    interval('cohort', first.cohort_id, present)
    lecturers = {r:model.new_bool_var(f'{prefix}_lecturer_{r}')
        for r in sorted({r for c in candidates for r in c.lecturer_ids})}
    rooms = {r:model.new_bool_var(f'{prefix}_room_{r}')
        for r in sorted({r for c in candidates for r in c.room_ids})}
    for kind, assignments in (('lecturer',lecturers),('room',rooms)):
        model.add(sum(assignments.values()) == present)
        for resource_id, assigned in assignments.items():
            interval(kind, resource_id, assigned)
    cost = model.new_int_var(0,len(lecturers)+len(rooms),prefix+'_resource_rank')
    model.add(cost <= (len(lecturers)+len(rooms))*present)
    groups = defaultdict(list)
    for candidate in candidates:
        control.check()
        groups[(candidate.lecturer_ids,candidate.room_ids)].append(variables.temporal[candidate.candidate_id])
        for resource_id in candidate.lecturer_ids:
            variables.lecturer[candidate.candidate_id,resource_id] = lecturers[resource_id]
        for resource_id in candidate.room_ids:
            variables.room[candidate.candidate_id,resource_id] = rooms[resource_id]
    for index, ((allowed_lecturers,allowed_rooms), choices) in enumerate(groups.items()):
        selected = model.new_bool_var(f'{prefix}_eligibility_{index}')
        model.add(selected == sum(choices))
        model.add(sum(lecturers[r] for r in allowed_lecturers) == 1).only_enforce_if(selected)
        model.add(sum(rooms[r] for r in allowed_rooms) == 1).only_enforce_if(selected)
        model.add(cost == sum((rank+1)*lecturers[r] for rank,r in enumerate(allowed_lecturers))
            + sum((rank+1)*rooms[r] for rank,r in enumerate(allowed_rooms))).only_enforce_if(selected)
    representative = replace(first, lecturer_ids=tuple(lecturers), room_ids=tuple(rooms))
    return representative, present, lecturers, rooms, cost


def _hint_compact(model, course_vars, incumbent, control):
    """Hint each shared day-resource variable exactly once."""
    solved = {c.course_id:c for c in incumbent.courses}
    for course_id, variables in course_vars.items():
        control.check()
        sessions = {(s.date,s.start_time,s.end_time,s.units,s.time_window_id,
            s.constraint_window_index):s for s in solved[course_id].sessions}
        values = {v.index:(v,0) for v in [*variables.temporal.values(),
            *variables.lecturer.values(),*variables.room.values()]}
        matched = set()
        for candidate in variables.candidate_set.candidates:
            control.check()
            signature = (candidate.date,candidate.start_time,candidate.end_time,candidate.units,
                candidate.time_window_id,candidate.constraint_window_index)
            session = sessions.get(signature)
            if session is None:
                continue
            if session.lecturer_id not in candidate.lecturer_ids or session.room_id not in candidate.room_ids:
                raise ValueError('Incumbent resources are unavailable')
            matched.add(signature)
            for variable in (variables.temporal[candidate.candidate_id],
                    variables.lecturer[candidate.candidate_id,session.lecturer_id],
                    variables.room[candidate.candidate_id,session.room_id]):
                values[variable.index] = (variable,1)
        if matched != set(sessions):
            raise ValueError('Incumbent sessions are not in the prepared model')
        for variable, value in values.values():
            model.add_hint(variable,value)


def _optimize_model(courses, fixed_sessions, unavailable, holidays,
        generated_only, control, allow_unproven, incumbent, candidate_sets, started):
    model = cp_model.CpModel()
    course_vars: dict[int, _CourseVariables] = {}
    all_temporal: list[tuple[TemporalCandidate, cp_model.IntVar]] = []
    lecturer_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)
    room_assignments: dict[int, list[tuple[TemporalCandidate, cp_model.IntVar]]] = defaultdict(list)
    compact_intervals = defaultdict(list)
    compact_resource_costs = []
    for course in sorted(courses, key=lambda item: item.course_id):
        control.check()
        candidate_set = candidate_sets[course.course_id]
        variables = _CourseVariables(course=course, candidate_set=candidate_set)
        course_vars[course.course_id] = variables
        by_date: dict[date, list[cp_model.IntVar]] = defaultdict(list)
        for candidate in candidate_set.candidates:
            control.check()
            selected = model.new_bool_var(f"course_{course.course_id}_candidate_{candidate.candidate_id}")
            variables.temporal[candidate.candidate_id] = selected
            all_temporal.append((candidate, selected))
            by_date[candidate.date].append(selected)
            if generated_only:
                continue
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
        if generated_only:
            candidates_by_date = defaultdict(list)
            for candidate in candidate_set.candidates:
                candidates_by_date[candidate.date].append(candidate)
            day_candidates = []
            day_variables = _CourseVariables(course, CandidateSet((), ()))
            for candidates in candidates_by_date.values():
                representative, present, lecturers, rooms, cost = _compact_day(
                    model, variables, candidates, compact_intervals, control)
                day_candidates.append(representative)
                day_variables.temporal[representative.candidate_id] = present
                for resource_id, assigned in lecturers.items():
                    day_variables.lecturer[representative.candidate_id,resource_id] = assigned
                    lecturer_assignments[resource_id].append((representative,assigned))
                for resource_id, assigned in rooms.items():
                    day_variables.room[representative.candidate_id,resource_id] = assigned
                    room_assignments[resource_id].append((representative,assigned))
                compact_resource_costs.append(cost)
            day_variables.candidate_set = CandidateSet(tuple(day_candidates), ())
            _add_continuity(model, day_variables, lecturer=True, control=control)
            _add_continuity(model, day_variables, lecturer=False, control=control)
            variables.lecturer_changes = day_variables.lecturer_changes
            variables.room_changes = day_variables.room_changes
        for date_vars in by_date.values():
            model.add(sum(date_vars) <= 1)
        dates_by_week: dict[date, list[tuple[date, list[cp_model.IntVar]]]] = defaultdict(list)
        for session_date, date_vars in by_date.items():
            dates_by_week[week_start(session_date)].append((session_date, date_vars))
        for week_index, week_dates in enumerate(sorted(dates_by_week.values())):
            ordered_dates = sorted(week_dates)
            for first_index, (_, first_vars) in enumerate(ordered_dates):
                for second_index, (_, second_vars) in enumerate(ordered_dates[first_index + 1:], start=first_index + 1):
                    same_week_pair = model.new_bool_var(
                        f"course_{course.course_id}_week_{week_index}_pair_{first_index}_{second_index}"
                    )
                    first_selected = sum(first_vars)
                    second_selected = sum(second_vars)
                    model.add(same_week_pair <= first_selected)
                    model.add(same_week_pair <= second_selected)
                    model.add(same_week_pair >= first_selected + second_selected - 1)
                    variables.weekly_concentration.append(same_week_pair)

        generated_units = sum(
            candidate.units * variables.temporal[candidate.candidate_id]
            for candidate in candidate_set.candidates
        )
        model.add(generated_units <= course.total_units)
        if course.current_sessions and not generated_only:
            retain = model.new_bool_var(f"course_{course.course_id}_retain_current")
            variables.retain = retain
            if variables.temporal:
                model.add(sum(variables.temporal.values()) <= len(variables.temporal) * (1 - retain))
            current_units = sum(session.units for session in course.current_sessions)
            if not _current_sessions_respect_hard_constraints(
                course,
                unavailable,
                holidays or {},
            ):
                model.add(retain == 0)
            elif current_units > course.total_units:
                model.add(retain == 1)
            else:
                model.add(generated_units >= current_units * (1 - retain))
        if not generated_only:
            _add_continuity(model, variables, lecturer=True, control=control)
            _add_continuity(model, variables, lecturer=False, control=control)

    if generated_only:
        for intervals in compact_intervals.values():
            control.check()
            model.add_no_overlap(intervals)
    else:
        _add_selected_conflict_constraints(model, all_temporal, lecturer_assignments, room_assignments, control=control)
    conflict_terms = _add_retained_alternatives(model, course_vars, fixed_sessions, control=control)

    total_units_terms = []
    lecturer_change_terms = []
    room_change_terms = []
    retain_terms = []
    session_size_deviation_terms = []
    weekly_concentration_terms = []
    canonical_temporal_terms = []
    canonical_resource_terms = list(compact_resource_costs)
    max_session_size_deviation = 0
    for variables in course_vars.values():
        control.check()
        preferred_size_twice = variables.course.preferred_size_twice
        max_generated_sessions = (
            variables.course.total_units // variables.course.min_session_units
            if variables.course.min_session_units > 0
            else 0
        )
        course_size_deviation_bound = max_generated_sessions * max(
            abs(2 * variables.course.min_session_units - preferred_size_twice),
            abs(2 * variables.course.max_session_units - preferred_size_twice),
        )
        for candidate in variables.candidate_set.candidates:
            selected = variables.temporal[candidate.candidate_id]
            total_units_terms.append(candidate.units * selected)
            session_size_deviation_terms.append(
                abs(2 * candidate.units - preferred_size_twice) * selected
            )
            canonical_temporal_terms.append(
                candidate.canonical_rank * selected
            )
            if generated_only:
                continue
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
        weekly_concentration_terms.extend(variables.weekly_concentration)
        if variables.retain is not None:
            current_units = sum(session.units for session in variables.course.current_sessions)
            total_units_terms.append(current_units * variables.retain)
            current_size_deviation = sum(
                abs(2 * session.units - preferred_size_twice)
                for session in variables.course.current_sessions
            )
            course_size_deviation_bound = max(
                course_size_deviation_bound,
                current_size_deviation,
            )
            current_weekly_concentration = weekly_concentration_cost(
                [session.date for session in variables.course.current_sessions]
            )
            session_size_deviation_terms.append(
                current_size_deviation * variables.retain
            )
            weekly_concentration_terms.append(
                current_weekly_concentration * variables.retain
            )
            lecturer_change_terms.append(_count_current_changes(variables.course.current_sessions, "lecturer_id") * variables.retain)
            room_change_terms.append(_count_current_changes(variables.course.current_sessions, "room_id") * variables.retain)
            retain_terms.append(variables.retain)
        max_session_size_deviation += course_size_deviation_bound

    room_change_terms.extend(_cohort_day_room_penalties(model, course_vars, room_assignments, fixed_sessions, control))
    schedule_shape_terms = (
        sum(weekly_concentration_terms) * (max_session_size_deviation + 1)
        + sum(session_size_deviation_terms)
    )

    intensive_time, daily_variety = _intensive_objectives(model,course_vars,fixed_sessions,control)
    weekly_spread = _weekly_spread(model, course_vars, control)
    objectives = [
        ("total_units", "max", sum(total_units_terms)),
        ("intensive_teaching_time", "max", intensive_time),
        ("daily_variety", "max", daily_variety),
        ("conflicts", "min", sum(conflict_terms)),
        ("weekly_spread", "min", weekly_spread),
        ("schedule_shape", "min", schedule_shape_terms),
        ("lecturer_changes", "min", sum(lecturer_change_terms)),
        ("room_changes", "min", sum(room_change_terms)),
        ("retained_drafts", "max", sum(retain_terms)),
        ("canonical_temporal", "min", sum(canonical_temporal_terms)),
        ("canonical_resource", "min", sum(canonical_resource_terms)),
    ]
    proof_states = {}
    def decode(solver, proofs, stage, fully_proven=False, unit_bound=None):
        values = {key: int(solver.value(expression)) for key, _direction, expression in objectives}
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
            if not evidence and fully_proven:
                evidence.append(BlockingEvidence(
                    "COURSE_CONSTRAINT",
                    1,
                    REASON_MESSAGES["COURSE_CONSTRAINT"],
                ))
            results[index] = replace(
                course_result,
                evidence=tuple(_deduplicate_evidence(evidence)),
            )
        if generated_only and values["total_units"] <= 0:
            course_details = []
            for course_result in results:
                course = course_vars[course_result.course_id].course
                name = course.course_name or f"Course {course.course_id}"
                reasons = ", ".join(item.message for item in course_result.evidence)
                course_details.append(f"{name}: {reasons}")
            raise NoGeneratedAlternative(
                "No non-empty valid generated alternative exists. "
                + "; ".join(course_details), courses=tuple(results)
            )
        return SemesterOptimizationResult(
            courses=tuple(results),
            optimal=fully_proven,
            objectives=tuple(ObjectiveEvidence(key, direction, proof_states.get(key, 'unfinished' if index == stage else 'not_attempted'), values[key])
                for index,(key,direction,_expression) in enumerate(objectives)),
            unit_upper_bound=(values['total_units'] if proof_states.get('total_units') == 'proven' else
                valid_unit_upper_bound(values['total_units'], sum(c.total_units for c in courses), unit_bound)),
            total_units=values["total_units"],
            intensive_teaching_time=values['intensive_teaching_time'],
            daily_variety=values['daily_variety'],
            conflicts=values["conflicts"],
            lecturer_changes=values["lecturer_changes"],
            room_changes=values["room_changes"],
            retained_drafts=values["retained_drafts"],
            elapsed_milliseconds=max(int((monotonic() - started) * 1000), 0),
            search_exhausted=control.clock() >= control.deadline,
        )

    solver: cp_model.CpSolver | None = None
    tracked_vars = list({var.index:var for variables in course_vars.values() for var in (
        list(variables.temporal.values()) + list(variables.lecturer.values()) + list(variables.room.values()) + ([variables.retain] if variables.retain is not None else [])
    )}.values())
    objective_values: dict[str, int] = {}
    # Try the course's preferred size first, then fall back without excluding any
    # allowed size. Keep canonical ranks and the coverage-first objectives intact.
    preferred_decisions = sorted(all_temporal, key=lambda item: (
        abs(2 * item[0].units - course_vars[item[0].course_id].course.preferred_size_twice),
        item[0].date, item[0].start_time, item[0].course_id, item[0].units,
    ))
    if preferred_decisions:
        model.add_decision_strategy([var for _, var in preferred_decisions],
                                    cp_model.CHOOSE_FIRST, cp_model.SELECT_MAX_VALUE)
    last_candidate = None
    last_solver = None
    unit_bound = None
    coverage_upper = sum(max(c.total_units, sum(s.units for s in c.current_sessions))
        if not generated_only else c.total_units for c in courses)
    if incumbent is not None:
        from app.services.optimization_incumbent import seed_incumbent
        last_candidate, objective_values = seed_incumbent(model, course_vars, objectives,
            incumbent, control, coverage_upper, hint=_hint_compact if generated_only else None)
        proof_states.update({key: 'proven' for key in objective_values})
        unit_bound = last_candidate.unit_upper_bound

    def completed(candidate):
        optimal = all(e.proof_status == 'proven' for e in candidate.objectives)
        if not optimal and not allow_unproven:
            raise OptimalResultNotProven('Standard Optimized preferences remain unproven.')
        exhausted = control.clock() >= control.deadline
        return replace(candidate, optimal=optimal, search_exhausted=exhausted,
            elapsed_milliseconds=max(0, int((monotonic()-started)*1000)),
            termination='deadline' if exhausted else 'standard_optimized_completed')

    for stage, (objective_name, direction, expression) in enumerate(objectives):
        if objective_name in objective_values:
            continue
        try:
            control.check()
        except OptimalResultNotProven:
            if last_candidate is not None:
                return completed(last_candidate)
            raise
        preceding_proven = all(proof_states.get(key) == 'proven' for key, _, _ in objectives[:stage])
        if stage and isinstance(expression, int):
            objective_values[objective_name] = expression
            proof_states[objective_name] = 'proven' if preceding_proven else 'conditional'
            if last_candidate is not None:
                last_candidate = replace(last_candidate, objectives=tuple(
                    replace(e, value=expression, proof_status=proof_states[objective_name])
                    if e.objective_key == objective_name else e for e in last_candidate.objectives))
            continue
        control.progress(objective_name)
        remaining = max(0, control.deadline - control.clock())
        seconds = remaining if stage == 0 and last_candidate is None else stage_budget_seconds(remaining, stage)
        # A nonconstant conflicts stage is not expected on generated-only inputs;
        # retain a small bounded allowance for direct retained-plan callers.
        if seconds <= 0:
            seconds = remaining * .01
        stage_deadline = min(control.deadline, control.clock() + seconds)
        model.clear_objective()
        if direction == 'max':
            model.maximize(expression)
        else:
            model.minimize(expression)
        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = seconds
        solver.parameters.num_search_workers = 1
        solver.parameters.random_seed = 0
        solver.parameters.cp_model_presolve = True
        if stage == 0:
            solver.parameters.search_branching = cp_model.FIXED_SEARCH
        finished = Event()
        def watch_search(active_solver=solver, limit=stage_deadline):
            while not finished.wait(.05):
                if control.cancelled() or control.clock() >= limit:
                    active_solver.stop_search()
                    return
        watcher = Thread(target=watch_search, daemon=True)
        watcher.start()
        class Checkpoint(cp_model.CpSolverSolutionCallback):
            last_sent = -float('inf')
            def on_solution_callback(self):
                nonlocal last_candidate
                if control.cancelled():
                    self.stop_search()
                    return
                complete = stage == 0 and int(self.value(expression)) == coverage_upper
                if complete or monotonic() - self.last_sent >= .25:
                    self.last_sent = monotonic()
                    try:
                        if complete:
                            proof_states['total_units'] = 'proven'
                        last_candidate = decode(self, objective_values, stage,
                            unit_bound=coverage_upper if complete else unit_bound)
                        if control.checkpoint is not None:
                            control.checkpoint(last_candidate)
                    except NoGeneratedAlternative:
                        pass
                if complete:
                    # Coverage cannot exceed the sum of per-course hard caps.
                    # Stop proving an already attained mathematical upper bound.
                    self.stop_search()
        try:
            status = solver.solve(model, Checkpoint())
        finally:
            finished.set()
            watcher.join()
        if control.cancelled():
            raise OptimizationCancelled('Optimization cancelled')
        if status == cp_model.MODEL_INVALID:
            raise OptimizationModelInvalid('The semester optimization model is invalid.')
        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            value = int(solver.value(expression))
            if stage == 0:
                unit_bound = solver.best_objective_bound
            proven = status == cp_model.OPTIMAL or (stage == 0 and value == coverage_upper)
            proof_states[objective_name] = ('proven' if preceding_proven else 'conditional') if proven else 'unfinished'
            objective_values[objective_name] = value
            last_solver = solver
            last_candidate = decode(solver, objective_values, stage,
                fully_proven=all(proof_states.get(key) == 'proven' for key, _, _ in objectives), unit_bound=unit_bound)
            if control.checkpoint is not None:
                control.checkpoint(last_candidate)
        elif last_candidate is not None:
            # A previous feasible assignment is valid for this unchanged model.
            # Keep its value and disclose that this stage was not proved optimal.
            value = next(e.value for e in last_candidate.objectives if e.objective_key == objective_name)
            proof_states[objective_name] = 'unfinished'
            objective_values[objective_name] = value
            last_candidate = replace(last_candidate, objectives=tuple(
                replace(e, proof_status='unfinished') if e.objective_key == objective_name else e
                for e in last_candidate.objectives))
        else:
            raise OptimalResultNotProven('No usable candidate found within the remaining coverage allowance.')
        # Preserve every attained higher-priority value, even when proof timed out.
        # Later results are conditional on those fixed values, never globally optimal.
        model.add(expression == value)
        if last_solver is not None:
            model.clear_hints()
            for variable in tracked_vars:
                model.add_hint(variable, last_solver.value(variable))

    assert last_candidate is not None
    return completed(last_candidate)
