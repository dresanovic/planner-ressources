"""Seed an exact model and protect the retained proposal in objective order."""
from dataclasses import replace


def seed_incumbent(model, course_vars, objectives, incumbent, control, coverage_upper, *, hint=None):
    values = {e.objective_key: e.value for e in incumbent.objectives}
    if set(values) != {key for key, _, _ in objectives} or any(v is None for v in values.values()):
        raise ValueError('Incumbent objectives do not match this strategy')
    model.clear_hints()
    (hint or _add_incumbent_hints)(model, course_vars, incumbent, control)

    # A lower objective may worsen only after a higher one strictly improves.
    prefix = None
    for index, (key, direction, expression) in enumerate(objectives):
        control.check()
        value = values[key]
        if isinstance(expression, int):
            if expression != value:
                raise ValueError('Incumbent constant objective changed')
            continue
        constraint = model.add(expression >= value if direction == 'max' else expression <= value)
        if prefix is not None:
            constraint.only_enforce_if(prefix)
        equal = model.new_bool_var(f'incumbent_equal_{index}')
        model.add(expression == value).only_enforce_if(equal)
        model.add(expression != value).only_enforce_if(equal.Not())
        if prefix is None:
            prefix = equal
        else:
            next_prefix = model.new_bool_var(f'incumbent_prefix_{index}')
            model.add_bool_and([prefix, equal]).only_enforce_if(next_prefix)
            model.add_bool_or([prefix.Not(), equal.Not()]).only_enforce_if(next_prefix.Not())
            prefix = next_prefix

    # Only the proven prefix can be fixed without limiting higher-priority search.
    proven = {}
    for evidence in incumbent.objectives:
        full_coverage = evidence.objective_key == 'total_units' and evidence.value == coverage_upper
        if evidence.proof_status != 'proven' and not full_coverage:
            break
        proven[evidence.objective_key] = evidence.value
    for key, _, expression in objectives:
        if key in proven:
            model.add(expression == proven[key])
    incumbent = replace(incumbent, objectives=tuple(
        replace(e, proof_status='proven') if e.objective_key in proven else e
        for e in incumbent.objectives), unit_upper_bound=coverage_upper)
    return incumbent, proven


def _add_incumbent_hints(model, course_vars, incumbent, control):
    solved = {c.course_id: c for c in incumbent.courses}
    for course_id, variables in course_vars.items():
        control.check()
        course = solved[course_id]
        sessions = {(s.date, s.start_time, s.end_time, s.units,
            s.time_window_id, s.constraint_window_index): s for s in course.sessions}
        matched = set()
        for candidate in variables.candidate_set.candidates:
            control.check()
            signature = (candidate.date, candidate.start_time, candidate.end_time, candidate.units,
                candidate.time_window_id, candidate.constraint_window_index)
            session = sessions.get(signature) if not course.retained_current else None
            if session is not None:
                if session.lecturer_id not in candidate.lecturer_ids or session.room_id not in candidate.room_ids:
                    raise ValueError('Incumbent resources are unavailable')
                matched.add(signature)
            model.add_hint(variables.temporal[candidate.candidate_id], int(session is not None))
            for lecturer in candidate.lecturer_ids:
                model.add_hint(variables.lecturer[candidate.candidate_id, lecturer],
                    int(session is not None and session.lecturer_id == lecturer))
            for room in candidate.room_ids:
                model.add_hint(variables.room[candidate.candidate_id, room],
                    int(session is not None and session.room_id == room))
        if not course.retained_current and matched != set(sessions):
            raise ValueError('Incumbent sessions are not in the prepared model')
        if variables.retain is not None:
            model.add_hint(variables.retain, int(course.retained_current))



def prefer_candidate(candidate, incumbent):
    """Parent-side guard, including checkpoints received at the deadline."""
    if incumbent is None:
        return candidate
    if candidate is None:
        return incumbent
    if [(e.objective_key, e.direction) for e in candidate.objectives] != [
            (e.objective_key, e.direction) for e in incumbent.objectives]:
        return incumbent
    score = lambda result: tuple(-e.value if e.direction == 'max' else e.value for e in result.objectives)
    if score(candidate) > score(incumbent):
        return incumbent
    if score(candidate) == score(incumbent):
        proven = lambda result: sum(e.proof_status == 'proven' for e in result.objectives)
        if proven(candidate) < proven(incumbent):
            return incumbent
    return candidate
