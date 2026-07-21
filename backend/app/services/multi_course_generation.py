from dataclasses import dataclass

from sqlalchemy import select, update
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    GenerationConstraintSet,
    Lecturer,
    ResourceUnavailabilityPeriod,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from app.schemas.multi_course_generation import (
    BatchGenerationResult,
    BatchGenerationSummary,
    BatchOperationKind,
    BatchPreparationResponse,
    CourseGenerationFailure,
    CourseGenerationOutcome,
    PreparedCourseInput,
    PreparedCourseSnapshot,
)
from app.services.draft_schedule_repository import (
    GenerationConstraints,
    replace_draft_schedule,
    save_generation_constraints,
)
from app.services.holiday_calendar import holiday_snapshot
from app.services.schedule_generation import (
    CoursePlan,
    PlanningPeriodPlan,
    SemesterPlan,
    ResourceCandidatePlan,
    TimeWindowPlan,
    generate_schedule,
)


class SemesterNotFoundError(ValueError):
    pass


@dataclass(frozen=True)
class LoadedBatchInput:
    course: Course
    plan: CoursePlan
    constraints: GenerationConstraints
    draft: DraftSchedule | None


def prepare_batch(
    db: Session,
    semester_id: int,
    operation_kind: BatchOperationKind,
    course_ids: list[int],
    schedule_revision_id: int | None = None,
) -> BatchPreparationResponse:
    semester, courses, drafts, _, default_windows = _bulk_load(db, semester_id, course_ids)
    active_window_types = {window.study_type_id for window in default_windows}
    by_id = {course.id: course for course in courses}
    drafts_by_course = {draft.course_id: draft for draft in drafts}
    snapshots: list[PreparedCourseSnapshot] = []
    replacements: list[int] = []
    for course_id in course_ids:
        course = by_id.get(course_id)
        draft = drafts_by_course.get(course_id)
        reasons = _eligibility_reasons(course, semester, active_window_types) if course is not None else ["COURSE_NOT_FOUND"]
        replacement = course is not None and draft is not None
        if replacement:
            replacements.append(course_id)
        snapshots.append(
            PreparedCourseSnapshot(
                courseId=course_id,
                courseName=course.name if course else None,
                available=course is not None and not reasons,
                draftScheduleId=draft.id if draft else None,
                draftRevision=draft.revision if draft else None,
                replacementRequired=replacement,
            )
        )
    return BatchPreparationResponse(
        semesterId=semester.id,
        scheduleRevisionId=schedule_revision_id,
        operationKind=operation_kind,
        courses=snapshots,
        replacementCourseIds=replacements,
    )


