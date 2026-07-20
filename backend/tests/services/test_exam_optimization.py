from datetime import date, time

from app.services.exam_optimization import CandidateInput, Occupancy, build_candidates, select_joint_candidates


def test_candidates_apply_hard_filters_soft_preference_and_stable_ties():
    spec = CandidateInput(
        course_id=1,
        semester_start=date(2026, 9, 1),
        semester_end=date(2026, 10, 31),
        final_teaching_date=date(2026, 10, 2),
        final_teaching_end_time=time(12),
        recommended_start=date(2026, 10, 9),
        recommended_end=date(2026, 10, 16),
        duration_minutes=120,
        lecturer_id=1,
        cohort_id=1,
        room_ids=(2, 1),
        start_proposals=((0, time(9)), (4, time(9))),
        holidays=frozenset({date(2026, 10, 9)}),
        fixed_occupancy=(Occupancy(date(2026, 10, 12), time(9), time(11), lecturer_id=1, room_id=9, cohort_id=9),),
    )
    candidates, issues = build_candidates(spec)
    assert issues == []
    assert candidates == sorted(candidates, key=lambda item: item.key)
    assert all(item.date != date(2026, 10, 9) for item in candidates)
    selected, proven = select_joint_candidates({1: candidates})
    assert proven is True
    assert selected[1].inside_recommendation is True
    assert selected[1].room_id == 1


def test_empty_start_domain_is_understandable():
    spec = CandidateInput(course_id=1, semester_start=date(2026, 9, 1), semester_end=date(2026, 10, 31), final_teaching_date=date(2026, 10, 2), final_teaching_end_time=time(12), recommended_start=date(2026, 10, 9), recommended_end=date(2026, 10, 16), duration_minutes=120, lecturer_id=1, cohort_id=1, room_ids=(1,), start_proposals=(), holidays=frozenset(), fixed_occupancy=())
    candidates, issues = build_candidates(spec)
    assert candidates == []
    assert issues[0].code == "AUTOMATIC_START_TIME_UNAVAILABLE"


def test_exhausted_domain_preserves_holiday_and_occupancy_evidence():
    holiday_day = date(2026, 10, 5)
    occupied_day = date(2026, 10, 6)
    spec = CandidateInput(
        course_id=1,
        semester_start=holiday_day,
        semester_end=occupied_day,
        final_teaching_date=date(2026, 10, 1),
        final_teaching_end_time=time(12),
        recommended_start=holiday_day,
        recommended_end=occupied_day,
        duration_minutes=60,
        lecturer_id=1,
        cohort_id=1,
        room_ids=(1,),
        start_proposals=((0, time(9)), (1, time(9))),
        holidays=frozenset({holiday_day}),
        fixed_occupancy=(Occupancy(occupied_day, time(9), time(10), lecturer_id=1, room_id=9, cohort_id=9, session_id=42),),
    )

    candidates, issues = build_candidates(spec)

    assert candidates == []
    assert {issue.code for issue in issues} == {"INSTITUTION_HOLIDAY", "LECTURER_OCCUPIED"}
    occupied = next(issue for issue in issues if issue.code == "LECTURER_OCCUPIED")
    assert occupied.related_date == occupied_day
    assert occupied.related_session_id == 42
