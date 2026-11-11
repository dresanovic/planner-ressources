"""Bounded owner-oriented construction and copy-on-write provisional repair.

The authoritative state is an immutable tuple per course. Demand, load and
occupancy are derived from it, so rejecting an alternative restores every ledger
by discarding that alternative. Protected sessions never enter the repair set.
"""
from dataclasses import replace
from datetime import datetime
from fractions import Fraction
from time import monotonic

from app.schemas.conflict_aware_generation import HEURISTIC_OBJECTIVE_KEYS
from app.services.schedule_generation import GeneratedSession, intensive_instruction_ticks
from app.services.semester_optimization import (
    CourseOptimization, SemesterOptimizationResult, ObjectiveEvidence,
    OptimizationSearchControl, OptimalResultNotProven, OptimizationCancelled, BlockingEvidence,
    generate_candidates, intervals_overlap, week_start, _candidate_start_times,
)
from app.services.teaching_preferences import derive_portions, score_arrangement, score_context, scarcity_key


REPAIR_LIMIT = 1000
MAX_DISPLACED = 8
CHECKPOINT_SECONDS = 5


def _overlaps(course, session, other_course, other):
    return (session.date == other.date and session.start_time < other.end_time and other.start_time < session.end_time
        and (course.cohort_id == other_course.cohort_id or session.lecturer_id == other.lecturer_id or session.room_id == other.room_id))


def _size_costs(course, target, control):
    costs = [Fraction()]
    for remaining in range(1, target + 1):
        control.check()
        options = [costs[remaining - size] + Fraction(abs(2 * size - course.preferred_size_twice), 2)
            for size in range(course.min_session_units, min(course.max_session_units, remaining) + 1)
            if costs[remaining - size] is not None]
        costs.append(min(options) if options else None)
    return costs


