import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    DraftSchedule,
    Room,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    InstitutionHoliday,
    PlanningOutcome,
    ResourceUnavailabilityPeriod,
    ResourceUnavailabilityWeekday,
    ScheduleRevision,
)
from tests.optimization_fixtures import active_exam, past_exam, seed_optimization_planner
from app.services.draft_schedule_repository import get_draft_schedule, load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from datetime import date, time


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture()
def client(db_session):
    def override():
        yield db_session
    app.dependency_overrides[get_db] = override
    with TestClient(app) as value:
        yield value
    app.dependency_overrides.clear()


def generation_payload(prepared):
    return {
        "semesterId": prepared["semesterId"],
        "scheduleRevisionId": prepared["scheduleRevisionId"],
        "unavailableDates": prepared["unavailableDates"],
        "sharedSnapshotToken": prepared["sharedSnapshotToken"],
        "courses": [{
            "courseId": item["courseId"],
            "expectedDraftScheduleId": item["draftScheduleId"],
            "expectedDraftRevision": item["draftRevision"],
            "inputSnapshotToken": item["inputSnapshotToken"],
        } for item in prepared["courses"]],
    }


def test_prepare_deduplicates_dates_and_generate_returns_proven_complete_saved_result(client, db_session):
    seed_optimization_planner(db_session, course_count=2)
    response = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [2, 1], "unavailableDates": ["2026-10-26", "2026-10-26"]})
    assert response.status_code == 200
    prepared = response.json()
    assert prepared["unavailableDates"] == ["2026-10-26"]
    assert [item["courseId"] for item in prepared["courses"]] == [1, 2]
    assert prepared["courses"][0]["effectiveConstraints"]["studyType"] == {
        "id": 1,
        "name": "Full-time",
    }
    assert prepared["courses"][0]["effectiveConstraints"]["allowedTeachingWindows"][0]["sourceTimeWindowId"] == 1

    generated = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    assert generated.status_code == 200
    assert generated.json()["summary"]["complete"] == 2
    assert generated.json()["summary"]["optimalForPreparedSnapshot"] is True
    assert [
        (row.course_id, row.classification)
        for row in db_session.query(PlanningOutcome).order_by(PlanningOutcome.course_id)
    ] == [(1, "successful"), (2, "successful")]


def test_optimizer_api_keeps_caller_dates_unchanged_and_returns_named_holiday_reason(client, db_session):
    seed_optimization_planner(db_session, course_count=1)
    db_session.add_all([
        GenerationConstraintSet(
            course_id=1,
            semester_id=1,
            planning_start_date=date(2026, 9, 7),
            planning_end_date=date(2026, 9, 7),
            windows=[GenerationConstraintWindow(
                source_time_window_id=1,
                weekday=0,
                start_time=time(8),
                end_time=time(12),
                sort_order=1,
            )],
        ),
        InstitutionHoliday(date=date(2026, 9, 7), name="Founders Day"),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": ["2026-10-26"]},
    ).json()

    generated = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))

    assert generated.status_code == 200
    assert prepared["unavailableDates"] == ["2026-10-26"]
    reason = next(item for item in generated.json()["outcomes"][0]["reasons"] if item["code"] == "INSTITUTION_HOLIDAY")
    assert reason["holidayDate"] == "2026-09-07"
    assert reason["holidayName"] == "Founders Day"
    assert reason["relatedCount"] == 1


def test_optimizer_api_rejects_holiday_snapshot_change_without_saving(client, db_session):
    seed_optimization_planner(db_session, course_count=1)
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    db_session.add(InstitutionHoliday(date=date(2026, 9, 7), name="New Closure"))
    db_session.commit()

    generated = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))

    assert generated.status_code == 200
    assert generated.json()["outcomes"][0]["status"] == "stale"
    assert generated.json()["outcomes"][0]["saved"] is False
    assert db_session.query(DraftSchedule).count() == 0
    assert db_session.query(PlanningOutcome).one().classification == "stale"


