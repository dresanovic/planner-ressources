from datetime import date, timedelta

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.services.holiday_calendar import (
    HolidayCalendarError,
    create_holiday,
    delete_holiday,
    holiday_snapshot,
    list_holidays,
    update_holiday,
)


@pytest.fixture()
def db():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    session = sessionmaker(bind=engine)()
    try:
        yield session
    finally:
        session.close()


def test_crud_is_sorted_revisioned_and_current_state_only(db):
    later = create_holiday(db, day=date(2027, 1, 1), name=" New Year ")
    earlier = create_holiday(db, day=date(2024, 2, 29), name="Leap Day")
    db.commit()
    assert [item.id for item in list_holidays(db)] == [earlier.id, later.id]
    changed = update_holiday(
        db,
        earlier.id,
        day=date(2026, 12, 24),
        name=" Winter Break ",
        expected_revision=1,
    )
    db.commit()
    assert (changed.date, changed.name, changed.revision) == (date(2026, 12, 24), "Winter Break", 2)
    delete_holiday(db, later.id, expected_revision=1, confirmed=True)
    db.commit()
    assert [(item.date, item.name) for item in list_holidays(db)] == [(date(2026, 12, 24), "Winter Break")]


def test_inclusive_range_and_snapshot_are_canonical(db):
    for offset in range(3):
        create_holiday(db, day=date(2026, 12, 24) + timedelta(days=offset), name=f"Holiday {offset}")
    db.commit()
    rows = list_holidays(db, start_date=date(2026, 12, 25), end_date=date(2026, 12, 26))
    assert [row.date for row in rows] == [date(2026, 12, 25), date(2026, 12, 26)]
    snapshot = holiday_snapshot(db, date(2026, 12, 25), date(2026, 12, 26))
    assert snapshot.by_date[date(2026, 12, 25)].name == "Holiday 1"
    assert len(snapshot.entries) == 2
    assert snapshot.token


@pytest.mark.parametrize("name", ["", "   ", "x" * 201])
def test_invalid_names_are_rejected_without_partial_change(db, name):
    with pytest.raises(HolidayCalendarError) as raised:
        create_holiday(db, day=date(2026, 12, 25), name=name)
    assert raised.value.status_code == 422
    assert list_holidays(db) == []


def test_duplicate_and_stale_changes_are_rejected(db):
    first = create_holiday(db, day=date(2026, 12, 24), name="First")
    second = create_holiday(db, day=date(2026, 12, 25), name="Second")
    db.commit()
    with pytest.raises(HolidayCalendarError) as duplicate:
        update_holiday(db, second.id, day=first.date, name="Collision", expected_revision=1)
    assert duplicate.value.status_code == 409
    update_holiday(db, second.id, day=second.date, name="Current", expected_revision=1)
    db.commit()
    with pytest.raises(HolidayCalendarError) as stale:
        delete_holiday(db, second.id, expected_revision=1, confirmed=True)
    assert stale.value.errors[0].code == "STALE_REVISION"


def test_delete_requires_confirmation(db):
    row = create_holiday(db, day=date(2026, 12, 25), name="Holiday")
    db.commit()
    with pytest.raises(HolidayCalendarError) as raised:
        delete_holiday(db, row.id, expected_revision=1, confirmed=False)
    assert raised.value.errors[0].code == "CONFIRMATION_REQUIRED"


def test_name_boundary_and_fifty_holiday_listing(db):
    boundary = create_holiday(db, day=date(2024, 2, 29), name="x" * 200)
    for offset in range(1, 50):
        create_holiday(
            db,
            day=date(2026, 1, 1) + timedelta(days=offset),
            name=f"Holiday {offset}",
        )
    db.commit()

    rows = list_holidays(db)

    assert len(rows) == 50
    assert boundary.name == "x" * 200
    assert rows == sorted(rows, key=lambda item: (item.date, item.id))
