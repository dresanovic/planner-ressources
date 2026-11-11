from __future__ import annotations

import asyncio
import os
import sys
from dataclasses import dataclass, field
from urllib.parse import urlsplit

import httpx


class PlannerError(Exception):
    """A safe error suitable for returning to the MCP caller."""


def _windows_user_variable(name: str) -> str | None:
    """Read a saved user variable even when the parent process predates it."""
    if sys.platform != "win32":
        return None
    import winreg

    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, "Environment") as key:
            value, kind = winreg.QueryValueEx(key, name)
    except OSError:
        return None
    return value if kind in {winreg.REG_SZ, winreg.REG_EXPAND_SZ} and isinstance(value, str) else None


def _setting_value(name: str, default: str = "") -> str:
    # An explicitly supplied value (including empty) always wins.
    if name in os.environ:
        return os.environ[name]
    saved = _windows_user_variable(name)
    return saved if saved is not None else default


@dataclass(frozen=True)
class Settings:
    base_url: str
    login_name: str
    password: str = field(repr=False)

    def __post_init__(self):
        url = urlsplit(self.base_url)
        if (
            url.scheme not in {"http", "https"}
            or not url.hostname
            or url.username is not None
            or url.password is not None
            or url.query
            or url.fragment
        ):
            raise ValueError("PLANNER_API_URL must be an HTTP(S) base URL without credentials, query or fragment.")
        if url.scheme == "http" and url.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ValueError("Use HTTPS for a remote PLANNER_API_URL.")
        if not self.login_name or not self.password:
            raise ValueError("Set PLANNER_LOGIN_NAME and PLANNER_PASSWORD before starting the server.")

    @classmethod
    def from_environment(cls) -> Settings:
        return cls(
            _setting_value("PLANNER_API_URL", "http://127.0.0.1:8000"),
            _setting_value("PLANNER_LOGIN_NAME"),
            _setting_value("PLANNER_PASSWORD"),
        )


class PlannerClient:
    def __init__(self, settings: Settings, *, transport=None):
        self.settings = settings
        self.http = httpx.AsyncClient(
            base_url=settings.base_url.rstrip("/") + "/",
            headers={"X-CSRF-Protection": "1", "X-Planner-Activity": "user"},
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=False,
            transport=transport,
        )
        self._logged_in = False
        self._lock = asyncio.Lock()

    async def close(self):
        await self.http.aclose()

    async def _send(self, method: str, path: str, **kwargs) -> httpx.Response:
        try:
            return await self.http.request(method, path.lstrip("/"), **kwargs)
        except httpx.RequestError:
            raise PlannerError(
                "Planner API connection failed or timed out. For writes, the outcome may be unknown; "
                "read the saved plan before attempting another write."
            ) from None

    @staticmethod
    def _check(response: httpx.Response):
        if response.is_success:
            return
        if response.status_code == 401:
            raise PlannerError("Planner authentication failed or session expired. Check credentials and restart the MCP server.")
        if response.status_code in {400, 403, 404, 409, 415, 422}:
            # Preserve domain validation codes, including lifecycle conflicts.
            try:
                detail = response.json()
            except ValueError:
                detail = "No JSON error details."
            raise PlannerError(f"Planner API HTTP {response.status_code}: {detail}")
        raise PlannerError(f"Planner API HTTP {response.status_code}. Read the saved plan before retrying any write.")

    async def request(self, method: str, path: str, **kwargs):
        # Serialize login and calls because the client owns one cookie session.
        async with self._lock:
            if not self._logged_in:
                response = await self._send("POST", "api/auth/login", json={
                    "loginName": self.settings.login_name,
                    "password": self.settings.password,
                })
                self._check(response)
                self._logged_in = True
            response = await self._send(method, path, **kwargs)
            # Never silently log in again/replay a write after session revocation.
            self._check(response)
            return response.json() if response.content else None
