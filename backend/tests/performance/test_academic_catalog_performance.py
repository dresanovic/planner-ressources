from datetime import date, time
from time import perf_counter

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.base import Base
from app.db.session import get_db
from app.main import app
from app.models.planning import Cohort, Course, CourseEligibleLecturer, CourseEligibleRoom, Lecturer, Room, Semester, StudyType, StudyTypeTimeWindow


def _client_with_100_of_each():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    Base.metadata.create_all(engine)
    db = sessionmaker(bind=engine)()
    db.add_all([Lecturer(id=1, name="Planner Lecturer"), Room(id=1, name="Planner Room", capacity=1000)])
    for index in range(1, 101):
        db.add_all([
            Semester(id=index, name=f"Semester {index:03}", normalized_name=f"semester {index:03}", normalized_name_key=f"semester {index:03}", start_date=date(2026, 1, 1), end_date=date(2026, 12, 31)),
            Cohort(id=index, name=f"Cohort {index:03}", normalized_name=f"cohort {index:03}", normalized_name_key=f"cohort {index:03}", student_count=30),
            StudyType(id=index, name=f"Study Type {index:03}", normalized_name=f"study type {index:03}", normalized_name_key=f"study type {index:03}"),
        ])
    db.flush()
    for index in range(1, 101):
        db.add_all([
            StudyTypeTimeWindow(id=index, study_type_id=index, weekday=index % 7, start_time=time(8), end_time=time(12), sort_order=0),
            Course(id=index, name=f"Course {index:03}", normalized_name=f"course {index:03}", normalized_name_key=f"course {index:03}", total_units=8, min_session_units=2, max_session_units=4, cohort_id=index, study_type_id=index, current_semester_id=index, eligible_lecturers=[CourseEligibleLecturer(lecturer_id=1)], eligible_rooms=[CourseEligibleRoom(room_id=1)]),
        ])
    db.commit()
    app.dependency_overrides[get_db] = lambda: (yield db)
    return db, TestClient(app)


def test_reference_100_record_catalog_timings():
    db, client = _client_with_100_of_each()
    try:
        client.get("/api/academic/courses?pageSize=200")
        administration = []
        paths = ["semesters", "cohorts", "courses", "study-types"]
        for trial in range(20):
            started = perf_counter()
            if trial % 2 == 0:
                response = client.get(f"/api/academic/{paths[(trial // 2) % len(paths)]}?pageSize=200")
            else:
                record_id = (trial + 1) // 2
                current = client.get(f"/api/academic/cohorts/{record_id}").json()
                response = client.patch(f"/api/academic/cohorts/{record_id}", json={"name": current["name"], "studentCount": current["studentCount"] + 1, "expectedRevision": current["revision"]})
            duration = perf_counter() - started
            administration.append(duration)
            print(f"ADMIN-{trial + 1:02}: {duration:.6f}s")
            assert response.status_code == 200

        refresh = []
        for trial in range(10):
            record_id = trial + 1
            current = client.get(f"/api/academic/courses/{record_id}").json()
            started = perf_counter()
            updated = client.patch(f"/api/academic/courses/{record_id}", json={
                "name": f"Course {record_id:03} refreshed", "totalUnits": current["totalUnits"], "minSessionUnits": current["minSessionUnits"], "maxSessionUnits": current["maxSessionUnits"],
                "semesterId": current["semester"]["id"], "cohortId": current["cohort"]["id"], "studyTypeId": current["studyType"]["id"], "expectedRevision": current["revision"],
            })
            options = client.get(f"/api/planning-options?semesterId={record_id}")
            duration = perf_counter() - started
            refresh.append(duration)
            print(f"REFRESH-{trial + 1:02}: {duration:.6f}s")
            assert updated.status_code == 200
            assert options.json()["courses"][0]["name"].endswith("refreshed")

        assert sum(duration <= 2 for duration in administration) >= 19
        assert all(duration <= 2 for duration in refresh)
    finally:
        client.close()
        db.close()
        app.dependency_overrides.clear()