@pytest.mark.parametrize("course_ids", [[], list(range(1, 22)), [1, 1], [999]])
def test_prepare_rejects_invalid_selection(client, db_session, course_ids):
    seed_optimization_planner(db_session, course_count=1)
    response = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": course_ids, "unavailableDates": []})
    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] in {"INVALID_OPTIMIZATION_SIZE", "DUPLICATE_COURSE_SELECTION", "COURSE_NOT_FOUND"}


def test_prepare_rejects_complete_selection_when_one_course_belongs_to_another_semester(client, db_session):
    seed_optimization_planner(db_session, course_count=2)
    db_session.get(Course, 2).current_semester_id = 2
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1, 2], "unavailableDates": []},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "COURSE_SEMESTER_MISMATCH"
    assert db_session.query(DraftSchedule).count() == 0


def test_prepare_rejects_complete_selection_when_one_course_is_unavailable(client, db_session):
    seed_optimization_planner(db_session, course_count=2)
    db_session.get(Cohort, 2).is_active = False
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1, 2], "unavailableDates": []},
    )

    assert response.status_code == 422
    assert response.json()["errors"][0]["code"] == "COHORT_INACTIVE"
    assert db_session.query(DraftSchedule).count() == 0


def test_existing_draft_returns_non_mutating_post_generation_comparison(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    original = replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1)
    ])
    db_session.get(Course, 1).max_session_units = 2
    db_session.add(GenerationConstraintSet(
        course_id=1,
        semester_id=1,
        planning_start_date=date(2026, 9, 14),
        planning_end_date=date(2026, 9, 14),
        windows=[GenerationConstraintWindow(
            source_time_window_id=1,
            weekday=0,
            start_time=time(8),
            end_time=time(10),
            sort_order=1,
        )],
    ))
    db_session.commit()
    original_revision = original.revision
    original_sessions = [
        (item.date, item.start_time, item.end_time, item.units)
        for item in original.sessions
    ]
    prepared = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []}).json()
    response = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    body = response.json()

    assert response.status_code == 200
    assert body["mode"] == "decision_required"
    assert body["saved"] is False
    assert len(body["candidateFingerprint"]) == 64
    assert body["preparedEvidence"] == generation_payload(prepared)
    assert body["comparison"]["current"] == {
        "requiredUnits": 4,
        "scheduledUnits": 4,
        "remainingUnits": 0,
        "status": "complete",
    }


    assert body["comparison"]["generated"] == {
        "requiredUnits": 4,
        "scheduledUnits": 2,
        "remainingUnits": 2,
        "status": "partial",
    }
    assert {
        item["code"] for item in body["comparison"]["courses"][0]["resolvedCurrentWarnings"]
    } >= {"GENERATION_CONSTRAINT_VIOLATION"}
    current = get_draft_schedule(db_session, 1, 1)
    assert current.revision == original_revision
    assert [
        (item.date, item.start_time, item.end_time, item.units)
        for item in current.sessions
    ] == original_sessions
    assert db_session.query(PlanningOutcome).count() == 0


