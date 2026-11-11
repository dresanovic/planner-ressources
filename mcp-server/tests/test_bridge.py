import asyncio
import json
import os
import sys
import threading
from contextlib import nullcontext
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import httpx
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from planner_resource_mcp.client import PlannerClient, PlannerError, Settings
from planner_resource_mcp import client as client_module
from planner_resource_mcp.server import NewSession, api_payload, create_server


def run(coro):
    return asyncio.run(coro)


def test_saved_windows_variables_work_without_parent_environment(monkeypatch):
    values = {"PLANNER_LOGIN_NAME": "saved-user", "PLANNER_PASSWORD": "saved-password"}
    for name in ("PLANNER_LOGIN_NAME", "PLANNER_PASSWORD", "PLANNER_API_URL"):
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setattr(client_module, "_windows_user_variable", values.get)
    settings = Settings.from_environment()
    assert settings.login_name == "saved-user"
    assert settings.password == "saved-password"
    assert settings.base_url == "http://127.0.0.1:8000"
    assert "saved-password" not in repr(settings)


def test_process_variables_override_saved_windows_variables(monkeypatch):
    monkeypatch.setattr(client_module, "_windows_user_variable", lambda name: "saved-value")
    monkeypatch.setenv("PLANNER_API_URL", "http://localhost:9000")
    monkeypatch.setenv("PLANNER_LOGIN_NAME", "explicit-user")
    monkeypatch.setenv("PLANNER_PASSWORD", "explicit-password")
    settings = Settings.from_environment()
    assert settings.login_name == "explicit-user"
    assert settings.password == "explicit-password"
    monkeypatch.setenv("PLANNER_PASSWORD", "")
    with pytest.raises(ValueError, match="PLANNER_PASSWORD"):
        Settings.from_environment()


def test_windows_registry_read_and_missing_key(monkeypatch):
    monkeypatch.setattr(client_module, "sys", SimpleNamespace(platform="win32"))
    registry = SimpleNamespace(HKEY_CURRENT_USER=1, REG_SZ=1, REG_EXPAND_SZ=2,
        OpenKey=lambda hive, key: nullcontext("key"),
        QueryValueEx=lambda key, name: ("saved", 1))
    monkeypatch.setitem(sys.modules, "winreg", registry)
    assert client_module._windows_user_variable("PLANNER_PASSWORD") == "saved"
    registry.QueryValueEx = lambda key, name: (b"invalid type", 3)
    assert client_module._windows_user_variable("PLANNER_PASSWORD") is None
    def unavailable(hive, key):
        raise FileNotFoundError()
    registry.OpenKey = unavailable
    assert client_module._windows_user_variable("PLANNER_PASSWORD") is None
    monkeypatch.setattr(client_module, "sys", SimpleNamespace(platform="linux"))
    assert client_module._windows_user_variable("PLANNER_PASSWORD") is None


def test_cookie_login_and_prefixed_api_request():
    seen = []

    def handler(request):
        seen.append(request)
        assert request.headers["x-csrf-protection"] == "1"
        assert request.headers["x-planner-activity"] == "user"
        if request.url.path.endswith("/login"):
            assert json.loads(request.content) == {"loginName": "planner", "password": "private"}
            return httpx.Response(200, json={}, headers={"set-cookie": "planner_session=abc; Path=/; HttpOnly"})
        assert request.headers["cookie"] == "planner_session=abc"
        assert "private" not in str(request.url)
        return httpx.Response(200, json={"items": [{"id": 1}]})

    async def scenario():
        client = PlannerClient(Settings("http://localhost/planner", "planner", "private"),
                               transport=httpx.MockTransport(handler))
        try:
            await client.request("GET", "api/academic/cohorts", params={"page": 2})
            await client.request("GET", "api/draft-schedules")
        finally:
            await client.close()
    run(scenario())
    assert [request.url.path for request in seen] == [
        "/planner/api/auth/login", "/planner/api/academic/cohorts", "/planner/api/draft-schedules"]
    assert seen[1].url.params["page"] == "2"


@pytest.mark.parametrize("status,detail", [(401, "expired"), (409, "STALE_WORKING_REVISION"),
                                          (422, "INVALID_SESSION_UNITS"), (500, "private internal error"),
                                          (302, "redirect")])
