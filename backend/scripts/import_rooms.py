"""Import a CAMPUSonline room export through the planner API (stdlib only)."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import getpass
import hashlib
from http.cookiejar import CookieJar
import json
import os
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener
from uuid import uuid4


class ImportFailure(Exception):
    pass


def key(code: str) -> str:
    return code.strip().casefold()


def read_export(path: Path) -> tuple[list[dict], list[dict], int]:
    document = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(document, dict) or not isinstance(document.get("resource"), list):
        raise ImportFailure("Expected a CAMPUSonline JSON object with a resource array.")
    unique: dict[str, dict] = {}
    duplicates = 0
    for index, resource in enumerate(document["resource"], 1):
        try:
            row = resource["content"]["MEINE_RAUM_V"]
            code = row["RAUMCODE"].strip()
        except (KeyError, TypeError, AttributeError):
            raise ImportFailure(f"Invalid room structure or code at source row {index}.") from None
        if not code or len(code) > 100:
            raise ImportFailure(f"Empty or oversized room code at source row {index}.")
        normalized = key(code)
        if normalized in unique:
            if unique[normalized] != row:
                raise ImportFailure(f"Conflicting duplicate source records for {code}; resolve before import.")
            duplicates += 1
        else:
            unique[normalized] = row

    rooms, skipped = [], []
    for row in unique.values():
        code, capacity = row["RAUMCODE"].strip(), row.get("SITZPLAETZE")
        if type(capacity) is not int or capacity <= 0:
            skipped.append({"referenceCode": code, "status": "skipped", "reason": "missing_or_invalid_capacity"})
            continue
        building = row.get("GEBAEUDE")
        if building is not None and not isinstance(building, str):
            raise ImportFailure(f"Invalid building for {code}.")
        name = f"{code} – {building.strip()}" if building and building.strip() else code
        if len(name) > 200:
            raise ImportFailure(f"Suggested room name for {code} exceeds 200 characters.")
        rooms.append({"name": name, "referenceCode": code, "capacity": capacity})
    return rooms, skipped, duplicates


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        # Never forward credentials or a write to an unexpected destination.
        return None


class PlannerAPI:
    def __init__(self, base_url: str):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise ImportFailure("Use the planner base URL, without credentials, query or fragment.")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise ImportFailure("Use HTTPS for remote planner access; HTTP is allowed only on localhost.")
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(NoRedirect(), HTTPCookieProcessor(CookieJar()))

    def request(self, method: str, path: str, payload: dict | None = None):
        headers = {"Accept": "application/json", "X-Planner-Activity": "user"}
        if method != "GET":
            headers.update({"Content-Type": "application/json", "X-CSRF-Protection": "1"})
        request = Request(self.base_url + path, method=method, headers=headers,
                          data=None if payload is None else json.dumps(payload).encode("utf-8"))
        try:
            with self.opener.open(request, timeout=45) as response:
                body = response.read()
                return json.loads(body) if body else None
        except HTTPError as exc:
            # Do not log request bodies, cookies, credentials, or arbitrary server HTML.
            raise ImportFailure(f"{method} {path.split('?')[0]}: HTTP {exc.code}.") from None
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise ImportFailure(
                f"{method} {path.split('?')[0]} failed ({type(exc).__name__}). "
                "A write may have succeeded: rerun to reconcile, do not blindly retry POST."
            ) from None

    def list_rooms(self) -> dict[str, dict]:
        result = {}
        page = 1
        while True:
            data = self.request("GET", "/api/resources/rooms?" + urlencode(
                {"status": "all", "page": page, "pageSize": 200}))
            if not isinstance(data, dict) or not isinstance(data.get("items"), list):
                raise ImportFailure("Unexpected room-list response; check the planner URL and version.")
            for room in data["items"]:
                normalized = key(room["referenceCode"])
                if normalized in result:
                    raise ImportFailure("Room listing contains duplicate reference codes; no safe import possible.")
                result[normalized] = room
            if len(result) >= data["total"]:
                return result
            if not data["items"]:
                raise ImportFailure("Incomplete pagination of existing rooms.")
            page += 1


def same_room(existing: dict, proposed: dict) -> bool:
    return (existing.get("name") == proposed["name"]
            and existing.get("capacity") == proposed["capacity"]
            and existing.get("isActive") is True)


def plan_rooms(rooms: list[dict], existing: dict[str, dict]) -> list[dict]:
    plan = []
    for room in rooms:
        prior = existing.get(key(room["referenceCode"]))
        entry = {"room": room, "status": "would_create"}
        if prior is not None:
            entry.update({"status": "existing" if same_room(prior, room) else "conflict",
                          "id": prior["id"], "existing": prior})
        plan.append(entry)
    return plan


def write_report(path: Path, report: dict) -> None:
    # Replace atomically so interrupted imports retain the last completed step.
    temporary = path.with_suffix(".tmp")
    temporary.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def apply_plan(api: PlannerAPI, report: dict, report_path: Path) -> None:
    for entry in report["plan"]:
        if entry["status"] != "would_create":
            continue
        entry["status"] = "in_progress"
        write_report(report_path, report)
        try:
            created = api.request("POST", "/api/resources/rooms", entry["room"])
            entry["id"] = created["id"]
            entry["status"] = "created"
        except Exception:
            entry["status"] = "uncertain_or_failed"
            write_report(report_path, report)
            raise
        write_report(report_path, report)
    verified = api.list_rooms()
    for entry in report["plan"]:
        if entry["status"] in {"created", "existing"}:
            actual = verified.get(key(entry["room"]["referenceCode"]))
            entry["verified"] = actual is not None and same_room(actual, entry["room"])
            if not entry["verified"]:
                write_report(report_path, report)
                raise ImportFailure("Post-import verification failed; inspect the report.")
    report["verified"] = True
    write_report(report_path, report)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="Original CAMPUSonline rooms.json")
    parser.add_argument("--base-url", help="Planner HTTPS base URL; omit for offline preview")
    parser.add_argument("--username", help="Planner account login (not the Linux sudo user)")
    parser.add_argument("--password-env", help="Optional environment variable containing the password")
    parser.add_argument("--apply", action="store_true", help="Create missing rooms; otherwise preview only")
    parser.add_argument("--report-dir", type=Path, help="Default: import-reports beside the input file")
    args = parser.parse_args(argv)
    if args.apply and not args.base_url:
        parser.error("--apply requires --base-url")
    report = None
    report_path = None
    api = None
    logged_in = False
    try:
        rooms, skipped, duplicates = read_export(args.input)
        report_dir = args.report_dir or args.input.resolve().parent / "import-reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = report_dir / f"rooms-{stamp}-{uuid4().hex[:8]}.json"
        report = {"source": str(args.input.resolve()),
                  "sourceSha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                  "createdAt": datetime.now(timezone.utc).isoformat(),
                  "baseUrl": args.base_url, "apply": args.apply,
                  "validUniqueRooms": len(rooms), "identicalDuplicatesRemoved": duplicates,
                  "skipped": skipped, "plan": [], "status": "preparing"}
        write_report(report_path, report)
        if args.base_url:
            api = PlannerAPI(args.base_url)
            username = args.username or input("Planner login: ").strip()
            if args.password_env:
                password = os.environ.get(args.password_env)
                if not password:
                    raise ImportFailure("Password environment variable is empty or missing.")
            else:
                if not sys.stdin.isatty():
                    raise ImportFailure("Interactive password entry needs a terminal; use docker exec -it or --password-env.")
                password = getpass.getpass("Planner password (not saved): ")
            try:
                api.request("POST", "/api/auth/login", {"loginName": username, "password": password})
                logged_in = True
            finally:
                password = None
            report["plan"] = plan_rooms(rooms, api.list_rooms())
        else:
            report["plan"] = [{"room": room, "status": "candidate"} for room in rooms]
        report["status"] = "preview"
        write_report(report_path, report)
        if args.apply:
            report["status"] = "running"
            write_report(report_path, report)
            apply_plan(api, report, report_path)
            report["status"] = "completed"
            write_report(report_path, report)
        counts = Counter(entry["status"] for entry in report["plan"])
        print(f"Valid unique rooms: {len(rooms)}; skipped: {len(skipped)}; duplicate rows removed: {duplicates}")
        print("Results: " + ", ".join(f"{status}={count}" for status, count in sorted(counts.items())))
        print(f"Report: {report_path}")
        return 2 if counts["conflict"] else 0
    except (ImportFailure, OSError, ValueError, KeyError, TypeError, EOFError, KeyboardInterrupt) as exc:
        message = str(exc) if isinstance(exc, ImportFailure) else f"Import stopped ({type(exc).__name__})."
        if report is not None and report_path is not None:
            report.update({"status": "failed", "error": message})
            write_report(report_path, report)
        print(message, file=sys.stderr)
        if report_path:
            print(f"Report: {report_path}", file=sys.stderr)
        return 1
    finally:
        if api is not None and logged_in:
            try:
                api.request("POST", "/api/auth/logout")
            except ImportFailure:
                print("Could not close the import login session; it expires under normal server rules.", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