def test_replacement_with_no_nonempty_alternative_reports_course_specific_blockers(
    client, db_session
):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 14), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db_session.add_all([
        GenerationConstraintSet(
            course_id=1,
            semester_id=1,
            planning_start_date=date(2026, 9, 7),
            planning_end_date=date(2026, 9, 7),
        ),
        InstitutionHoliday(date=date(2026, 9, 7), name="Founders Day"),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    response = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    )

    assert response.status_code == 503
    assert response.json()["code"] == "NO_VALID_ALTERNATIVE"
    assert "Course 1" in response.json()["message"]
    assert "Founders Day" in response.json()["message"]
    assert get_draft_schedule(db_session, 1, 1).revision == 1
    assert db_session.query(PlanningOutcome).count() == 0


def acceptance_payload(preview):
    return {
        **preview["preparedEvidence"],
        "candidateFingerprint": preview["candidateFingerprint"],
    }


def test_accepts_exact_lower_coverage_preview_once_and_retains_only_saved_outcome(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    original = replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1)
    ])
    original_revision = original.revision
    db_session.get(Course, 1).max_session_units = 2
    db_session.add(GenerationConstraintSet(
        course_id=1,
        semester_id=1,
        planning_start_date=date(2026, 9, 14),
        planning_end_date=date(2026, 9, 14),
    ))
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()

    accepted = client.post(
        "/api/draft-schedules/optimization/accept", json=acceptance_payload(preview)
    )

    assert accepted.status_code == 200
    assert accepted.json()["mode"] == "direct_saved"
    assert accepted.json()["outcomes"][0]["saved"] is True
    assert accepted.json()["outcomes"][0]["scheduledUnits"] == 2
    current = get_draft_schedule(db_session, 1, 1)
    assert current.id == original.id
    assert current.revision == original_revision + 1
    assert sum(item.units for item in current.sessions) == 2
    assert db_session.query(PlanningOutcome).one().classification == "successful"

    repeated = client.post(
        "/api/draft-schedules/optimization/accept", json=acceptance_payload(preview)
    )
    assert repeated.status_code == 409
    assert get_draft_schedule(db_session, 1, 1).revision == current.revision
    assert db_session.query(PlanningOutcome).count() == 1


def test_mixed_acceptance_applies_existing_and_unplanned_courses_as_one_result(client, db_session):
    seed_optimization_planner(db_session, course_count=2, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1, 2], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()

    accepted = client.post(
        "/api/draft-schedules/optimization/accept", json=acceptance_payload(preview)
    )

    assert accepted.status_code == 200, accepted.text
    assert {item.course_id for item in db_session.query(DraftSchedule)} == {1, 2}
    assert all(item["saved"] for item in accepted.json()["outcomes"])
    assert db_session.query(PlanningOutcome).count() == 2


def test_acceptance_clears_a_zero_session_course_without_creating_an_empty_draft(
    client, db_session
):
    seed_optimization_planner(db_session, course_count=3, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 14), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    replace_draft_schedule(db_session, load_course_plan(db_session, 3), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1)
    ])
    db_session.add(GenerationConstraintSet(
        course_id=1,
        semester_id=1,
        planning_start_date=date(2026, 9, 7),
        planning_end_date=date(2026, 9, 7),
    ))
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1, 2], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()
    by_course = {
        item["courseId"]: item for item in preview["comparison"]["courses"]
    }
    assert by_course[1]["generated"]["scheduledUnits"] == 0
    assert by_course[2]["generated"]["scheduledUnits"] == 4

    accepted = client.post(
        "/api/draft-schedules/optimization/accept", json=acceptance_payload(preview)
    )

    assert accepted.status_code == 200
    assert get_draft_schedule(db_session, 1, 1) is None
    assert get_draft_schedule(db_session, 2, 1) is not None
    assert db_session.query(DraftSchedule).filter_by(course_id=1).count() == 0


