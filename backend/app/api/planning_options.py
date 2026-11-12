from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.session import get_db
from app.models.planning import Cohort, Course, CourseEligibleLecturer, CourseEligibleRoom, GenerationConstraintSet, Lecturer, Room, Semester, CohortCalendarTimeWindow
from app.schemas.academic_catalog import AvailabilityResponse
from app.schemas.draft_schedule import PlanningEntityResponse
from app.schemas.planning_options import (
    CohortOptionResponse,
    CourseOptionResponse,
    PlanningOptionsResponse,
    RoomOptionResponse,
    SemesterOptionResponse,
    TimeWindowOptionResponse,
    CoursePlanningResourceExtension,
)
from app.services.academic_catalog import availability_for_course
from app.services.schedule_generation import format_clock
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
                selectinload(Course.cohort_calendar),
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
        and course.cohort_calendar is not None and course.cohort_calendar.is_active
    ]
    semesters = db.execute(select(Semester).where(Semester.is_active.is_(True)).order_by(Semester.start_date, Semester.name)).scalars().all()
    cohorts = db.execute(select(Cohort).where(Cohort.is_active.is_(True)).order_by(Cohort.name)).scalars().all()
    rooms = db.execute(select(Room).where(Room.is_active.is_(True)).order_by(Room.name)).scalars().all()
    lecturers = db.execute(select(Lecturer).where(Lecturer.is_active.is_(True)).order_by(Lecturer.name)).scalars().all()
    time_windows = (
        db.execute(
            select(CohortCalendarTimeWindow).where(CohortCalendarTimeWindow.is_active.is_(True)).order_by(
                CohortCalendarTimeWindow.cohort_calendar_id,
                CohortCalendarTimeWindow.sort_order,
                CohortCalendarTimeWindow.weekday,
            )
        )
        .scalars()
        .all()
    )
    windows_by_cohort_calendar = {}
    for window in time_windows:
        windows_by_cohort_calendar.setdefault(window.cohort_calendar_id,[]).append(window)
    constraint_sets = {(row.course_id,row.semester_id):row for row in db.scalars(
        select(GenerationConstraintSet).where(GenerationConstraintSet.course_id.in_([c.id for c in courses])))} if courses else {}

    return PlanningOptionsResponse(
        courses=[
            CourseOptionResponse(
                id=course.id,
                name=course.name,
                totalUnits=course.total_units,
                minSessionUnits=course.min_session_units,
                maxSessionUnits=course.max_session_units,
                preferredSessionUnits=course.preferred_session_units,
                semesterId=course.current_semester_id,
                availability=AvailabilityResponse(
                    available=not (reasons := availability_for_course(
                        db, course, active_windows_by_cohort_calendar=windows_by_cohort_calendar,
                        constraint_sets_by_course_semester=constraint_sets
                    )),
                    reasons=reasons,
                ),
                lecturer=PlanningEntityResponse(id=course.lecturer.id, name=course.lecturer.name) if course.lecturer else None,
                cohort=PlanningEntityResponse(id=course.cohort.id, name=course.cohort.name),
                cohortSize=course.cohort.student_count,
                room=PlanningEntityResponse(id=course.room.id, name=course.room.name) if course.room else None,
                cohortCalendar=PlanningEntityResponse(id=course.cohort_calendar.id, name=course.cohort_calendar.name) if course.cohort_calendar else None,
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
        cohorts=[
            CohortOptionResponse(
                id=cohort.id,
                name=cohort.name,
                studentCount=cohort.student_count,
            )
            for cohort in cohorts
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
                cohortCalendarId=window.cohort_calendar_id,
                weekday=window.weekday,
                kind=window.kind, date=window.date, is_intensive=window.is_intensive,
                startTime=format_clock(window.start_time),
                endTime=format_clock(window.end_time),
                sortOrder=window.sort_order,
            )
            for window in time_windows
        ],
        courseResources=[
            _course_resource_extension(course)
            for course in courses
        ],
    )
