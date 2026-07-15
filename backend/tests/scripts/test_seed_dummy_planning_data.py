from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models.planning import Course
from scripts import seed_dummy_planning_data as seed_script


def test_seeded_courses_have_current_semester_and_canonical_catalog_fields(tmp_path, monkeypatch):
    engine = create_engine(f"sqlite:///{tmp_path / 'seed.db'}")
    monkeypatch.setattr(seed_script, "engine", engine)
    seed_script.seed()
    with Session(engine) as db:
        courses = list(db.execute(select(Course)).scalars())
        assert courses
        assert all(course.current_semester_id is not None for course in courses)
        assert all(course.normalized_name == course.name.strip().casefold() for course in courses)
        assert all(course.normalized_name_key == course.normalized_name for course in courses)
        assert all(course.is_active and course.revision == 1 for course in courses)
