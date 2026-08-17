from __future__ import annotations

import hashlib
import hmac
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
from typing import Mapping, Sequence
from zoneinfo import ZoneInfo

from icalendar import Calendar, Event, Timezone

from app.services.lecturer_review import LecturerCalendarProjection


PRODUCT_ID = "-//Resource Planner//Lecturer Calendar Export 1.0//EN"
UID_KEY_CONTEXT = b"fs020-calendar-uid-key-v1"
UID_MESSAGE_CONTEXT = b"fs020-calendar-event-v1\0"
UID_DOMAIN = "resource-planner.invalid"
ASCII_FILENAME = "resource-planner-calendar.ics"
EN_DASH = "\N{EN DASH}"


@dataclass(frozen=True)
class CalendarEvent:
    uid: str
    dtstamp: datetime
    start: datetime
    end: datetime
    summary: str
    location: str | None
    description_lines: tuple[str, ...]


@dataclass(frozen=True)
class CalendarSnapshot:
    filename: str
    content: bytes
    event_count: int


def build_lecturer_calendar(
    projection: LecturerCalendarProjection,
    *,
    terminology: Mapping[str, str],
    uid_base_key: bytes,
) -> CalendarSnapshot:
    review = projection.review
    schedule_label = _required_text(terminology, "schedule.heading")
    display_name = f"{schedule_label} {EN_DASH} {review.revision.semester_name} {EN_DASH} {review.revision.label}"
    zone = ZoneInfo(review.time_zone)
    events: list[CalendarEvent] = []
    for course in review.courses:
        for session in course.sessions:
            start = _local_datetime(session.date, session.start_time, zone)
            end = _local_datetime(session.date, session.end_time, zone)
            events.append(
                CalendarEvent(
                    uid=calendar_event_uid(
                        uid_base_key,
                        projection.revision_id,
                        session.session_kind,
                        session.source_session_id,
                    ),
                    dtstamp=_utc_whole_second(projection.revision_created_at),
                    start=start,
                    end=end,
                    summary=f" {EN_DASH} ".join(
                        part for part in (course.code, course.title, session.session_type)
                        if part
                    ),
                    location=session.room_name or None,
                    description_lines=tuple(
                        _description_lines(
                            course,
                            session,
                            review.revision.semester_name,
                            review.revision.label,
                            terminology,
                        )
                    ),
                )
            )

    return CalendarSnapshot(
        filename=calendar_filename(
            schedule_label,
            review.revision.semester_name,
            review.revision.label,
        ),
        content=serialize_calendar(
            display_name=display_name,
            time_zone=review.time_zone,
            timezone_start=review.semester_start_date - timedelta(days=366),
            timezone_end=review.semester_end_date + timedelta(days=366),
            events=events,
        ),
        event_count=len(events),
    )


def serialize_calendar(
    *,
    display_name: str,
    time_zone: str,
    timezone_start: date,
    timezone_end: date,
    events: Sequence[CalendarEvent],
) -> bytes:
    zone = ZoneInfo(time_zone)
    if timezone_end < timezone_start:
        raise ValueError("Calendar timezone range is invalid.")

    calendar = Calendar()
    calendar.add("version", "2.0")
    calendar.add("prodid", PRODUCT_ID)
    calendar.add("calscale", "GREGORIAN")
    calendar.add("name", display_name)
    calendar.add("x-wr-calname", display_name)
    calendar.add_component(
        Timezone.from_tzinfo(
            zone,
            tzid=time_zone,
            first_date=timezone_start,
            last_date=timezone_end,
        )
    )

    seen_uids: set[str] = set()
    ordered = sorted(
        events,
        key=lambda item: (
            item.start.astimezone(timezone.utc),
            item.end.astimezone(timezone.utc),
            item.uid,
        ),
    )
    for item in ordered:
        _validate_calendar_event(item, time_zone)
        if item.uid in seen_uids:
            raise ValueError("Calendar event UIDs must be unique.")
        seen_uids.add(item.uid)
        event = Event()
        event.add("uid", item.uid)
        event.add("dtstamp", _utc_whole_second(item.dtstamp))
        event.add("dtstart", item.start)
        event.add("dtend", item.end)
        event.add("summary", item.summary)
        if item.location:
            event.add("location", item.location)
        event.add("description", "\n".join(item.description_lines))
        event.add("transp", "OPAQUE")
        calendar.add_component(event)

    content = calendar.to_ical(sorted=False)
    if content.startswith(b"\xef\xbb\xbf") or not content.endswith(b"END:VCALENDAR\r\n"):
        raise ValueError("Calendar serialization produced an invalid byte envelope.")
    return content


