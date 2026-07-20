import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.db.session import get_db
from app.main import app


@pytest.fixture()
def client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    initialize_database(engine)
    session = sessionmaker(bind=engine)()
    app.dependency_overrides[get_db] = lambda: (yield session)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        app.dependency_overrides.clear()
        session.close()


def test_lecturer_crud_search_usage_delete_and_not_found(client):
    created = client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "LECT-A"})
    assert created.status_code == 201
    assert created.json() == {"id": 1, "name": "Ada", "referenceCode": "LECT-A", "isActive": True, "revision": 1}
    assert client.get("/api/resources/lecturers?query=lect-a").json()["total"] == 1
    assert client.get("/api/resources/lecturers/1").json()["name"] == "Ada"
    usage = client.get("/api/resources/lecturers/1/usage")
    assert usage.json()["disposition"] == "delete"
    assert usage.json()["examUsage"] == {"examSessionCount": 0, "currentConfigurationCount": 0}
    updated = client.patch("/api/resources/lecturers/1", json={"name": "Ada L.", "referenceCode": "LECT-A", "expectedRevision": 1})
    assert updated.json()["revision"] == 2
    removed = client.delete("/api/resources/lecturers/1?expectedRevision=2&confirmed=true")
    assert removed.status_code == 200 and removed.json()["outcome"] == "deleted"
    assert client.get("/api/resources/lecturers/1").status_code == 404


def test_room_crud_returns_capacity_impacts_and_reactivation_shape(client):
    created = client.post("/api/resources/rooms", json={"name": "R1", "referenceCode": "ROOM-1", "capacity": 40})
    assert created.status_code == 201 and created.json()["capacity"] == 40
    changed = client.patch("/api/resources/rooms/1", json={"name": "R1", "referenceCode": "ROOM-1", "capacity": 30, "expectedRevision": 1})
    assert changed.status_code == 200
    assert changed.json() == {"room": {"id": 1, "name": "R1", "referenceCode": "ROOM-1", "capacity": 30, "isActive": True, "revision": 2}, "affectedRelationships": []}
    removed = client.delete("/api/resources/rooms/1?expectedRevision=2&confirmed=true")
    assert removed.json()["outcome"] == "deleted"


def test_structured_duplicate_stale_validation_and_confirmation_errors(client):
    assert client.post("/api/resources/lecturers", json={"name": "Same", "referenceCode": "CODE"}).status_code == 201
    duplicate = client.post("/api/resources/lecturers", json={"name": "Same", "referenceCode": " code "})
    assert duplicate.status_code == 409 and duplicate.json()["errors"][0]["code"] == "DUPLICATE_REFERENCE_CODE"
    invalid = client.post("/api/resources/rooms", json={"name": "", "referenceCode": "", "capacity": 0})
    assert invalid.status_code == 422
    stale = client.patch("/api/resources/lecturers/1", json={"name": "Edit", "referenceCode": "CODE", "expectedRevision": 99})
    assert stale.status_code == 409 and stale.json()["errors"][0]["meta"]["currentRevision"] == 1
    unconfirmed = client.delete("/api/resources/lecturers/1?expectedRevision=1&confirmed=false")
    assert unconfirmed.status_code == 409


def test_resource_lists_default_active_and_support_explicit_inactive(client):
    client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "A"})
    client.post("/api/resources/lecturers", json={"name": "Grace", "referenceCode": "G"})
    deleted = client.delete("/api/resources/lecturers/2?expectedRevision=1&confirmed=true")
    assert deleted.json()["outcome"] == "deleted"
    assert [item["name"] for item in client.get("/api/resources/lecturers").json()["items"]] == ["Ada"]
    assert client.get("/api/resources/lecturers?status=inactive").json()["items"] == []


