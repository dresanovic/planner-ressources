import json
import platform
import sys
from datetime import date, time
from time import perf_counter

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.models.planning import GenerationConstraintSet, InstitutionHoliday
from app.schemas.conflict_aware_generation import PreparedOptimizationCourseInput
from app.services.conflict_aware_generation import generate_optimization, prepare_optimization
from app.services.draft_schedule_repository import load_course_plan, replace_draft_schedule
from app.services.schedule_generation import GeneratedSession
from app.services.semester_optimization import optimize_semester
from tests.optimization_fixtures import SEMESTER_START, fixed_session, reference_fixed_sessions, reference_performance_courses, seed_optimization_planner


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


@pytest.mark.parametrize("workflow", ["direct_save", "replacement_preview", "no_result"])
def test_generation_workflows_meet_the_thirty_second_service_level(workflow, record_property):
    workload_sizes = [1, 5, 10, 15, 20] * 4
    evidence = []
    for run_number, course_count in enumerate(workload_sizes, start=1):
        engine = create_engine(
            "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
        )
        Base.metadata.create_all(engine)
        db = sessionmaker(bind=engine)()
        try:
            seed_optimization_planner(db, course_count=course_count, total_units=4)
            if workflow == "replacement_preview":
                replace_draft_schedule(db, load_course_plan(db, 1), 1, [
                    GeneratedSession(date(2026, 9, 7), time(8), time(9, 40), 2, 1, 0, 1, 1)
                ])
            elif workflow == "no_result":
                db.add_all([
                    GenerationConstraintSet(
                        course_id=course_id,
                        semester_id=1,
                        planning_start_date=date(2026, 9, 7),
                        planning_end_date=date(2026, 9, 7),
                    )
                    for course_id in range(1, course_count + 1)
                ])
                db.add(InstitutionHoliday(date=date(2026, 9, 7), name="Closure"))
            db.commit()
            course_ids = list(range(1, course_count + 1))
            prepared = prepare_optimization(db, 1, course_ids, [], schedule_revision_id=1)
            courses = [PreparedOptimizationCourseInput(
                courseId=item.course_id,
                expectedDraftScheduleId=item.draft_schedule_id,
                expectedDraftRevision=item.draft_revision,
                inputSnapshotToken=item.input_snapshot_token,
            ) for item in prepared.courses]

            started = perf_counter()
            result = generate_optimization(
                db, 1, courses, [], prepared.shared_snapshot_token, schedule_revision_id=1
            )
            elapsed = perf_counter() - started
            evidence.append({"run": run_number, "courseCount": course_count, "seconds": elapsed})

            if workflow == "replacement_preview":
                assert result.mode == "decision_required" and result.saved is False
                assert len(result.comparison.courses) == course_count
            elif workflow == "direct_save":
                assert result.mode == "direct_saved"
                assert len(result.outcomes) == course_count and all(item.saved for item in result.outcomes)
            else:
                assert result.mode == "direct_saved"
                assert len(result.outcomes) == course_count and all(not item.saved for item in result.outcomes)
        finally:
            db.close()
            engine.dispose()

    record_property(f"{workflow}_performance", json.dumps(evidence))
    assert sum(item["seconds"] < 30 for item in evidence) >= 19
