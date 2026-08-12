import json
import platform
import sys
from datetime import time
from time import perf_counter

from app.services.semester_optimization import optimize_semester
from tests.optimization_fixtures import SEMESTER_START, fixed_session, reference_fixed_sessions, reference_performance_courses


def _fresh_reference_input():
    active_exams = [
        fixed_session(
            course_id=course_id,
            cohort_id=course_id,
            lecturer_id=course_id,
            room_id=course_id,
            session_date=SEMESTER_START,
            start=time(8),
            end=time(12),
            source_kind="active_exam",
            source_id=10_000 + course_id,
        )
        for course_id in range(1, 21)
    ]
    return reference_performance_courses(), [*reference_fixed_sessions(), *active_exams]


def test_reference_workload_protocol_records_twenty_fresh_measured_runs(record_property):
    warm_courses, warm_fixed = _fresh_reference_input()
    warmup = optimize_semester(warm_courses, warm_fixed, deadline_seconds=60)
    assert warmup.optimal is True

    evidence = []
    for run_number in range(1, 21):
        courses, fixed = _fresh_reference_input()
        started = perf_counter()
        result = optimize_semester(courses, fixed, deadline_seconds=60)
        elapsed = perf_counter() - started
        evidence.append({"run": run_number, "seconds": elapsed})
        assert result.optimal is True
        assert result.total_units == 600

    environment = {
        "platform": platform.platform(),
        "python": sys.version,
        "processor": platform.processor(),
        "runs": evidence,
    }
    record_property("semester_optimization_performance", json.dumps(environment))
    assert all(item["seconds"] < 60 for item in evidence)
    assert sum(item["seconds"] < 30 for item in evidence) >= 19
