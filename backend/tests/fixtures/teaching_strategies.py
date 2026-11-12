"""Fixed I-011 acceptance inputs; no installation data or policy reads."""
from dataclasses import asdict, replace
from datetime import time, timedelta
import hashlib
import json

from app.services.schedule_generation import PlanningPeriodPlan, TimeWindowPlan
from tests.optimization_fixtures import SEMESTER_START, optimization_course, fixed_session
from tests.optimization_fixtures import seed_optimization_planner
from tests.planner_auth_fixtures import file_backed_engine


def standard_cases():
    """Small fully provable baselines, including shared-resource competition."""
    one_day = PlanningPeriodPlan(SEMESTER_START, SEMESTER_START)
    single = replace(optimization_course(1, total_units=2, min_units=2, max_units=2),
                     planning_period=one_day)
    competing = tuple(replace(optimization_course(i, total_units=2, min_units=2,
        max_units=2, cohort_id=1, lecturer_ids=(1,), room_ids=(1, 2)),
        planning_period=one_day) for i in (1, 2))
    exam = fixed_session(course_id=99, cohort_id=1, lecturer_id=1, room_id=1,
        start=time(8), end=time(9), source_kind='exam_session', source_id=711)
    return {'single': ((single,), ()), 'competition': (competing, ()),
            'protected_exam': ((single,), (exam,))}


def snapshot_identity(courses, fixed):
    records = [asdict(c) for c in (*courses, *fixed)]
    for record in records:
        # Compare solver facts to the prechange recording despite metadata rename.
        if "cohort_calendar_id" in record:
            record["study_type_id"] = record.pop("cohort_calendar_id")
        if record.get('explicit_lecturer_portions') is None:
            record.pop('explicit_lecturer_portions', None)
    return hashlib.sha256(json.dumps(records,
        sort_keys=True, default=str).encode()).hexdigest()


def completed_facts(result):
    """Exclude wall-clock measurements; retain assignments and proof semantics."""
    facts = asdict(result)
    del facts['elapsed_milliseconds']
    if facts.get('termination') is None:
        facts.pop('termination', None)
        facts.pop('repair_attempts', None)
    return json.loads(json.dumps(facts, sort_keys=True, default=str))


def exact22():
    return replace(optimization_course(1, total_units=22), preferred_session_units=3,
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START + timedelta(days=48)))


def selection(count):
    assert count in (1, 20)
    return tuple(replace(optimization_course(i, total_units=2, min_units=2, max_units=2),
        planning_period=PlanningPeriodPlan(SEMESTER_START, SEMESTER_START))
        for i in range(1, count + 1))


def intensive22():
    return replace(exact22(), windows=(
        TimeWindowPlan(1, 0, time(8), time(12)),
        TimeWindowPlan(2, None, time(8), time(12), kind='dated',
            date=SEMESTER_START + timedelta(days=9), is_intensive=True),
    ))


# Expected scores/targets are independent constants from the approved spec.
BALANCE_CASES = (
    ((3, 3, 3, 3), (1, 1, 1, 1), 36),
    ((6, 6, 0, 0), (1, 1, 1, 1), 72),
    ((3, 6, 3), (1, 2, 1), 36),
    ((6, 3, 3), (1, 2, 1), 49.5),
)
PORTION_CASES = ((22, 2, (11, 11)), (24, 3, (8, 8, 8)),
                 (23, 2, (12, 11)), (22, 3, (8, 7, 7)),
                 (22, 1, (22,)), (2, 3, (1, 1, 0)))


def preference_inputs():
    """Named immutable calendar/competition/owner examples for later assertions."""
    base = exact22()
    monday = SEMESTER_START
    two_weeks = PlanningPeriodPlan(monday, monday + timedelta(days=13))
    short = replace(base, total_units=3, planning_period=two_weeks)
    fixed_owner = fixed_session(course_id=99, cohort_id=1, lecturer_id=99,
        room_id=99, session_date=monday, start=time(6), end=time(7))
    # FixedSession's helper has no instructional units parameter.
    fixed_owner = replace(fixed_owner, units=3)
    fixed_lecturer = replace(fixed_owner, course_id=100, cohort_id=99,
        lecturer_id=1, date=monday + timedelta(days=7))
    four_weeks = PlanningPeriodPlan(monday, monday + timedelta(days=27))
    six = replace(short, total_units=6, planning_period=four_weeks)
    ordinary_extra = replace(six, planning_period=PlanningPeriodPlan(monday, monday + timedelta(days=6)),
        windows=(TimeWindowPlan(1, 0, time(8), time(12)), TimeWindowPlan(2, 2, time(8), time(12))))
    intensive_extra = replace(ordinary_extra, total_units=9, windows=tuple(
        TimeWindowPlan(i + 1, None, time(8), time(12), kind='dated', date=monday + timedelta(days=day), is_intensive=True)
        for i, day in enumerate((0, 2, 4))))
    return {
        'exact22': ((base,), ()),
        'staggered_cohort': ((six, replace(six, course_id=2, windows=(TimeWindowPlan(2, 2, time(8), time(12)),))), ()),
        'distinct_owner': ((short,), (fixed_owner, fixed_lecturer)),
        'rhythm_before_owner': ((six, replace(six, course_id=2, cohort_id=2)), ()),
        'ordinary_extra_days': ((ordinary_extra,), ()),
        'intensive_extra_days': ((intensive_extra,), ()),
        'intensive_mixed_increase': ((intensive22(), replace(short, course_id=2)), ()),
        'partial_boundary': ((replace(short, planning_period=PlanningPeriodPlan(
            monday + timedelta(days=2), monday + timedelta(days=13))),), ()),
        'zero_opportunity': ((replace(short, windows=()),), ()),
        'duplicate_opportunities': ((replace(short, windows=short.windows * 2),), ()),
        'shared_lecturer_competition': ((short, replace(short, course_id=2, cohort_id=2)), ()),
        'incompatible_portion': ((replace(short, total_units=7,
            lecturers=selection(20)[0].lecturers + selection(20)[1].lecturers),), ()),
        'twenty': (selection(20), ()),
    }


def isolated_planner(tmp_path, monkeypatch, *, count=1, algorithm='standard', total_units=8):
    """Caller owns engine disposal; initialization targets only its temp path."""
    from sqlalchemy.orm import Session
    policy = tmp_path / 'policy.json'
    policy.write_text(json.dumps({'activeAlgorithm': algorithm,
        'defaultSeconds': 10, 'ceilingSeconds': 10}), encoding='utf-8')
    monkeypatch.setenv('TEACHING_OPTIMIZATION_POLICY_FILE', str(policy))
    engine = file_backed_engine(tmp_path / 'teaching.db')
    with Session(engine) as db:
        seed_optimization_planner(db, course_count=count, total_units=total_units)
    return engine, policy