def test_fingerprint_mismatch_rejects_acceptance_without_mutation(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    original = replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()
    payload = acceptance_payload(preview)
    payload["candidateFingerprint"] = "0" * 64

    rejected = client.post("/api/draft-schedules/optimization/accept", json=payload)

    assert rejected.status_code == 409
    assert rejected.json()["errors"][0]["code"] == "CANDIDATE_NOT_REPRODUCIBLE"
    assert get_draft_schedule(db_session, 1, 1).revision == original.revision
    assert db_session.query(PlanningOutcome).count() == 0


@pytest.mark.parametrize("changed_input", [
    "lifecycle",
    "selected_draft",
    "protected_teaching",
    "active_exam",
    "course",
    "constraint",
    "holiday",
    "unavailable_dates",
    "resource_availability",
    "eligibility",
    "capacity",
])
def test_acceptance_rejects_every_material_snapshot_change_without_mutation(
    client, db_session, monkeypatch, changed_input
):
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(service, "institution_today", lambda: date(2026, 9, 1))
    seed_optimization_planner(db_session, course_count=2, total_units=4)
    original = replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()
    payload = acceptance_payload(preview)

    if changed_input == "lifecycle":
        db_session.get(ScheduleRevision, 1).row_version += 1
    elif changed_input == "selected_draft":
        replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
            GeneratedSession(date(2026, 9, 9), time(8), time(9, 40), 2, 1, 0, 1, 1)
        ], existing_draft=original)
    elif changed_input == "protected_teaching":
        replace_draft_schedule(db_session, load_course_plan(db_session, 2), 1, [
            GeneratedSession(date(2026, 9, 8), time(8), time(9, 40), 2, 1, 0, 1, 1)
        ])
    elif changed_input == "active_exam":
        db_session.add(active_exam(exam_id=90, course_id=1, exam_date=date(2026, 10, 5)))
    elif changed_input == "course":
        db_session.get(Course, 1).total_units = 6
        db_session.get(Course, 1).revision += 1
    elif changed_input == "constraint":
        db_session.add(GenerationConstraintSet(
            course_id=1,
            semester_id=1,
            planning_start_date=date(2026, 9, 14),
            planning_end_date=date(2026, 12, 20),
        ))
    elif changed_input == "holiday":
        db_session.add(InstitutionHoliday(date=date(2026, 9, 14), name="New closure"))
    elif changed_input == "unavailable_dates":
        payload["unavailableDates"] = ["2026-10-26"]
    elif changed_input == "resource_availability":
        db_session.add(ResourceUnavailabilityPeriod(
            lecturer_id=1,
            kind="recurring",
            start_time=time(8),
            end_time=time(12),
            weekdays=[ResourceUnavailabilityWeekday(weekday=0)],
        ))
    elif changed_input == "eligibility":
        db_session.query(CourseEligibleLecturer).filter_by(
            course_id=1, lecturer_id=1
        ).delete()
    elif changed_input == "capacity":
        room = db_session.get(Room, 1)
        room.capacity = 1
        room.revision += 1
    db_session.commit()
    revision_before_accept = get_draft_schedule(db_session, 1, 1).revision

    response = client.post("/api/draft-schedules/optimization/accept", json=payload)

    assert response.status_code == 409
    assert response.json()["errors"][0]["code"] == "STALE_PLANNING_INPUT"
    assert get_draft_schedule(db_session, 1, 1).revision == revision_before_accept
    assert db_session.query(PlanningOutcome).count() == 0


def test_past_exam_added_after_preview_does_not_invalidate_acceptance(
    client, db_session, monkeypatch
):
    import app.services.conflict_aware_generation as service

    monkeypatch.setattr(service, "institution_today", lambda: date(2026, 9, 1))
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    preview = client.post(
        "/api/draft-schedules/optimization/generate", json=generation_payload(prepared)
    ).json()
    db_session.add(past_exam(exam_id=91, course_id=1))
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/accept", json=acceptance_payload(preview)
    )

    assert response.status_code == 200
    assert response.json()["outcomes"][0]["saved"] is True


def test_unproven_solver_result_returns_503_and_saves_nothing(client, db_session, monkeypatch):
    seed_optimization_planner(db_session, course_count=1)
    prepared = client.post("/api/draft-schedules/optimization/prepare", json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []}).json()
    from app.services.semester_optimization import OptimalResultNotProven
    import app.services.conflict_aware_generation as service
    monkeypatch.setattr(service, "optimize_semester", lambda *args, **kwargs: (_ for _ in ()).throw(OptimalResultNotProven("not proven")))
    response = client.post("/api/draft-schedules/optimization/generate", json=generation_payload(prepared))
    assert response.status_code == 503
    assert response.json() == {"code": "OPTIMAL_RESULT_NOT_PROVEN", "message": "not proven", "saved": False}


