"""Exact, lexicographic heuristic preferences and authoritative per-run portions."""
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import timedelta
from fractions import Fraction

from app.services.schedule_generation import intensive_instruction_ticks
from app.services.semester_optimization import week_start, intensive_arrangement


@dataclass(frozen=True)
class LecturerPortion:
    lecturer_id: int
    lecturer_code: str
    sequence_index: int
    source: str
    required_units: int


def derive_portions(course, explicit=None):
    if explicit is not None and not isinstance(explicit, dict):
        pairs = tuple(explicit)
        explicit = dict(pairs)
        if len(explicit) != len(pairs):
            raise ValueError('Duplicate explicit lecturer portion')
    eligible = {item.id: item for item in course.lecturers if item.active}
    ordered = sorted(eligible.values(), key=lambda item: (item.normalized_code.strip().casefold(), item.id))
    total = course.total_units
    if isinstance(total, bool) or not isinstance(total, int) or total < 0:
        raise ValueError('Portions require whole nonnegative course units')
    if explicit is not None:
        if (set(explicit) != set(eligible) or any(isinstance(v, bool) or not isinstance(v, int) or v < 0 for v in explicit.values())
                or sum(explicit.values()) != total):
            raise ValueError('Explicit portions must cover each active lecturer and sum to the course requirement')
    quotient, remainder = divmod(total, len(ordered)) if ordered else (0, 0)
    return tuple(LecturerPortion(item.id, item.normalized_code, index,
        'explicit' if explicit is not None else 'derived',
        explicit[item.id] if explicit is not None else quotient + (index < remainder))
        for index, item in enumerate(ordered))


def balance_cost(loads, weights):
    return sum((Fraction(load) ** 2 / weight for load, weight in zip(loads, weights, strict=True)), Fraction())


def scarcity_key(course, candidates, *, lecturer_id=None, control=None):
    opportunities = set()
    dates = set()
    for candidate in candidates:
        if control:
            control.check()
        if lecturer_id is None or lecturer_id in candidate.lecturer_ids:
            opportunities.add((candidate.date, candidate.start_time, candidate.units))
            dates.add(candidate.date)
    return len(opportunities), len(dates), course.course_id


def opportunity_calendar(course, candidates, control=None):
    dates = defaultdict(set)
    marked = set()
    for candidate in candidates:
        if control:
            control.check()
        if candidate.units != course.min_session_units:
            continue
        week = week_start(candidate.date)
        dates[week].add(candidate.date)
        if intensive_instruction_ticks(candidate.date, candidate.start_time, candidate.end_time, candidate.units, course.windows):
            marked.add(week)
    return {week: (frozenset(days), min(2, len(days)) if week in marked else 1)
            for week, days in sorted(dates.items())}


def rhythm_penalty(counts, calendar, control=None):
    if not counts:
        return 0
    first, last = min(counts), max(counts)
    penalty = 0
    for week, count in counts.items():
        if control:
            control.check()
        penalty += max(0, count - calendar.get(week, ((), 1))[1])
    for week, (_, cadence) in calendar.items():
        if control:
            control.check()
        if first < week < last:
            penalty += max(0, cadence - counts.get(week, 0))
    return penalty


def assignment_key(course, session):
    lecturers = {item.id: item.normalized_code for item in course.lecturers}
    rooms = {item.id: item.normalized_code for item in course.rooms}
    return (session.date, session.start_time, course.course_id, session.units,
            lecturers.get(session.lecturer_id, ''), session.lecturer_id,
            rooms.get(session.room_id, ''), session.room_id)


def score_context(courses, candidate_sets, algorithm, control=None):
    calendars = {c.course_id: opportunity_calendar(c, candidate_sets[c.course_id], control) for c in courses}
    weights = defaultdict(dict)
    for course in courses:
        for candidate in candidate_sets[course.course_id]:
            if control:
                control.check()
            if candidate.units != course.min_session_units:
                continue
            week = week_start(candidate.date)
            intensive = bool(intensive_instruction_ticks(candidate.date, candidate.start_time,
                candidate.end_time, candidate.units, course.windows))
            relevant = (course.cohort_id,) if algorithm == 'cohort' else candidate.lecturer_ids
            for owner in relevant:
                weights[owner][week] = max(weights[owner].get(week, 1), 2 if intensive else 1)
    return calendars, weights


def score_arrangement(courses, fixed, sessions, candidate_sets, algorithm, control=None, context=None):
    """Smaller tuple is better. No weighted sum trades away a higher priority."""
    check = control.check if control else lambda: None
    calendars, original_weights = context or score_context(courses, candidate_sets, algorithm, control)
    owners = {c.cohort_id for c in courses} if algorithm == 'cohort' else {
        lecturer.id for c in courses for lecturer in c.lecturers if lecturer.active}
    owner_loads = defaultdict(Counter)
    weights = defaultdict(dict, {owner: dict(weeks) for owner, weeks in original_weights.items()})
    room_sets = defaultdict(set)
    coverage = deviation = rhythm = changes = 0
    sequence = []
    for course in courses:
        check()
        values = sorted(sessions.get(course.course_id, ()), key=lambda s: (s.date, s.start_time))
        calendar = calendars[course.course_id]
        for session in values:
            check()
            coverage += session.units
            deviation += Fraction(abs(2 * session.units - course.preferred_size_twice), 2)
            owner = course.cohort_id if algorithm == 'cohort' else session.lecturer_id
            owner_loads[owner][week_start(session.date)] += session.units
            room_sets[(course.cohort_id, session.date)].add(session.room_id)
            sequence.append(assignment_key(course, session))
        rhythm += rhythm_penalty(Counter(week_start(s.date) for s in values), calendar, control)
        changes += sum(left.room_id != right.room_id for left, right in zip(values, values[1:]))
    start = min((c.planning_period.start_date for c in courses), default=None)
    end = max((c.planning_period.end_date for c in courses), default=None)
    seen = set()
    for session in fixed:
        check()
        identity = (session.source_kind, session.source_id) if session.source_id is not None else session
        if identity in seen or session.source_kind != 'teaching_session' or not start <= session.date <= end:
            continue
        seen.add(identity)
        if session.cohort_id in {c.cohort_id for c in courses}:
            room_sets[(session.cohort_id, session.date)].add(session.room_id)
        owner = session.cohort_id if algorithm == 'cohort' else session.lecturer_id
        if owner in owners:
            week = week_start(session.date)
            owner_loads[owner][week] += session.units
            if intensive_instruction_ticks(session.date, session.start_time, session.end_time, session.units, session.marked_windows):
                weights[owner][week] = 2
    balance = Fraction()
    for owner, weeks in owner_loads.items():
        for week, load in weeks.items():
            check()
            balance += Fraction(load * load, weights[owner].get(week, 1))
    intensive = intensive_arrangement(courses, fixed, sessions, control=control)
    check()
    ticks, variety = (intensive[1], intensive[2]) if intensive else (0, 0)
    return (-coverage, -ticks, -variety, deviation, rhythm, balance,
            sum(max(0, len(rooms) - 1) for rooms in room_sets.values()), changes, tuple(sorted(sequence)))
