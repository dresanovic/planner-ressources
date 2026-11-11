from __future__ import annotations

import sys
from contextlib import asynccontextmanager
from datetime import date
from typing import Annotated

from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations
from pydantic import BaseModel, ConfigDict, Field

from .client import PlannerClient, PlannerError, Settings

PositiveId = Annotated[int, Field(strict=True, ge=1)]
Clock = Annotated[str, Field(pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$")]
READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, openWorldHint=False)
WRITE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


class NewSession(BaseModel):
    model_config = ConfigDict(extra="forbid")
    semester_id: PositiveId
    schedule_revision_id: PositiveId
    date: date
    start_time: Clock
    end_time: Clock
    units: PositiveId
    lecturer_id: PositiveId
    cohort_id: PositiveId
    room_id: PositiveId


class SessionUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schedule_revision_id: PositiveId
    date: date
    start_time: Clock
    end_time: Clock
    room_id: PositiveId
    lecturer_id: PositiveId | None = None
    units: PositiveId | None = None


def api_payload(model: BaseModel) -> dict:
    def camel(key):
        head, *tail = key.split("_")
        return head + "".join(word.capitalize() for word in tail)
    return {camel(key): value for key, value in model.model_dump(mode="json", exclude_none=True).items()}


def create_server(settings: Settings | None = None, *, transport=None) -> FastMCP:
    @asynccontextmanager
    async def lifespan(_server):
        client = PlannerClient(settings or Settings.from_environment(), transport=transport)
        try:
            yield client
        finally:
            await client.close()

    server = FastMCP(
        "planner-resource",
        instructions=(
            "Read planning options, course constraints and schedule lifecycle before planning. "
            "Use the current working schedule revision ID for saves. Saves persist immediately, "
            "one session per call. Inspect returned validation alerts and reread after conflicts. "
            "Do not blindly retry writes after connection failures. This server does not publish schedules."
        ),
        lifespan=lifespan,
    )

    async def call(ctx: Context, method, path, **kwargs):
        try:
            return await ctx.request_context.lifespan_context.request(method, path, **kwargs)
        except PlannerError as exc:
            raise ToolError(str(exc)) from None

    @server.tool(annotations=READ)
    async def list_cohorts(ctx: Context, page: Annotated[int, Field(ge=1)] = 1,
                           page_size: Annotated[int, Field(ge=1, le=200)] = 50,
                           query: str | None = None) -> dict:
        """Retrieve active cohorts, with pagination and optional name search."""
        params = {"page": page, "pageSize": page_size, "status": "active"}
        if query is not None:
            params["query"] = query
        return await call(ctx, "GET", "api/academic/cohorts", params=params)

    @server.tool(annotations=READ)
    async def get_planning_options(ctx: Context, semester_id: PositiveId | None = None) -> dict:
        """Read semesters, courses, cohorts, eligible lecturers/rooms and teaching windows."""
        return await call(ctx, "GET", "api/planning-options",
                          params={"semesterId": semester_id} if semester_id else {})

    @server.tool(annotations=READ)
    async def get_course_constraints(ctx: Context, course_id: PositiveId, semester_id: PositiveId) -> dict:
        """Read the course planning period and allowed teaching windows."""
        return await call(ctx, "GET", f"api/courses/{course_id}/generation-constraints",
                          params={"semesterId": semester_id})

    @server.tool(annotations=READ)
    async def get_schedule_lifecycle(ctx: Context, semester_id: PositiveId) -> dict:
        """Read lifecycle state, working revision and state token before saving sessions."""
        return await call(ctx, "GET", f"api/semesters/{semester_id}/schedule-lifecycle")

    @server.tool(annotations=READ)
    async def get_saved_plans(ctx: Context, semester_id: PositiveId) -> list[dict]:
        """Retrieve saved draft schedules, sessions and validation alerts for a semester."""
        return await call(ctx, "GET", "api/draft-schedules", params={"semesterId": semester_id})

    @server.tool(annotations=WRITE)
    async def create_working_revision(ctx: Context, semester_id: PositiveId, expected_state_token: str) -> dict:
        """Create a working revision when needed, using the freshly read lifecycle state token."""
        return await call(ctx, "POST", f"api/semesters/{semester_id}/schedule-revisions",
                          json={"expectedStateToken": expected_state_token})

    @server.tool(annotations=WRITE)
    async def save_plan_session(ctx: Context, course_id: PositiveId, session: NewSession) -> dict:
        """Persist one new draft session. Each call commits separately; returns saved plan and alerts.

        Read options, constraints, saved plans and lifecycle first. Supply the current working
        revision ID. The API validates resources, units and dates; inspect validationAlerts.
        """
        return await call(ctx, "POST", f"api/courses/{course_id}/draft-schedule/sessions",
                          json=api_payload(session))

    @server.tool(annotations=WRITE)
    async def update_plan_session(ctx: Context, session_id: PositiveId, session: SessionUpdate) -> dict:
        """Save edits to an existing draft session using the current working revision ID.

        Reread the saved plan first. Omitted lecturer/units preserve existing values.
        """
        return await call(ctx, "PATCH", f"api/draft-sessions/{session_id}", json=api_payload(session))

    return server


def main():
    try:
        settings = Settings.from_environment()
    except ValueError as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(2) from None
    create_server(settings).run(transport="stdio")


if __name__ == "__main__":
    main()