def test_nested_unavailability_routes_support_discriminated_crud_and_stale_errors(client):
    lecturer = client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "A"}).json()
    base = f"/api/resources/lecturers/{lecturer['id']}/unavailability"
    recurring = client.post(base, json={"kind": "recurring", "weekdays": [2, 0], "startTime": "09:00", "endTime": "11:00"})
    dated = client.post(base, json={"kind": "dated", "startDate": "2026-09-07", "startTime": "15:00", "endDate": "2026-09-08", "endTime": "10:00"})
    assert recurring.status_code == 201 and recurring.json()["weekdays"] == [0, 2]
    assert dated.status_code == 201 and dated.json()["kind"] == "dated"
    assert [item["id"] for item in client.get(base).json()] == [recurring.json()["id"], dated.json()["id"]]
    changed = client.patch(f"{base}/{recurring.json()['id']}", json={"kind": "recurring", "weekdays": [1], "startTime": "10:00", "endTime": "12:00", "expectedRevision": 1})
    assert changed.json()["revision"] == 2
    stale = client.delete(f"{base}/{recurring.json()['id']}?expectedRevision=1")
    assert stale.status_code == 409 and stale.json()["errors"][0]["code"] == "STALE_REVISION"
    assert client.delete(f"{base}/{dated.json()['id']}?expectedRevision=1").status_code == 204


def test_course_resource_eligibility_contract_is_atomic_and_returns_candidates(client):
    lecturer = client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "A"}).json()
    second = client.post("/api/resources/lecturers", json={"name": "Grace", "referenceCode": "G"}).json()
    room = client.post("/api/resources/rooms", json={"name": "R", "referenceCode": "R", "capacity": 40}).json()
    semester = client.post("/api/academic/semesters", json={"name": "Fall", "startDate": "2026-09-01", "endDate": "2026-12-20"}).json()
    cohort = client.post("/api/academic/cohorts", json={"name": "C", "studentCount": 30}).json()
    study_type = client.post("/api/academic/study-types", json={"name": "Type"}).json()
    course = client.post("/api/academic/courses", json={"name": "Course", "totalUnits": 4, "minSessionUnits": 2, "maxSessionUnits": 4, "semesterId": semester["id"], "cohortId": cohort["id"], "studyTypeId": study_type["id"], "lecturerId": lecturer["id"], "roomId": room["id"]}).json()
    url = f"/api/academic/courses/{course['id']}/resource-eligibility"
    changed = client.put(url, json={"expectedRevision": course["revision"], "lecturerIds": [lecturer["id"], second["id"]], "roomIds": [room["id"]]})
    assert changed.status_code == 200
    body = changed.json()
    assert body["eligibleLecturerIds"] == [lecturer["id"], second["id"]]
    assert body["preferences"] == {"minimizeLecturerChanges": True, "minimizeRoomChanges": True}
    assert all("referenceCode" in candidate for candidate in body["lecturerCandidates"])
    failed = client.put(url, json={"expectedRevision": body["courseRevision"], "lecturerIds": [], "roomIds": [room["id"]]})
    assert failed.status_code == 422
    assert client.get(url).json()["eligibleLecturerIds"] == body["eligibleLecturerIds"]


