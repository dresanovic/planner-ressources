from datetime import date, time
import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from app.db.schema import initialize_database
from app.models.planning import Cohort, CohortCalendar, CohortCalendarTimeWindow, Course, Semester
from app.services.academic_catalog import AcademicCatalogError, create_cohort_calendar, update_cohort_calendar, usage_for
from app.services.draft_schedule_repository import load_course_plan, load_semester_plan, load_generation_constraints

@pytest.fixture
def db():
    engine=create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        db.add_all([Cohort(id=1,name='AI 2',student_count=30),Cohort(id=2,name='WI 2',student_count=30),Semester(id=1,name='SS2027',start_date=date(2027,2,26),end_date=date(2027,7,9)),Semester(id=2,name='SS2028',start_date=date(2028,2,26),end_date=date(2028,7,9))])
        db.flush()
        yield db
    engine.dispose()

def calendar(db,cohort=1,semester=1):
    year=2026+semester
    return create_cohort_calendar(db,cohort_id=cohort,semester_id=semester,start_date=date(year,3,1),end_date=date(year,7,9))

def test_calendar_unique_per_cohort_and_semester_and_reusable_cohort(db):
    a=calendar(db)
    with pytest.raises(AcademicCatalogError) as error: calendar(db)
    assert error.value.status_code==409
    b=calendar(db,semester=2)
    c=calendar(db,cohort=2)
    assert len({a.id,b.id,c.id})==3
    assert any(item['type']=='cohort_calendar' and item['count']==2 for item in usage_for(db,db.get(Cohort,1))['dependentRecords'])

def test_lv_inherits_calendar_from_cohort_and_semester_without_calendar_fk(db):
    a,b,c=calendar(db),calendar(db,cohort=2),calendar(db,semester=2)
    course=Course(id=1,name='LV',total_units=8,min_session_units=2,max_session_units=4,cohort_id=1,current_semester_id=1)
    db.add(course);db.flush()
    assert 'cohort_calendar_id' not in Course.__table__.columns
    assert course.cohort_calendar.id==a.id
    course.cohort_id=2;db.flush();db.expire(course,['cohort_calendar'])
    assert course.cohort_calendar.id==b.id
    course.cohort_id=1;course.current_semester_id=2;db.flush();db.expire(course,['cohort_calendar'])
    assert course.cohort_calendar.id==c.id
    assert course.cohort_id==1

def test_calendar_period_is_inherited_and_semester_isolation(db):
    a=calendar(db)
    b=calendar(db,semester=2)
    db.add_all([CohortCalendarTimeWindow(cohort_calendar_id=a.id,weekday=0,start_time=time(8),end_time=time(17)),CohortCalendarTimeWindow(cohort_calendar_id=b.id,weekday=1,start_time=time(9),end_time=time(12)),Course(id=1,name='LV',total_units=8,min_session_units=2,max_session_units=4,cohort_id=1,current_semester_id=1)])
    db.flush()
    for semester,weekday,year in [(1,0,2027),(2,1,2028)]:
        result=load_generation_constraints(db,load_course_plan(db,1),load_semester_plan(db,semester))
        assert result.planning_period.start_date==date(year,3,1)
        assert [w.weekday for w in result.allowed_windows]==[weekday]

def test_calendar_owner_immutable_and_period_must_fit_semester(db):
    a=calendar(db)
    with pytest.raises(AcademicCatalogError):update_cohort_calendar(db,a,cohort_id=2,semester_id=1,start_date=a.start_date,end_date=a.end_date,expected_revision=a.revision)
    with pytest.raises(AcademicCatalogError):create_cohort_calendar(db,cohort_id=2,semester_id=1,start_date=date(2027,2,1),end_date=date(2027,7,9))
