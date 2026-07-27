from __future__ import annotations

from datetime import date, timedelta


SEMESTER_START = date(2026, 9, 1)
SEMESTER_END = date(2027, 1, 31)


def calendar_workspace_scale_fixture(
    *,
    course_count: int = 100,
    occurrence_count: int = 500,
    holiday_count: int = 50,
) -> dict:
    """Return deterministic, bounded source records for workspace tests."""

    courses = [
        {
            "course_id": index,
            "name": f"Course {index:03d}",
            "total_units": 10,
            "cohort_id": index,
            "cohort_name": f"Cohort {index:03d}",
            "cohort_size": 20 + index % 25,
            "study_type_id": 1 + index % 3,
            "study_type_name": ("Full-time", "Part-time", "Evening")[index % 3],
            "lecturer_id": 1 + index % 20,
            "lecturer_name": f"Lecturer {1 + index % 20:02d}",
            "room_id": 1 + index % 30,
            "room_name": f"Room {1 + index % 30:02d}",
            "room_capacity": 20 + (index % 6) * 10,
        }
        for index in range(1, course_count + 1)
    ]
    occurrences = []
    for index in range(1, occurrence_count + 1):
        course = courses[(index - 1) % course_count]
        occurrence_date = SEMESTER_START + timedelta(days=(index * 3) % 145)
        kind = "exam" if index % 10 == 0 else "teaching"
        occurrences.append(
            {
                "id": index,
                "kind": kind,
                "course_id": course["course_id"],
                "date": occurrence_date,
                "start_hour": 8 + index % 8,
                "units": 0 if kind == "exam" else 2,
                "lecturer_id": course["lecturer_id"],
                "room_id": course["room_id"],
                "cohort_id": course["cohort_id"],
            }
        )
    holidays = [
        {
            "id": index,
            "date": SEMESTER_START + timedelta(days=(index * 2) % 145),
            "name": f"Institution holiday {index:02d}",
        }
        for index in range(1, holiday_count + 1)
    ]
    return {
        "semester": {
            "semester_id": 1,
            "name": "Reference Semester",
            "start_date": SEMESTER_START,
            "end_date": SEMESTER_END,
        },
        "courses": courses,
        "occurrences": occurrences,
        "holidays": holidays,
    }


def small_calendar_workspace_fixture() -> dict:
    return calendar_workspace_scale_fixture(
        course_count=4,
        occurrence_count=12,
        holiday_count=2,
    )
