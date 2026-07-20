from datetime import date, time

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    InstitutionHoliday,
    Lecturer,
    Room,
    Semester,
    StudyType,
    StudyTypeTimeWindow,
)


def exam_catalog(*, course_id: int = 1, semester_id: int = 1):
    lecturer = Lecturer(id=course_id, name=f"Lecturer {course_id}", reference_code=f"L-{course_id}", normalized_reference_code=f"l-{course_id}")
    room = Room(id=course_id, name=f"Room {course_id}", reference_code=f"R-{course_id}", normalized_reference_code=f"r-{course_id}", capacity=80)
    cohort = Cohort(id=course_id, name=f"Cohort {course_id}", student_count=30)
    semester = Semester(id=semester_id, name="Fall 2026", start_date=date(2026, 9, 1), end_date=date(2026, 12, 31))
    study_type = StudyType(
        id=course_id,
        name="Full-time",
        time_windows=[StudyTypeTimeWindow(weekday=weekday, start_time=time(9), end_time=time(17), sort_order=weekday) for weekday in range(5)],
    )
    course = Course(
        id=course_id,
        name=f"Course {course_id}",
        total_units=4,
        min_session_units=2,
        max_session_units=2,
        cohort_id=cohort.id,
        study_type_id=study_type.id,
        current_semester_id=semester.id,
        eligible_lecturers=[CourseEligibleLecturer(lecturer_id=lecturer.id)],
        eligible_rooms=[CourseEligibleRoom(room_id=room.id)],
    )
    return lecturer, room, cohort, semester, study_type, course


def teaching_draft(*, course_id: int = 1, semester_id: int = 1, final_date: date = date(2026, 10, 2)):
    return DraftSchedule(
        course_id=course_id,
        semester_id=semester_id,
        revision=1,
        status="generated",
        course_name_snapshot=f"Course {course_id}",
        course_total_units_snapshot=4,
        course_min_session_units_snapshot=2,
        course_max_session_units_snapshot=2,
        cohort_id_snapshot=course_id,
        cohort_name_snapshot=f"Cohort {course_id}",
        cohort_size_snapshot=30,
        study_type_id_snapshot=course_id,
        study_type_name_snapshot="Full-time",
        semester_name_snapshot="Fall 2026",
        semester_start_date_snapshot=date(2026, 9, 1),
        semester_end_date_snapshot=date(2026, 12, 31),
        sessions=[DraftSession(course_id=course_id, lecturer_id=course_id, cohort_id=course_id, room_id=course_id, date=final_date, start_time=time(9), end_time=time(12), units=2, constraint_window_index=0)],
    )


def holiday(*, day: date = date(2026, 10, 12)):
    return InstitutionHoliday(date=day, name="Public holiday", revision=1)


def configuration_values(**overrides):
    values = {
        "enabled": True,
        "identifier": "Final exam",
        "duration_minutes": 120,
        "recommended_start_override": None,
        "recommended_end_override": None,
        "required_capacity": 40,
        "exam_type": "Written",
        "responsible_lecturer_id": 1,
        "configuration_consumed": False,
        "revision": 1,
    }
    values.update(overrides)
    return values


def exam_session_values(*, active: bool = True, **overrides):
    values = {
        "course_id": 1,
        "semester_id": 1,
        "cohort_id": 1,
        "lecturer_id": 1,
        "room_id": 1,
        "exam_date": date(2026, 10, 16) if active else date(2025, 10, 16),
        "start_time": time(9),
        "end_time": time(11),
        "source": "manual",
        "revision": 1,
        "configuration_identifier": "Final exam",
        "configuration_revision": 1,
        "duration_minutes": 120,
        "exam_type": "Written",
        "required_capacity": 40,
        "recommended_start_date": date(2026, 10, 9),
        "recommended_end_date": date(2026, 10, 16),
        "recommendation_was_overridden": False,
        "final_teaching_date": date(2026, 10, 2),
        "final_teaching_end_time": time(12),
        "final_teaching_session_id_snapshot": 1,
        "course_name_snapshot": "Course 1",
        "semester_name_snapshot": "Fall 2026",
        "cohort_name_snapshot": "Cohort 1",
        "lecturer_name_snapshot": "Lecturer 1",
        "lecturer_reference_snapshot": "L-1",
        "room_name_snapshot": "Room 1",
        "room_reference_snapshot": "R-1",
    }
    values.update(overrides)
    return values
