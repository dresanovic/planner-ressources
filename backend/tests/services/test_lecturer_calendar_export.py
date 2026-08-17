from __future__ import annotations

import importlib
from datetime import date, datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from icalendar import Calendar
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.services.lecturer_review import issue_lecturer_review_link
from tests.lecturer_calendar_fixtures import (
    CALENDAR_SOURCE_FINGERPRINT_KEY,
    remove_all_assignments,
    reassign_session,
    seed_lecturer_calendar_fixture,
)


@pytest.fixture()
def db(monkeypatch):
    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY",
        CALENDAR_SOURCE_FINGERPRINT_KEY,
    )
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    with Session(engine) as session:
        yield session
    engine.dispose()


def _issue(db: Session, lecturer_id: int = 1):
    fixture = seed_lecturer_calendar_fixture(db)
    result = issue_lecturer_review_link(
        db,
        fixture.review.working_revision_id,
        lecturer_id,
        clock=fixture.clock,
    )
    db.commit()
    return fixture, result.secret


def _session_refs(projection) -> list[str]:
    return [
        session.session_ref
        for course in projection.review.courses
        for session in course.sessions
    ]


def test_confirmed_projection_contains_every_and_only_scoped_mixed_session(db):
    fixture, secret = _issue(db)
    service = importlib.import_module("app.services.lecturer_review")

    projection = service.get_lecturer_calendar_projection(
        db, secret, clock=fixture.clock
    )

    assert projection.revision_id == fixture.review.working_revision_id
    assert projection.revision_created_at is not None
    assert set(_session_refs(projection)) == {
        "teaching:101",
        "teaching:102",
        "teaching:110",
        "teaching:112",
        "teaching:201",
        "teaching:210",
        "teaching:212",
        "exam:401",
        "exam:410",
    }
    assert {session.session_kind for course in projection.review.courses for session in course.sessions} == {
        "teaching",
        "exam",
    }


def test_confirmed_projection_reloads_assignment_additions_and_removals(db):
    fixture, secret = _issue(db)
    service = importlib.import_module("app.services.lecturer_review")
    before = set(
        _session_refs(
            service.get_lecturer_calendar_projection(
                db, secret, clock=fixture.clock
            )
        )
    )

    reassign_session(db, "teaching", 101, 2)
    reassign_session(db, "teaching", 202, 1)
    db.commit()
    after = set(
        _session_refs(
            service.get_lecturer_calendar_projection(
                db, secret, clock=fixture.clock
            )
        )
    )

    assert after == (before - {"teaching:101"}) | {"teaching:202"}


def test_confirmed_projection_accepts_an_explicit_complete_empty_scope(db):
    fixture, secret = _issue(db)
    service = importlib.import_module("app.services.lecturer_review")
    remove_all_assignments(db, fixture.review.primary_lecturer_id)
    db.commit()

    projection = service.get_lecturer_calendar_projection(
        db, secret, clock=fixture.clock
    )

    assert projection.review.courses == []
    assert _session_refs(projection) == []


def test_confirmed_projection_event_membership_ignores_source_order(db, monkeypatch):
    fixture, secret = _issue(db)
    service = importlib.import_module("app.services.lecturer_review")
    expected = set(
        _session_refs(
            service.get_lecturer_calendar_projection(
                db, secret, clock=fixture.clock
            )
        )
    )
    original = service._live_public_courses

    def reversed_courses(*args, **kwargs):
        courses = original(*args, **kwargs)
        for course in courses:
            course["sessions"].reverse()
        courses.reverse()
        return courses

    monkeypatch.setattr(service, "_live_public_courses", reversed_courses)

    reordered = service.get_lecturer_calendar_projection(
        db, secret, clock=fixture.clock
    )
    assert set(_session_refs(reordered)) == expected


def test_distinct_lecturer_link_cannot_project_another_lecturers_sessions(db):
    fixture, secret = _issue(db, lecturer_id=2)
    service = importlib.import_module("app.services.lecturer_review")

    projection = service.get_lecturer_calendar_projection(
        db, secret, clock=fixture.clock
    )

    assert set(_session_refs(projection)) == {
        "teaching:111",
        "teaching:301",
        "teaching:310",
        "teaching:312",
        "exam:403",
        "exam:412",
    }
    assert "teaching:101" not in _session_refs(projection)


