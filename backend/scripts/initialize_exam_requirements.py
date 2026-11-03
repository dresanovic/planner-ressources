"""Initialize missing exam requirements through the planner API (stdlib only)."""
from __future__ import annotations

import argparse
from collections import Counter
import getpass
from http.cookiejar import CookieJar
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import HTTPCookieProcessor, HTTPRedirectHandler, Request, build_opener


class InitializationError(Exception):
    pass


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


class PlannerAPI:
    def __init__(self, base_url: str):
        parsed = urlsplit(base_url)
        if (parsed.scheme not in {"http", "https"} or not parsed.hostname
                or parsed.username or parsed.password or parsed.query or parsed.fragment):
            raise InitializationError("Basis-URL ohne Zugangsdaten, Query oder Fragment angeben.")
        if parsed.scheme == "http" and parsed.hostname not in {"localhost", "127.0.0.1", "::1"}:
            raise InitializationError("Entfernter Zugriff erfordert HTTPS.")
        self.base_url = base_url.rstrip("/")
        self.opener = build_opener(NoRedirect(), HTTPCookieProcessor(CookieJar()))

    def request(self, method: str, path: str, payload=None):
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
            raise InitializationError(f"{method} {path}: HTTP {exc.code}.") from None
        except (URLError, TimeoutError, OSError, ValueError) as exc:
            raise InitializationError(
                f"{method} {path}: {type(exc).__name__}. Ein Schreibzugriff kann bereits "
                "gespeichert sein; erneute Ausführung prüft den Bestand.") from None


def build_plan(options: dict, overview: dict, semester_id: int) -> list[dict]:
    courses = {row["id"]: row for row in options["courses"]}
    active_lecturers = {row["id"] for row in options["lecturers"] if row["isActive"]}
    plan = []
    for state in overview["courses"]:
        entry = {"courseId": state["courseId"], "courseName": state["courseName"]}
        course = courses.get(state["courseId"])
        lecturer = course.get("lecturer") if course else None
        capacity = course.get("cohortSize") if course else None
        if state["configuration"] is not None:
            entry.update(status="existing", reason="Anforderung bereits gespeichert (bleibt unverändert).")
        elif state["activeExam"] is not None:
            entry.update(status="skipped", reason="Aktive Prüfung vorhanden.")
        elif course is None or course["semesterId"] != semester_id:
            entry.update(status="skipped", reason="LV oder zugehörige Stammdaten nicht aktiv/verfügbar.")
        elif not lecturer or lecturer["id"] not in active_lecturers:
            entry.update(status="skipped", reason="Keine aktive LV-Lehrperson vorhanden.")
        elif type(capacity) is not int or capacity <= 0:
            entry.update(status="skipped", reason="Keine gültige positive LV-Gruppengröße vorhanden.")
        else:
            entry.update(status="would_create", lecturerName=lecturer["name"],
                         cohortId=course.get("cohort", {}).get("id"),
                         payload={"semesterId": semester_id, "enabled": True,
                                  "expectedRevision": None, "configuration": {
                                      "identifier": "Prüfung", "durationMinutes": 90,
                                      "examType": "Schriftlich", "requiredCapacity": capacity,
                                      "responsibleLecturerId": lecturer["id"],
                                      "recommendedStartOverride": None, "recommendedEndOverride": None}})
        plan.append(entry)
    return plan


def load_plan(api, semester_id):
    options = api.request("GET", f"/api/planning-options?semesterId={semester_id}")
    overview = api.request("GET", f"/api/exam-planning?semesterId={semester_id}")
    return build_plan(options, overview, semester_id)


def execute(api, plan: list[dict], semester_id: int, *, apply: bool):
    if not apply:
        return
    for entry in plan:
        if entry["status"] != "would_create":
            continue
        try:
            fresh = next((row for row in load_plan(api, semester_id)
                          if row["courseId"] == entry["courseId"]), None)
            if fresh != entry:
                entry.update(status="skipped", reason="LV-Daten oder Anforderungen seit Vorschau geändert.")
                continue
            api.request("PUT", f'/api/courses/{entry["courseId"]}/exam-configuration', entry["payload"])
            entry["status"] = "created"
        except InitializationError:
            entry["status"] = "failed_or_unknown"
            raise


def show_plan(plan):
    for row in plan:
        detail = row.get("reason")
        if detail is None:
            config = row["payload"]["configuration"]
            detail = f'90 Min.; Schriftlich; {config["requiredCapacity"]} Plätze; {row["lecturerName"]}'
        print(f'{row["courseId"]}: {row["courseName"]} | {row["status"]} | {detail}')
    print(json.dumps(dict(Counter(row["status"] for row in plan)), ensure_ascii=False))


def main(argv=None):
    parser = argparse.ArgumentParser(description="Fehlende Prüfungsanforderungen mit 2 UE initialisieren.")
    parser.add_argument("--base-url", required=True, help="Planner-Basis-URL, ohne /api")
    parser.add_argument("--username", help="Planner-Anmeldename")
    parser.add_argument("--semester-id", type=int, help="Semester-ID; ohne diese werden Semester aufgelistet")
    parser.add_argument("--apply", action="store_true", help="Vorgeschlagene Anforderungen tatsächlich speichern")
    parser.add_argument("--report", type=Path, help="Optionaler JSON-Bericht (wird überschrieben)")
    args = parser.parse_args(argv)
    if args.semester_id is not None and args.semester_id <= 0:
        parser.error("--semester-id muss positiv sein")
    if args.apply and args.semester_id is None:
        parser.error("--apply erfordert --semester-id")
    api, logged_in, plan = None, False, []
    result = 0
    try:
        api = PlannerAPI(args.base_url)
        username = args.username or input("Planner-Anmeldename: ").strip()
        password = getpass.getpass("Planner-Passwort: ")
        try:
            api.request("POST", "/api/auth/login", {"loginName": username, "password": password})
        finally:
            del password
        logged_in = True
        if args.semester_id is None:
            for semester in api.request("GET", "/api/planning-options")["semesters"]:
                print(f'{semester["id"]}: {semester["name"]}')
        else:
            plan = load_plan(api, args.semester_id)
            print("Vorschau:")
            show_plan(plan)
            execute(api, plan, args.semester_id, apply=args.apply)
            if args.apply:
                print("Ergebnis:")
                show_plan(plan)
            if any(row["status"] == "skipped" for row in plan):
                result = 2
    except (InitializationError, OSError, ValueError, KeyError, TypeError, EOFError) as exc:
        print(f"Abbruch: {exc}", file=sys.stderr)
        result = 1
    finally:
        if args.report and plan:
            try:
                args.report.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            except OSError as exc:
                print(f"Bericht konnte nicht gespeichert werden: {exc}", file=sys.stderr)
                result = 1
        if logged_in:
            try:
                api.request("POST", "/api/auth/logout")
            except InitializationError:
                print("Abmeldung fehlgeschlagen; Sitzung läuft regulär ab.", file=sys.stderr)
    return result


if __name__ == "__main__":
    sys.exit(main())
