from datetime import date
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class FailureCode(StrEnum):
    INSUFFICIENT_ROOM_CAPACITY = "INSUFFICIENT_ROOM_CAPACITY"
    INVALID_SESSION_PREFERENCE = "INVALID_SESSION_PREFERENCE"
    NO_FITTING_TIME_WINDOW = "NO_FITTING_TIME_WINDOW"
    INSUFFICIENT_SEMESTER_CAPACITY = "INSUFFICIENT_SEMESTER_CAPACITY"
    INVALID_PLANNING_PERIOD = "INVALID_PLANNING_PERIOD"
    INVALID_TEACHING_WINDOW = "INVALID_TEACHING_WINDOW"
    MISSING_TEACHING_WINDOW = "MISSING_TEACHING_WINDOW"


class SessionEditFailureCode(StrEnum):
    INVALID_SESSION_DATE = "INVALID_SESSION_DATE"
    INVALID_SESSION_TIME_RANGE = "INVALID_SESSION_TIME_RANGE"
    INSUFFICIENT_ROOM_CAPACITY = "INSUFFICIENT_ROOM_CAPACITY"
    DUPLICATE_SESSION_DATE = "DUPLICATE_SESSION_DATE"


class UpdateDraftSessionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    date: str
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    room_id: int = Field(alias="roomId")


class PlanningPeriodInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")


class AllowedTeachingWindowInput(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weekday: int
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    source_time_window_id: int | None = Field(default=None, alias="sourceTimeWindowId")


class GenerateDraftScheduleRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    semester_id: int = Field(alias="semesterId")
    planning_period: PlanningPeriodInput = Field(alias="planningPeriod")
    allowed_teaching_windows: list[AllowedTeachingWindowInput] = Field(alias="allowedTeachingWindows")


class PlanningPeriodResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")


class AllowedTeachingWindowResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    weekday: int
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    source_time_window_id: int | None = Field(default=None, alias="sourceTimeWindowId")


class GenerationConstraintsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    course_id: int = Field(alias="courseId")
    semester_id: int = Field(alias="semesterId")
    is_custom: bool = Field(alias="isCustom")
    planning_period: PlanningPeriodResponse = Field(alias="planningPeriod")
    allowed_teaching_windows: list[AllowedTeachingWindowResponse] = Field(alias="allowedTeachingWindows")


class DraftSessionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    date: date
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    units: int
    course_id: int = Field(alias="courseId")
    lecturer_id: int = Field(alias="lecturerId")
    cohort_id: int = Field(alias="cohortId")
    room_id: int = Field(alias="roomId")
    study_type_id: int = Field(alias="studyTypeId")
    time_window_id: int | None = Field(alias="timeWindowId")
    constraint_window_index: int = Field(alias="constraintWindowIndex")


class PlanningEntityResponse(BaseModel):
    id: int
    name: str


class DraftScheduleContextResponse(BaseModel):
    course: PlanningEntityResponse
    cohort: PlanningEntityResponse
    cohort_size: int = Field(alias="cohortSize")
    lecturer: PlanningEntityResponse
    room: PlanningEntityResponse
    study_type: PlanningEntityResponse = Field(alias="studyType")


class DraftScheduleResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    draft_schedule_id: int = Field(alias="draftScheduleId")
    course_id: int = Field(alias="courseId")
    semester_id: int = Field(alias="semesterId")
    context: DraftScheduleContextResponse
    sessions: list[DraftSessionResponse]


class GenerationFailure(BaseModel):
    code: FailureCode
    message: str


class GenerationFailureResponse(BaseModel):
    errors: list[GenerationFailure]


class SessionEditFailure(BaseModel):
    code: SessionEditFailureCode
    message: str


class SessionEditFailureResponse(BaseModel):
    errors: list[SessionEditFailure]


class ErrorResponse(BaseModel):
    message: str
