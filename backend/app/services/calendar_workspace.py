from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timezone
from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Course,
    CourseEligibleLecturer,
    DraftSchedule,
    ExamSession,
    GenerationConstraintSet,
    InstitutionHoliday,
    Lecturer,
    PlanningOutcome,
    ResourceUnavailabilityPeriod,
    Room,
    ScheduleRevision,
    Semester,
    StudyTypeTimeWindow,
)
from app.services.draft_schedule_validation import (
    ValidationOccurrenceRecord,
    evaluate_teaching_constraints,
    evaluate_occurrence_records,
)
from app.services.holiday_calendar import HolidayReference
from app.services.resource_rules import resource_is_unavailable
from app.services.schedule_generation import TimeWindowPlan


WORKING_STATES = {"draft", "ready_for_review"}


class CalendarWorkspaceError(RuntimeError):
    def __init__(self, status_code: int, detail: str) -> None:
        super().__init__(detail)
        self.status_code = status_code
        self.detail = detail


def get_calendar_workspace(
    db: Session, semester_id: int, revision_id: int | None = None
) -> dict[str, Any]:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise CalendarWorkspaceError(404, "The selected semester does not exist.")
    revisions = list(
        db.scalars(
            select(ScheduleRevision)
            .where(ScheduleRevision.semester_id == semester_id)
            .order_by(ScheduleRevision.revision_number.desc())
        )
    )
    initial_context_signature = tuple(
        (row.id, row.state, row.row_version) for row in revisions
    )
    active = next((row for row in revisions if row.state in WORKING_STATES), None)
    published = next((row for row in revisions if row.state == "published"), None)
    available = {
        "activeWorking": _selector(active, "active_working") if active else None,
        "currentPublished": _selector(published, "current_published")
        if published
        else None,
    }
    if revision_id is None:
        selected = active or published
    else:
        selected = next((row for row in revisions if row.id == revision_id), None)
        if selected is None:
            raise CalendarWorkspaceError(
                404, "The requested schedule revision does not exist."
            )
        if selected not in {active, published}:
            raise CalendarWorkspaceError(
                422,
                "Only the active Working or Current Published revision can be opened in the calendar workspace.",
            )
    if selected is None:
        return _no_revision_response(semester)
    initial_selected_state = selected.state
    initial_selected_version = selected.row_version

    if selected is active:
        courses, occurrences, lecturer_labels = _working_content(db, semester)
        designation = "active_working"
        content_source = "active_working"
        read_only = False
    else:
        courses, occurrences, lecturer_labels = _published_content(selected)
        designation = "current_published"
        content_source = "captured_published"
        read_only = True

    _mark_planning_eligibility(db, semester, courses)
    holidays = [
        {
            "holidayRef": f"holiday:{row.id}",
            "date": row.date.isoformat(),
            "name": row.name,
        }
        for row in db.scalars(
            select(InstitutionHoliday)
            .where(
                InstitutionHoliday.date >= semester.start_date,
                InstitutionHoliday.date <= semester.end_date,
            )
            .order_by(InstitutionHoliday.date, InstitutionHoliday.id)
        )
    ]
    findings = derive_calendar_validation_findings(
        db, courses, occurrences, holidays
    )
    course_refs = {row["courseRef"] for row in courses}
    outcomes = [
        row for row in _outcomes(db, selected.id) if row["courseRef"] in course_refs
    ]
    _link_refs(courses, occurrences, findings, outcomes)
    summary = _summary(courses, occurrences, findings, outcomes)
    constraint_context_missing = (
        designation == "current_published"
        and any(
            course.get("constraintProfileAvailable") is False
            and any(
                occurrence["kind"] == "teaching"
                and occurrence["courseRef"] == course["courseRef"]
                for occurrence in occurrences
            )
            for course in courses
        )
    )
    validation_source_missing = constraint_context_missing or any(
        row["category"] == "other"
        and row["details"].get("issueCode")
        in {"VALIDATION_DATA_MISSING", "HOLIDAY_DATA_MISSING"}
        for row in findings
    )
    if (
        validation_source_missing
        and summary["needsReview"]["availability"] == "available"
    ):
        summary["needsReview"]["availability"] = "partial"
    facets = _facets(
        courses,
        occurrences,
        findings,
        outcomes,
        designation,
        selected.state,
        lecturer_labels,
    )
    for course in courses:
        course.pop("cohortSize", None)
        course.pop("constraintProfileAvailable", None)
    for occurrence in occurrences:
        occurrence.pop("cohortSize", None)
        if occurrence["kind"] != "exam":
            occurrence.pop("requiredCapacity", None)
        occurrence.pop("constraintProfile", None)
    response = {
        "semester": _semester(semester),
        "workspaceState": "loaded",
        "selectedRevision": {
            **_selector(selected, designation),
            "readOnly": read_only,
            "contentSource": content_source,
            "validationBasis": "current",
            "snapshotSchemaVersion": selected.snapshot_schema_version,
        },
        "availableContexts": available,
        "workspaceToken": "pending",
        "sectionStatus": {
            name: (
                {
                    "availability": "partial",
                    "reason": (
                        "Legacy Published content lacks captured constraint "
                        "context for part of current validation."
                        if constraint_context_missing
                        else "Some current validation source data is unavailable."
                    ),
                    "coverage": "Known current findings remain available.",
                }
                if name == "validationFindings" and validation_source_missing
                else {"availability": "available"}
            )
            for name in (
                "courses",
                "occurrences",
                "holidays",
                "validationFindings",
                "planningOutcomes",
                "summary",
            )
        },
        "courses": courses,
        "occurrences": occurrences,
        "holidays": holidays,
        "validationFindings": findings,
        "planningOutcomes": outcomes,
        "summary": summary,
        "filterFacets": facets,
    }
    response["workspaceToken"] = _token(response)
    db.refresh(selected)
    current_context_signature = tuple(
        tuple(row)
        for row in db.execute(
            select(
                ScheduleRevision.id,
                ScheduleRevision.state,
                ScheduleRevision.row_version,
            )
            .where(ScheduleRevision.semester_id == semester_id)
            .order_by(ScheduleRevision.revision_number.desc())
        )
    )
    if (
        selected.state != initial_selected_state
        or selected.row_version != initial_selected_version
        or current_context_signature != initial_context_signature
    ):
        raise CalendarWorkspaceError(
            409, "The selected revision changed while the workspace was loading."
        )
    return response


