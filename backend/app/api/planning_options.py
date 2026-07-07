from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.planning import Course, Semester, StudyTypeTimeWindow
from app.schemas.draft_schedule import PlanningEntityResponse
from app.schemas.planning_options import (
    CourseOptionResponse,
    PlanningOptionsResponse,
    SemesterOptionResponse,
    TimeWindowOptionResponse,
)

router = APIRouter(prefix="/api/planning-options", tags=["planning options"])


@router.get("", response_model=PlanningOptionsResponse)
def read_planning_options(db: Session = Depends(get_db)) -> PlanningOptionsResponse:
    courses = (
        db.execute(
            select(Course)
            .options(
                selectinload(Course.lecturer),
                selectinload(Course.cohort),
                selectinload(Course.room),
                selectinload(Course.study_type),
            )
            .order_by(Course.name)
        )
        .scalars()
        .all()
    )
    semesters = db.execute(select(Semester).order_by(Semester.start_date, Semester.name)).scalars().all()
    time_windows = (
        db.execute(
            select(StudyTypeTimeWindow).order_by(
                StudyTypeTimeWindow.study_type_id,
                StudyTypeTimeWindow.sort_order,
                StudyTypeTimeWindow.weekday,
            )
        )
        .scalars()
        .all()
    )

    return PlanningOptionsResponse(
        courses=[
            CourseOptionResponse(
                id=course.id,
                name=course.name,
                totalUnits=course.total_units,
                minSessionUnits=course.min_session_units,
                maxSessionUnits=course.max_session_units,
                lecturer=PlanningEntityResponse(id=course.lecturer.id, name=course.lecturer.name),
                cohort=PlanningEntityResponse(id=course.cohort.id, name=course.cohort.name),
                room=PlanningEntityResponse(id=course.room.id, name=course.room.name),
                studyType=PlanningEntityResponse(id=course.study_type.id, name=course.study_type.name),
            )
            for course in courses
        ],
        semesters=[
            SemesterOptionResponse(
                id=semester.id,
                name=semester.name,
                startDate=semester.start_date,
                endDate=semester.end_date,
            )
            for semester in semesters
        ],
        timeWindows=[
            TimeWindowOptionResponse(
                id=window.id,
                studyTypeId=window.study_type_id,
                weekday=window.weekday,
                startTime=window.start_time.strftime("%H:%M"),
                endTime=window.end_time.strftime("%H:%M"),
                sortOrder=window.sort_order,
            )
            for window in time_windows
        ],
    )