def _snapshot(db: Session):
    fixture, secret = _issue(db)
    review_service = importlib.import_module("app.services.lecturer_review")
    export_service = importlib.import_module("app.services.lecturer_calendar_export")
    projection = review_service.get_lecturer_calendar_projection(
        db, secret, clock=fixture.clock
    )
    snapshot = export_service.build_lecturer_calendar(
        projection,
        terminology={
            "schedule.heading": "Terminplanung",
            "course.fieldLabel": "Lehrveranstaltung",
            "cohort.fieldLabel": "Kohorte",
        },
        uid_base_key=b"fs020-test-source-fingerprint-key-material-2026",
    )
    return projection, snapshot


def test_final_profile_has_exact_components_properties_order_and_bounded_lines(db):
    projection, snapshot = _snapshot(db)
    parsed = Calendar.from_ical(snapshot.content)
    components = list(parsed.subcomponents)
    events = [item for item in components if item.name == "VEVENT"]

    assert parsed.get("VERSION") == "2.0"
    assert parsed.get("PRODID") == "-//Resource Planner//Lecturer Calendar Export 1.0//EN"
    assert parsed.get("CALSCALE") == "GREGORIAN"
    assert str(parsed.get("NAME")) == str(parsed.get("X-WR-CALNAME"))
    assert [item.name for item in components].count("VTIMEZONE") == 1
    assert {item.name for item in components} == {"VTIMEZONE", "VEVENT"}
    assert len(events) == snapshot.event_count == len(_session_refs(projection))
    for event in events:
        expected = [
            "UID", "DTSTAMP", "DTSTART", "DTEND", "SUMMARY", "LOCATION",
            "DESCRIPTION", "TRANSP",
        ]
        assert list(event.keys()) == expected
        assert event["TRANSP"] == "OPAQUE"
        assert event["DTSTART"].params["TZID"] == projection.review.time_zone
        assert event["DTEND"].params["TZID"] == projection.review.time_zone
        assert event["DTSTAMP"].dt.microsecond == 0
    assert snapshot.content.endswith(b"END:VCALENDAR\r\n")
    assert not snapshot.content.startswith(b"\xef\xbb\xbf")
    assert all(len(line) <= 75 for line in snapshot.content.split(b"\r\n"))
    assert b"\nMETHOD:" not in snapshot.content
    for forbidden in (b"ORGANIZER", b"ATTENDEE", b"VALARM", b"URL:", b"SEQUENCE"):
        assert forbidden not in snapshot.content


def test_uid_vector_event_order_and_three_run_byte_equality(db):
    projection, first = _snapshot(db)
    service = importlib.import_module("app.services.lecturer_calendar_export")
    assert service.calendar_event_uid(
        b"fs020-test-source-fingerprint-key-material-2026", 2, "teaching", 101
    ) == "0a229f84f6ea9b85ee90f6d4d32d1a1976dd9c364b8f20a3b93e252f928e7cf1@resource-planner.invalid"
    repeated = [
        service.build_lecturer_calendar(
            projection,
            terminology={
                "schedule.heading": "Terminplanung",
                "course.fieldLabel": "Lehrveranstaltung",
                "cohort.fieldLabel": "Kohorte",
            },
            uid_base_key=b"fs020-test-source-fingerprint-key-material-2026",
        )
        for _ in range(2)
    ]
    assert all(item.filename == first.filename and item.content == first.content for item in repeated)
    events = [item for item in Calendar.from_ical(first.content).walk() if item.name == "VEVENT"]
    order = [
        (item["DTSTART"].dt.astimezone(timezone.utc), item["DTEND"].dt.astimezone(timezone.utc), str(item["UID"]))
        for item in events
    ]
    assert order == sorted(order)


def test_synthetic_cross_midnight_missing_location_unicode_and_folding():
    service = importlib.import_module("app.services.lecturer_calendar_export")
    zone = ZoneInfo("Europe/Vienna")
    event = service.CalendarEvent(
        uid=service.calendar_event_uid(b"k" * 32, 7, "exam", 9),
        dtstamp=datetime(2026, 1, 1, 12, 34, 56, 999999, tzinfo=timezone.utc),
        start=datetime(2026, 10, 24, 23, 30, tzinfo=zone),
        end=datetime(2026, 10, 25, 1, 15, tzinfo=zone),
        summary="Prüfung, Teil; A \\ " + ("Ü" * 100),
        location=None,
        description_lines=("Zeile 1", "Zeile 2, mit; Zeichen \\ und\nUmbruch"),
    )
    content = service.serialize_calendar(
        display_name="Terminplanung – Wintersemester – Revision 2",
        time_zone="Europe/Vienna",
        timezone_start=date(2025, 9, 1),
        timezone_end=date(2027, 9, 1),
        events=[event],
    )
    parsed = Calendar.from_ical(content)
    serialized_event = [item for item in parsed.walk() if item.name == "VEVENT"][0]
    assert "LOCATION" not in serialized_event
    assert serialized_event["DTEND"].dt.date() == date(2026, 10, 25)
    assert serialized_event["SUMMARY"] == event.summary
    assert str(serialized_event["DESCRIPTION"]) == "\n".join(event.description_lines)
    assert serialized_event["DTSTAMP"].dt.microsecond == 0
    assert all(len(line) <= 75 for line in content.split(b"\r\n"))


