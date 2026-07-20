from dataclasses import dataclass
from datetime import date
import hashlib
import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.planning import InstitutionHoliday


@dataclass(frozen=True)
class HolidayErrorItem:
    code: str
    message: str
    field: str | None = None
    meta: dict | None = None


class HolidayCalendarError(ValueError):
    def __init__(self, status_code: int, errors: list[HolidayErrorItem]):
        super().__init__(errors[0].message if errors else "Holiday calendar error.")
        self.status_code = status_code
        self.errors = errors


@dataclass(frozen=True)
class HolidayReference:
    id: int
    date: date
    name: str
    revision: int


@dataclass(frozen=True)
class HolidayCalendarSnapshot:
    range_start: date
    range_end: date
    entries: tuple[tuple[int, date, str, int], ...]
    by_date: dict[date, HolidayReference]
    token: str


def list_holidays(
    db: Session,
    *,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[InstitutionHoliday]:
    query = select(InstitutionHoliday)
    if start_date is not None:
        query = query.where(InstitutionHoliday.date >= start_date)
    if end_date is not None:
        query = query.where(InstitutionHoliday.date <= end_date)
    return list(db.scalars(query.order_by(InstitutionHoliday.date, InstitutionHoliday.id)))


def require_holiday(db: Session, holiday_id: int) -> InstitutionHoliday:
    row = db.get(InstitutionHoliday, holiday_id)
    if row is None:
        raise HolidayCalendarError(
            404,
            [HolidayErrorItem("NOT_FOUND", "Holiday not found.")],
        )
    return row


def create_holiday(db: Session, *, day: date, name: str) -> InstitutionHoliday:
    display = _validate_name(name)
    _ensure_unique_date(db, day)
    row = InstitutionHoliday(date=day, name=display)
    db.add(row)
    db.flush()
    return row


def update_holiday(
    db: Session,
    holiday_id: int,
    *,
    day: date,
    name: str,
    expected_revision: int,
) -> InstitutionHoliday:
    row = require_holiday(db, holiday_id)
    _ensure_revision(row, expected_revision)
    display = _validate_name(name)
    _ensure_unique_date(db, day, exclude_id=holiday_id)
    row.date = day
    row.name = display
    row.revision += 1
    db.flush()
    return row


def delete_holiday(
    db: Session,
    holiday_id: int,
    *,
    expected_revision: int,
    confirmed: bool,
) -> None:
    row = require_holiday(db, holiday_id)
    if not confirmed:
        raise HolidayCalendarError(
            422,
            [HolidayErrorItem("CONFIRMATION_REQUIRED", "Confirm holiday removal.", "confirmed")],
        )
    _ensure_revision(row, expected_revision)
    db.delete(row)
    db.flush()


def holiday_snapshot(db: Session, start_date: date, end_date: date) -> HolidayCalendarSnapshot:
    rows = list_holidays(db, start_date=start_date, end_date=end_date)
    entries = tuple((row.id, row.date, row.name, row.revision) for row in rows)
    payload = [[item[0], item[1].isoformat(), item[2], item[3]] for item in entries]
    token = hashlib.sha256(json.dumps(payload, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()
    return HolidayCalendarSnapshot(
        range_start=start_date,
        range_end=end_date,
        entries=entries,
        by_date={
            row.date: HolidayReference(row.id, row.date, row.name, row.revision)
            for row in rows
        },
        token=token,
    )


def _validate_name(value: str) -> str:
    display = value.strip()
    if not display:
        raise HolidayCalendarError(
            422,
            [HolidayErrorItem("VALIDATION_ERROR", "Enter a holiday name.", "name")],
        )
    if len(display) > 200:
        raise HolidayCalendarError(
            422,
            [HolidayErrorItem("VALIDATION_ERROR", "Holiday name cannot exceed 200 characters.", "name")],
        )
    return display


def _ensure_unique_date(db: Session, day: date, *, exclude_id: int | None = None) -> None:
    query = select(InstitutionHoliday.id).where(InstitutionHoliday.date == day)
    if exclude_id is not None:
        query = query.where(InstitutionHoliday.id != exclude_id)
    conflicting_id = db.scalar(query)
    if conflicting_id is not None:
        raise HolidayCalendarError(
            409,
            [HolidayErrorItem(
                "DUPLICATE_HOLIDAY_DATE",
                "Another holiday already uses this date.",
                "date",
                {"conflictingRecordId": conflicting_id},
            )],
        )


def _ensure_revision(row: InstitutionHoliday, expected_revision: int) -> None:
    if row.revision != expected_revision:
        raise HolidayCalendarError(
            409,
            [HolidayErrorItem(
                "STALE_REVISION",
                "This holiday changed since it was opened. Refresh and try again.",
                None,
                {"currentRevision": row.revision},
            )],
        )