def test_material_change_after_preparation_returns_saved_state_stale_outcome(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()
    room = db_session.get(Room, 1)
    room.capacity = 20
    room.revision += 1
    db_session.commit()

    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )

    assert response.status_code == 200
    assert response.json()["summary"]["stale"] == 1
    assert response.json()["summary"]["optimalForPreparedSnapshot"] is False
    assert response.json()["outcomes"][0]["status"] == "stale"
    assert db_session.query(DraftSchedule).count() == 0


def test_equal_coverage_candidate_is_only_replaced_after_acceptance(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    preview = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )
    assert preview.status_code == 200
    assert preview.json()["mode"] == "decision_required"
    assert get_draft_schedule(db_session, 1, 1).revision == 1
    assert db_session.query(PlanningOutcome).count() == 0

    response = client.post(
        "/api/draft-schedules/optimization/accept",
        json=acceptance_payload(preview.json()),
    )

    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "complete"
    assert response.json()["outcomes"][0]["saved"] is True
    assert get_draft_schedule(db_session, 1, 1).revision == 2
    assert db_session.query(PlanningOutcome).one().classification == "successful"


def test_saved_partial_improvement_is_retained_as_a_successful_completed_result(client, db_session):
    seed_optimization_planner(db_session, course_count=1, total_units=8)
    db_session.add(GenerationConstraintSet(
        course_id=1,
        semester_id=1,
        planning_start_date=date(2026, 9, 7),
        planning_end_date=date(2026, 9, 7),
        windows=[GenerationConstraintWindow(
            source_time_window_id=1,
            weekday=0,
            start_time=time(8),
            end_time=time(12),
            sort_order=1,
        )],
    ))
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )

    assert response.status_code == 200
    assert response.json()["outcomes"][0]["status"] == "improved_partial"
    assert response.json()["outcomes"][0]["saved"] is True
    outcome = db_session.query(PlanningOutcome).one()
    assert outcome.classification == "successful"
    assert outcome.source_status == "improved_partial"


def test_acceptance_replaces_a_current_draft_that_conflicts_with_fixed_teaching(client, db_session):
    seed_optimization_planner(db_session, course_count=2, total_units=4)
    replace_draft_schedule(db_session, load_course_plan(db_session, 1), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    replace_draft_schedule(db_session, load_course_plan(db_session, 2), 1, [
        GeneratedSession(date(2026, 9, 7), time(8), time(11, 30), 4, 1, 0, 1, 1),
    ])
    db_session.commit()
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1], "unavailableDates": []},
    ).json()

    preview = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )
    assert preview.status_code == 200
    assert preview.json()["mode"] == "decision_required"
    assert get_draft_schedule(db_session, 1, 1).revision == 1

    response = client.post(
        "/api/draft-schedules/optimization/accept",
        json=acceptance_payload(preview.json()),
    )
    outcome = response.json()["outcomes"][0]
    current = get_draft_schedule(db_session, 1, 1)

    assert response.status_code == 200
    assert outcome["status"] == "complete" and outcome["saved"] is True
    assert current.revision == 2
    assert current.sessions[0].date != date(2026, 9, 7)


def test_persistence_failure_rolls_back_every_selected_draft_and_outcome(client, db_session, monkeypatch):
    seed_optimization_planner(db_session, course_count=2, total_units=4)
    prepared = client.post(
        "/api/draft-schedules/optimization/prepare",
        json={"semesterId": 1, "scheduleRevisionId": 1, "courseIds": [1, 2], "unavailableDates": []},
    ).json()
    import app.services.conflict_aware_generation as service
    original = service.replace_draft_schedule

    def fail_second(database, course_plan, *args, **kwargs):
        if course_plan.id == 2:
            raise RuntimeError("injected course save failure")
        return original(database, course_plan, *args, **kwargs)

    monkeypatch.setattr(service, "replace_draft_schedule", fail_second)
    response = client.post(
        "/api/draft-schedules/optimization/generate",
        json=generation_payload(prepared),
    )

    assert response.status_code == 500
    assert response.json()["saved"] is False
    assert db_session.query(DraftSchedule).count() == 0
    assert db_session.query(PlanningOutcome).count() == 0