@pytest.mark.parametrize(
    ("segments", "expected"),
    [
        (("  Términ  ", "WS / 2026", "R:2"), "Términ-WS-2026-R-2.ics"),
        (("A--B", "C___", "D..."), "A-B-C-D.ics"),
        (("CON", "x", "y"), "CON-x-y.ics"),
    ],
)
def test_filename_profile(segments, expected):
    service = importlib.import_module("app.services.lecturer_calendar_export")
    assert service.calendar_filename(*segments) == expected


def test_filename_rejects_empty_segment_and_limits_stem_to_180_scalars():
    service = importlib.import_module("app.services.lecturer_calendar_export")
    with pytest.raises(ValueError):
        service.calendar_filename("Terminplanung", "///", "R2")
    value = service.calendar_filename("Ä" * 200, "Semester", "R2")
    assert len(value.removesuffix(".ics")) == 180


def test_display_edits_change_bytes_but_preserve_uid_within_revision(db):
    projection, original = _snapshot(db)
    service = importlib.import_module("app.services.lecturer_calendar_export")
    changed = projection.review.model_copy(deep=True)
    changed.courses[0].title = "Changed display title"
    changed.courses[0].sessions[0].session_type = "Changed display type"
    changed_projection = service.LecturerCalendarProjection(
        review=changed,
        revision_id=projection.revision_id,
        revision_created_at=projection.revision_created_at,
    )
    changed_snapshot = service.build_lecturer_calendar(
        changed_projection,
        terminology={"schedule.heading": "Terminplanung"},
        uid_base_key=b"fs020-test-source-fingerprint-key-material-2026",
    )
    original_uids = {str(item["UID"]) for item in Calendar.from_ical(original.content).walk() if item.name == "VEVENT"}
    changed_uids = {str(item["UID"]) for item in Calendar.from_ical(changed_snapshot.content).walk() if item.name == "VEVENT"}
    assert changed_snapshot.content != original.content
    assert changed_uids == original_uids


def test_add_remove_identical_display_and_cross_revision_uid_behavior(db):
    projection, original = _snapshot(db)
    service = importlib.import_module("app.services.lecturer_calendar_export")
    changed = projection.review.model_copy(deep=True)
    source = changed.courses[0].sessions[0]
    duplicate = source.model_copy(
        update={
            "source_session_id": 9999,
            "session_ref": "teaching:9999",
        }
    )
    changed.courses[0].sessions.append(duplicate)
    changed.courses[-1].sessions.pop()
    changed_projection = service.LecturerCalendarProjection(
        review=changed,
        revision_id=projection.revision_id,
        revision_created_at=projection.revision_created_at,
    )
    changed_snapshot = service.build_lecturer_calendar(
        changed_projection,
        terminology={"schedule.heading": "Terminplanung"},
        uid_base_key=b"fs020-test-source-fingerprint-key-material-2026",
    )
    changed_events = [item for item in Calendar.from_ical(changed_snapshot.content).walk() if item.name == "VEVENT"]
    assert len({str(item["UID"]) for item in changed_events}) == len(changed_events)
    assert changed_snapshot.content != original.content

    other_revision = service.LecturerCalendarProjection(
        review=projection.review,
        revision_id=projection.revision_id + 100,
        revision_created_at=projection.revision_created_at,
    )
    other_snapshot = service.build_lecturer_calendar(
        other_revision,
        terminology={"schedule.heading": "Terminplanung"},
        uid_base_key=b"fs020-test-source-fingerprint-key-material-2026",
    )
    original_uids = {str(item["UID"]) for item in Calendar.from_ical(original.content).walk() if item.name == "VEVENT"}
    other_uids = {str(item["UID"]) for item in Calendar.from_ical(other_snapshot.content).walk() if item.name == "VEVENT"}
    assert original_uids.isdisjoint(other_uids)
