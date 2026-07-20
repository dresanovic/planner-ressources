from datetime import date, time

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.db.schema import initialize_database
from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    ExamSession,
    Lecturer,
    ResourceUnavailabilityPeriod,
    Room,
    Semester,
    StudyType,
)
from app.services.resource_catalog import (
    ResourceCatalogError,
    assess_resource_usage,
    create_resource,
    list_resources,
    reactivate_resource,
    remove_resource,
    update_resource,
    create_unavailability,
    delete_unavailability,
    list_unavailability,
    update_unavailability,
    get_course_resource_configuration,
    replace_course_eligibility,
)
from app.services.exam_scheduling import create_manual_exam, get_exam_planning_overview, save_exam_configuration


@pytest.fixture()
def db():
    engine = create_engine("sqlite://")
    initialize_database(engine)
    with Session(engine) as session:
        yield session


def _add_course(db: Session, lecturer: Lecturer, room: Room, *, active: bool = True) -> Course:
    semester = Semester(name=f"Semester {active}", normalized_name=f"semester {active}", normalized_name_key=f"semester {active}", start_date=date(2026, 9, 1), end_date=date(2026, 12, 20))
    cohort = Cohort(name=f"Cohort {active}", normalized_name=f"cohort {active}", normalized_name_key=f"cohort {active}", student_count=30)
    study_type = StudyType(name=f"Type {active}", normalized_name=f"type {active}", normalized_name_key=f"type {active}")
    db.add_all([semester, cohort, study_type]); db.flush()
    course = Course(name=f"Course {active}", normalized_name=f"course {active}", normalized_name_key=f"course {active}", total_units=4, min_session_units=2, max_session_units=4, cohort_id=cohort.id, study_type_id=study_type.id, current_semester_id=semester.id, is_active=active)
    db.add(course); db.flush()
    db.add_all([CourseEligibleLecturer(course_id=course.id, lecturer_id=lecturer.id), CourseEligibleRoom(course_id=course.id, room_id=room.id)])
    db.flush()
    return course


def _add_saved_session(db: Session, course: Course, lecturer: Lecturer, room: Room) -> None:
    draft = DraftSchedule(course_id=course.id, semester_id=course.current_semester_id, course_name_snapshot=course.name, course_total_units_snapshot=4, course_min_session_units_snapshot=2, course_max_session_units_snapshot=4, cohort_id_snapshot=course.cohort_id, cohort_name_snapshot=course.cohort.name, cohort_size_snapshot=course.cohort.student_count, study_type_id_snapshot=course.study_type_id, study_type_name_snapshot=course.study_type.name, semester_name_snapshot=course.current_semester.name, semester_start_date_snapshot=course.current_semester.start_date, semester_end_date_snapshot=course.current_semester.end_date)
    db.add(draft); db.flush()
    db.add(DraftSession(draft_schedule_id=draft.id, course_id=course.id, lecturer_id=lecturer.id, cohort_id=course.cohort_id, room_id=room.id, date=date(2026, 9, 7), start_time=time(8), end_time=time(10), units=2, constraint_window_index=0))
    db.flush()


