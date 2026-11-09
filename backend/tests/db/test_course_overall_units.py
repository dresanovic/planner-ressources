from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


def test_migration_copies_units_once_and_preserves_schedules():
    engine = create_engine('sqlite://')
    initialize_database(engine)
    with Session(engine) as db:
        seed_lifecycle_semester(db, with_schedule=True)
    with engine.begin() as connection:
        drafts = connection.exec_driver_sql('SELECT * FROM draft_schedules').fetchall()
        sessions = connection.exec_driver_sql('SELECT * FROM draft_sessions').fetchall()
        connection.exec_driver_sql('ALTER TABLE courses DROP COLUMN overall_units')
    initialize_database(engine)
    with engine.begin() as connection:
        assert connection.exec_driver_sql('SELECT total_units, overall_units FROM courses').fetchall() == [(4, 4)]
        assert not next(c for c in inspect(connection).get_columns('courses') if c['name'] == 'overall_units')['nullable']
        assert connection.exec_driver_sql('SELECT * FROM draft_schedules').fetchall() == drafts
        assert connection.exec_driver_sql('SELECT * FROM draft_sessions').fetchall() == sessions
        assert connection.exec_driver_sql('PRAGMA foreign_key_check').fetchall() == []
        connection.exec_driver_sql('UPDATE courses SET overall_units=12')
    initialize_database(engine)
    with engine.connect() as connection:
        assert connection.exec_driver_sql('SELECT total_units, overall_units FROM courses').fetchall() == [(4, 12)]
