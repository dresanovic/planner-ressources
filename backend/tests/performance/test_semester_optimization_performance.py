from time import perf_counter

from app.services.semester_optimization import optimize_semester
from tests.optimization_fixtures import reference_fixed_sessions, reference_performance_courses


def test_reference_20_course_600_unit_500_fixed_session_workload_completes_within_30_seconds():
    started = perf_counter()
    result = optimize_semester(reference_performance_courses(), reference_fixed_sessions(), deadline_seconds=60)
    elapsed = perf_counter() - started

    assert result.optimal is True
    assert result.total_units == 600
    assert elapsed < 30
