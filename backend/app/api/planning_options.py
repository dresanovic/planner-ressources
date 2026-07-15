from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.planning import Course, CourseEligibleLecturer, CourseEligibleRoom, Lecturer, Room, Semester, StudyTypeTimeWindow
from app.schemas.academic_catalog import AvailabilityResponse
from app.schemas.draft_schedule import PlanningEntityResponse
from app.schemas.planning_options import (
    CourseOptionResponse,
    PlanningOptionsResponse,
    RoomOptionResponse,
    SemesterOptionResponse,
    TimeWindowOptionResponse,
    CoursePlanningResourceExtension,
)
from app.services.academic_catalog import availability_for_course
from app.services.resource_catalog import resource_candidate

router = APIRouter(prefix="/api/planning-options", tags=["planning options"])


def _course_resource_extension(course: Course) -> CoursePlanningResourceExtension:
    cohort_size = course.cohort.student_count
    return CoursePlanningResourceExtension(
        courseId=course.id,
        eligibleLecturers=[
            resource_candidate(item.lecturer, kind="lecturer", eligible=True, cohort_size=cohort_size)
            for item in course.eligible_lecturers
        ],
        eligibleRooms=[
            resource_candidate(item.room, kind="room", eligible=True, cohort_size=cohort_size)
            for item in course.eligible_rooms
        ],
        preferences={"minimizeLecturerChanges": True, "minimizeRoomChanges": True},
    )


@router.get("", response_model=PlanningOptionsResponse)
def read_planning_options(
    semester_id: int | None = Query(None, alias="semesterId"),
    db: Session = Depends(get_db),
) -> PlanningOptionsResponse:
    courses = (
        db.execute(
            select(Course)
            .options(
                selectinload(Course.eligible_lecturers).selectinload(CourseEligibleLecturer.lecturer),
                selectinload(Course.cohort),
                selectinload(Course.eligible_rooms).selectinload(CourseEligibleRoom.room),
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
    rooms = db.execute(select(Room).where(Room.is_active.is_(True)).order_by(Room.name)).scalars().all()
    lecturers = db.execute(select(Lecturer).where(Lecturer.is_active.is_(True)).order_by(Lecturer.name)).scalars().all()
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
    active_window_study_type_ids = {window.study_type_id for window in time_windows}

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
                    available=not (reasons := availability_for_course(
                        db, course, active_window_study_type_ids=active_window_study_type_ids
                    )),
                    reasons=reasons,
                ),
                lecturer=PlanningEntityResponse(id=course.lecturer.id, name=course.lecturer.name) if course.lecturer else None,
                cohort=PlanningEntityResponse(id=course.cohort.id, name=course.cohort.name),
                room=PlanningEntityResponse(id=course.room.id, name=course.room.name) if course.room else None,
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
            {
                "id": room.id,
                "name": room.name,
                "referenceCode": room.reference_code,
                "capacity": room.capacity,
                "isActive": room.is_active,
                "revision": room.revision,
            }
            for room in rooms
        ],
        lecturers=[
            {"id": lecturer.id, "name": lecturer.name, "referenceCode": lecturer.reference_code, "isActive": lecturer.is_active, "revision": lecturer.revision}
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
        courseResources=[
            _course_resource_extension(course)
            for course in courses
        ],
    )
