"""Preview/import lecturers, courses, or institution holidays through the planner API.

Keep import_rooms.py beside this script; its authenticated HTTP client is reused.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import date, datetime, timezone
import getpass
import hashlib
import json
import os
from pathlib import Path
import sys
from uuid import uuid4

from import_rooms import ImportFailure, PlannerAPI, key, write_report


def list_all(api, path):
    if path == "/api/holidays":
        data = api.request("GET", path)
        if not isinstance(data, list) or len({row["date"] for row in data}) != len(data):
            raise ImportFailure("Unexpected holiday list or duplicate dates on server.")
        return data
    rows, page = [], 1
    while True:
        data = api.request("GET", f"{path}?status=all&page={page}&pageSize=200")
        if not isinstance(data, dict) or not isinstance(data.get("items"), list):
            raise ImportFailure(f"Unexpected catalog response: {path}")
        rows.extend(data["items"])
        if len(rows) >= data["total"]:
            if len({r['id'] for r in rows}) != len(rows):
                raise ImportFailure(f"Duplicate records in paginated response: {path}")
            return rows
        if not data["items"]:
            raise ImportFailure(f"Incomplete catalog response: {path}")
        page += 1


def find_active(rows, field, value, label):
    if not isinstance(value, str) or not value.strip():
        raise ImportFailure(f"Missing {label}.")
    matches = [row for row in rows if key(row[field]) == key(value)]
    if len(matches) != 1:
        raise ImportFailure(f"{label} must match exactly one existing record: {value}")
    if not matches[0].get("isActive"):
        raise ImportFailure(f"Inactive {label}: {value}")
    return matches[0]


def holiday_plan(document, existing=None):
    start, end = date.fromisoformat(document["rangeStart"]), date.fromisoformat(document["rangeEnd"])
    if start > end:
        raise ImportFailure("Holiday range start must not be after its end.")
    plan, seen = [], set()
    for row in document["holidays"]:
        day, name = row["date"], row["name"]
        if not isinstance(day, str) or date.fromisoformat(day).isoformat() != day:
            raise ImportFailure("Holiday dates must use YYYY-MM-DD.")
        if not start <= date.fromisoformat(day) <= end:
            raise ImportFailure(f"Holiday outside requested semester range: {day}")
        if day in seen:
            raise ImportFailure(f"Duplicate holiday date in source: {day}")
        seen.add(day)
        if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
            raise ImportFailure("Holiday name must have 1 to 200 characters.")
        payload = {"date": day, "name": name.strip()}
        entry = {"sourceKey": day, "payload": payload, "status": "candidate"}
        if existing is not None:
            matches = [prior for prior in existing if prior["date"] == day]
            if len(matches) > 1:
                raise ImportFailure("Ambiguous existing holiday date.")
            entry["status"] = "would_create"
            if matches:
                prior = matches[0]
                entry.update({"id": prior["id"], "status": "existing" if matches_payload("holidays", prior, payload) else "conflict"})
        plan.append(entry)
    return plan


def lecturer_plan(document, existing=None):
    plan, seen = [], set()
    for lecturer in document["lecturers"]:
        payload = {field: lecturer[field] for field in ("name", "referenceCode")}
        if not all(isinstance(v, str) and v.strip() for v in payload.values()):
            raise ImportFailure("Lecturer name and referenceCode are required.")
        payload = {field: value.strip() for field, value in payload.items()}
        if len(payload["name"]) > 200 or len(payload["referenceCode"]) > 100:
            raise ImportFailure("Oversized lecturer name or referenceCode.")
        ref = key(payload["referenceCode"])
        if ref in seen:
            raise ImportFailure("Duplicate lecturer referenceCode in input.")
        seen.add(ref)
        entry = {"sourceKey": payload["referenceCode"], "payload": payload, "status": "candidate"}
        if existing is not None:
            matches = [r for r in existing if key(r["referenceCode"]) == ref]
            if len(matches) > 1:
                raise ImportFailure("Duplicate lecturer referenceCode on server.")
            entry["status"] = "would_create"
            if matches:
                prior = matches[0]
                entry.update({"id": prior["id"], "status": "existing" if matches_payload("lecturers", prior, payload) else "conflict"})
        plan.append(entry)
    return plan


def course_plan(document, mapping, catalogs=None, minimum=None, maximum=None, api=None):
    course_rows = document["courses"]
    sources = {row["sourceCourseId"]: row for row in course_rows}
    if len(sources) != len(course_rows):
        raise ImportFailure("Duplicate source course IDs.")
    entries = mapping["courses"]
    if len({r["sourceCourseId"] for r in entries}) != len(entries):
        raise ImportFailure("Duplicate mapping source course IDs.")
    if set(sources) != {r["sourceCourseId"] for r in entries}:
        raise ImportFailure("Mapping must cover exactly the source course IDs; use include=false to omit rows.")
    plan, seen_names = [], set()
    for row in entries:
        entry = {"sourceKey": row["sourceCourseId"], "code": sources[row["sourceCourseId"]]["code"]}
        plan.append(entry)
        try:
            if type(row.get("include")) is not bool:
                raise ImportFailure("include must be true or false.")
            if not row["include"]:
                entry.update({"status": "skipped", "reason": row.get("note", "excluded_by_mapping")})
                continue
            name = row.get("name")
            if not isinstance(name, str) or not name.strip() or len(name.strip()) > 200:
                raise ImportFailure("A unique course name of at most 200 characters is required.")
            if key(name) in seen_names:
                raise ImportFailure("Duplicate normalized course name in mapping.")
            seen_names.add(key(name))
            total = row.get("totalUnits")
            lower = row.get("minSessionUnits") if row.get("minSessionUnits") is not None else minimum
            upper = row.get("maxSessionUnits") if row.get("maxSessionUnits") is not None else maximum
            if any(type(v) is not int or v <= 0 for v in (total, lower, upper)) or not lower <= upper <= total:
                raise ImportFailure("Require positive integers with minSessionUnits <= maxSessionUnits <= totalUnits.")
            preferred = row.get("preferredSessionUnits")
            if preferred is not None and (type(preferred) is not int or 2 * preferred != lower + upper):
                raise ImportFailure("The optimizer prefers the midpoint of min/max; preferredSessionUnits must match it.")
            lookup = {"semesterName": mapping.get("semesterName"),
                      **{k: row.get(k) for k in ("cohortName", "lecturerReferenceCode", "roomReferenceCode")}}
            missing = [k for k, v in lookup.items() if not isinstance(v, str) or not v.strip()]
            if missing:
                raise ImportFailure("Missing mapping fields: " + ", ".join(missing))
            additional = row.get("additionalLecturerReferenceCodes", [])
            if (not isinstance(additional, list) or any(not isinstance(v, str) or not v.strip() for v in additional)
                    or len({key(v) for v in [lookup["lecturerReferenceCode"], *additional]}) != len(additional) + 1):
                raise ImportFailure("Additional lecturer references must be a list of distinct nonempty codes, excluding the initial lecturer.")
            additional_rooms = row.get("additionalRoomReferenceCodes", [])
            if (not isinstance(additional_rooms, list) or any(not isinstance(v, str) or not v.strip() for v in additional_rooms)
                    or len({key(v) for v in [lookup["roomReferenceCode"], *additional_rooms]}) != len(additional_rooms) + 1):
                raise ImportFailure("Additional room references must be distinct nonempty codes, excluding the initial room.")
            payload = {"name": name.strip(), "totalUnits": total, "minSessionUnits": lower, "maxSessionUnits": upper}
            entry.update({"status": "candidate", "lookup": lookup, "payload": payload})
            if catalogs is None:
                continue
            relations = {}
            for group, field, value_field in (
                ("semesters", "semesterId", "semesterName"), ("cohorts", "cohortId", "cohortName"),
                ("lecturers", "lecturerId", "lecturerReferenceCode"), ("rooms", "roomId", "roomReferenceCode")):
                relation = find_active(catalogs[group], "referenceCode" if group in {"lecturers", "rooms"} else "name",
                                       lookup[value_field], value_field)
                payload[field] = relation["id"]
                relations[group] = relation
            extra_rooms = [find_active(catalogs["rooms"], "referenceCode", ref, "additionalRoomReferenceCode")
                           for ref in additional_rooms]
            if additional or additional_rooms:
                entry["eligibility"] = {"lecturerIds": [payload["lecturerId"], *[
                    find_active(catalogs["lecturers"], "referenceCode", reference, "additionalLecturerReferenceCode")["id"]
                    for reference in additional]], "roomIds": [payload["roomId"], *[r["id"] for r in extra_rooms]]}
            if any(r["capacity"] < relations["cohorts"]["studentCount"] for r in [relations["rooms"], *extra_rooms]):
                raise ImportFailure("Selected room is smaller than the cohort.")
            calendar = next((c for c in catalogs.get('cohort-calendars',[]) if c.get('cohortId')==payload['cohortId'] and c.get('semesterId')==payload['semesterId'] and c.get('isActive')),None)
            if calendar is None or not any(window.get("isActive") for window in calendar.get("timeWindows", [])):
                raise ImportFailure("Cohort semester calendar has no active time windows; complete them before importing courses.")
            matches = [r for r in catalogs["courses"] if key(r["name"]) == key(name)]
            entry["status"] = "would_create"
            if len(matches) > 1:
                raise ImportFailure("Ambiguous existing course name.")
            if matches:
                prior = matches[0]
                entry.update({"id": prior["id"], "status": "existing" if matches_entry("courses", prior, entry) else "conflict"})
                if entry["status"] == "existing" and entry.get("eligibility"):
                    if api is None:
                        raise ImportFailure("Online API is required to verify multiple lecturer eligibility.")
                    state, _ = eligibility_state(api, prior["id"], entry["eligibility"])
                    entry["status"] = {"equal": "existing", "expand": "would_configure", "conflict": "conflict"}[state]
        except ImportFailure as exc:
            entry.update({"status": "blocked", "reason": str(exc)})
    return plan


def matches_payload(kind, actual, payload):
    if kind == "holidays":
        return actual.get("date") == payload["date"] and key(actual.get("name", "")) == key(payload["name"])
    if actual.get("isActive") is not True:
        return False
    if kind == "lecturers":
        return actual.get("name") == payload["name"] and key(actual.get("referenceCode", "")) == key(payload["referenceCode"])
    if any(actual.get(k) != payload[k] for k in ("name", "totalUnits", "minSessionUnits", "maxSessionUnits")):
        return False
    return all((actual.get(response) or {}).get("id") == payload[field]
               for response, field in (("semester", "semesterId"), ("cohort", "cohortId"),
 ("lecturer", "lecturerId"), ("room", "roomId")))


def matches_entry(kind, actual, entry):
    if kind == "courses" and entry.get("eligibility"):
        # The course summary can expose any one of its eligible resources.
        lecturer_id = (actual.get("lecturer") or {}).get("id")
        room_id = (actual.get("room") or {}).get("id")
        if lecturer_id not in entry["eligibility"]["lecturerIds"] or room_id not in entry["eligibility"]["roomIds"]:
            return False
        actual = {**actual, "lecturer": {"id": entry["payload"]["lecturerId"]}, "room": {"id": entry["payload"]["roomId"]}}
    return matches_payload(kind, actual, entry["payload"])


def eligibility_state(api, course_id, desired):
    current = api.request("GET", f"/api/academic/courses/{course_id}/resource-eligibility")
    lecturers = set(current["eligibleLecturerIds"])
    rooms = set(current["eligibleRoomIds"])
    wanted_lecturers, wanted_rooms = set(desired["lecturerIds"]), set(desired["roomIds"])
    if lecturers == wanted_lecturers and rooms == wanted_rooms:
        return "equal", current
    if lecturers and rooms and lecturers <= wanted_lecturers and rooms <= wanted_rooms:
        return "expand", current
    return "conflict", current


def configure_eligibility(api, entry):
    state, current = eligibility_state(api, entry["id"], entry["eligibility"])
    if state == "conflict":
        raise ImportFailure("Existing eligible resources differ from the requested mapping; no resources were removed.")
    if state == "expand":
        api.request("PUT", f"/api/academic/courses/{entry['id']}/resource-eligibility",
                    {"expectedRevision": current["courseRevision"], **entry["eligibility"]})


def apply_plan(api, kind, report, report_path):
    if any(e["status"] in {"blocked", "conflict"} for e in report["plan"]):
        raise ImportFailure("Preflight contains blocked/conflicting records; no new records were written.")
    endpoint = {"lecturers": "/api/resources/lecturers", "courses": "/api/academic/courses", "holidays": "/api/holidays"}[kind]
    for entry in report["plan"]:
        if entry["status"] not in {"would_create", "would_configure"}:
            continue
        create = entry["status"] == "would_create"
        entry["status"] = "in_progress"
        write_report(report_path, report)
        try:
            if create:
                result = api.request("POST", endpoint, entry["payload"])
                entry["id"] = result["id"]
            if entry.get("eligibility"):
                entry["status"] = "configuration_pending"
                write_report(report_path, report)
                configure_eligibility(api, entry)
            entry["status"] = "created" if create else "configured"
        except BaseException:
            entry["status"] = "uncertain_or_failed"
            write_report(report_path, report)
            raise
        write_report(report_path, report)
    saved = {r["id"]: r for r in list_all(api, endpoint)}
    for entry in report["plan"]:
        if entry["status"] in {"created", "existing", "configured"}:
            entry["verified"] = matches_entry(kind, saved.get(entry["id"], {}), entry)
            if entry.get("eligibility"):
                entry["verified"] = entry["verified"] and eligibility_state(api, entry["id"], entry["eligibility"])[0] == "equal"
            if not entry["verified"]:
                write_report(report_path, report)
                raise ImportFailure("Post-import verification failed; inspect the report.")
    report["verified"] = True
    write_report(report_path, report)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kind", choices=["lecturers", "courses", "holidays"])
    parser.add_argument("input", type=Path)
    parser.add_argument("--mapping", type=Path, help="Required for courses")
    parser.add_argument("--min-session-units", type=int, help="Fallback if a mapping row leaves this null")
    parser.add_argument("--max-session-units", type=int, help="Fallback if a mapping row leaves this null")
    parser.add_argument("--base-url")
    parser.add_argument("--username")
    parser.add_argument("--password-env")
    parser.add_argument("--report-dir", type=Path)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if args.apply and not args.base_url:
        parser.error("--apply requires --base-url")
    if args.kind == "courses" and not args.mapping:
        parser.error("courses requires --mapping")
    api, logged_in, report, report_path = None, False, None, None
    try:
        document = json.loads(args.input.read_text(encoding="utf-8-sig"))
        mapping = json.loads(args.mapping.read_text(encoding="utf-8-sig")) if args.mapping else None
        local_plan = (lecturer_plan(document) if args.kind == "lecturers" else holiday_plan(document)
                      if args.kind == "holidays" else course_plan(
                          document, mapping, minimum=args.min_session_units, maximum=args.max_session_units))
        directory = args.report_dir or args.input.resolve().parent / "import-reports"
        directory.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        report_path = directory / f"{args.kind}-{stamp}-{uuid4().hex[:8]}.json"
        report = {"kind": args.kind, "source": str(args.input.resolve()),
                  "sourceSha256": hashlib.sha256(args.input.read_bytes()).hexdigest(),
                  "mappingSha256": hashlib.sha256(args.mapping.read_bytes()).hexdigest() if args.mapping else None,
                  "baseUrl": args.base_url, "apply": args.apply, "plan": local_plan, "status": "preview"}
        write_report(report_path, report)
        if args.base_url and not any(e["status"] == "blocked" for e in local_plan):
            api = PlannerAPI(args.base_url)
            username = args.username or input("Planner login: ").strip()
            password = os.environ.get(args.password_env) if args.password_env else None
            if args.password_env and not password:
                raise ImportFailure("Password environment variable is empty or missing.")
            if not args.password_env:
                if not sys.stdin.isatty():
                    raise ImportFailure("Interactive password entry requires a terminal (docker exec -it).")
                password = getpass.getpass("Planner password (not saved): ")
            try:
                api.request("POST", "/api/auth/login", {"loginName": username, "password": password})
                logged_in = True
            finally:
                password = None
            if args.kind == "lecturers":
                report["plan"] = lecturer_plan(document, list_all(api, "/api/resources/lecturers"))
            elif args.kind == "holidays":
                report["plan"] = holiday_plan(document, list_all(api, "/api/holidays"))
            else:
                catalogs = {group: list_all(api, "/api/" + ("resources/" if group in {"lecturers", "rooms"} else "academic/") + group)
                            for group in ("semesters", "cohorts", "cohort-calendars", "lecturers", "rooms", "courses")}
                report["plan"] = course_plan(document, mapping, catalogs, args.min_session_units, args.max_session_units, api)
            write_report(report_path, report)
        issues = any(e["status"] in {"blocked", "conflict"} for e in report["plan"])
        if args.apply and not issues:
            report["status"] = "running"
            write_report(report_path, report)
            apply_plan(api, args.kind, report, report_path)
            report["status"] = "completed"
            write_report(report_path, report)
        elif issues:
            report["status"] = "needs_resolution"
            write_report(report_path, report)
        counts = Counter(e["status"] for e in report["plan"])
        print("Results: " + ", ".join(f"{k}={v}" for k, v in sorted(counts.items())))
        print(f"Report: {report_path}")
        if issues:
            print("Resolve blocked/conflicting records before applying; no new records were written.")
        return 2 if issues else 0
    except (ImportFailure, OSError, ValueError, KeyError, TypeError, EOFError, KeyboardInterrupt) as exc:
        message = str(exc) if isinstance(exc, ImportFailure) else f"Import stopped ({type(exc).__name__})."
        if report is not None and report_path:
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
                print("Import session could not be closed; normal server expiration applies.", file=sys.stderr)


if __name__ == "__main__":
    raise SystemExit(main())