def generate_batch(
    db: Session,
    semester_id: int,
    operation_kind: BatchOperationKind,
    prepared_courses: list[PreparedCourseInput],
) -> BatchGenerationResult:
    course_ids = [item.course_id for item in prepared_courses]
    semester, courses, drafts, saved_sets, default_windows = _bulk_load(
        db, semester_id, course_ids
    )
    semester_plan = SemesterPlan(
        id=semester.id, start_date=semester.start_date, end_date=semester.end_date
    )
    courses_by_id = {course.id: course for course in courses}
    drafts_by_course = {draft.course_id: draft for draft in drafts}
    saved_by_course = {item.course_id: item for item in saved_sets}
    windows_by_study_type: dict[int, list[StudyTypeTimeWindow]] = {}
    for window in default_windows:
        windows_by_study_type.setdefault(window.study_type_id, []).append(window)
    active_window_types = set(windows_by_study_type)
    initial_holidays = holiday_snapshot(db, semester.start_date, semester.end_date)

    outcomes: list[CourseGenerationOutcome] = []
    candidates: list[tuple[PreparedCourseInput, LoadedBatchInput, object]] = []
    for prepared in prepared_courses:
        course = courses_by_id.get(prepared.course_id)
        if course is None:
            outcomes.append(_failure(prepared.course_id, None, "COURSE_NOT_FOUND", "Course is not available in the planner."))
            continue
        eligibility = _eligibility_reasons(course, semester, active_window_types)
        if eligibility:
            code = eligibility[0]
            if code == "NO_USABLE_ELIGIBLE_ROOM" and any(link.room.is_active for link in course.eligible_rooms):
                code = "INSUFFICIENT_ROOM_CAPACITY"
            outcomes.append(_failure(course.id, course.name, code, "Course academic data is not eligible for this Semester."))
            continue
        if course.cohort is None:
            outcomes.append(_failure(course.id, course.name, "PLANNING_INPUT_INCOMPLETE", "Course planning input is incomplete."))
            continue
        plan = _course_to_plan(course)
        constraints = _active_constraints(
            plan,
            semester_plan,
            saved_by_course.get(course.id),
            windows_by_study_type.get(course.study_type_id, []),
        )
        generation = generate_schedule(
            course=plan,
            semester=semester_plan,
            planning_period=constraints.planning_period,
            time_windows=constraints.allowed_windows,
            holidays=initial_holidays.by_date,
        )
        if not generation.ok:
            outcomes.append(
                CourseGenerationOutcome(
                    courseId=course.id,
                    courseName=course.name,
                    status="failed",
                    draftScheduleId=None,
                    draftRevision=None,
                    errors=[
                        CourseGenerationFailure(
                            code=e.code.value,
                            message=e.message,
                            holidayDate=e.holiday_date,
                            holidayName=e.holiday_name,
                        )
                        for e in generation.errors
                    ],
                )
            )
            continue
        candidates.append(
            (
                prepared,
                LoadedBatchInput(
                    course=course,
                    plan=plan,
                    constraints=constraints,
                    draft=drafts_by_course.get(course.id),
                ),
                generation,
            )
        )

    candidate_outcomes: dict[int, CourseGenerationOutcome] = {}
    _, current_courses, current_drafts, current_saved_sets, current_default_windows = _bulk_load(
        db, semester_id, course_ids
    )
    current_courses_by_id = {course.id: course for course in current_courses}
    current_drafts_by_course = {draft.course_id: draft for draft in current_drafts}
    current_saved_by_course = {item.course_id: item for item in current_saved_sets}
    current_windows_by_study_type: dict[int, list[StudyTypeTimeWindow]] = {}
    for window in current_default_windows:
        current_windows_by_study_type.setdefault(window.study_type_id, []).append(window)
    if candidates:
        # SQLite defers its physical outer transaction until the first write. Establish it
        # before SAVEPOINT so releasing a course savepoint cannot commit the whole attempt.
        db.execute(
            update(Semester)
            .where(Semester.id == semester_id)
            .values(id=Semester.id)
        )
    current_holidays = holiday_snapshot(db, semester.start_date, semester.end_date)
    if current_holidays.token != initial_holidays.token:
        outcomes = [
            _failure(
                outcome.course_id,
                outcome.course_name,
                "STALE_HOLIDAY_CALENDAR",
                "The holiday calendar changed during generation. Review the current calendar and generate again.",
            )
            if any(error.code == "INSTITUTION_HOLIDAY" for error in outcome.errors)
            else outcome
            for outcome in outcomes
        ]
    for prepared, loaded, generation in candidates:
        current_course = current_courses_by_id.get(prepared.course_id)
        current_draft = current_drafts_by_course.get(prepared.course_id)
        if not _draft_matches(prepared, current_draft):
            candidate_outcomes[prepared.course_id] = _failure(
                prepared.course_id,
                loaded.course.name,
                "STALE_DRAFT_SCHEDULE",
                "The Draft Schedule changed after preparation. Prepare this course again.",
            )
            continue
        current_constraints = (
            _active_constraints(
                loaded.plan,
                semester_plan,
                current_saved_by_course.get(prepared.course_id),
                current_windows_by_study_type.get(current_course.study_type_id, []) if current_course else [],
            )
            if current_course
            else None
        )
        if current_constraints is None or not _same_constraint_source(current_constraints, loaded.constraints):
            candidate_outcomes[prepared.course_id] = _failure(
                prepared.course_id,
                loaded.course.name,
                "STALE_GENERATION_CONSTRAINTS",
                "Generation constraints changed during the operation. Prepare this course again.",
            )
            continue
        conflicting_session = next(
            (session for session in generation.sessions if session.date in current_holidays.by_date),
            None,
        )
        if conflicting_session is not None:
            holiday = current_holidays.by_date[conflicting_session.date]
            candidate_outcomes[prepared.course_id] = _failure(
                prepared.course_id,
                loaded.course.name,
                "STALE_HOLIDAY_CALENDAR",
                f"{holiday.name} on {holiday.date.isoformat()} was added while generation was in progress. Generate again.",
            )
            continue
        with db.begin_nested():
            draft = replace_draft_schedule(
                db,
                course_plan=loaded.plan,
                semester_id=semester_id,
                generated_sessions=generation.sessions,
                existing_draft=current_draft,
                reload=False,
            )
            if not loaded.constraints.is_custom:
                save_generation_constraints(
                    db,
                    course_plan=loaded.plan,
                    semester_plan=semester_plan,
                    planning_period=loaded.constraints.planning_period,
                    allowed_windows=loaded.constraints.allowed_windows,
                    existing_set=current_saved_by_course.get(prepared.course_id),
                    reload=False,
                )
            candidate_outcomes[prepared.course_id] = CourseGenerationOutcome(
                courseId=prepared.course_id,
                courseName=loaded.course.name,
                status="succeeded",
                draftScheduleId=draft.id,
                draftRevision=draft.revision,
                errors=[],
            )

    existing_outcomes = {outcome.course_id: outcome for outcome in outcomes}
    ordered = [candidate_outcomes.get(item.course_id) or existing_outcomes[item.course_id] for item in prepared_courses]
    succeeded = sum(outcome.status == "succeeded" for outcome in ordered)
    return BatchGenerationResult(
        semesterId=semester_id,
        operationKind=operation_kind,
        summary=BatchGenerationSummary(
            total=len(ordered), succeeded=succeeded, failed=len(ordered) - succeeded
        ),
        outcomes=ordered,
    )