def test_exam_history_forces_resource_inactivation_and_is_preserved(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    room, _ = create_resource(db, Room, name="Room", reference_code="R", capacity=60)
    course = _add_course(db, lecturer, room)
    _add_saved_session(db, course, lecturer, room)
    state, _ = save_exam_configuration(db, course_id=course.id, semester_id=course.current_semester_id, enabled=True, expected_revision=None, configuration={"identifier": "Exam", "duration_minutes": 60, "recommended_start_override": None, "recommended_end_override": None, "required_capacity": 40, "exam_type": "Written", "responsible_lecturer_id": lecturer.id}, today=date(2026, 9, 1))
    create_manual_exam(db, course_id=course.id, semester_id=course.current_semester_id, exam_date=date(2026, 9, 21), start_time=time(12), lecturer_id=lecturer.id, room_id=room.id, expected_configuration_revision=1, input_snapshot_token=state["inputSnapshotToken"], today=date(2026, 9, 1))
    db.flush()
    lecturer_usage = assess_resource_usage(db, lecturer)
    room_usage = assess_resource_usage(db, room)
    assert lecturer_usage["disposition"] == "inactivate"
    assert room_usage["disposition"] == "inactivate"
    assert lecturer_usage["examUsage"] == {"examSessionCount": 1, "currentConfigurationCount": 1}
    assert room_usage["examUsage"] == {"examSessionCount": 1, "currentConfigurationCount": 0}
    exam_id = db.query(ExamSession.id).scalar()
    remove_resource(db, lecturer, expected_revision=lecturer.revision, confirmed=True)
    assert db.get(ExamSession, exam_id) is not None


def test_create_allows_duplicate_names_but_rejects_normalized_code_and_invalid_fields(db):
    first, _ = create_resource(db, Lecturer, name="Ada", reference_code=" LECT-ADA ")
    second, _ = create_resource(db, Lecturer, name="Ada", reference_code="LECT-ADA-2")
    assert (first.name, first.reference_code, first.normalized_reference_code) == ("Ada", "LECT-ADA", "lect-ada")
    assert second.name == first.name
    with pytest.raises(ResourceCatalogError) as duplicate:
        create_resource(db, Lecturer, name="Other", reference_code="lect-ADA")
    assert duplicate.value.status_code == 409
    assert duplicate.value.errors[0].code == "DUPLICATE_REFERENCE_CODE"
    with pytest.raises(ResourceCatalogError) as invalid:
        create_resource(db, Room, name=" ", reference_code=" ", capacity=0)
    assert {error.field for error in invalid.value.errors} == {"name", "referenceCode", "capacity"}


def test_list_defaults_active_searches_name_and_code_and_paginates(db):
    create_resource(db, Lecturer, name="Ada Lovelace", reference_code="AL-1")
    inactive, _ = create_resource(db, Lecturer, name="Grace Hopper", reference_code="GH-1")
    inactive.is_active = False
    rows, total = list_resources(db, Lecturer, status="active", query="al-", page=1, page_size=10)
    assert total == 1 and [row.name for row in rows] == ["Ada Lovelace"]
    rows, total = list_resources(db, Lecturer, status="inactive", query="hopper", page=1, page_size=10)
    assert total == 1 and rows[0] is inactive


def test_updates_are_revisioned_and_room_capacity_impacts_are_reported(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    room, _ = create_resource(db, Room, name="Large", reference_code="R", capacity=40)
    course = _add_course(db, lecturer, room)
    room, impacts = update_resource(db, room, name="Smaller", reference_code="R", capacity=20, expected_revision=1)
    assert room.revision == 2 and room.capacity == 20
    assert impacts == [{"course": {"id": course.id, "name": course.name}, "resourceId": room.id, "usable": False, "reasons": ["INSUFFICIENT_CAPACITY"]}]
    with pytest.raises(ResourceCatalogError) as stale:
        update_resource(db, room, name="Stale", reference_code="R", capacity=50, expected_revision=1)
    assert stale.value.errors[0].meta["currentRevision"] == 2


def test_concurrent_resource_update_cannot_overwrite_newer_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'resource-concurrency.db'}")
    initialize_database(engine)
    with Session(engine) as setup:
        resource, _ = create_resource(setup, Lecturer, name="Initial", reference_code="L-1")
        setup.commit()
        resource_id = resource.id

    with Session(engine) as first, Session(engine) as second:
        first_copy = first.get(Lecturer, resource_id)
        second_copy = second.get(Lecturer, resource_id)
        update_resource(first, first_copy, name="Planner A", reference_code="L-1", expected_revision=1)
        first.commit()

        with pytest.raises(StaleDataError):
            update_resource(second, second_copy, name="Planner B", reference_code="L-1", expected_revision=1)
        second.rollback()

    with Session(engine) as verify:
        saved = verify.get(Lecturer, resource_id)
        assert (saved.name, saved.revision) == ("Planner A", 2)


def test_concurrent_availability_update_cannot_overwrite_newer_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'availability-concurrency.db'}")
    initialize_database(engine)
    with Session(engine) as setup:
        lecturer, _ = create_resource(setup, Lecturer, name="Ada", reference_code="L-1")
        period = create_unavailability(setup, lecturer, kind="recurring", weekdays=[0], start_time_value="08:00", end_time_value="10:00")
        setup.commit()
        lecturer_id, period_id = lecturer.id, period.id

    with Session(engine) as first, Session(engine) as second:
        first_owner = first.get(Lecturer, lecturer_id)
        second_owner = second.get(Lecturer, lecturer_id)
        second_period = second.get(ResourceUnavailabilityPeriod, period_id)
        assert second_period.revision == 1
        update_unavailability(first, first_owner, period_id, expected_revision=1, kind="recurring", weekdays=[1], start_time_value="08:00", end_time_value="10:00")
        first.commit()

        with pytest.raises(StaleDataError):
            update_unavailability(second, second_owner, period_id, expected_revision=1, kind="recurring", weekdays=[2], start_time_value="08:00", end_time_value="10:00")
        second.rollback()

    with Session(engine) as verify:
        saved = verify.get(ResourceUnavailabilityPeriod, period_id)
        assert saved.revision == 2
        assert [item.weekday for item in saved.weekdays] == [1]


