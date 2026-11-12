import pytest


def test_window_concurrent_edits_cannot_silently_overwrite_and_duplicates_rollback():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session
    from sqlalchemy.orm.exc import StaleDataError
    from app.db.schema import initialize_database
    from app.models.planning import CohortCalendarTimeWindow
    from app.services.academic_catalog import create_time_window, update_time_window
    from tests.fixtures.dated_intensive_windows import seed_forms
    engine = create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        seed_forms(db)
        row = create_time_window(db,1,kind='dated',date='2026-11-09',start_time='09:00',end_time='12:00')
        db.commit()
        row_id = row.id
    with Session(engine) as first, Session(engine) as second:
        one, two = first.get(CohortCalendarTimeWindow,row_id), second.get(CohortCalendarTimeWindow,row_id)
        update_time_window(first,one,kind='dated',date='2026-11-09',start_time='09:00',end_time='13:00',expected_revision=1)
        first.commit()
        with pytest.raises(StaleDataError):
            update_time_window(second,two,kind='dated',date='2026-11-09',start_time='09:00',end_time='14:00',expected_revision=1)
        second.rollback()
        assert second.get(CohortCalendarTimeWindow,row_id).end_time.hour == 13
        with pytest.raises(AcademicCatalogError) as duplicate:
            create_time_window(second,1,kind='dated',date='2026-11-09',start_time='09:00',end_time='13:00',is_intensive=True)
        second.rollback()
        assert duplicate.value.status_code == 409
        assert second.query(CohortCalendarTimeWindow).count() == 1

from app.services.academic_catalog import (
    AcademicCatalogError,
    course_availability_reasons,
    normalize_name,
    validate_course_units,
)


@pytest.mark.parametrize('preferred', [1, 5, 2.25, float('inf'), float('nan'), True])
def test_preferred_session_units_must_be_in_range_whole_or_half(preferred):
    with pytest.raises(AcademicCatalogError):
        validate_course_units(8, 2, 4, preferred)


@pytest.mark.parametrize('preferred', [None, 2, 3, 3.5, 4])
def test_valid_optional_preferred_session_units(preferred):
    validate_course_units(8, 2, 4, preferred)


def test_normalize_name_trims_and_casefolds_unicode():
    assert normalize_name("  STRASSE  ") == "strasse"
    assert normalize_name("  Straße  ") == "strasse"


@pytest.mark.parametrize(
    ("total", "minimum", "maximum"),
    [(0, 1, 1), (4, 0, 2), (4, 3, 2), (4, 2, 5)],
)
def test_course_unit_validation_returns_uniform_field_errors(total, minimum, maximum):
    with pytest.raises(AcademicCatalogError) as exc_info:
        validate_course_units(total, minimum, maximum)
    assert exc_info.value.status_code == 422
    assert exc_info.value.errors
    assert all(error.code == "VALIDATION_ERROR" for error in exc_info.value.errors)


def test_course_unit_validation_has_no_artificial_upper_limit():
    validate_course_units(10**12, 1, 10**12)


def test_missing_window_is_visible_but_unavailable():
    reasons = course_availability_reasons(
        course_active=True,
        semester_assigned=True,
        semester_active=True,
        cohort_active=True,
        cohort_calendar_active=True,
        has_active_window=False,
        resources_valid=True,
    )
    assert reasons == ["MISSING_ACTIVE_TIME_WINDOW"]


def test_inactive_parent_reasons_are_categorized():
    reasons = course_availability_reasons(
        course_active=True,
        semester_assigned=True,
        semester_active=False,
        cohort_active=False,
        cohort_calendar_active=False,
        has_active_window=False,
        resources_valid=True,
    )
    assert reasons == [
        "SEMESTER_INACTIVE",
        "COHORT_INACTIVE",
        "COHORT_CALENDAR_INACTIVE",
        "MISSING_ACTIVE_TIME_WINDOW",
    ]
