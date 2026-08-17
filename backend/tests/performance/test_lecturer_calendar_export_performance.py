from __future__ import annotations

import importlib
import json
import os
import platform
from datetime import date, timedelta, time
from math import ceil
from time import perf_counter

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.db.schema import initialize_database
from app.db.session import get_db
from app.models.planning import DraftSchedule, DraftSession
from tests.lecturer_calendar_fixtures import (
    CALENDAR_SOURCE_FINGERPRINT_KEY,
    seed_lecturer_calendar_fixture,
)


app_main = importlib.import_module("app.main")


@pytest.mark.skipif(
    os.getenv("FS020_RUN_RELEASE_PERFORMANCE") != "1",
    reason="requires the constrained release backend container",
)
def test_complete_100_event_export_meets_release_latency_contract(monkeypatch):
    assert os.getenv("FS020_CONTAINER_CPUS") == "2"
    assert os.getenv("FS020_CONTAINER_MEMORY") == "2GiB"
    assert os.getenv("APP_ENV", "").casefold() == "production"
    assert os.getenv("FS020_DEBUG_INSTRUMENTATION", "off").casefold() == "off"
    assert os.getenv("FS020_CONCURRENT_REQUESTS", "0") == "0"
    image_digest = os.environ["FS020_IMAGE_DIGEST"]
    docker_version = os.environ["FS020_DOCKER_VERSION"]
    host_cpu = os.environ["FS020_HOST_CPU"]

    monkeypatch.setenv(
        "LECTURER_REVIEW_SOURCE_FINGERPRINT_KEY",
        CALENDAR_SOURCE_FINGERPRINT_KEY,
    )
    database_path = os.environ["FS020_SQLITE_PATH"]
    engine = create_engine(
        f"sqlite:///{database_path}",
        connect_args={"check_same_thread": False},
    )
    initialize_database(engine)
    db = Session(engine)
    app_main.app.dependency_overrides[get_db] = lambda: db
    monkeypatch.setattr(app_main, "SessionLocal", lambda: Session(engine))
    try:
        fixture = seed_lecturer_calendar_fixture(db)
        schedule = db.get(DraftSchedule, 1)
        assert schedule is not None
        occupied = {session.date for session in schedule.sessions}
        candidate = date(2026, 9, 1)
        new_sessions: list[DraftSession] = []
        while len(new_sessions) < 91:
            if candidate not in occupied:
                new_sessions.append(
                    DraftSession(
                        id=1000 + len(new_sessions),
                        draft_schedule_id=schedule.id,
                        course_id=1,
                        lecturer_id=fixture.review.primary_lecturer_id,
                        cohort_id=1,
                        room_id=1,
                        date=candidate,
                        start_time=time(9),
                        end_time=time(11),
                        units=2,
                        constraint_window_index=0,
                    )
                )
            candidate += timedelta(days=1)
        db.add_all(new_sessions)
        db.commit()

        with TestClient(app_main.app) as client:
            issued = client.post(
                "/api/schedule-revisions/2/lecturer-review-links",
                json={"lecturerId": fixture.review.primary_lecturer_id},
            )
            assert issued.status_code == 201, issued.text
            headers = {
                "Authorization": f"Bearer {issued.json()['secret']}",
                "Accept": "text/calendar",
            }

            for _ in range(10):
                warmup = client.get(
                    "/api/public/lecturer-review/calendar", headers=headers
                )
                assert warmup.status_code == 200

            samples: list[float] = []
            for _ in range(100):
                started = perf_counter()
                response = client.get(
                    "/api/public/lecturer-review/calendar", headers=headers
                )
                elapsed = perf_counter() - started
                assert response.status_code == 200
                assert response.content.count(b"BEGIN:VEVENT") == 100
                samples.append(elapsed)

        ordered = sorted(samples)
        p95 = ordered[ceil(0.95 * len(ordered)) - 1]
        maximum = ordered[-1]
        evidence = {
            "imageDigest": image_digest,
            "hostCpu": host_cpu,
            "dockerVersion": docker_version,
            "python": platform.python_version(),
            "warmups": 10,
            "samplesSeconds": samples,
            "p95Seconds": p95,
            "maximumSeconds": maximum,
        }
        print(json.dumps(evidence, separators=(",", ":")))
        assert p95 <= 3.0
        assert maximum <= 10.0
    finally:
        app_main.app.dependency_overrides.clear()
        db.close()
        engine.dispose()