def test_api_failures_are_errors_and_writes_are_not_retried(status, detail):
    writes = []

    def handler(request):
        if request.url.path.endswith("/login"):
            return httpx.Response(200, json={})
        writes.append(request)
        return httpx.Response(status, json={"code": detail})

    async def scenario():
        client = PlannerClient(Settings("http://localhost", "planner", "private"),
                               transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(PlannerError) as exc:
                await client.request("POST", "api/courses/1/draft-schedule/sessions", json={})
            if status in {409, 422}:
                assert detail in str(exc.value)
            assert "private" not in str(exc.value)
        finally:
            await client.close()
    run(scenario())
    assert len(writes) == 1


def test_login_failure_never_sends_write():
    seen = []
    def handler(request):
        seen.append(request)
        return httpx.Response(401, json={})

    async def scenario():
        client = PlannerClient(Settings("http://localhost", "planner", "private"),
                               transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(PlannerError, match="authentication"):
                await client.request("POST", "api/courses/1/draft-schedule/sessions", json={})
        finally:
            await client.close()
    run(scenario())
    assert len(seen) == 1 and seen[0].url.path == "/api/auth/login"


def test_timeout_reports_unknown_write_outcome_without_replay():
    count = 0
    def handler(request):
        nonlocal count
        count += 1
        if request.url.path.endswith("/login"):
            return httpx.Response(200, json={})
        raise httpx.ReadTimeout("private", request=request)

    async def scenario():
        client = PlannerClient(Settings("http://localhost", "planner", "private"),
                               transport=httpx.MockTransport(handler))
        try:
            with pytest.raises(PlannerError, match="outcome may be unknown"):
                await client.request("POST", "api/courses/1/draft-schedule/sessions", json={})
        finally:
            await client.close()
    run(scenario())
    assert count == 2


@pytest.mark.parametrize("url", ["http://remote.example", "https://user:pass@example.org", "file:///tmp",
                                "https://example.org/?secret=x", "https://example.org/#fragment"])
def test_invalid_api_urls(url):
    with pytest.raises(ValueError):
        Settings(url, "user", "private")


def test_session_schema_and_payload():
    session = NewSession(semester_id=1, schedule_revision_id=2, date="2026-09-07",
                         start_time="08:00", end_time="09:30", units=2,
                         lecturer_id=3, cohort_id=4, room_id=5)
    assert api_payload(session) == {
        "semesterId": 1, "scheduleRevisionId": 2, "date": "2026-09-07",
        "startTime": "08:00", "endTime": "09:30", "units": 2,
        "lecturerId": 3, "cohortId": 4, "roomId": 5}
    for changes in [{"units": True}, {"units": 0}, {"start_time": "25:00"}, {"date": "bad"}]:
        with pytest.raises(ValueError):
            NewSession(**{**session.model_dump(), **changes})


def test_tool_discovery_and_annotations():
    async def scenario():
        tools = {tool.name: tool for tool in await create_server().list_tools()}
        assert len(tools) == 8
        assert tools["list_cohorts"].annotations.readOnlyHint
        assert not tools["save_plan_session"].annotations.readOnlyHint
        assert tools["save_plan_session"].inputSchema["$defs"]["NewSession"]["properties"]["units"]["minimum"] == 1
        assert "password" not in json.dumps([tool.inputSchema for tool in tools.values()])
    run(scenario())


def test_stdio_initialize_discover_read_save_and_error():
    calls = []
    saved = []

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def reply(self, status, payload, cookie=False):
            body = json.dumps(payload).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(body)))
            if cookie:
                self.send_header("Set-Cookie", "planner_session=abc; Path=/; HttpOnly")
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            calls.append(("GET", self.path))
            assert self.headers.get("Cookie") == "planner_session=abc"
            if self.path.startswith("/api/academic/cohorts"):
                self.reply(200, {"items": [{"id": 1, "name": "Cohort"}], "total": 1})
            elif self.path.startswith("/api/draft-schedules"):
                self.reply(200, saved)
            else:
                self.reply(200, {})

        def do_POST(self):
            payload = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
            calls.append(("POST", self.path))
            assert self.headers["X-CSRF-Protection"] == "1"
            if self.path == "/api/auth/login":
                assert payload == {"loginName": "planner", "password": "private"}
                self.reply(200, {}, cookie=True)
            else:
                assert self.headers.get("Cookie") == "planner_session=abc"
                if saved:
                    self.reply(422, {"errors": [{"code": "DUPLICATE_SESSION_DATE"}]})
                else:
                    saved.append(payload)
                    self.reply(201, {"draftSchedule": {"sessions": saved}})

    http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=http.serve_forever, daemon=True)
    thread.start()

    async def scenario():
        params = StdioServerParameters(command=sys.executable,
            args=["-m", "planner_resource_mcp.server"],
            env={**os.environ, "PLANNER_API_URL": f"http://127.0.0.1:{http.server_port}",
                 "PLANNER_LOGIN_NAME": "planner", "PLANNER_PASSWORD": "private"})
        async with stdio_client(params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                assert len((await session.list_tools()).tools) == 8
                result = await session.call_tool("list_cohorts", {})
                assert not result.isError and "Cohort" in result.content[0].text
                args = {"course_id": 7, "session": {"semester_id": 1, "schedule_revision_id": 2,
                        "date": "2026-09-07", "start_time": "08:00", "end_time": "09:30",
                        "units": 2, "lecturer_id": 3, "cohort_id": 4, "room_id": 5}}
                assert not (await session.call_tool("save_plan_session", args)).isError
                result = await session.call_tool("get_saved_plans", {"semester_id": 1})
                assert not result.isError and "2026-09-07" in result.content[0].text
                error = await session.call_tool("save_plan_session", args)
                assert error.isError and "DUPLICATE_SESSION_DATE" in error.content[0].text
    try:
        run(scenario())
    finally:
        http.shutdown()
        http.server_close()
        thread.join(timeout=5)
    assert saved[0]["scheduleRevisionId"] == 2
    assert calls.count(("POST", "/api/auth/login")) == 1
    assert calls.count(("POST", "/api/courses/7/draft-schedule/sessions")) == 2
