from datetime import date, time, timedelta
from time import monotonic

from app.services.exam_optimization import CandidateInput, Occupancy, build_candidates, select_joint_candidates


def test_reference_generation_is_deterministic_and_under_sixty_seconds():
    started = monotonic()
    semester_start = date(2026, 9, 1)
    teaching_occupancy = tuple(
        Occupancy(
            date=semester_start + timedelta(days=index % 100),
            start_time=time(14),
            end_time=time(15),
            lecturer_id=10_000 + index,
            room_id=20_000 + index,
            cohort_id=30_000 + index,
            session_id=index + 1,
        )
        for index in range(500)
    )
    existing_exam_occupancy = tuple(
        Occupancy(
            date=semester_start + timedelta(days=index % 100),
            start_time=time(16),
            end_time=time(17),
            lecturer_id=40_000 + index,
            room_id=50_000 + index,
            cohort_id=60_000 + index,
            session_id=501 + index,
        )
        for index in range(100)
    )
    reference_occupancy = teaching_occupancy + existing_exam_occupancy
    inputs = {
        course_id: CandidateInput(course_id=course_id, semester_start=semester_start, semester_end=date(2026, 12, 31), final_teaching_date=date(2026, 10, 2), final_teaching_end_time=time(12), recommended_start=date(2026, 10, 9), recommended_end=date(2026, 10, 16), duration_minutes=60, lecturer_id=course_id, cohort_id=course_id, room_ids=(course_id,), start_proposals=tuple((weekday, time(9)) for weekday in range(5)), holidays=frozenset({date(2026, 10, 12)}), fixed_occupancy=reference_occupancy)
        for course_id in range(1, 101)
    }
    candidates = {key: build_candidates(value)[0] for key, value in inputs.items()}
    first, proven = select_joint_candidates(candidates)
    second, proven_again = select_joint_candidates(candidates)
    assert proven and proven_again
    assert first == second
    assert len(first) == 100
    unproven, proven_at_zero_budget = select_joint_candidates(candidates, max_seconds=0.0)
    assert not proven_at_zero_budget
    assert unproven == {}
    assert monotonic() - started < 60
