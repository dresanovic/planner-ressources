from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.planning import Course, Lecturer, Room, Semester, StudyTypeTimeWindow
from app.schemas.academic_catalog import AvailabilityResponse
from app.schemas.draft_schedule import PlanningEntityResponse
from app.schemas.planning_options import (
    CourseOptionResponse,
    PlanningOptionsResponse,
    RoomOptionResponse,
    SemesterOptionResponse,
    TimeWindowOptionResponse,
)
from app.services.academic_catalog import availability_for_course

router = APIRouter(prefix="/api/planning-options", tags=["planning options"])


@router.get("", response_model=PlanningOptionsResponse)
def read_planning_options(
    semester_id: int | None = Query(None, alias="semesterId"),
    db: Session = Depends(get_db),
) -> PlanningOptionsResponse:
    courses = (
        db.execute(
            select(Course)
            .options(
                selectinload(Course.lecturer),
                selectinload(Course.cohort),
                selectinload(Course.room),
                selectinload(Course.study_type),
                selectinload(Course.current_semester),
            )
            .where(Course.is_active.is_(True))
            .order_by(Course.name)
        )
        .scalars()
        .all()
    )
    courses = [
        course
        for course in courses
        if course.current_semester_id is not None
        and (semester_id is None or course.current_semester_id == semester_id)
        and course.current_semester.is_active
        and course.cohort.is_active
        and course.study_type.is_active
    ]
    semesters = db.execute(select(Semester).where(Semester.is_active.is_(True)).order_by(Semester.start_date, Semester.name)).scalars().all()
    rooms = db.execute(select(Room).order_by(Room.name)).scalars().all()
    lecturers = db.execute(select(Lecturer).order_by(Lecturer.name)).scalars().all()
    time_windows = (
        db.execute(
            select(StudyTypeTimeWindow).where(StudyTypeTimeWindow.is_active.is_(True)).order_by(
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
                semesterId=course.current_semester_id,
                availability=AvailabilityResponse(
                    available=not (reasons := availability_for_course(db, course)),
                    reasons=reasons,
                ),
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
        rooms=[
            RoomOptionResponse(
                id=room.id,
                name=room.name,
                capacity=room.capacity,
            )
            for room in rooms
        ],
        lecturers=[
            PlanningEntityResponse(id=lecturer.id, name=lecturer.name)
            for lecturer in lecturers
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
