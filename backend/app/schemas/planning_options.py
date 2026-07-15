from datetime import date

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.academic_catalog import AvailabilityResponse
from app.schemas.draft_schedule import PlanningEntityResponse
from app.schemas.resource_catalog import AssignmentPreferences, LecturerRecord, ResourceCandidate, RoomRecord


class CourseOptionResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    name: str
    total_units: int = Field(alias="totalUnits")
    min_session_units: int = Field(alias="minSessionUnits")
    max_session_units: int = Field(alias="maxSessionUnits")
    semester_id: int = Field(alias="semesterId")
    availability: AvailabilityResponse
    lecturer: PlanningEntityResponse | None
    cohort: PlanningEntityResponse
    room: PlanningEntityResponse | None
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


class RoomOptionResponse(BaseModel):
    id: int
    name: str
    capacity: int


class PlanningOptionsResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    courses: list[CourseOptionResponse]
    semesters: list[SemesterOptionResponse]
    time_windows: list[TimeWindowOptionResponse] = Field(alias="timeWindows")
    rooms: list[RoomRecord]
    lecturers: list[LecturerRecord]
    course_resources: list["CoursePlanningResourceExtension"] = Field(alias="courseResources")


class CoursePlanningResourceExtension(BaseModel):
    model_config = ConfigDict(populate_by_name=True)
    course_id: int = Field(alias="courseId")
    eligible_lecturers: list[ResourceCandidate] = Field(alias="eligibleLecturers")
    eligible_rooms: list[ResourceCandidate] = Field(alias="eligibleRooms")
    preferences: AssignmentPreferences