def repair_base(by_id, state, course, proposed, *, portions=None, max_displaced=MAX_DISPLACED, control=None):
    """Return a detached provisional alternative, or reject it without mutation."""
    check = control.check if control else lambda: None
    trial = {}
    removed = 0
    affected = {course.course_id}
    for other_id, values in state.items():
        kept = []
        for session in values:
            check()
            if ((other_id == course.course_id and session.date == proposed.date)
                    or _overlaps(course, proposed, by_id[other_id], session)):
                removed += 1
                affected.add(other_id)
            else:
                kept.append(session)
        trial[other_id] = tuple(kept)
        if removed > max_displaced:
            return None
    # Moving a fully allocated LV to a new date must release its old demand,
    # including size redistributions that would otherwise leave a 1-LE remainder.
    own = None
    if portions is not None:
        own = next((p for p in portions[course.course_id] if p.lecturer_id == proposed.lecturer_id),None)
        if own is None:
            return None
    limit = own.required_units if own else course.total_units
    if proposed.units > limit:
        return None
    pool = tuple(s for s in trial[course.course_id] if own is None or s.lecturer_id == own.lecturer_id)
    remaining = limit - sum(s.units for s in pool) - proposed.units
    def representable(units):
        return units == 0 or (units > 0 and (units+course.max_session_units-1)//course.max_session_units <= units//course.min_session_units)
    def removal_rank(session):
        check()
        return (intensive_instruction_ticks(session.date,session.start_time,session.end_time,session.units,course.windows),
                -session.units,session.date,session.start_time)
    for old in sorted(pool,key=removal_rank):
        check()
        if remaining >= 0 and representable(remaining):
            break
        trial[course.course_id] = tuple(s for s in trial[course.course_id] if s != old)
        remaining += old.units
        removed += 1
        if removed > max_displaced:
            return None
    if remaining < 0:
        return None
    if portions is not None:
        for other_id in affected:
            check()
            kept = trial[other_id]
            for portion in portions[other_id]:
                check()
                if sum(s.units for s in kept if s.lecturer_id == portion.lecturer_id) < portion.required_units:
                    successors = {p.lecturer_id for p in portions[other_id] if p.sequence_index > portion.sequence_index}
                    revised = []
                    for session in kept:
                        check()
                        if session.lecturer_id in successors:
                            removed += 1
                        else:
                            revised.append(session)
                    trial[other_id] = tuple(revised)
                    break
            if removed > max_displaced:
                return None
    return trial, affected


def search_teaching(courses, fixed_sessions, unavailable_dates=(), *, algorithm,
                    holidays=None, deadline_seconds=60, control=None, incumbent=None, **_options):
    started = monotonic()
    control = control or OptimizationSearchControl(started + deadline_seconds)
    control.check()
    raw_control = control
    courses = tuple(sorted(courses, key=lambda c: c.course_id))
    fixed_sessions = tuple(fixed_sessions)
    by_id = {c.course_id: c for c in courses}
    best = {c.course_id: () for c in courses} if incumbent is None else {
        c.course_id: c.sessions for c in incumbent.courses}
    candidate_sets = {c.course_id: () for c in courses}
    evidence = {c.course_id: () for c in courses}
    portions = {c.course_id: derive_portions(c, getattr(c, 'explicit_lecturer_portions', None)) for c in courses} if algorithm == 'lecturer' else {}
    best_score = None
    last_checkpoint = control.clock()
    repair_attempts = 0
    termination = 'heuristic_completed'
    context = None
    best_packet = None

    def checked(values, *, packet=False):
        for value in values:
            (raw_control if packet else control).check()
            yield value

    def score(state):
        return score_arrangement(courses, fixed_sessions, state, candidate_sets, algorithm, control, context)

    def result(state, actual):
        # Construct under the allowance, then publish the state and packet
        # together. Timeout returns an already completed immutable packet.
        raw_control.check()
        required = sum(c.total_units for c in checked(courses, packet=True))
        total = -actual[0]
        values = (total, -actual[1], -actual[2], *actual[3:8])
        objectives = tuple(ObjectiveEvidence(key, 'max' if index < 3 else 'min',
            'proven' if index == 0 and total == required else 'unfinished',
            float(values[index]) if isinstance(values[index], Fraction) else values[index])
            for index, key in checked(enumerate(HEURISTIC_OBJECTIVE_KEYS), packet=True))
        solved = tuple(CourseOptimization(c.course_id, tuple(sorted(checked(state[c.course_id], packet=True), key=lambda s: (s.date, s.start_time))),
            False, sum(s.units for s in checked(state[c.course_id], packet=True)), 0,
            sum(a.room_id != b.room_id for a, b in checked(zip(state[c.course_id], state[c.course_id][1:]), packet=True)),
            evidence[c.course_id] if not state[c.course_id] else ()) for c in checked(courses, packet=True))
        candidate_result = SemesterOptimizationResult(solved, total, 0, 0, sum(c.room_changes for c in solved),
            0, max(0, int((monotonic() - started) * 1000)), optimal=False,
            objectives=objectives, unit_upper_bound=required, search_exhausted=False,
            intensive_teaching_time=-actual[1], daily_variety=-actual[2],
            termination='heuristic_completed', repair_attempts=repair_attempts)
        raw_control.check()
        return candidate_result

    def retained_result(termination_code):
        if raw_control.cancelled():
            raise OptimizationCancelled('Optimization cancelled')
        if raw_control.clock() >= raw_control.deadline:
            termination_code = 'deadline'
        # Only constant-size metadata changes remain after deadline/cancellation.
        packet = replace(best_packet, termination=termination_code,
            search_exhausted=termination_code == 'deadline', repair_attempts=repair_attempts,
            elapsed_milliseconds=max(0, int((monotonic() - started) * 1000)))
        if raw_control.cancelled():
            raise OptimizationCancelled('Optimization cancelled')
        return packet

    def checkpoint(state, force=False):
        nonlocal best, best_score, best_packet, last_checkpoint
        control.check()
        measured = score(state)
        improved = best_score is None or measured < best_score
        if improved:
            packet = result(state, measured)
            best, best_score, best_packet = dict(state), measured, packet
        if control.checkpoint and -measured[0] > 0 and (improved or force or control.clock() - last_checkpoint >= CHECKPOINT_SECONDS):
            raw_control.check()
            control.checkpoint(retained_result('heuristic_completed'))
            last_checkpoint = control.clock()

    def legal(course, session, state):
        for other_id, values in state.items():
            control.check()
            for other in values:
                control.check()
                if (other_id == course.course_id and session.date == other.date) or _overlaps(course, session, by_id[other_id], other):
                    return False
        return True

    def finish(course, initial, first_week=None, owner=None):
        state = dict(initial)
        shares = tuple(p for p in portions[course.course_id] if p.lecturer_id == owner) if algorithm == 'lecturer' else (None,)
        for portion in shares:
            control.check()
            predecessors = portions[course.course_id][:portion.sequence_index] if portion else ()
            if any(sum(s.units for s in checked(state[course.course_id]) if s.lecturer_id == p.lecturer_id)
                   != p.required_units for p in checked(predecessors)):
                return state
            target = portion.required_units if portion else course.total_units
            own = tuple(s for s in checked(state[course.course_id]) if portion is None or s.lecturer_id == portion.lecturer_id)
            remaining = target - sum(s.units for s in own)
            previous_ids = {p.lecturer_id for p in predecessors}
            previous = tuple(s for s in checked(state[course.course_id]) if s.lecturer_id in previous_ids)
            boundary = max((datetime.combine(s.date, s.end_time) for s in previous), default=None)
            daily_capacity = {}
            used_dates = {s.date for s in checked(state[course.course_id])}
            for candidate in candidate_sets[course.course_id]:
                control.check()
                if candidate.date in used_dates or (portion and portion.lecturer_id not in candidate.lecturer_ids):
                    continue
                if first_week is not None and week_start(candidate.date) < first_week:
                    continue
                if boundary is not None and datetime.combine(candidate.date, candidate.start_time) < boundary:
                    continue
                daily_capacity[candidate.date] = max(daily_capacity.get(candidate.date, 0), candidate.units)
            # A necessary optimistic ceiling, not a claim of feasible packing:
            # overlapping windows/resource alternatives count once per date.
            costs = _size_costs(course, min(remaining, sum(checked(daily_capacity.values()))), control)
            while remaining >= course.min_session_units:
                control.check()
                selected = selected_score = None
                occupied_dates = {s.date for s in checked(state[course.course_id])}
                for candidate in candidate_sets[course.course_id]:
                    control.check()
                    if candidate.units > remaining or (first_week is not None and week_start(candidate.date) < first_week):
                        continue
                    if boundary is not None and datetime.combine(candidate.date, candidate.start_time) < boundary:
                        continue
                    for lecturer in candidate.lecturer_ids:
                        if portion and lecturer != portion.lecturer_id:
                            continue
                        for room in candidate.room_ids:
                            control.check()
                            session = GeneratedSession(candidate.date, candidate.start_time, candidate.end_time, candidate.units,
                                candidate.time_window_id, candidate.constraint_window_index, lecturer, room)
                            if not legal(course, session, state):
                                continue
                            trial = dict(state)
                            trial[course.course_id] = (*state[course.course_id], session)
                            measured = score(trial)
                            residual = remaining - candidate.units
                            # The proposed date and dates already used by this LV
                            # cannot supply another session's remainder capacity.
                            capacity_left = sum(units for day, units in checked(daily_capacity.items())
                                if day != candidate.date and day not in occupied_dates)
                            attainable = min(residual, capacity_left, len(costs) - 1)
                            while attainable > 0 and costs[attainable] is None:
                                control.check()
                                attainable -= 1
                            # Optimistic remainder completion compares all sizes,
                            # rather than stranding an inflexible preferred split.
                            ranking = (measured[0] - attainable, *measured[1:3],
                                measured[3] + costs[attainable], *measured[4:])
                            if selected_score is None or ranking < selected_score:
                                selected, selected_score = session, ranking
                if selected is None:
                    break
                state[course.course_id] = (*state[course.course_id], selected)
                remaining -= selected.units
                checkpoint(state)
            if remaining:
                break  # An incomplete nonzero predecessor cannot be bypassed.
        return state

    def cancelled_with_refresh():
        nonlocal last_checkpoint
        if raw_control.cancelled():
            return True
        now = raw_control.clock()
        if (control.checkpoint and best_score is not None and -best_score[0] > 0
                and now < raw_control.deadline and now - last_checkpoint >= CHECKPOINT_SECONDS):
            last_checkpoint = now
            control.checkpoint(retained_result('heuristic_completed'))
        return False

    control = replace(control, cancelled=cancelled_with_refresh)
    best_packet = incumbent or result(best, (0, 0, 0, Fraction(), 0, Fraction(), 0, 0, ()))
    try:
        # Shared temporal event closure allows later starts around other courses,
        # while generate_candidates remains the source of all static legality.
        starts = {}
        def starts_for_date(day):
            if day not in starts:
                starts[day] = _candidate_start_times(courses, fixed_sessions, day, control)
            return starts[day]
        for course in courses:
            control.check()
            generated = generate_candidates(course, fixed_sessions, frozenset(unavailable_dates), holidays or {},
                control=control, start_times_for_date=starts_for_date)
            unique = {}
            for item in generated.candidates:
                control.check()
                key = (item.date, item.start_time, item.units, item.lecturer_ids, item.room_ids)
                unique.setdefault(key, item)
            candidate_sets[course.course_id] = tuple(unique.values())
            evidence[course.course_id] = generated.evidence
        context = score_context(courses, candidate_sets, algorithm, control)
        if incumbent is not None:
            best_score = score(best)
        def scarcity(course, owner=None):
            return scarcity_key(course, candidate_sets[course.course_id],
                lecturer_id=owner if algorithm == 'lecturer' else None, control=control)
        groups = {}
        for course in courses:
            control.check()
            if course.total_units <= 0:
                continue
            owners = (course.cohort_id,) if algorithm == 'cohort' else tuple(p.lecturer_id for p in portions[course.course_id] if p.required_units)
            for owner in owners:
                groups.setdefault(owner, []).append(course)
        def ordered_work(state, visited=(), affected=None, include_completed=False):
            pending = {}
            for owner, grouped in groups.items():
                control.check()
                for course in grouped:
                    control.check()
                    if (owner, course.course_id) in visited or (affected is not None and course.course_id not in affected):
                        continue
                    values = state[course.course_id]
                    if algorithm == 'lecturer':
                        share = next(p for p in portions[course.course_id] if p.lecturer_id == owner)
                        remaining = share.required_units - sum(s.units for s in checked(values) if s.lecturer_id == owner)
                        ready = all(sum(s.units for s in checked(values) if s.lecturer_id == p.lecturer_id) == p.required_units
                                    for p in checked(portions[course.course_id][:share.sequence_index]))
                    else:
                        remaining = course.total_units - sum(s.units for s in checked(values))
                        ready = True
                    if ready and (remaining > 0 or include_completed):
                        pending.setdefault(owner, []).append(course)
            return [(owner, course)
                for owner in sorted(pending, key=lambda g: (min(scarcity(c, g)[0] for c in pending[g]), g))
                for course in sorted(pending[owner], key=lambda c: scarcity(c, owner))]

        def construct(initial, affected=None, compare_starts=False):
            state = dict(initial)
            visited = set()
            while work := ordered_work(state, visited, affected):
                control.check()
                owner, course = work[0]
                visited.add((owner, course.course_id))
                if compare_starts:
                    alternatives = [state]
                    for start_week in sorted({week_start(c.date) for c in checked(candidate_sets[course.course_id])}):
                        control.check()
                        alternatives.append(finish(course, state, start_week, owner))
                    state = min(alternatives, key=score)
                else:
                    state = finish(course, state, owner=owner)
                checkpoint(state)
            return state

        state = construct(best, compare_starts=True)
        # Bounded cross-group remove/reinsert repair. Every attempted alternative,
        # including rejected conflicts and partial candidates, spends the cap.
        while True:
            control.check()
            pass_score = best_score
            for owner, course in ordered_work(best, include_completed=True):
                for candidate in candidate_sets[course.course_id]:
                    for lecturer in candidate.lecturer_ids:
                        if algorithm == 'lecturer' and lecturer != owner:
                            continue
                        for room in candidate.room_ids:
                            control.check()
                            if repair_attempts >= REPAIR_LIMIT:
                                termination = 'repair_limit'
                                return retained_result(termination)
                            repair_attempts += 1
                            session = GeneratedSession(candidate.date, candidate.start_time, candidate.end_time, candidate.units,
                                candidate.time_window_id, candidate.constraint_window_index, lecturer, room)
                            base = repair_base(by_id, best, course, session,
                                portions=portions if algorithm == 'lecturer' else None,
                                max_displaced=MAX_DISPLACED, control=control)
                            if base is None:
                                continue
                            trial, affected = base
                            # Reconstruct affected courses from the retained immutable
                            # state; arbitrary injected assignments never bypass portions.
                            portion_valid = True
                            if algorithm == 'lecturer':
                                own_portions = portions[course.course_id]
                                own = next((p for p in own_portions if p.lecturer_id == lecturer), None)
                                portion_valid = own is not None
                                if own:
                                    own_units = sum(s.units for s in trial[course.course_id] if s.lecturer_id == lecturer)
                                    portion_valid = own_units + session.units <= own.required_units
                                    for previous in own_portions[:own.sequence_index]:
                                        control.check()
                                        values = tuple(s for s in trial[course.course_id] if s.lecturer_id == previous.lecturer_id)
                                        if (sum(s.units for s in values) != previous.required_units
                                                or any(datetime.combine(s.date,s.end_time) > datetime.combine(session.date,session.start_time) for s in values)):
                                            portion_valid = False
                                            break
                            if portion_valid and sum(s.units for s in trial[course.course_id]) + session.units <= course.total_units:
                                trial[course.course_id] = (*trial[course.course_id], session)
                            trial = construct(trial, affected)
                            checkpoint(trial)
            if best_score == pass_score:
                break
        checkpoint(best, force=True)
    except OptimalResultNotProven:
        termination = 'deadline'
    return retained_result(termination)
