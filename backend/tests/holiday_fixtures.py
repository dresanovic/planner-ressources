from datetime import date

from app.models.planning import InstitutionHoliday


def holiday(
    *,
    holiday_id: int | None = None,
    day: date = date(2026, 12, 25),
    name: str = "Winter Holiday",
    revision: int = 1,
) -> InstitutionHoliday:
    values = {"date": day, "name": name, "revision": revision}
    if holiday_id is not None:
        values["id"] = holiday_id
    return InstitutionHoliday(**values)


def holiday_payload(*, day: str = "2026-12-25", name: str = "Winter Holiday") -> dict:
    return {"date": day, "name": name}


def holiday_update_payload(
    *,
    day: str = "2026-12-25",
    name: str = "Winter Holiday",
    expected_revision: int = 1,
) -> dict:
    return {"date": day, "name": name, "expectedRevision": expected_revision}


def stale_holiday(*, day: date = date(2026, 12, 25), name: str = "Updated Holiday") -> InstitutionHoliday:
    return holiday(day=day, name=name, revision=2)


def cross_year_holidays() -> list[InstitutionHoliday]:
    return [
        holiday(day=date(2024, 2, 29), name="Leap Day"),
        holiday(day=date(2026, 12, 25), name="Winter Holiday"),
        holiday(day=date(2027, 1, 1), name="New Year"),
    ]


def holiday_for_session(session, *, name: str = "Session Holiday") -> InstitutionHoliday:
    return holiday(day=session.date, name=name)