def calendar_event_uid(
    base_key: bytes,
    revision_id: int,
    session_kind: str,
    session_id: int,
) -> str:
    if revision_id < 1 or session_id < 1 or session_kind not in {"teaching", "exam"}:
        raise ValueError("Invalid calendar identity input.")
    uid_key = hmac.new(base_key, UID_KEY_CONTEXT, hashlib.sha256).digest()
    message = (
        UID_MESSAGE_CONTEXT
        + str(revision_id).encode("ascii")
        + b"\0"
        + session_kind.encode("ascii")
        + b"\0"
        + str(session_id).encode("ascii")
    )
    digest = hmac.new(uid_key, message, hashlib.sha256).hexdigest()
    return f"{digest}@{UID_DOMAIN}"


def calendar_filename(*segments: str) -> str:
    cleaned = [_filename_segment(segment) for segment in segments]
    if any(not segment for segment in cleaned):
        raise ValueError("Calendar filename segment is empty.")
    stem = _trim_filename_boundary("-".join(cleaned)[:180])
    if not stem:
        raise ValueError("Calendar filename is empty.")
    if re.fullmatch(r"(?i:CON|PRN|AUX|NUL|COM[1-9]|LPT[1-9])", stem):
        stem = f"calendar-{stem}"
    return f"{stem}.ics"


def _filename_segment(value: str) -> str:
    normalized = unicodedata.normalize("NFC", value).strip()
    output: list[str] = []
    previous_hyphen = False
    for character in normalized:
        allowed = unicodedata.category(character)[0] in {"L", "N"} or character in "._-"
        emitted = character if allowed else "-"
        if emitted == "-":
            if previous_hyphen:
                continue
            previous_hyphen = True
        else:
            previous_hyphen = False
        output.append(emitted)
    return _trim_filename_boundary("".join(output))


def _trim_filename_boundary(value: str) -> str:
    return value.strip("._-")


def _local_datetime(source_date: date, clock_text: str, zone: ZoneInfo) -> datetime:
    local_time = time.fromisoformat(clock_text)
    naive = datetime.combine(source_date, local_time)
    first = naive.replace(tzinfo=zone, fold=0)
    second = naive.replace(tzinfo=zone, fold=1)
    first_roundtrip = first.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    second_roundtrip = second.astimezone(timezone.utc).astimezone(zone).replace(tzinfo=None)
    if first.utcoffset() != second.utcoffset() or first_roundtrip != naive or second_roundtrip != naive:
        raise ValueError("Ambiguous or nonexistent institution-local time.")
    return first


def _validate_calendar_event(item: CalendarEvent, expected_tzid: str) -> None:
    if not re.fullmatch(r"[0-9a-f]{64}@resource-planner\.invalid", item.uid):
        raise ValueError("Calendar event UID is invalid.")
    if item.start.tzinfo is None or item.end.tzinfo is None:
        raise ValueError("Calendar events require timezone-aware date-times.")
    if getattr(item.start.tzinfo, "key", None) != expected_tzid or getattr(item.end.tzinfo, "key", None) != expected_tzid:
        raise ValueError("Calendar event timezone does not match the calendar.")
    if item.end.astimezone(timezone.utc) <= item.start.astimezone(timezone.utc):
        raise ValueError("Calendar event end must be later than start.")
    if not item.summary or not item.description_lines or any(not line for line in item.description_lines):
        raise ValueError("Calendar event display content is incomplete.")


def _description_lines(course, session, semester_label: str, revision_label: str, terminology: Mapping[str, str]):
    course_label = terminology.get("course.fieldLabel", "Lehrveranstaltung")
    cohort_label = terminology.get("cohort.fieldLabel", "Kohorte")
    course_display = f"{course.code} {EN_DASH} {course.title}" if course.code else course.title
    lines = [
        f"Terminart: {session.session_type}",
        f"{course_label}: {course_display}",
        f"{cohort_label}: {session.cohort_name}",
        f"Studienart: {course.study_type}",
    ]
    if session.session_kind == "teaching" and session.teaching_units is not None:
        lines.append(f"Lehreinheiten: {session.teaching_units}")
    if session.session_kind == "exam" and session.exam_duration_minutes is not None:
        lines.append(f"Pr\N{LATIN SMALL LETTER U WITH DIAERESIS}fungsdauer: {session.exam_duration_minutes} Minuten")
    lines.extend((f"Semester: {semester_label}", f"Revision: {revision_label}"))
    return lines


def _required_text(values: Mapping[str, str], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Missing required terminology label: {key}")
    return value.strip()


def _utc_whole_second(value: datetime) -> datetime:
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).replace(microsecond=0)
