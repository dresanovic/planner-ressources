import pytest

from app.services.academic_catalog import (
    AcademicCatalogError,
    course_availability_reasons,
    normalize_name,
    validate_course_units,
)


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
        study_type_active=True,
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
        study_type_active=False,
        has_active_window=False,
        resources_valid=True,
    )
    assert reasons == [
        "SEMESTER_INACTIVE",
        "COHORT_INACTIVE",
        "STUDY_TYPE_INACTIVE",
        "MISSING_ACTIVE_TIME_WINDOW",
    ]