def test_concurrent_eligibility_update_cannot_overwrite_newer_revision(tmp_path):
    engine = create_engine(f"sqlite:///{tmp_path / 'eligibility-concurrency.db'}")
    initialize_database(engine)
    with Session(engine) as setup:
        first_lecturer, _ = create_resource(setup, Lecturer, name="Ada", reference_code="L-1")
        second_lecturer, _ = create_resource(setup, Lecturer, name="Grace", reference_code="L-2")
        room, _ = create_resource(setup, Room, name="Room", reference_code="R-1", capacity=40)
        course = _add_course(setup, first_lecturer, room)
        setup.commit()
        course_id = course.id
        first_lecturer_id, second_lecturer_id, room_id = first_lecturer.id, second_lecturer.id, room.id

    with Session(engine) as first, Session(engine) as second:
        first_course = first.get(Course, course_id)
        second_course = second.get(Course, course_id)
        list(first_course.eligible_lecturers); list(first_course.eligible_rooms)
        list(second_course.eligible_lecturers); list(second_course.eligible_rooms)
        replace_course_eligibility(first, first_course, expected_revision=1, lecturer_ids=[second_lecturer_id], room_ids=[room_id])
        first.commit()

        with pytest.raises(StaleDataError):
            replace_course_eligibility(second, second_course, expected_revision=1, lecturer_ids=[first_lecturer_id], room_ids=[room_id])
        second.rollback()

    with Session(engine) as verify:
        saved = verify.get(Course, course_id)
        assert saved.revision == 2
        assert [item.lecturer_id for item in saved.eligible_lecturers] == [second_lecturer_id]


