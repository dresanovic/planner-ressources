"""Verify the initialization script against the real API without a plan/version."""
import importlib.util
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import CourseExamConfiguration, ScheduleRevision
from tests.exam_fixtures import exam_catalog
from tests.planner_auth_fixtures import authenticate_test_client


def test_initialize_without_teaching_or_schedule_revision():
    spec = importlib.util.spec_from_file_location(
        "initialize_exams", Path(__file__).resolve().parents[2] / "scripts" / "initialize_exam_requirements.py")
    script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(script)
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([row for row in exam_catalog() if not isinstance(row, ScheduleRevision)])
    db.commit()
    app.dependency_overrides[get_db] = lambda: (yield db)
    try:
        with TestClient(app) as client:
            authenticate_test_client(client, db)

            class API:
                def request(self, method, path, payload=None):
                    response = client.request(method, path, json=payload)
                    assert response.is_success, response.text
                    return response.json()

            api = API()
            plan = script.load_plan(api, 1)
            assert plan[0]["status"] == "would_create"
            script.execute(api, plan, 1, apply=False)
            assert db.query(CourseExamConfiguration).count() == 0
            script.execute(api, plan, 1, apply=True)
            assert plan[0]["status"] == "created"
            saved = db.query(CourseExamConfiguration).one()
            assert (saved.duration_minutes, saved.exam_type, saved.required_capacity,
                    saved.responsible_lecturer_id) == (90, "Schriftlich", 30, 1)
            assert db.query(ScheduleRevision).count() == 0
            assert script.load_plan(api, 1)[0]["status"] == "existing"
    finally:
        app.dependency_overrides.clear()
        db.close()
        engine.dispose()
