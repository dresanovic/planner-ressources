"""Disposable, independently specified I-009 examples; no application database access."""
from datetime import date, time

from app.models.planning import StudyType, StudyTypeTimeWindow


MONDAY = date(2026, 11, 9)
OTHER_MONDAY = date(2026, 11, 16)
LEAP_DAY = date(2028, 2, 29)
# Two 45-minute instructional intervals; the ten-minute break earns no LE.
INSTRUCTION = ((time(9), time(9, 45)), (time(9, 55), time(10, 40)))
MARKER = (time(9, 30), time(10, 10))
EXPECTED_MARKED_MICROSECONDS = 30 * 60 * 1_000_000
SMALL_ALTERNATIVES = ((12, 4, 0), (10, 10, 2), (12, 8, 0), (12, 8, 2))


def seed_forms(db):
    db.add_all([
        StudyType(id=1, name="Berufsbegleitend", normalized_name="berufsbegleitend", normalized_name_key="berufsbegleitend"),
        StudyType(id=2, name="Vollzeit", normalized_name="vollzeit", normalized_name_key="vollzeit"),
    ])
    db.flush()


def weekly_window(**changes):
    return StudyTypeTimeWindow(**{
        "id": 10, "study_type_id": 1, "weekday": 4,
        "start_time": time(9), "end_time": time(12), "sort_order": 7,
        "is_active": True, "revision": 3, **changes,
    })


def seed_acceptance_context(db, *, with_selected):
    from tests.optimization_fixtures import seed_optimization_planner, active_exam
    from app.models.planning import Course
    from app.services.draft_schedule_repository import load_course_plan,replace_draft_schedule
    from app.services.schedule_generation import GeneratedSession
    seed_optimization_planner(db,course_count=3,total_units=2)
    selected=db.get(StudyTypeTimeWindow,1)
    selected.kind,selected.weekday,selected.date,selected.is_intensive='dated',None,date(2026,9,7),True
    db.add_all([StudyType(id=2,name='Fixed form'),StudyType(id=3,name='Other fixed form')])
    fixed_course=db.get(Course,3)
    fixed_course.study_type_id=2;fixed_course.cohort_id=1
    fixed_course.min_session_units=fixed_course.max_session_units=1
    db.add(StudyTypeTimeWindow(id=3,study_type_id=2,kind='dated',weekday=None,date=date(2026,9,7),
        start_time=time(7),end_time=time(8),is_intensive=True))
    db.flush()
    replace_draft_schedule(db,load_course_plan(db,3),1,[GeneratedSession(date(2026,9,7),time(7),time(7,45),1,3,0,3,3)])
    if with_selected:
        replace_draft_schedule(db,load_course_plan(db,1),1,[GeneratedSession(date(2026,9,7),time(10),time(11,40),2,1,1,1,1)])
    db.add(active_exam(exam_id=90,course_id=1,exam_date=date(2026,12,1)))
    db.commit()


ACCEPTANCE_WINDOW_CHANGES=('date','hours','form','activity','marker','fixed_date','fixed_hours','fixed_form','fixed_activity','fixed_marker')


def mutate_acceptance_window(db, change):
    fixed=change.startswith('fixed_')
    field=change.removeprefix('fixed_')
    row=db.get(StudyTypeTimeWindow,3 if fixed else 1)
    if field=='date':row.date=date(2026,9,8)
    if field=='hours':row.end_time=time(7,30) if fixed else time(13)
    if field=='form':row.study_type_id=3 if fixed else 2
    if field=='activity':row.is_active=False
    if field=='marker':row.is_intensive=False
    # Deliberately keep revision unchanged to prove captured facts, not merely
    # an incidental revision increment, participate in freshness protection.
    db.commit()


def business_rows(engine):
    with engine.connect() as connection:
        tables=connection.exec_driver_sql("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' AND name != 'optimization_operations' ORDER BY name").scalars().all()
        return tuple((name,tuple(connection.exec_driver_sql(f'SELECT * FROM "{name}" ORDER BY rowid').fetchall())) for name in tables)
