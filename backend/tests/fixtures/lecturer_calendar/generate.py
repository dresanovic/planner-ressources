from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, timedelta, timezone
from importlib.metadata import version
from pathlib import Path
from zoneinfo import ZoneInfo

from app.services.lecturer_calendar_export import (
    CalendarEvent,
    calendar_event_uid,
    serialize_calendar,
)


ZONE = ZoneInfo("Europe/Vienna")
STAMP = datetime(2026, 2, 3, 10, 20, 30, tzinfo=timezone.utc)
KEY = b"fs020-retained-conformance-fixture-key"
OUTPUT = Path(__file__).parents[4] / "specs/020-lecturer-calendar-export/validation/fixtures"


def event(
    number: int,
    *,
    kind: str = "teaching",
    start: datetime | None = None,
    end: datetime | None = None,
    summary: str | None = None,
    location: str | None = "Raum A",
    description: tuple[str, ...] | None = None,
) -> CalendarEvent:
    start = start or datetime(2026, 10, 5, 9, 0, tzinfo=ZONE) + timedelta(days=number)
    end = end or start + timedelta(minutes=90)
    return CalendarEvent(
        uid=calendar_event_uid(KEY, 20, kind, number),
        dtstamp=STAMP,
        start=start,
        end=end,
        summary=summary or f"COURSE-{number} – Beispiellehrveranstaltung – {'Prüfung' if kind == 'exam' else 'Lehrtermin'}",
        location=location,
        description_lines=description or (
            f"Terminart: {'Prüfung' if kind == 'exam' else 'Lehrtermin'}",
            f"Lehrveranstaltung: COURSE-{number} – Beispiellehrveranstaltung",
            "Kohorte: CS-26",
            "Studienart: Vollzeit",
            "Prüfungsdauer: 90 Minuten" if kind == "exam" else "Lehreinheiten: 2",
            "Semester: Wintersemester 2026",
            "Revision: Revision 2",
        ),
    )


def cases() -> dict[str, list[CalendarEvent]]:
    identical = event(70, summary="CS101 – Grundlagen – Lehrtermin")
    return {
        "teaching-only": [event(1), event(2)],
        "exam-only": [event(3, kind="exam"), event(4, kind="exam")],
        "mixed-multi-course": [event(5), event(6, kind="exam"), event(7), event(8, kind="exam")],
        "empty": [],
        "dst": [
            event(9, start=datetime(2026, 1, 15, 9, tzinfo=ZONE), end=datetime(2026, 1, 15, 10, 30, tzinfo=ZONE)),
            event(10, start=datetime(2026, 7, 15, 9, tzinfo=ZONE), end=datetime(2026, 7, 15, 10, 30, tzinfo=ZONE)),
        ],
        "cross-midnight": [event(11, kind="exam", start=datetime(2026, 10, 24, 23, 30, tzinfo=ZONE), end=datetime(2026, 10, 25, 1, 15, tzinfo=ZONE))],
        "missing-location": [event(12, location=None)],
        "identical-display": [
            identical,
            event(71, start=identical.start, end=identical.end, summary=identical.summary),
        ],
        "one-hundred-events": [event(1000 + index) for index in range(100)],
        "unicode-reserved": [event(13, summary="Ästhetik, Recht; Pfad \\ – Prüfung")],
        "embedded-newline": [event(14, description=("Terminart: Lehrtermin", "Kontext: erste Zeile\nzweite Zeile", "Semester: Wintersemester 2026", "Revision: Revision 2"))],
        "long-line": [event(15, summary="Überlange Lehrveranstaltung – " + ("ÄÖÜ abcdef " * 40))],
    }


def main() -> None:
    OUTPUT.mkdir(parents=True, exist_ok=True)
    records = []
    for case_id, items in cases().items():
        content = serialize_calendar(
            display_name="Terminplanung – Wintersemester 2026 – Revision 2",
            time_zone="Europe/Vienna",
            timezone_start=date(2025, 9, 1),
            timezone_end=date(2027, 9, 1),
            events=items,
        )
        filename = f"{case_id}.ics"
        (OUTPUT / filename).write_bytes(content)
        records.append({
            "id": case_id,
            "file": filename,
            "eventCount": len(items),
            "sha256": hashlib.sha256(content).hexdigest(),
            "events": [
                {
                    "uid": item.uid,
                    "summary": item.summary,
                    "start": item.start.isoformat(),
                    "end": item.end.isoformat(),
                    "location": item.location,
                    "descriptionLines": list(item.description_lines),
                    "transparency": "OPAQUE",
                }
                for item in sorted(items, key=lambda value: (value.start.astimezone(timezone.utc), value.end.astimezone(timezone.utc), value.uid))
            ],
        })
    manifest = {
        "schemaVersion": 1,
        "generatedBy": "backend/tests/fixtures/lecturer_calendar/generate.py",
        "serializer": {"icalendar": version("icalendar"), "tzdata": version("tzdata")},
        "timeZone": "Europe/Vienna",
        "timezoneRange": {"start": "2025-09-01", "end": "2027-09-01"},
        "fixtures": records,
    }
    (OUTPUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main()
