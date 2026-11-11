"""Run explicitly with backend dependencies; see README for the command."""
import asyncio

import httpx
import pytest
from sqlalchemy import select

from app.main import app
from app.models.planning import PlannerAccount
from app.services.planner_auth import hash_password
from tests.api.test_draft_schedule import client, db_session, seed_valid_course  # noqa: F401

from planner_resource_mcp.client import PlannerClient, PlannerError, Settings


def test_real_backend_login_read_save_update_and_lifecycle_conflict(client, db_session):
    seed_valid_course(db_session, total_units=8)
    account = db_session.scalar(select(PlannerAccount))
    account.password_hash = hash_password("MCP test password")
    db_session.commit()

    async def scenario():
        bridge = PlannerClient(Settings("http://localhost", account.login_name, "MCP test password"),
                               transport=httpx.ASGITransport(app=app))
        try:
            cohorts = await bridge.request("GET", "api/academic/cohorts", params={"status": "active"})
            assert cohorts["items"][0]["name"] == "AI 1"
            options = await bridge.request("GET", "api/planning-options", params={"semesterId": 1})
            assert options["courses"][0]["id"] == 1
            constraints = await bridge.request("GET", "api/courses/1/generation-constraints", params={"semesterId": 1})
            assert constraints["allowedTeachingWindows"]
            await bridge.request("GET", "api/semesters/1/schedule-lifecycle")
            payload = {"semesterId": 1, "scheduleRevisionId": 1, "date": "2026-09-07",
                       "startTime": "08:00", "endTime": "09:30", "units": 2,
                       "lecturerId": 1, "cohortId": 1, "roomId": 3}
            result = await bridge.request("POST", "api/courses/1/draft-schedule/sessions", json=payload)
            assert result["scheduledUnits"] == 2
            session_id = result["draftSchedule"]["sessions"][0]["id"]
            result = await bridge.request("PATCH", f"api/draft-sessions/{session_id}", json={
                "scheduleRevisionId": 1, "date": "2026-09-07", "startTime": "09:00",
                "endTime": "10:30", "roomId": 3})
            assert result["sessions"][0]["startTime"] == "09:00"
            saved = await bridge.request("GET", "api/draft-schedules", params={"semesterId": 1})
            assert len(saved) == 1 and len(saved[0]["sessions"]) == 1
            with pytest.raises(PlannerError, match="409"):
                await bridge.request("POST", "api/courses/1/draft-schedule/sessions",
                                     json={**payload, "scheduleRevisionId": 999, "date": "2026-09-14"})
            saved = await bridge.request("GET", "api/draft-schedules", params={"semesterId": 1})
            assert len(saved[0]["sessions"]) == 1
        finally:
            await bridge.close()
    asyncio.run(scenario())