def _working_content(
    db: Session, semester: Semester
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    lecturer_labels = {
        f"lecturer:{row.id}": row.name
        for row in db.scalars(select(Lecturer))
    }
    course_rows = list(
        db.scalars(
            select(Course)
            .where(
                or_(
                    Course.current_semester_id == semester.id,
                    Course.id.in_(
                        select(DraftSchedule.course_id).where(
                            DraftSchedule.semester_id == semester.id
                        )
                    ),
                    Course.id.in_(
                        select(ExamSession.course_id).where(
                            ExamSession.semester_id == semester.id
                        )
                    ),
                )
            )
            .options(
                selectinload(Course.cohort),
                selectinload(Course.study_type),
                selectinload(Course.eligible_lecturers).selectinload(
                    CourseEligibleLecturer.lecturer
                ),
            )
            .order_by(Course.id)
        ).unique()
    )
    drafts = list(
        db.scalars(
            select(DraftSchedule)
            .where(DraftSchedule.semester_id == semester.id)
            .options(selectinload(DraftSchedule.sessions))
        )
    )
    drafts_by_course = {row.course_id: row for row in drafts}
    saved_constraints = {
        row.course_id: row
        for row in db.scalars(
            select(GenerationConstraintSet)
            .where(GenerationConstraintSet.semester_id == semester.id)
            .options(selectinload(GenerationConstraintSet.windows))
        ).unique()
    }
    study_windows: dict[int, list[StudyTypeTimeWindow]] = {}
    for row in db.scalars(
        select(StudyTypeTimeWindow)
        .where(StudyTypeTimeWindow.is_active.is_(True))
        .order_by(
            StudyTypeTimeWindow.study_type_id,
            StudyTypeTimeWindow.sort_order,
        )
    ):
        study_windows.setdefault(row.study_type_id, []).append(row)
    courses: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    for course in course_rows:
        draft = drafts_by_course.get(course.id)
        sessions = sorted(
            list(draft.sessions) if draft else [],
            key=lambda item: (item.date, item.start_time, item.id or 0),
        )
        scheduled = sum(item.units for item in sessions)
        saved_constraint = saved_constraints.get(course.id)
        constraint_profile = {
            "isCustom": saved_constraint is not None,
            "sourceRevision": (
                saved_constraint.revision if saved_constraint is not None else None
            ),
            "planningStartDate": (
                saved_constraint.planning_start_date.isoformat()
                if saved_constraint
                else semester.start_date.isoformat()
            ),
            "planningEndDate": (
                saved_constraint.planning_end_date.isoformat()
                if saved_constraint
                else semester.end_date.isoformat()
            ),
            "allowedTeachingWindows": [
                {
                    "weekday": window.weekday,
                    "startTime": _clock(window.start_time),
                    "endTime": _clock(window.end_time),
                    "sortOrder": window.sort_order,
                    "sourceTimeWindowId": window.id,
                }
                for window in study_windows.get(course.study_type_id, [])
            ],
        }
        courses.append(
            _course(
                course_id=course.id,
                name=course.name,
                cohort=course.cohort.name,
                cohort_size=course.cohort.student_count,
                study_type=course.study_type.name,
                total=course.total_units,
                scheduled=scheduled,
                lecturer_refs=[
                    f"lecturer:{link.lecturer_id}"
                    for link in course.eligible_lecturers
                ],
            )
        )
        for session in sessions:
            occurrences.append(
                {
                    "occurrenceRef": f"teaching:{session.id}",
                    "kind": "teaching",
                    "courseRef": f"course:{course.id}",
                    "date": session.date.isoformat(),
                    "startTime": _clock(session.start_time),
                    "endTime": _clock(session.end_time),
                    "cohort": course.cohort.name,
                    "cohortSize": course.cohort.student_count,
                    "lecturerRefs": [f"lecturer:{session.lecturer_id}"],
                    "roomRef": f"room:{session.room_id}",
                    "findingRefs": [],
                    "teachingUnits": session.units,
                    "source": draft.status or "saved",
                    "constraintProfile": constraint_profile,
                }
            )
    exams = list(
        db.scalars(
            select(ExamSession)
            .where(ExamSession.semester_id == semester.id)
            .options(
                selectinload(ExamSession.course),
                selectinload(ExamSession.cohort),
            )
            .order_by(ExamSession.exam_date, ExamSession.start_time, ExamSession.id)
        )
    )
    for exam in exams:
        if not any(row["courseId"] == exam.course_id for row in courses):
            courses.append(
                _course(
                    course_id=exam.course_id,
                    name=exam.course_name_snapshot,
                    cohort=exam.cohort_name_snapshot,
                    cohort_size=exam.required_capacity,
                    study_type=exam.course.study_type.name,
                    total=exam.course.total_units,
                    scheduled=0,
                    lecturer_refs=[f"lecturer:{exam.lecturer_id}"],
                )
            )
        occurrences.append(
            {
                "occurrenceRef": f"exam:{exam.id}",
                "kind": "exam",
                "courseRef": f"course:{exam.course_id}",
                "date": exam.exam_date.isoformat(),
                "startTime": _clock(exam.start_time),
                "endTime": _clock(exam.end_time),
                "cohort": exam.cohort_name_snapshot,
                "cohortSize": exam.required_capacity,
                "lecturerRefs": [f"lecturer:{exam.lecturer_id}"],
                "roomRef": f"room:{exam.room_id}",
                "findingRefs": [],
                "examType": exam.exam_type,
                "durationMinutes": exam.duration_minutes,
                "requiredCapacity": exam.required_capacity,
                "assignedRoomName": exam.room_name_snapshot,
                "currentRoomCapacity": None,
                "validityContext": {
                    "configurationIdentifier": exam.configuration_identifier,
                    "configurationRevision": exam.configuration_revision,
                    "finalTeachingDate": exam.final_teaching_date.isoformat(),
                    "finalTeachingEndTime": _clock(exam.final_teaching_end_time),
                    "source": exam.source,
                },
                "recommendationContext": {
                    "recommendedStartDate": exam.recommended_start_date.isoformat(),
                    "recommendedEndDate": exam.recommended_end_date.isoformat(),
                    "recommendationWasOverridden": exam.recommendation_was_overridden,
                    "outsideRecommendedWindow": not (
                        exam.recommended_start_date
                        <= exam.exam_date
                        <= exam.recommended_end_date
                    ),
                },
            }
        )
    return (
        sorted(courses, key=lambda item: item["courseId"]),
        occurrences,
        lecturer_labels,
    )


def _published_content(
    revision: ScheduleRevision,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, str]]:
    snapshot = revision.snapshot_document or {}
    courses: list[dict[str, Any]] = []
    occurrences: list[dict[str, Any]] = []
    lecturer_labels: dict[str, str] = {}
    for source in snapshot.get("courses", []):
        course_id = source["sourceCourseId"]
        lecturer_labels.update(
            {
                f"lecturer:{session['lecturer']['sourceId']}": session[
                    "lecturer"
                ]["name"]
                for session in source.get("teachingSessions", [])
            }
        )
        course = _course(
            course_id=course_id,
            name=source["name"],
            cohort=source["cohort"]["name"],
            cohort_size=source["cohort"]["size"],
            study_type=source["studyType"]["name"],
            total=source["totalUnits"],
            scheduled=source["scheduledUnits"],
            lecturer_refs=sorted(
                {
                    f"lecturer:{session['lecturer']['sourceId']}"
                    for session in source.get("teachingSessions", [])
                }
            ),
        )
        course["constraintProfileAvailable"] = (
            source.get("constraintProfile") is not None
        )
        courses.append(course)
        for session in source.get("teachingSessions", []):
            occurrences.append(
                {
                    "occurrenceRef": f"teaching:{session['sourceSessionId']}",
                    "kind": "teaching",
                    "courseRef": f"course:{course_id}",
                    "date": session["date"],
                    "startTime": _clock(session["startTime"]),
                    "endTime": _clock(session["endTime"]),
                    "cohort": source["cohort"]["name"],
                    "cohortSize": source["cohort"]["size"],
                    "lecturerRefs": [
                        f"lecturer:{session['lecturer']['sourceId']}"
                    ],
                    "roomRef": f"room:{session['room']['sourceId']}",
                    "findingRefs": [],
                    "teachingUnits": session["units"],
                    "source": source.get("draftStatus") or "published",
                    "constraintProfile": source.get("constraintProfile"),
                }
            )
    course_by_id = {row["courseId"]: row for row in courses}
    for exam in snapshot.get("examSessions", []):
        course_id = exam["course"]["sourceId"]
        lecturer_labels[
            f"lecturer:{exam['lecturer']['sourceId']}"
        ] = exam["lecturer"]["name"]
        if course_id not in course_by_id:
            course = _course(
                course_id=course_id,
                name=exam["course"]["name"],
                cohort=exam["cohort"]["name"],
                cohort_size=exam["requiredCapacity"],
                study_type="Captured",
                total=0,
                scheduled=0,
                lecturer_refs=[f"lecturer:{exam['lecturer']['sourceId']}"],
            )
            course["constraintProfileAvailable"] = True
            courses.append(course)
            course_by_id[course_id] = course
        occurrences.append(
            {
                "occurrenceRef": f"exam:{exam['sourceExamId']}",
                "kind": "exam",
                "courseRef": f"course:{course_id}",
                "date": exam["examDate"],
                "startTime": _clock(exam["startTime"]),
                "endTime": _clock(exam["endTime"]),
                "cohort": exam["cohort"]["name"],
                "cohortSize": exam["requiredCapacity"],
                "lecturerRefs": [f"lecturer:{exam['lecturer']['sourceId']}"],
                "roomRef": f"room:{exam['room']['sourceId']}",
                "findingRefs": [],
                "examType": exam["examType"],
                "durationMinutes": exam["durationMinutes"],
                "requiredCapacity": exam["requiredCapacity"],
                "assignedRoomName": exam["room"]["name"],
                "currentRoomCapacity": None,
                "validityContext": {
                    "configurationIdentifier": exam["configurationIdentifier"],
                    "configurationRevision": exam["configurationRevision"],
                    "finalTeachingDate": exam["finalTeachingDate"],
                    "finalTeachingEndTime": _clock(exam["finalTeachingEndTime"]),
                    "source": exam["source"],
                    "capturedIssues": exam.get("validityIssues", []),
                },
                "recommendationContext": {
                    "recommendedStartDate": exam["recommendedStartDate"],
                    "recommendedEndDate": exam["recommendedEndDate"],
                    "recommendationWasOverridden": exam[
                        "recommendationWasOverridden"
                    ],
                    "outsideRecommendedWindow": exam[
                        "outsideRecommendedWindow"
                    ],
                },
            }
        )
    return (
        sorted(courses, key=lambda item: item["courseId"]),
        occurrences,
        lecturer_labels,
    )