def _bulk_load(db: Session, semester_id: int, course_ids: list[int]):
    semester = db.execute(
        select(Semester)
        .where(Semester.id == semester_id)
        .execution_options(populate_existing=True)
    ).scalar_one_or_none()
    if semester is None:
        raise SemesterNotFoundError("Semester not found.")
    courses = list(
        db.execute(
            select(Course)
            .where(Course.id.in_(course_ids))
            .execution_options(populate_existing=True)
            .options(
                selectinload(Course.eligible_lecturers)
                .selectinload(CourseEligibleLecturer.lecturer)
                .selectinload(Lecturer.unavailability_periods)
                .selectinload(ResourceUnavailabilityPeriod.weekdays),
                selectinload(Course.cohort),
                selectinload(Course.eligible_rooms)
                .selectinload(CourseEligibleRoom.room)
                .selectinload(Room.unavailability_periods)
                .selectinload(ResourceUnavailabilityPeriod.weekdays),
                selectinload(Course.study_type),
            )
        ).scalars().all()
    )
    drafts = list(
        db.execute(
            select(DraftSchedule).where(
                DraftSchedule.semester_id == semester_id,
                DraftSchedule.course_id.in_(course_ids),
            ).execution_options(populate_existing=True)
        ).scalars().all()
    )
    saved_sets = list(
        db.execute(
            select(GenerationConstraintSet)
            .where(
                GenerationConstraintSet.semester_id == semester_id,
                GenerationConstraintSet.course_id.in_(course_ids),
            )
            .options(selectinload(GenerationConstraintSet.windows))
            .execution_options(populate_existing=True)
        ).scalars().all()
    )
    study_type_ids = {course.study_type_id for course in courses}
    default_windows = list(
        db.execute(
            select(StudyTypeTimeWindow)
            .where(StudyTypeTimeWindow.study_type_id.in_(study_type_ids), StudyTypeTimeWindow.is_active.is_(True))
            .order_by(StudyTypeTimeWindow.sort_order, StudyTypeTimeWindow.weekday)
            .execution_options(populate_existing=True)
        ).scalars().all()
    ) if study_type_ids else []
    return semester, courses, drafts, saved_sets, default_windows


