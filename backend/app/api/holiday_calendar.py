from fastapi import APIRouter, Depends, Query, status
from fastapi.responses import JSONResponse, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy.orm.exc import StaleDataError

from app.db.session import get_db
from app.schemas.holiday_calendar import (
    HolidayErrorEnvelope,
    HolidayErrorItem as HolidayErrorResponseItem,
    HolidayInput,
    HolidayRecord,
    HolidayUpdateInput,
)
from app.services.holiday_calendar import (
    HolidayCalendarError,
    HolidayErrorItem,
    create_holiday,
    delete_holiday,
    list_holidays,
    require_holiday,
    update_holiday,
)

router = APIRouter(prefix="/api/holidays", tags=["holidays"])


def _record(row) -> HolidayRecord:
    return HolidayRecord.model_validate(row)


def _error_response(exc: HolidayCalendarError) -> JSONResponse:
    payload = HolidayErrorEnvelope(
        errors=[
            HolidayErrorResponseItem(code=item.code, message=item.message, field=item.field, meta=item.meta)
            for item in exc.errors
        ]
    )
    return JSONResponse(status_code=exc.status_code, content=payload.model_dump(mode="json"))


def _concurrent_error() -> HolidayCalendarError:
    return HolidayCalendarError(
        409,
        [HolidayErrorItem("STALE_REVISION", "The holiday calendar changed. Refresh and try again.")],
    )


@router.get("", response_model=list[HolidayRecord])
def get_holidays(db: Session = Depends(get_db)):
    return [_record(row) for row in list_holidays(db)]


@router.post("", response_model=HolidayRecord, status_code=status.HTTP_201_CREATED)
def post_holiday(payload: HolidayInput, db: Session = Depends(get_db)):
    try:
        row = create_holiday(db, day=payload.date, name=payload.name)
        db.commit()
        db.refresh(row)
        return _record(row)
    except HolidayCalendarError as exc:
        db.rollback()
        return _error_response(exc)
    except IntegrityError:
        db.rollback()
        return _error_response(HolidayCalendarError(409, [HolidayErrorItem("DUPLICATE_HOLIDAY_DATE", "Another holiday already uses this date.", "date")]))


@router.get("/{holiday_id}", response_model=HolidayRecord)
def get_holiday(holiday_id: int, db: Session = Depends(get_db)):
    try:
        return _record(require_holiday(db, holiday_id))
    except HolidayCalendarError as exc:
        return _error_response(exc)


@router.patch("/{holiday_id}", response_model=HolidayRecord)
def patch_holiday(holiday_id: int, payload: HolidayUpdateInput, db: Session = Depends(get_db)):
    try:
        row = update_holiday(
            db,
            holiday_id,
            day=payload.date,
            name=payload.name,
            expected_revision=payload.expected_revision,
        )
        db.commit()
        db.refresh(row)
        return _record(row)
    except HolidayCalendarError as exc:
        db.rollback()
        return _error_response(exc)
    except IntegrityError:
        db.rollback()
        return _error_response(HolidayCalendarError(409, [HolidayErrorItem("DUPLICATE_HOLIDAY_DATE", "Another holiday already uses this date.", "date")]))
    except StaleDataError:
        db.rollback()
        return _error_response(_concurrent_error())


@router.delete("/{holiday_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_holiday(
    holiday_id: int,
    expected_revision: int = Query(alias="expectedRevision", ge=1),
    confirmed: bool = Query(),
    db: Session = Depends(get_db),
):
    try:
        delete_holiday(
            db,
            holiday_id,
            expected_revision=expected_revision,
            confirmed=confirmed,
        )
        db.commit()
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except HolidayCalendarError as exc:
        db.rollback()
        return _error_response(exc)
    except StaleDataError:
        db.rollback()
        return _error_response(_concurrent_error())
