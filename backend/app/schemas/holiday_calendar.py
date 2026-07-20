import re
from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


_DATE_ONLY_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2}")


class HolidayRecord(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    date: date
    name: str
    revision: int


class HolidayInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    date: date
    name: str

    @field_validator("date", mode="before")
    @classmethod
    def require_date_only_string(cls, value):
        if isinstance(value, str) and _DATE_ONLY_PATTERN.fullmatch(value) is None:
            raise ValueError("Holiday date must use YYYY-MM-DD.")
        return value


class HolidayUpdateInput(HolidayInput):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    expected_revision: int = Field(alias="expectedRevision", ge=1)


class HolidayErrorItem(BaseModel):
    code: str
    message: str
    field: str | None = None
    meta: dict[str, Any] | None = None


class HolidayErrorEnvelope(BaseModel):
    errors: list[HolidayErrorItem]