def test_unprotected_resource_deletes_and_cleans_only_inactive_course_links(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    room, _ = create_resource(db, Room, name="Room", reference_code="R", capacity=40)
    course = _add_course(db, lecturer, room, active=False)
    assessment = assess_resource_usage(db, lecturer)
    assert assessment["disposition"] == "delete"
    result = remove_resource(db, lecturer, expected_revision=1, confirmed=True)
    assert result == {"outcome": "deleted", "resourceId": lecturer.id, "removedInactiveCourseLinks": [{"id": course.id, "name": course.name}]}
    assert db.get(Lecturer, lecturer.id) is None


def test_active_course_or_saved_session_inactivates_and_preserves_every_assignment(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    room, _ = create_resource(db, Room, name="Room", reference_code="R", capacity=40)
    course = _add_course(db, lecturer, room)
    _add_saved_session(db, course, lecturer, room)
    assessment = assess_resource_usage(db, lecturer)
    assert assessment["disposition"] == "inactivate"
    assert assessment["activeCourses"] == [{"id": course.id, "name": course.name}]
    assert assessment["sessionUsage"] == {"draftSessionCount": 1, "draftScheduleCount": 1}
    result = remove_resource(db, lecturer, expected_revision=1, confirmed=True)
    assert result["outcome"] == "inactivated"
    assert result["resource"].is_active is False and result["resource"].revision == 2
    assert db.query(DraftSession).one().lecturer_id == lecturer.id
    assert db.get(CourseEligibleLecturer, (course.id, lecturer.id)) is not None


def test_removal_requires_confirmation_and_reactivation_reports_relationship_usability(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    room, _ = create_resource(db, Room, name="Small", reference_code="R", capacity=20)
    course = _add_course(db, lecturer, room)
    with pytest.raises(ResourceCatalogError) as unconfirmed:
        remove_resource(db, lecturer, expected_revision=1, confirmed=False)
    assert unconfirmed.value.status_code == 409
    removed = remove_resource(db, room, expected_revision=1, confirmed=True)
    assert removed["outcome"] == "inactivated"
    result = reactivate_resource(db, room, expected_revision=2)
    assert result["resource"].is_active is True
    assert result["restoredRelationships"] == []
    assert result["unusableRelationships"][0]["reasons"] == ["INSUFFICIENT_CAPACITY"]


def test_recurring_and_dated_unavailability_crud_is_revisioned_and_canonical(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    recurring_period = create_unavailability(db, lecturer, kind="recurring", weekdays=[2, 0, 2], start_time_value="09:00", end_time_value="11:00")
    dated_period = create_unavailability(db, lecturer, kind="dated", start_date_value="2026-09-07", end_date_value="2026-09-08", start_time_value="15:00", end_time_value="10:00")
    assert [weekday.weekday for weekday in recurring_period.weekdays] == [0, 2]
    assert [period.id for period in list_unavailability(db, lecturer)] == [recurring_period.id, dated_period.id]
    changed = update_unavailability(db, lecturer, recurring_period.id, expected_revision=1, kind="recurring", weekdays=[1], start_time_value="10:00", end_time_value="12:00")
    assert changed.revision == 2 and [weekday.weekday for weekday in changed.weekdays] == [1]
    delete_unavailability(db, lecturer, dated_period.id, expected_revision=1)
    assert [period.id for period in list_unavailability(db, lecturer)] == [recurring_period.id]


def test_unavailability_rejects_invalid_shapes_duplicates_stale_writes_and_wrong_owner(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    other, _ = create_resource(db, Lecturer, name="Grace", reference_code="G")
    period = create_unavailability(db, lecturer, kind="recurring", weekdays=[0], start_time_value="09:00", end_time_value="11:00")
    with pytest.raises(ResourceCatalogError) as duplicate:
        create_unavailability(db, lecturer, kind="recurring", weekdays=[0], start_time_value="09:00", end_time_value="11:00")
    assert duplicate.value.errors[0].code == "DUPLICATE_UNAVAILABILITY"
    with pytest.raises(ResourceCatalogError) as invalid:
        create_unavailability(db, lecturer, kind="recurring", weekdays=[], start_time_value="11:00", end_time_value="09:00")
    assert {error.field for error in invalid.value.errors} == {"weekdays", "endTime"}
    with pytest.raises(ResourceCatalogError) as stale:
        update_unavailability(db, lecturer, period.id, expected_revision=99, kind="recurring", weekdays=[1], start_time_value="09:00", end_time_value="11:00")
    assert stale.value.errors[0].code == "STALE_REVISION"
    with pytest.raises(ResourceCatalogError) as wrong_owner:
        delete_unavailability(db, other, period.id, expected_revision=1)
    assert wrong_owner.value.status_code == 404


def test_course_configuration_exposes_multiple_coded_candidates_and_fixed_preferences(db):
    first, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    second, _ = create_resource(db, Lecturer, name="Grace", reference_code="G")
    room, _ = create_resource(db, Room, name="Room", reference_code="R", capacity=40)
    course = _add_course(db, first, room)
    configuration = replace_course_eligibility(db, course, expected_revision=1, lecturer_ids=[first.id, second.id], room_ids=[room.id])
    assert configuration["courseRevision"] == 2
    assert configuration["eligibleLecturerIds"] == [first.id, second.id]
    assert configuration["preferences"] == {"minimizeLecturerChanges": True, "minimizeRoomChanges": True}
    candidates = get_course_resource_configuration(db, course)["lecturerCandidates"]
    assert [(item["referenceCode"], item["isEligible"], item["isUsable"]) for item in candidates] == [("A", True, True), ("G", True, True)]


def test_atomic_eligibility_replacement_rejects_duplicates_inactive_capacity_last_and_stale(db):
    lecturer, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    inactive, _ = create_resource(db, Lecturer, name="Inactive", reference_code="I")
    inactive.is_active = False
    room, _ = create_resource(db, Room, name="Room", reference_code="R", capacity=40)
    small, _ = create_resource(db, Room, name="Small", reference_code="S", capacity=20)
    course = _add_course(db, lecturer, room)
    cases = [
        ({"lecturer_ids": [], "room_ids": [room.id]}, "lecturerIds"),
        ({"lecturer_ids": [lecturer.id, lecturer.id], "room_ids": [room.id]}, "lecturerIds"),
        ({"lecturer_ids": [inactive.id], "room_ids": [room.id]}, "lecturerIds"),
        ({"lecturer_ids": [lecturer.id], "room_ids": [small.id]}, "roomIds"),
    ]
    for values, field in cases:
        with pytest.raises(ResourceCatalogError) as failure:
            replace_course_eligibility(db, course, expected_revision=1, **values)
        assert any(error.field == field for error in failure.value.errors)
        assert [item.lecturer_id for item in course.eligible_lecturers] == [lecturer.id]
        assert [item.room_id for item in course.eligible_rooms] == [room.id]
    with pytest.raises(ResourceCatalogError) as stale:
        replace_course_eligibility(db, course, expected_revision=99, lecturer_ids=[lecturer.id], room_ids=[room.id])
    assert stale.value.errors[0].code == "STALE_REVISION"


def test_relationship_removal_preserves_used_draft_session_assignment(db):
    first, _ = create_resource(db, Lecturer, name="Ada", reference_code="A")
    second, _ = create_resource(db, Lecturer, name="Grace", reference_code="G")
    first_room, _ = create_resource(db, Room, name="R1", reference_code="R1", capacity=40)
    second_room, _ = create_resource(db, Room, name="R2", reference_code="R2", capacity=40)
    course = _add_course(db, first, first_room)
    replace_course_eligibility(db, course, expected_revision=1, lecturer_ids=[first.id, second.id], room_ids=[first_room.id, second_room.id])
    _add_saved_session(db, course, first, first_room)
    replace_course_eligibility(db, course, expected_revision=2, lecturer_ids=[second.id], room_ids=[second_room.id])
    session = db.query(DraftSession).one()
    assert (session.lecturer_id, session.room_id) == (first.id, first_room.id)
