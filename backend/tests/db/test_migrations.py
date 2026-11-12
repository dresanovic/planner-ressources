"""Fresh development schema and explicit reset replace historical upgrade support."""
from pathlib import Path
import importlib.util
import sqlite3
from datetime import date
import pytest
from sqlalchemy import create_engine, inspect
from app.db.schema import initialize_database, UnsupportedSchemaStateError


def test_fresh_schema_is_idempotent_and_has_no_independent_lv_calendar_fk(tmp_path):
    engine=create_engine('sqlite:///'+(tmp_path/'new.db').as_posix())
    initialize_database(engine)
    initialize_database(engine)
    inspector=inspect(engine)
    assert 'study_types' not in inspector.get_table_names()
    assert 'cohort_calendars' in inspector.get_table_names()
    assert 'cohort_calendar_id' not in {c['name'] for c in inspector.get_columns('courses')}
    assert {'cohort_id','semester_id','start_date','end_date'} <= {c['name'] for c in inspector.get_columns('cohort_calendars')}
    engine.dispose()


def test_previous_development_schema_requires_explicit_reset_without_mutation(tmp_path):
    path=tmp_path/'previous.db'
    with sqlite3.connect(path) as db:db.execute('CREATE TABLE study_types(id INTEGER PRIMARY KEY,name TEXT)')
    before=path.read_bytes()
    engine=create_engine('sqlite:///'+path.as_posix())
    with pytest.raises(UnsupportedSchemaStateError,match='reset_cohort_calendar_baseline'):
        initialize_database(engine)
    engine.dispose()
    assert path.read_bytes()==before


def test_development_reset_preserves_courses_and_cohorts_and_does_not_activate(tmp_path):
    from sqlalchemy.orm import Session
    from app.models.planning import Cohort,Course,Semester
    source=tmp_path/'source.db'
    engine=create_engine('sqlite:///'+source.as_posix())
    initialize_database(engine)
    with Session(engine) as db:
        db.add(Semester(id=1,name='2027 S',start_date=date(2027,2,19),end_date=date(2027,8,17)))
        db.add_all([Cohort(id=i,name=f'Cohort {i}',student_count=30) for i in range(1,11)])
        db.flush()
        db.add_all([Course(id=i,name=f'LV {i}',total_units=8,min_session_units=2,max_session_units=4,current_semester_id=1,cohort_id=(i-1)%10+1) for i in range(1,95)])
        db.commit()
    engine.dispose()
    before=source.read_bytes()
    path=Path(__file__).resolve().parents[2]/'scripts/reset_cohort_calendar_baseline.py'
    spec=importlib.util.spec_from_file_location('reset_calendar',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    report=module.prepare(source,tmp_path/'output')
    assert source.read_bytes()==before
    assert report['courseCohortLinksAndUnitsPreserved']==94
    assert report['windows']=={'weekly':25,'dated':37}
    with sqlite3.connect(report['baseline']) as db:
        assert db.execute('SELECT count(*) FROM cohort_calendars').fetchone()[0]==10
        assert db.execute('SELECT count(*) FROM draft_sessions').fetchone()[0]==0
        assert db.execute('SELECT count(*) FROM schedule_revisions').fetchone()[0]==0