def test_course_resource_configuration_includes_unavailability_and_course_session_usage(client):
    lecturer = client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "A"}).json()
    alternative_lecturer = client.post("/api/resources/lecturers", json={"name": "Grace", "referenceCode": "Z"}).json()
    room = client.post("/api/resources/rooms", json={"name": "R", "referenceCode": "R", "capacity": 40}).json()
    alternative_room = client.post("/api/resources/rooms", json={"name": "S", "referenceCode": "Z", "capacity": 40}).json()
    semester = client.post("/api/academic/semesters", json={"name": "Fall", "startDate": "2026-09-01", "endDate": "2026-12-20"}).json()
    cohort = client.post("/api/academic/cohorts", json={"name": "C", "studentCount": 30}).json()
    study_type = client.post("/api/academic/study-types", json={"name": "Type"}).json()
    window = client.post(
        f"/api/academic/study-types/{study_type['id']}/time-windows",
        json={"weekday": 0, "startTime": "09:00", "endTime": "12:00", "sortOrder": 0},
    ).json()
    course = client.post("/api/academic/courses", json={"name": "Course", "totalUnits": 2, "minSessionUnits": 2, "maxSessionUnits": 2, "semesterId": semester["id"], "cohortId": cohort["id"], "studyTypeId": study_type["id"], "lecturerId": lecturer["id"], "roomId": room["id"]}).json()
    eligibility = client.put(
        f"/api/academic/courses/{course['id']}/resource-eligibility",
        json={
            "expectedRevision": course["revision"],
            "lecturerIds": [lecturer["id"], alternative_lecturer["id"]],
            "roomIds": [room["id"], alternative_room["id"]],
        },
    ).json()
    unavailable = client.post(
        f"/api/resources/lecturers/{lecturer['id']}/unavailability",
        json={"kind": "recurring", "weekdays": [1], "startTime": "09:00", "endTime": "11:00"},
    ).json()
    generated = client.post(
        f"/api/courses/{course['id']}/draft-schedule/generate",
        json={
            "semesterId": semester["id"],
            "planningPeriod": {"startDate": "2026-09-07", "endDate": "2026-09-07"},
            "allowedTeachingWindows": [{"weekday": 0, "startTime": "09:00", "endTime": "12:00", "sourceTimeWindowId": window["id"]}],
        },
    )
    assert generated.status_code == 201
    assert client.delete(f"/api/resources/lecturers/{lecturer['id']}?expectedRevision={lecturer['revision']}&confirmed=true").json()["outcome"] == "inactivated"
    assert client.delete(f"/api/resources/rooms/{room['id']}?expectedRevision={room['revision']}&confirmed=true").json()["outcome"] == "inactivated"
    replaced = client.put(
        f"/api/academic/courses/{course['id']}/resource-eligibility",
        json={
            "expectedRevision": eligibility["courseRevision"],
            "lecturerIds": [alternative_lecturer["id"]],
            "roomIds": [alternative_room["id"]],
        },
    )
    assert replaced.status_code == 200

    configuration = client.get(f"/api/academic/courses/{course['id']}/resource-eligibility").json()
    lecturer_candidate = next(item for item in configuration["lecturerCandidates"] if item["id"] == lecturer["id"])
    room_candidate = next(item for item in configuration["roomCandidates"] if item["id"] == room["id"])

    assert lecturer_candidate["unavailabilityPeriods"] == [unavailable]
    assert lecturer_candidate["courseSessionUsage"] == {"draftSessionCount": 1, "draftScheduleCount": 1}
    assert room_candidate["courseSessionUsage"] == {"draftSessionCount": 1, "draftScheduleCount": 1}
    assert lecturer_candidate["isActive"] is False and lecturer_candidate["isEligible"] is False
    assert room_candidate["isActive"] is False and room_candidate["isEligible"] is False


def test_cohort_growth_removes_insufficient_rooms_and_reports_course_revision(client):
    lecturer = client.post("/api/resources/lecturers", json={"name": "Ada", "referenceCode": "A"}).json()
    room = client.post("/api/resources/rooms", json={"name": "R", "referenceCode": "R", "capacity": 30}).json()
    semester = client.post("/api/academic/semesters", json={"name": "Fall", "startDate": "2026-09-01", "endDate": "2026-12-20"}).json()
    cohort = client.post("/api/academic/cohorts", json={"name": "C", "studentCount": 20}).json()
    study_type = client.post("/api/academic/study-types", json={"name": "Type"}).json()
    course = client.post("/api/academic/courses", json={"name": "Course", "totalUnits": 4, "minSessionUnits": 2, "maxSessionUnits": 4, "semesterId": semester["id"], "cohortId": cohort["id"], "studyTypeId": study_type["id"], "lecturerId": lecturer["id"], "roomId": room["id"]}).json()
    changed = client.patch(f"/api/academic/cohorts/{cohort['id']}", json={"name": "C", "studentCount": 35, "expectedRevision": cohort["revision"]})
    assert changed.status_code == 200
    impact = changed.json()["capacityImpact"]
    assert impact["removedRelationships"] == [{"courseId": course["id"], "roomId": room["id"], "courseRevision": course["revision"] + 1}]
    assert impact["coursesWithoutRooms"] == [{"id": course["id"], "name": "Course"}]
    configuration = client.get(f"/api/academic/courses/{course['id']}/resource-eligibility").json()
    assert configuration["eligibleRoomIds"] == []
