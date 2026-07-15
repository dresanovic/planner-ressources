from dataclasses import dataclass
from datetime import date, datetime, time

from app.models.planning import ResourceUnavailabilityPeriod


@dataclass(frozen=True)
class ResourceChoice:
    id: int
    normalized_code: str


def assign_resource_sequence(
    choices: list[ResourceChoice],
    feasible_ids_by_session: list[set[int]],
) -> list[int] | None:
    """Choose one resource per session with minimum changes and stable tie-breaks."""
    if not feasible_ids_by_session:
        return []
    choice_key = {choice.id: (choice.normalized_code, choice.id) for choice in choices}
    ordered_ids = [choice.id for choice in sorted(choices, key=lambda item: (item.normalized_code, item.id))]
    if any(not feasible for feasible in feasible_ids_by_session):
        return None

    states: dict[int, tuple[int, tuple[tuple[str, int], ...], tuple[int, ...]]] = {
        resource_id: (0, (choice_key[resource_id],), (resource_id,))
        for resource_id in ordered_ids
        if resource_id in feasible_ids_by_session[0]
    }
    for feasible_ids in feasible_ids_by_session[1:]:
        next_states: dict[int, tuple[int, tuple[tuple[str, int], ...], tuple[int, ...]]] = {}
        for resource_id in ordered_ids:
            if resource_id not in feasible_ids:
                continue
            candidates = [
                (
                    cost + (previous_id != resource_id),
                    path_keys + (choice_key[resource_id],),
                    path_ids + (resource_id,),
                )
                for previous_id, (cost, path_keys, path_ids) in states.items()
            ]
            if candidates:
                next_states[resource_id] = min(candidates, key=lambda item: (item[0], item[1]))
        states = next_states
        if not states:
            return None
    return list(min(states.values(), key=lambda item: (item[0], item[1]))[2])


def intervals_overlap(left_start: datetime, left_end: datetime, right_start: datetime, right_end: datetime) -> bool:
    return left_start < right_end and left_end > right_start


def period_overlaps_session(
    period: ResourceUnavailabilityPeriod,
    session_date: date,
    session_start: time,
    session_end: time,
) -> bool:
    session_start_at = datetime.combine(session_date, session_start)
    session_end_at = datetime.combine(session_date, session_end)
    if period.kind == "recurring":
        if session_date.weekday() not in {item.weekday for item in period.weekdays}:
            return False
        period_start = datetime.combine(session_date, period.start_time)
        period_end = datetime.combine(session_date, period.end_time)
    else:
        period_start = datetime.combine(period.start_date, period.start_time)
        period_end = datetime.combine(period.end_date, period.end_time)
    return intervals_overlap(session_start_at, session_end_at, period_start, period_end)


def resource_is_unavailable(
    periods: list[ResourceUnavailabilityPeriod],
    session_date: date,
    session_start: time,
    session_end: time,
) -> bool:
    return any(
        period_overlaps_session(period, session_date, session_start, session_end)
        for period in periods
    )