def derive_calendar_validation_findings(
    db: Session,
    courses: list[dict[str, Any]],
    occurrences: list[dict[str, Any]],
    holidays: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Derive FS-014 findings for the complete selected revision."""

    findings: list[dict[str, Any]] = []
    course_by_ref = {row["courseRef"]: row for row in courses}
    occurrence_by_ref = {
        row["occurrenceRef"]: row for row in occurrences
    }
    holiday_by_date = {
        date.fromisoformat(row["date"]): HolidayReference(
            id=index,
            date=date.fromisoformat(row["date"]),
            name=row["name"],
            revision=1,
        )
        for index, row in enumerate(holidays, start=1)
    }
    holiday_ref_by_date = {
        row["date"]: row["holidayRef"] for row in holidays
    }
    course_ids = [row["courseId"] for row in courses]
    current_courses = {
        row.id: row
        for row in db.scalars(
            select(Course)
            .where(Course.id.in_(course_ids))
            .options(
                selectinload(Course.cohort),
                selectinload(Course.eligible_lecturers),
                selectinload(Course.eligible_rooms),
            )
        ).unique()
    } if course_ids else {}
    lecturers = {
        f"lecturer:{row.id}": row
        for row in db.scalars(
            select(Lecturer).options(
                selectinload(Lecturer.unavailability_periods).selectinload(
                    ResourceUnavailabilityPeriod.weekdays
                )
            )
        ).unique()
    }
    rooms = {
        f"room:{row.id}": row
        for row in db.scalars(
            select(Room).options(
                selectinload(Room.unavailability_periods).selectinload(
                    ResourceUnavailabilityPeriod.weekdays
                )
            )
        ).unique()
    }
    for occurrence in occurrences:
        if occurrence["kind"] != "exam":
            continue
        current_room = rooms.get(occurrence["roomRef"])
        occurrence["currentRoomCapacity"] = (
            current_room.capacity if current_room is not None else None
        )
        if current_room is not None:
            occurrence["assignedRoomName"] = current_room.name
    common_findings = evaluate_occurrence_records(
        [
            ValidationOccurrenceRecord(
                occurrence_ref=occurrence["occurrenceRef"],
                course_ref=occurrence["courseRef"],
                date=date.fromisoformat(occurrence["date"]),
                start_time=time.fromisoformat(occurrence["startTime"]),
                end_time=time.fromisoformat(occurrence["endTime"]),
                lecturer_refs=tuple(occurrence["lecturerRefs"]),
                room_ref=occurrence["roomRef"],
                cohort_ref=f"cohort:{occurrence['cohort']}",
                required_capacity=(
                    occurrence.get("requiredCapacity")
                    if occurrence["kind"] == "exam"
                    else current_courses.get(
                        int(occurrence["courseRef"].split(":")[1])
                    ).cohort.student_count
                    if int(occurrence["courseRef"].split(":")[1])
                    in current_courses
                    else None
                )
                or (
                    occurrence.get("requiredCapacity")
                    or course_by_ref.get(occurrence["courseRef"], {}).get(
                        "cohortSize"
                    )
                    or occurrence.get("cohortSize")
                    or 0
                ),
            )
            for occurrence in occurrences
        ],
        room_capacities={
            room_ref: room.capacity for room_ref, room in rooms.items()
        },
        holidays_by_date=holiday_by_date,
        eligible_lecturer_refs_by_course={
            f"course:{course_id}": {
                f"lecturer:{link.lecturer_id}"
                for link in course.eligible_lecturers
            }
            for course_id, course in current_courses.items()
        },
        eligible_room_refs_by_course={
            f"course:{course_id}": {
                f"room:{link.room_id}" for link in course.eligible_rooms
            }
            for course_id, course in current_courses.items()
        },
        active_lecturer_refs={
            lecturer_ref
            for lecturer_ref, lecturer in lecturers.items()
            if lecturer.is_active
        },
        active_room_refs={
            room_ref for room_ref, room in rooms.items() if room.is_active
        },
        unavailable_lecturer_refs_by_occurrence={
            occurrence["occurrenceRef"]: {
                lecturer_ref
                for lecturer_ref in occurrence["lecturerRefs"]
                if lecturer_ref in lecturers
                and resource_is_unavailable(
                    lecturers[lecturer_ref].unavailability_periods,
                    date.fromisoformat(occurrence["date"]),
                    time.fromisoformat(occurrence["startTime"]),
                    time.fromisoformat(occurrence["endTime"]),
                )
            }
            for occurrence in occurrences
        },
        unavailable_room_refs_by_occurrence={
            occurrence["occurrenceRef"]: {
                occurrence["roomRef"]
            }
            if occurrence["roomRef"] in rooms
            and resource_is_unavailable(
                rooms[occurrence["roomRef"]].unavailability_periods,
                date.fromisoformat(occurrence["date"]),
                time.fromisoformat(occurrence["startTime"]),
                time.fromisoformat(occurrence["endTime"]),
            )
            else set()
            for occurrence in occurrences
        },
    )
    for finding in common_findings:
        affected_occurrences = list(finding.occurrence_refs)
        affected_courses = sorted(
            {
                occurrence_by_ref[ref]["courseRef"]
                for ref in affected_occurrences
            }
        )
        if finding.category.endswith("_conflict"):
            conflict_type = finding.category.removesuffix("_conflict")
            findings.append(
                {
                    "findingRef": (
                        f"finding:conflict:{conflict_type}:"
                        f"{affected_occurrences[0]}:{affected_occurrences[1]}"
                    ),
                    "category": finding.category,
                    "validationBasis": "current",
                    "affectedCourseRefs": affected_courses,
                    "affectedOccurrenceRefs": affected_occurrences,
                    "details": {
                        "kind": "conflict",
                        "conflictType": conflict_type,
                        "occurrenceRefs": affected_occurrences,
                        "subjectRef": finding.subject_ref,
                    },
                }
            )
        elif finding.category == "room_capacity":
            room = rooms[finding.room_ref]
            occurrence_ref = affected_occurrences[0]
            findings.append(
                {
                    "findingRef": f"finding:capacity:{occurrence_ref}",
                    "category": "room_capacity",
                    "validationBasis": "current",
                    "affectedCourseRefs": affected_courses,
                    "affectedOccurrenceRefs": affected_occurrences,
                    "details": {
                        "kind": "capacity",
                        "occurrenceRef": occurrence_ref,
                        "requiredCapacity": finding.required_capacity,
                        "roomRef": finding.room_ref,
                        "roomName": room.name,
                        "currentCapacity": finding.current_capacity,
                    },
                }
            )
        elif finding.category == "holiday":
            holiday_date = finding.holiday_date.isoformat()
            occurrence_ref = affected_occurrences[0]
            findings.append(
                {
                    "findingRef": f"finding:holiday:{occurrence_ref}",
                    "category": "holiday",
                    "validationBasis": "current",
                    "affectedCourseRefs": affected_courses,
                    "affectedOccurrenceRefs": affected_occurrences,
                    "details": {
                        "kind": "holiday",
                        "holidayRef": holiday_ref_by_date[holiday_date],
                        "holidayDate": holiday_date,
                        "holidayName": finding.holiday_name,
                        "occurrenceRefs": affected_occurrences,
                    },
                }
            )
        else:
            occurrence_ref = affected_occurrences[0]
            findings.append(
                {
                    "findingRef": (
                        f"finding:other:{occurrence_ref}:"
                        f"{finding.issue_code or 'UNKNOWN'}"
                    ),
                    "category": "other",
                    "validationBasis": "current",
                    "affectedCourseRefs": affected_courses,
                    "affectedOccurrenceRefs": affected_occurrences,
                    "details": {
                        "kind": "other",
                        "issueCode": finding.issue_code or "UNKNOWN",
                        "occurrenceRefs": affected_occurrences,
                        "roomRef": finding.room_ref,
                        "subjectRef": finding.subject_ref,
                    },
                }
            )
    for occurrence in occurrences:
        if occurrence["kind"] == "teaching":
            profile = occurrence.get("constraintProfile")
            if profile is not None:
                windows = [
                    TimeWindowPlan(
                        id=window.get("sourceTimeWindowId"),
                        weekday=window["weekday"],
                        start_time=time.fromisoformat(
                            _clock(window["startTime"])
                        ),
                        end_time=time.fromisoformat(_clock(window["endTime"])),
                        sort_order=window["sortOrder"],
                        constraint_window_index=index,
                    )
                    for index, window in enumerate(
                        profile.get("allowedTeachingWindows", [])
                    )
                ]
                constraint_evaluation = evaluate_teaching_constraints(
                    session_date=date.fromisoformat(occurrence["date"]),
                    start_time=time.fromisoformat(occurrence["startTime"]),
                    end_time=time.fromisoformat(occurrence["endTime"]),
                    planning_start_date=date.fromisoformat(
                        profile["planningStartDate"]
                    ),
                    planning_end_date=date.fromisoformat(
                        profile["planningEndDate"]
                    ),
                    allowed_windows=windows,
                )
                for issue_code in constraint_evaluation.issue_codes:
                    findings.append(
                        {
                            "findingRef": (
                                "finding:other:"
                                f"{occurrence['occurrenceRef']}:"
                                f"{issue_code}"
                            ),
                            "category": "other",
                            "validationBasis": "current",
                            "affectedCourseRefs": [occurrence["courseRef"]],
                            "affectedOccurrenceRefs": [
                                occurrence["occurrenceRef"]
                            ],
                            "details": {
                                "kind": "other",
                                "issueCode": issue_code,
                                "occurrenceRefs": [
                                    occurrence["occurrenceRef"]
                                ],
                            },
                        }
                    )
            else:
                findings.append(
                    {
                        "findingRef": (
                            "finding:other:"
                            f"{occurrence['occurrenceRef']}:"
                            "VALIDATION_DATA_MISSING:constraint_profile"
                        ),
                        "category": "other",
                        "validationBasis": "current",
                        "affectedCourseRefs": [occurrence["courseRef"]],
                        "affectedOccurrenceRefs": [
                            occurrence["occurrenceRef"]
                        ],
                        "details": {
                            "kind": "other",
                            "issueCode": "VALIDATION_DATA_MISSING",
                            "occurrenceRefs": [
                                occurrence["occurrenceRef"]
                            ],
                            "subjectRef": "constraint_profile",
                        },
                    }
                )
        if occurrence["kind"] == "exam":
            recommendation = occurrence.get("recommendationContext") or {}
            captured = occurrence.get("validityContext", {}).get(
                "capturedIssues", []
            )
            issues = [
                (
                    "OUTSIDE_RECOMMENDED_WINDOW",
                    {
                        "recommendedStartDate": recommendation.get(
                            "recommendedStartDate", ""
                        ),
                        "recommendedEndDate": recommendation.get(
                            "recommendedEndDate", ""
                        ),
                    },
                )
            ] if recommendation.get("outsideRecommendedWindow") else []
            issues.extend(
                (issue.get("code", "EXAM_VALIDITY"), issue.get("details", {}))
                for issue in captured
                if issue.get("code") not in {
                    "RESPONSIBLE_LECTURER_INELIGIBLE",
                    "ROOM_INELIGIBLE",
                    "INSUFFICIENT_ROOM_CAPACITY",
                    "LECTURER_UNAVAILABLE",
                    "ROOM_UNAVAILABLE",
                    "INSTITUTION_HOLIDAY",
                    "LECTURER_OCCUPIED",
                    "ROOM_OCCUPIED",
                    "COHORT_OCCUPIED",
                }
            )
            for issue_code, values in issues:
                findings.append(
                    {
                        "findingRef": f"finding:exam:{occurrence['occurrenceRef']}:{issue_code}",
                        "category": "exam_validity",
                        "validationBasis": "current",
                        "affectedCourseRefs": [occurrence["courseRef"]],
                        "affectedOccurrenceRefs": [occurrence["occurrenceRef"]],
                        "details": {
                            "kind": "exam_validity",
                            "examOccurrenceRef": occurrence["occurrenceRef"],
                            "issueCode": issue_code,
                            "supportingValues": {
                                key: value
                                for key, value in values.items()
                                if isinstance(value, (str, int, bool))
                            },
                        },
                    }
                )
    return sorted(findings, key=lambda item: item["findingRef"])


def _outcomes(db: Session, revision_id: int) -> list[dict[str, Any]]:
    rows = list(
        db.scalars(
            select(PlanningOutcome)
            .where(PlanningOutcome.schedule_revision_id == revision_id)
            .order_by(PlanningOutcome.course_id, PlanningOutcome.operation_kind)
        )
    )
    return [
        {
            "outcomeRef": f"outcome:{row.id}",
            "revisionId": revision_id,
            "courseRef": f"course:{row.course_id}",
            "operationKind": row.operation_kind,
            "classification": row.classification,
            "sourceStatus": row.source_status,
            "reasons": _outcome_reasons(row.result_payload),
            "completedAt": _iso(row.completed_at),
        }
        for row in rows
    ]


def _link_refs(courses, occurrences, findings, outcomes) -> None:
    course_by_ref = {row["courseRef"]: row for row in courses}
    occurrence_by_ref = {row["occurrenceRef"]: row for row in occurrences}
    for occurrence in occurrences:
        course_by_ref[occurrence["courseRef"]]["occurrenceRefs"].append(
            occurrence["occurrenceRef"]
        )
    for finding in findings:
        for course_ref in finding["affectedCourseRefs"]:
            if course_ref in course_by_ref:
                course_by_ref[course_ref]["findingRefs"].append(
                    finding["findingRef"]
                )
                course_by_ref[course_ref]["needsReviewReasonRefs"].append(
                    finding["findingRef"]
                )
        for occurrence_ref in finding["affectedOccurrenceRefs"]:
            if occurrence_ref in occurrence_by_ref:
                occurrence_by_ref[occurrence_ref]["findingRefs"].append(
                    finding["findingRef"]
                )
    for outcome in outcomes:
        course = course_by_ref.get(outcome["courseRef"])
        if course is None:
            continue
        course["outcomeRefs"].append(outcome["outcomeRef"])
        if outcome["classification"] in {"failed", "stale"}:
            course["needsReviewReasonRefs"].append(outcome["outcomeRef"])
    for course in courses:
        if course["remainingTeachingUnits"] > 0:
            course["needsReviewReasonRefs"].insert(
                0, f"remaining:{course['courseRef']}"
            )
        for key in (
            "occurrenceRefs",
            "findingRefs",
            "outcomeRefs",
            "needsReviewReasonRefs",
        ):
            course[key] = sorted(set(course[key]))


def _summary(courses, occurrences, findings, outcomes) -> dict[str, Any]:
    remaining = [row for row in courses if row["remainingTeachingUnits"] > 0]
    conflicts = [row for row in findings if row["category"].endswith("_conflict")]
    capacity = [row for row in findings if row["category"] == "room_capacity"]
    capacity_unverified_refs = {
        occurrence_ref
        for row in findings
        if row["category"] == "other"
        and row["details"].get("issueCode") == "VALIDATION_DATA_MISSING"
        and row["details"].get("roomRef")
        for occurrence_ref in row["affectedOccurrenceRefs"]
    }
    eligible = {
        row["courseRef"] for row in courses if row.get("planningEligible", True)
    }
    eligible_outcomes = [
        row for row in outcomes if row["courseRef"] in eligible
    ]
    covered = {row["courseRef"] for row in eligible_outcomes}
    if not eligible:
        planning = _not_applicable(
            "No eligible course-semester context is included."
        )
        planning["coverage"] = {
            "eligibleCourseCount": 0,
            "coveredCourseCount": 0,
            "coverageComplete": False,
        }
    elif not covered:
        planning = {
            "availability": "unavailable",
            "scope": "complete_revision",
            "coverage": {
                "eligibleCourseCount": len(eligible),
                "coveredCourseCount": 0,
                "coverageComplete": False,
            },
            "contributorRefs": [],
            "unavailableReason": "No reliable completed planning outcome is retained for the selected revision.",
        }
    else:
        availability = "available" if covered >= eligible else "partial"
        planning = {
            "availability": availability,
            "scope": "complete_revision",
            "coverage": {
                "eligibleCourseCount": len(eligible),
                "coveredCourseCount": len(covered & eligible),
                "coverageComplete": availability == "available",
            },
            "failedOutcomeCount": sum(
                row["classification"] == "failed" for row in eligible_outcomes
            ),
            "staleOutcomeCount": sum(
                row["classification"] == "stale" for row in eligible_outcomes
            ),
            "unchangedOutcomeCount": sum(
                row["classification"] == "unchanged"
                for row in eligible_outcomes
            ),
            "contributorRefs": [
                row["outcomeRef"]
                for row in eligible_outcomes
                if row["classification"] in {"failed", "stale", "unchanged"}
            ],
        }
    needs_review = [
        row for row in courses if row["needsReviewReasonRefs"]
    ]
    return {
        "unscheduledWork": {
            "availability": "available" if courses else "not_applicable",
            "scope": "complete_revision",
            **(
                {
                    "remainingTeachingUnits": sum(
                        row["remainingTeachingUnits"] for row in courses
                    ),
                    "remainingInstructionalMinutes": sum(
                        row["remainingInstructionalMinutes"] for row in courses
                    ),
                    "contributingCourseCount": len(remaining),
                }
                if courses
                else {
                    "notApplicableReason": "No course-semester context is included."
                }
            ),
            "contributorRefs": [row["courseRef"] for row in remaining],
        },
        "conflicts": {
            "availability": "available" if occurrences else "not_applicable",
            "scope": "complete_revision",
            **(
                {
                    "distinctFindingCount": len(conflicts),
                    "countByType": {
                        kind: sum(
                            row["category"] == f"{kind}_conflict"
                            for row in conflicts
                        )
                        for kind in ("lecturer", "room", "cohort")
                    },
                }
                if occurrences
                else {"notApplicableReason": "No scheduled occurrence is included."}
            ),
            "contributorRefs": [row["findingRef"] for row in conflicts],
        },
        "capacityIssues": {
            "availability": (
                "not_applicable"
                if not occurrences
                else "unavailable"
                if len(capacity_unverified_refs) == len(occurrences)
                else "partial"
                if capacity_unverified_refs
                else "available"
            ),
            "scope": "complete_revision",
            **(
                {"affectedOccurrenceCount": len(capacity)}
                if occurrences
                and len(capacity_unverified_refs) < len(occurrences)
                else {
                    (
                        "unavailableReason"
                        if occurrences
                        else "notApplicableReason"
                    ): (
                        "Room capacity data is unavailable for every included occurrence."
                        if occurrences
                        else "No scheduled occurrence requires capacity evaluation."
                    )
                }
            ),
            "contributorRefs": sorted(
                {
                    ref
                    for row in capacity
                    for ref in row["affectedOccurrenceRefs"]
                }
            ),
        },
        "planningFailures": planning,
        "needsReview": {
            "availability": "available" if courses else "not_applicable",
            "scope": "complete_revision",
            **(
                {"distinctCourseCount": len(needs_review)}
                if courses
                else {"notApplicableReason": "No course-semester context is included."}
            ),
            "contributorRefs": [row["courseRef"] for row in needs_review],
        },
    }


def _facets(
    courses,
    occurrences,
    findings,
    outcomes,
    designation,
    lifecycle_state,
    lecturer_labels=None,
):
    lecturer_labels = lecturer_labels or {}
    outcome_issue_course_refs = {
        row["courseRef"]
        for row in outcomes
        if row["classification"] in {"failed", "stale"}
    }
    scheduled_course_refs = {row["courseRef"] for row in occurrences}
    validation_values = {
        (row["category"], row["category"].replace("_", " ").title())
        for row in findings
    }
    if any(
        not row["findingRefs"]
        and row["courseRef"] not in outcome_issue_course_refs
        for row in occurrences
    ) or any(
        row["courseRef"] not in scheduled_course_refs
        and not row["findingRefs"]
        and row["courseRef"] not in outcome_issue_course_refs
        for row in courses
    ):
        validation_values.add(("none", "No current issue"))
    if any(row["classification"] == "failed" for row in outcomes):
        validation_values.add(("planning_failure", "Planning failure"))
    if any(row["classification"] == "stale" for row in outcomes):
        validation_values.add(("stale_outcome", "Stale outcome"))
    return {
        "courses": _facet((row["courseRef"], row["name"]) for row in courses),
        "cohorts": _facet((row["cohort"], row["cohort"]) for row in courses),
        "lecturers": _facet(
            (ref, lecturer_labels.get(ref, ref.replace(":", " ")))
            for row in occurrences
            for ref in row["lecturerRefs"]
        ),
        "rooms": _facet(
            (row["roomRef"], row["roomRef"].replace(":", " "))
            for row in occurrences
        ),
        "studyTypes": _facet(
            (row["studyType"], row["studyType"]) for row in courses
        ),
        "sessionTypes": _facet(
            (row["kind"], row["kind"].title()) for row in occurrences
        ),
        "lifecycleContexts": _facet(
            (
                (designation, designation.replace("_", " ").title()),
                (
                    lifecycle_state,
                    lifecycle_state.replace("_", " ").title(),
                ),
            )
        ),
        "validationCategories": _facet(validation_values),
    }


def _mark_planning_eligibility(
    db: Session,
    semester: Semester,
    courses: list[dict[str, Any]],
) -> None:
    course_ids = [row["courseId"] for row in courses]
    current_courses = {
        row.id: row
        for row in db.scalars(
            select(Course)
            .where(Course.id.in_(course_ids))
            .options(
                selectinload(Course.cohort),
                selectinload(Course.study_type),
            )
        )
    }
    for course in courses:
        current = current_courses.get(course["courseId"])
        course["planningEligible"] = bool(
            current
            and current.is_active
            and semester.is_active
            and current.current_semester_id == semester.id
            and current.cohort.is_active
            and current.study_type.is_active
        )


def _course(
    *,
    course_id,
    name,
    cohort,
    cohort_size,
    study_type,
    total,
    scheduled,
    lecturer_refs,
):
    remaining = max(total - scheduled, 0)
    return {
        "courseRef": f"course:{course_id}",
        "courseId": course_id,
        "code": f"COURSE-{course_id}",
        "name": name,
        "cohort": cohort,
        "cohortSize": cohort_size,
        "lecturerRefs": lecturer_refs,
        "studyType": study_type,
        "totalTeachingUnits": total,
        "scheduledTeachingUnits": scheduled,
        "remainingTeachingUnits": remaining,
        "remainingInstructionalMinutes": remaining * 45,
        "occurrenceRefs": [],
        "findingRefs": [],
        "outcomeRefs": [],
        "needsReviewReasonRefs": [],
    }


def _no_revision_response(semester: Semester) -> dict[str, Any]:
    empty_facets = {
        key: []
        for key in (
            "courses",
            "cohorts",
            "lecturers",
            "rooms",
            "studyTypes",
            "sessionTypes",
            "lifecycleContexts",
            "validationCategories",
        )
    }
    metric = _not_applicable(
        "No schedule revision exists for the selected semester.",
        scope="no_revision",
    )
    response = {
        "semester": _semester(semester),
        "workspaceState": "no_revision",
        "selectedRevision": None,
        "availableContexts": {
            "activeWorking": None,
            "currentPublished": None,
        },
        "workspaceToken": "pending",
        "sectionStatus": {
            name: {
                "availability": "unavailable",
                "reason": "No schedule revision exists.",
            }
            for name in (
                "courses",
                "occurrences",
                "holidays",
                "validationFindings",
                "planningOutcomes",
                "summary",
            )
        },
        "courses": [],
        "occurrences": [],
        "holidays": [],
        "validationFindings": [],
        "planningOutcomes": [],
        "summary": {
            key: dict(metric)
            for key in (
                "unscheduledWork",
                "conflicts",
                "capacityIssues",
                "planningFailures",
                "needsReview",
            )
        },
        "filterFacets": empty_facets,
    }
    response["workspaceToken"] = _token(response)
    return response


def _selector(revision, designation):
    return {
        "revisionId": revision.id,
        "revisionNumber": revision.revision_number,
        "lifecycleState": revision.state,
        "designation": designation,
    }


def _semester(semester):
    return {
        "semesterId": semester.id,
        "name": semester.name,
        "startDate": semester.start_date.isoformat(),
        "endDate": semester.end_date.isoformat(),
    }


def _not_applicable(reason, scope="complete_revision"):
    return {
        "availability": "not_applicable",
        "scope": scope,
        "contributorRefs": [],
        "notApplicableReason": reason,
    }


def _facet(values):
    return [
        {"value": value, "label": label}
        for value, label in sorted(set(values), key=lambda item: item[1])
    ]


def _outcome_reasons(payload):
    for key in ("errors", "reasons"):
        value = payload.get(key) if isinstance(payload, dict) else None
        if isinstance(value, list):
            return [item for item in value if isinstance(item, dict)]
    return []


def _clock(value):
    if isinstance(value, time):
        return value.strftime("%H:%M")
    return str(value)[:5]


def _iso(value):
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _token(response):
    canonical = json.dumps(response, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()
