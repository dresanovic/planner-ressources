from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FailureCode(StrEnum):
    INSUFFICIENT_ROOM_CAPACITY = "INSUFFICIENT_ROOM_CAPACITY"
    INVALID_SESSION_PREFERENCE = "INVALID_SESSION_PREFERENCE"
    NO_FITTING_TIME_WINDOW = "NO_FITTING_TIME_WINDOW"
    INSUFFICIENT_SEMESTER_CAPACITY = "INSUFFICIENT_SEMESTER_CAPACITY"


class GenerateDraftScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    selected_time_window_id: int = Field(alias="selectedTimeWindowId")


class DraftSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    date: date
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    units: int
    time_window_id: int = Field(alias="timeWindowId")


class DraftScheduleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    draft_schedule_id: int = Field(alias="draftScheduleId")
    course_id: int = Field(alias="courseId")
    semester_id: int = Field(alias="semesterId")
    selected_time_window_id: int = Field(alias="selectedTimeWindowId")
    sessions: list[DraftSessionResponse]


class GenerationFailure(BaseModel):
    code: FailureCode
    message: str


class GenerationFailureResponse(BaseModel):
    errors: list[GenerationFailure]


class ErrorResponse(BaseModel):
    message: str
