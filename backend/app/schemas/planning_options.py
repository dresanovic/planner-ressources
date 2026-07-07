from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.draft_schedule import PlanningEntityResponse


class CourseOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    total_units: int = Field(alias="totalUnits")
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    lecturer: PlanningEntityResponse
    cohort: PlanningEntityResponse
    room: PlanningEntityResponse
    study_type: PlanningEntityResponse = Field(alias="studyType")


class SemesterOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    start_date: date = Field(alias="startDate")
    end_date: date = Field(alias="endDate")


class TimeWindowOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    study_type_id: int = Field(alias="studyTypeId")
    weekday: int
    start_time: str = Field(alias="startTime")
    end_time: str = Field(alias="endTime")
    sort_order: int = Field(alias="sortOrder")


class PlanningOptionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    courses: list[CourseOptionResponse]
    semesters: list[SemesterOptionResponse]
    time_windows: list[TimeWindowOptionResponse] = Field(alias="timeWindows")
