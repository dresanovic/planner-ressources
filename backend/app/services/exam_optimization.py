from dataclasses import dataclass
from datetime import date, datetime, time, timedelta

from ortools.sat.python import cp_model

from app.services.resource_rules import intervals_overlap


@dataclass(frozen=True)
class OptimizationIssue:
    code: str
    message: str
    related_date: date | None = None
    related_resource_kind: str | None = None
    related_resource_id: int | None = None
    related_session_id: int | None = None


@dataclass(frozen=True)
class Occupancy:
    date: date
    start_time: time
    end_time: time
    lecturer_id: int
    room_id: int
    cohort_id: int
    session_id: int | None = None


@dataclass(frozen=True)
class CandidateInput:
    course_id: int
    semester_start: date
    semester_end: date
    final_teaching_date: date
    final_teaching_end_time: time
    recommended_start: date
    recommended_end: date
    duration_minutes: int
    lecturer_id: int
    cohort_id: int
    room_ids: tuple[int, ...]
    start_proposals: tuple[tuple[int, time], ...]
    holidays: frozenset[date]
    fixed_occupancy: tuple[Occupancy, ...]


@dataclass(frozen=True)
class ExamCandidate:
    course_id: int
    date: date
    start_time: time
    end_time: time
    lecturer_id: int
    room_id: int
    cohort_id: int
    inside_recommendation: bool
    key: tuple


def build_candidates(spec: CandidateInput) -> tuple[list[ExamCandidate], list[OptimizationIssue]]:
    if not spec.start_proposals:
        return [], [OptimizationIssue("AUTOMATIC_START_TIME_UNAVAILABLE", "No active Study Type time-window start is available for automatic placement.")]
    candidates: list[ExamCandidate] = []
    blocked: list[OptimizationIssue] = []
    day = max(spec.semester_start, spec.final_teaching_date)
    proposals = sorted(set(spec.start_proposals), key=lambda item: (item[0], item[1]))
    rooms = sorted(set(spec.room_ids))
    while day <= spec.semester_end:
        day_proposals = [start for weekday, start in proposals if day.weekday() == weekday]
        if day in spec.holidays and day_proposals:
            blocked.append(OptimizationIssue("INSTITUTION_HOLIDAY", "The exam date is an institution holiday.", related_date=day))
            day += timedelta(days=1)
            continue
        for start in day_proposals:
            start_at = datetime.combine(day, start)
            end_at = start_at + timedelta(minutes=spec.duration_minutes)
            if end_at.date() != day:
                blocked.append(OptimizationIssue("INVALID_EXAM_INTERVAL", "The configured duration would make the exam cross midnight.", related_date=day))
                continue
            end = end_at.time()
            if day == spec.final_teaching_date and start < spec.final_teaching_end_time:
                blocked.append(OptimizationIssue("BEFORE_FINAL_TEACHING", "The automatic start is before the final teaching session ends.", related_date=day))
                continue
            for room_id in rooms:
                candidate = ExamCandidate(
                    course_id=spec.course_id,
                    date=day,
                    start_time=start,
                    end_time=end,
                    lecturer_id=spec.lecturer_id,
                    room_id=room_id,
                    cohort_id=spec.cohort_id,
                    inside_recommendation=spec.recommended_start <= day <= spec.recommended_end,
                    key=(day, start, room_id),
                )
                conflicts = [fixed for fixed in spec.fixed_occupancy if _candidate_conflicts_occupancy(candidate, fixed)]
                if conflicts:
                    for fixed in conflicts:
                        blocked.extend(_occupancy_issues(candidate, fixed))
                else:
                    candidates.append(candidate)
        day += timedelta(days=1)
    candidates.sort(key=lambda item: item.key)
    if not candidates:
        return [], _unique_issues(blocked) or [OptimizationIssue("NO_VALID_EXAM_PLACEMENT", "No placement satisfies the exam hard constraints.")]
    return candidates, []