def _course_to_plan(course: Course) -> CoursePlan:
    return CoursePlan(
        id=course.id,
        total_units=course.total_units,
        min_session_units=course.min_session_units,
        max_session_units=course.max_session_units,
        lecturer_id=course.lecturer_id or 0,
        cohort_id=course.cohort_id,
        room_id=course.room_id or 0,
        study_type_id=course.study_type_id,
        cohort_size=course.cohort.student_count,
        room_capacity=course.room.capacity if course.room is not None else 0,
        lecturer_candidates=tuple(
            ResourceCandidatePlan(
                id=link.lecturer.id,
                normalized_code=link.lecturer.normalized_reference_code,
                active=link.lecturer.is_active,
                unavailable_periods=tuple(link.lecturer.unavailability_periods),
            )
            for link in course.eligible_lecturers
        ),
        room_candidates=tuple(
            ResourceCandidatePlan(
                id=link.room.id,
                normalized_code=link.room.normalized_reference_code,
                active=link.room.is_active,
                capacity=link.room.capacity,
                unavailable_periods=tuple(link.room.unavailability_periods),
            )
            for link in course.eligible_rooms
        ),
    )


def _eligibility_reasons(course: Course, semester: Semester, active_window_types: set[int]) -> list[str]:
    reasons = []
    if not course.is_active: reasons.append("RECORD_INACTIVE")
    if course.current_semester_id is None: reasons.append("SEMESTER_ASSIGNMENT_REQUIRED")
    elif course.current_semester_id != semester.id: reasons.append("COURSE_SEMESTER_MISMATCH")
    if not semester.is_active: reasons.append("SEMESTER_INACTIVE")
    if not course.cohort.is_active: reasons.append("COHORT_INACTIVE")
    if not course.study_type.is_active: reasons.append("STUDY_TYPE_INACTIVE")
    if course.study_type_id not in active_window_types: reasons.append("MISSING_ACTIVE_TIME_WINDOW")
    if not any(link.lecturer.is_active for link in course.eligible_lecturers): reasons.append("NO_ACTIVE_ELIGIBLE_LECTURER")
    if not any(link.room.is_active and link.room.capacity >= course.cohort.student_count for link in course.eligible_rooms): reasons.append("NO_USABLE_ELIGIBLE_ROOM")
    return reasons


def _active_constraints(plan, semester, saved, defaults) -> GenerationConstraints:
    if saved is not None:
        return GenerationConstraints(
            course_id=plan.id,
            semester_id=semester.id,
            planning_period=PlanningPeriodPlan(saved.planning_start_date, saved.planning_end_date),
            allowed_windows=[
                TimeWindowPlan(
                    id=w.source_time_window_id,
                    weekday=w.weekday,
                    start_time=w.start_time,
                    end_time=w.end_time,
                    sort_order=w.sort_order,
                    constraint_window_index=index,
                )
                for index, w in enumerate(saved.windows)
            ],
            is_custom=True,
            constraint_set_id=saved.id,
            revision=saved.revision,
        )
    return GenerationConstraints(
        course_id=plan.id,
        semester_id=semester.id,
        planning_period=PlanningPeriodPlan(semester.start_date, semester.end_date),
        allowed_windows=[
            TimeWindowPlan(
                id=w.id,
                weekday=w.weekday,
                start_time=w.start_time,
                end_time=w.end_time,
                sort_order=w.sort_order,
                constraint_window_index=index,
            )
            for index, w in enumerate(defaults)
        ],
        is_custom=False,
    )


def _draft_matches(prepared: PreparedCourseInput, current: DraftSchedule | None) -> bool:
    if current is None:
        return prepared.expected_draft_schedule_id is None and prepared.expected_draft_revision is None
    return (
        prepared.expected_draft_schedule_id == current.id
        and prepared.expected_draft_revision == current.revision
    )


def _same_constraint_source(current, snapshot) -> bool:
    if snapshot.constraint_set_id is not None:
        return current.constraint_set_id == snapshot.constraint_set_id and current.revision == snapshot.revision
    return current.constraint_set_id is None and _constraint_values(current) == _constraint_values(snapshot)


def _constraint_values(value: GenerationConstraints):
    return (
        value.planning_period.start_date,
        value.planning_period.end_date,
        tuple((w.id, w.weekday, w.start_time, w.end_time, w.sort_order) for w in value.allowed_windows),
    )


def _failure(course_id, course_name, code, message):
    return CourseGenerationOutcome(
        courseId=course_id,
        courseName=course_name,
        status="failed",
        draftScheduleId=None,
        draftRevision=None,
        errors=[CourseGenerationFailure(code=code, message=message)],
    )