def select_joint_candidates(candidates_by_course: dict[int, list[ExamCandidate]], *, max_seconds: float = 55.0) -> tuple[dict[int, ExamCandidate], bool]:
    model = cp_model.CpModel()
    variables: dict[tuple[int, int], cp_model.IntVar] = {}
    for course_id, candidates in sorted(candidates_by_course.items()):
        course_vars = []
        for index, _candidate in enumerate(candidates):
            variable = model.new_bool_var(f"exam_{course_id}_{index}")
            variables[(course_id, index)] = variable
            course_vars.append(variable)
        if course_vars:
            model.add(sum(course_vars) <= 1)

    entries = [
        (course_id, index, candidate, variables[(course_id, index)])
        for course_id, candidates in sorted(candidates_by_course.items())
        for index, candidate in enumerate(candidates)
    ]
    grouped: dict[tuple, list[tuple[int, int, ExamCandidate, cp_model.IntVar]]] = {}
    for entry in entries:
        candidate = entry[2]
        for key in ((candidate.date, "lecturer", candidate.lecturer_id), (candidate.date, "room", candidate.room_id), (candidate.date, "cohort", candidate.cohort_id)):
            grouped.setdefault(key, []).append(entry)
    seen: set[tuple[int, int, int, int]] = set()
    for group in grouped.values():
        for left_index, left in enumerate(group):
            for right in group[left_index + 1 :]:
                if left[0] == right[0]:
                    continue
                pair = (left[0], left[1], right[0], right[1])
                reverse = (right[0], right[1], left[0], left[1])
                if pair in seen or reverse in seen:
                    continue
                if _candidate_conflicts(left[2], right[2]):
                    model.add(left[3] + right[3] <= 1)
                    seen.add(pair)
    objective = []
    for course_id, index, candidate, variable in entries:
        canonical_penalty = index + 1
        score = 1_000_000_000 + (1_000_000 if candidate.inside_recommendation else 0) - canonical_penalty
        objective.append(score * variable)
    model.maximize(sum(objective))
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = max_seconds
    solver.parameters.num_search_workers = 1
    solver.parameters.random_seed = 0
    status = solver.solve(model)
    if status != cp_model.OPTIMAL:
        return {}, False
    selected = {
        course_id: candidates_by_course[course_id][index]
        for (course_id, index), variable in variables.items()
        if solver.value(variable)
    }
    return selected, True


def _candidate_conflicts_occupancy(candidate: ExamCandidate, occupancy: Occupancy) -> bool:
    if candidate.date != occupancy.date:
        return False
    shares = candidate.lecturer_id == occupancy.lecturer_id or candidate.room_id == occupancy.room_id or candidate.cohort_id == occupancy.cohort_id
    return shares and intervals_overlap(
        datetime.combine(candidate.date, candidate.start_time),
        datetime.combine(candidate.date, candidate.end_time),
        datetime.combine(occupancy.date, occupancy.start_time),
        datetime.combine(occupancy.date, occupancy.end_time),
    )


def _occupancy_issues(candidate: ExamCandidate, occupancy: Occupancy) -> list[OptimizationIssue]:
    if not _candidate_conflicts_occupancy(candidate, occupancy):
        return []
    common = {"related_date": candidate.date, "related_session_id": occupancy.session_id}
    issues = []
    if candidate.lecturer_id == occupancy.lecturer_id:
        issues.append(OptimizationIssue("LECTURER_OCCUPIED", "The responsible lecturer is occupied by another teaching or exam session.", related_resource_kind="lecturer", related_resource_id=candidate.lecturer_id, **common))
    if candidate.room_id == occupancy.room_id:
        issues.append(OptimizationIssue("ROOM_OCCUPIED", "The room is occupied by another teaching or exam session.", related_resource_kind="room", related_resource_id=candidate.room_id, **common))
    if candidate.cohort_id == occupancy.cohort_id:
        issues.append(OptimizationIssue("COHORT_OCCUPIED", "The cohort is occupied by another teaching or exam session.", **common))
    return issues


def _unique_issues(issues: list[OptimizationIssue]) -> list[OptimizationIssue]:
    result = []
    seen = set()
    for issue in issues:
        key = (issue.code, issue.related_resource_kind, issue.related_resource_id)
        if key not in seen:
            seen.add(key)
            result.append(issue)
    return result


def _candidate_conflicts(left: ExamCandidate, right: ExamCandidate) -> bool:
    if left.date != right.date:
        return False
    shares = left.lecturer_id == right.lecturer_id or left.room_id == right.room_id or left.cohort_id == right.cohort_id
    return shares and intervals_overlap(
        datetime.combine(left.date, left.start_time),
        datetime.combine(left.date, left.end_time),
        datetime.combine(right.date, right.start_time),
        datetime.combine(right.date, right.end_time),
    )
