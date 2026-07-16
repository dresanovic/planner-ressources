from sqlalchemy import delete, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Cohort,
    Course,
    CourseEligibleLecturer,
    CourseEligibleRoom,
    DraftSchedule,
    DraftSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Lecturer,
    Room,
    ResourceUnavailabilityPeriod,
    Semester,
    StudyTypeTimeWindow,
)
from app.services.schedule_generation import (
    CoursePlan,
    GeneratedSession,
    PlanningPeriodPlan,
    SemesterPlan,
    ResourceCandidatePlan,
    TimeWindowPlan,
)
from app.services.resource_rules import resource_is_unavailable

_UNSET = object()


class PlanningInputNotFoundError(ValueError):
    pass


class DraftSessionEditValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class ManualSessionValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class StaleDraftError(ValueError):
    def __init__(self, current_revision: int | None) -> None:
        super().__init__("The confirmed Draft Schedule changed. Refresh and confirm again.")
        self.current_revision = current_revision


class GenerationConstraints:
    def __init__(
        self,
        course_id: int,
        semester_id: int,
        planning_period: PlanningPeriodPlan,
        allowed_windows: list[TimeWindowPlan],
        is_custom: bool,
        constraint_set_id: int | None = None,
        revision: int | None = None,
    ) -> None:
        self.course_id = course_id
        self.semester_id = semester_id
        self.planning_period = planning_period
        self.allowed_windows = allowed_windows
        self.is_custom = is_custom
        self.constraint_set_id = constraint_set_id
        self.revision = revision


def load_course_plan(db: Session, course_id: int) -> CoursePlan:
    course = (
        db.execute(
            select(Course)
            .where(Course.id == course_id)
            .options(
                selectinload(Course.cohort),
                selectinload(Course.eligible_lecturers)
                .selectinload(CourseEligibleLecturer.lecturer)
                .selectinload(Lecturer.unavailability_periods)
                .selectinload(ResourceUnavailabilityPeriod.weekdays),
                selectinload(Course.eligible_rooms)
                .selectinload(CourseEligibleRoom.room)
                .selectinload(Room.unavailability_periods)
                .selectinload(ResourceUnavailabilityPeriod.weekdays),
            )
        )
        .scalars()
        .one_or_none()
    )
    if course is None:
        raise PlanningInputNotFoundError("Course not found.")
    cohort = course.cohort
    room = course.room
    if cohort is None:
        raise PlanningInputNotFoundError("Course planning input is incomplete.")
    return CoursePlan(
        id=course.id,
        total_units=course.total_units,
        min_session_units=course.min_session_units,
        max_session_units=course.max_session_units,
        lecturer_id=course.lecturer_id or 0,
        cohort_id=course.cohort_id,
        room_id=course.room_id or 0,
        study_type_id=course.study_type_id,
        cohort_size=cohort.student_count,
        room_capacity=room.capacity if room is not None else 0,
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


def load_semester_plan(db: Session, semester_id: int) -> SemesterPlan:
    semester = db.get(Semester, semester_id)
    if semester is None:
        raise PlanningInputNotFoundError("Semester not found.")
    return SemesterPlan(id=semester.id, start_date=semester.start_date, end_date=semester.end_date)


def load_time_windows(db: Session, study_type_id: int) -> list[TimeWindowPlan]:
    rows = (
        db.execute(
            select(StudyTypeTimeWindow)
            .where(StudyTypeTimeWindow.study_type_id == study_type_id)
            .order_by(StudyTypeTimeWindow.sort_order, StudyTypeTimeWindow.weekday)
        )
        .scalars()
        .all()
    )
    return [
        TimeWindowPlan(
            id=row.id,
            weekday=row.weekday,
            start_time=row.start_time,
            end_time=row.end_time,
            sort_order=row.sort_order,
            constraint_window_index=index,
        )
        for index, row in enumerate(rows)
    ]


def load_generation_constraints(
    db: Session,
    course_plan: CoursePlan,
    semester_plan: SemesterPlan,
) -> GenerationConstraints:
    saved = (
        db.execute(
            select(GenerationConstraintSet)
            .where(
                GenerationConstraintSet.course_id == course_plan.id,
                GenerationConstraintSet.semester_id == semester_plan.id,
            )
            .options(selectinload(GenerationConstraintSet.windows))
        )
        .scalars()
        .one_or_none()
    )
    if saved is not None:
        return GenerationConstraints(
            course_id=course_plan.id,
            semester_id=semester_plan.id,
            planning_period=PlanningPeriodPlan(
                start_date=saved.planning_start_date,
                end_date=saved.planning_end_date,
            ),
            allowed_windows=[
                TimeWindowPlan(
                    id=window.source_time_window_id,
                    weekday=window.weekday,
                    start_time=window.start_time,
                    end_time=window.end_time,
                    sort_order=window.sort_order,
                    constraint_window_index=index,
                )
                for index, window in enumerate(saved.windows)
            ],
            is_custom=True,
            constraint_set_id=saved.id,
            revision=saved.revision,
        )

    return GenerationConstraints(
        course_id=course_plan.id,
        semester_id=semester_plan.id,
        planning_period=PlanningPeriodPlan(
            start_date=semester_plan.start_date,
            end_date=semester_plan.end_date,
        ),
        allowed_windows=load_time_windows(db, course_plan.study_type_id),
        is_custom=False,
    )


def save_generation_constraints(
    db: Session,
    course_plan: CoursePlan,
    semester_plan: SemesterPlan,
    planning_period: PlanningPeriodPlan,
    allowed_windows: list[TimeWindowPlan],
    *,
    existing_set=_UNSET,
    reload: bool = True,
) -> GenerationConstraints:
    existing = existing_set
    if existing is _UNSET:
        existing = (
            db.execute(
                select(GenerationConstraintSet)
                .where(
                    GenerationConstraintSet.course_id == course_plan.id,
                    GenerationConstraintSet.semester_id == semester_plan.id,
                )
                .options(selectinload(GenerationConstraintSet.windows))
            )
            .scalars()
            .one_or_none()
        )
    new_windows = [
        GenerationConstraintWindow(
            source_time_window_id=window.id,
            weekday=window.weekday,
            start_time=window.start_time,
            end_time=window.end_time,
            sort_order=index,
        )
        for index, window in enumerate(allowed_windows)
    ]
    if existing is None:
        constraint_set = GenerationConstraintSet(
            course_id=course_plan.id,
            semester_id=semester_plan.id,
            planning_start_date=planning_period.start_date,
            planning_end_date=planning_period.end_date,
            revision=1,
            windows=new_windows,
        )
        db.add(constraint_set)
    elif not _constraints_match(existing, planning_period, allowed_windows):
        existing.planning_start_date = planning_period.start_date
        existing.planning_end_date = planning_period.end_date
        existing.revision += 1
        existing.windows = new_windows
    db.flush()
    if reload:
        return load_generation_constraints(db, course_plan, semester_plan)
    active = constraint_set if existing is None else existing
    return GenerationConstraints(
        course_id=course_plan.id,
        semester_id=semester_plan.id,
        planning_period=planning_period,
        allowed_windows=allowed_windows,
        is_custom=True,
        constraint_set_id=active.id,
        revision=active.revision,
    )


def clear_generation_constraints(db: Session, course_id: int, semester_id: int) -> None:
    existing = (
        db.execute(
            select(GenerationConstraintSet).where(
                GenerationConstraintSet.course_id == course_id,
                GenerationConstraintSet.semester_id == semester_id,
            )
        )
        .scalars()
        .one_or_none()
    )
    if existing is not None:
        db.delete(existing)
        db.flush()


def replace_draft_schedule(
    db: Session,
    course_plan: CoursePlan,
    semester_id: int,
    generated_sessions: list[GeneratedSession],
    *,
    existing_draft=_UNSET,
    reload: bool = True,
) -> DraftSchedule:
    draft = existing_draft
    if draft is _UNSET:
        draft = get_draft_schedule(db, course_plan.id, semester_id)
    if draft is None:
        course = db.get(Course, course_plan.id)
        semester = db.get(Semester, semester_id)
        if course is None or semester is None:
            raise PlanningInputNotFoundError("Course or Semester not found.")
        cohort = db.get(Cohort, course.cohort_id)
        if cohort is None:
            raise PlanningInputNotFoundError("Course planning input is incomplete.")
        draft = DraftSchedule(
            course_id=course_plan.id,
            semester_id=semester_id,
            selected_time_window_id=None,
            status="generated",
            revision=1,
            course_name_snapshot=course.name,
            course_total_units_snapshot=course.total_units,
            course_min_session_units_snapshot=course.min_session_units,
            course_max_session_units_snapshot=course.max_session_units,
            cohort_id_snapshot=cohort.id,
            cohort_name_snapshot=cohort.name,
            cohort_size_snapshot=cohort.student_count,
            study_type_id_snapshot=course.study_type_id,
            study_type_name_snapshot=course.study_type.name,
            semester_name_snapshot=semester.name,
            semester_start_date_snapshot=semester.start_date,
            semester_end_date_snapshot=semester.end_date,
        )
        db.add(draft)
    else:
        draft.revision += 1
        db.execute(delete(DraftSession).where(DraftSession.draft_schedule_id == draft.id))
        db.flush()
        db.expire(draft, ["sessions"])
    draft.sessions = [
        DraftSession(
            course_id=course_plan.id,
            lecturer_id=session.lecturer_id if session.lecturer_id is not None else course_plan.lecturer_id,
            cohort_id=course_plan.cohort_id,
            room_id=session.room_id if session.room_id is not None else course_plan.room_id,
            date=session.date,
            start_time=session.start_time,
            end_time=session.end_time,
            units=session.units,
            time_window_id=session.time_window_id,
            constraint_window_index=session.constraint_window_index,
        )
        for session in generated_sessions
    ]
    db.flush()
    if reload:
        return get_draft_schedule(db, course_plan.id, semester_id) or draft
    return draft


def get_draft_schedule(db: Session, course_id: int, semester_id: int) -> DraftSchedule | None:
    return (
        db.execute(
            select(DraftSchedule)
            .where(
                DraftSchedule.course_id == course_id,
                DraftSchedule.semester_id == semester_id,
            )
            .options(
                selectinload(DraftSchedule.sessions),
                selectinload(DraftSchedule.course).selectinload(Course.eligible_lecturers).selectinload(CourseEligibleLecturer.lecturer),
                selectinload(DraftSchedule.course).selectinload(Course.cohort),
                selectinload(DraftSchedule.course).selectinload(Course.eligible_rooms).selectinload(CourseEligibleRoom.room),
                selectinload(DraftSchedule.course).selectinload(Course.study_type),
            )
        )
        .scalars()
        .one_or_none()
    )


def course_semester_progress(db: Session, course_id: int, semester_id: int) -> tuple[int, int, int]:
    course = db.get(Course, course_id)
    if course is None:
        raise PlanningInputNotFoundError("Course not found.")
    if db.get(Semester, semester_id) is None:
        raise PlanningInputNotFoundError("Semester not found.")
    draft = get_draft_schedule(db, course_id, semester_id)
    scheduled = sum(session.units for session in draft.sessions) if draft is not None else 0
    return course.total_units, scheduled, max(course.total_units - scheduled, 0)


def create_manual_draft_session(
    db: Session,
    course_id: int,
    semester_id: int,
    *,
    session_date,
    start_time,
    end_time,
    units,
    room_id: int,
) -> DraftSchedule:
    for _attempt in range(3):
        course = (
            db.execute(
                select(Course)
                .where(Course.id == course_id)
                .options(
                    selectinload(Course.cohort),
                    selectinload(Course.study_type),
                    selectinload(Course.eligible_lecturers).selectinload(CourseEligibleLecturer.lecturer),
                )
            )
            .scalars()
            .one_or_none()
        )
        semester = db.get(Semester, semester_id)
        room = db.get(Room, room_id)
        if course is None:
            raise PlanningInputNotFoundError("Course not found.")
        if semester is None:
            raise PlanningInputNotFoundError("Semester not found.")
        if course.cohort is None or course.lecturer is None or course.study_type is None:
            raise PlanningInputNotFoundError("Course planning input is incomplete.")
        if room is None:
            raise PlanningInputNotFoundError("Room not found.")

        draft = get_draft_schedule(db, course_id, semester_id)
        scheduled = sum(item.units for item in draft.sessions) if draft is not None else 0
        remaining = max(course.total_units - scheduled, 0)
        _validate_manual_session(
            draft=draft,
            semester=semester,
            room=room,
            cohort=course.cohort,
            session_date=session_date,
            start_time=start_time,
            end_time=end_time,
            units=units,
            remaining_units=remaining,
        )

        if draft is None:
            candidate = DraftSchedule(
                course_id=course.id,
                semester_id=semester.id,
                selected_time_window_id=None,
                status="draft",
                revision=1,
                course_name_snapshot=course.name,
                course_total_units_snapshot=course.total_units,
                course_min_session_units_snapshot=course.min_session_units,
                course_max_session_units_snapshot=course.max_session_units,
                cohort_id_snapshot=course.cohort.id,
                cohort_name_snapshot=course.cohort.name,
                cohort_size_snapshot=course.cohort.student_count,
                study_type_id_snapshot=course.study_type.id,
                study_type_name_snapshot=course.study_type.name,
                semester_name_snapshot=semester.name,
                semester_start_date_snapshot=semester.start_date,
                semester_end_date_snapshot=semester.end_date,
            )
            candidate.sessions.append(
                DraftSession(
                    course_id=course.id,
                    lecturer_id=course.lecturer.id,
                    cohort_id=course.cohort.id,
                    room_id=room.id,
                    date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                    units=int(units),
                    time_window_id=None,
                    constraint_window_index=0,
                )
            )
            try:
                with db.begin_nested():
                    db.add(candidate)
                    db.flush()
                draft = candidate
            except IntegrityError:
                db.expire_all()
                continue
        else:
            expected_revision = draft.revision
            claimed = db.execute(
                update(DraftSchedule)
                .where(DraftSchedule.id == draft.id, DraftSchedule.revision == expected_revision)
                .values(revision=expected_revision + 1),
                execution_options={"synchronize_session": False},
            )
            if claimed.rowcount != 1:
                db.expire_all()
                continue
            draft.revision = expected_revision + 1
            db.add(
                DraftSession(
                    draft_schedule=draft,
                    course_id=course.id,
                    lecturer_id=course.lecturer.id,
                    cohort_id=course.cohort.id,
                    room_id=room.id,
                    date=session_date,
                    start_time=start_time,
                    end_time=end_time,
                    units=int(units),
                    time_window_id=None,
                    constraint_window_index=0,
                )
            )
            db.flush()
        db.expire(draft, ["sessions"])
        saved = get_draft_schedule(db, course_id, semester_id)
        if saved is None:
            raise PlanningInputNotFoundError("Draft Schedule not found after manual creation.")
        return saved
    raise RuntimeError("Could not serialize manual Draft Session creation after concurrent updates.")


def _validate_manual_session(
    *, draft, semester, room, cohort, session_date, start_time, end_time, units, remaining_units: int
) -> None:
    if session_date < semester.start_date or session_date > semester.end_date:
        raise ManualSessionValidationError("INVALID_SESSION_DATE", "Session date must be inside the selected semester.")
    if end_time <= start_time:
        raise ManualSessionValidationError("INVALID_SESSION_TIME_RANGE", "Session end time must be later than start time.")
    if isinstance(units, bool) or not isinstance(units, (int, float)):
        raise ManualSessionValidationError("INVALID_SESSION_UNITS", "Units must be a positive whole number.")
    if units <= 0 or (isinstance(units, float) and not units.is_integer()):
        raise ManualSessionValidationError("INVALID_SESSION_UNITS", "Units must be a positive whole number.")
    if int(units) > remaining_units:
        raise ManualSessionValidationError("UNITS_EXCEED_REMAINING", f"Only {remaining_units} course units remain.")
    if draft is not None and any(item.date == session_date for item in draft.sessions):
        raise ManualSessionValidationError("DUPLICATE_SESSION_DATE", "Another Draft Session in this course draft already uses that date.")
    if room.capacity < cohort.student_count:
        raise ManualSessionValidationError(
            "INSUFFICIENT_ROOM_CAPACITY",
            f"Room capacity {room.capacity} is lower than Cohort size {cohort.student_count}.",
        )


def delete_draft_session(
    db: Session,
    session_id: int,
    *,
    expected_draft_schedule_id: int,
    expected_revision: int,
) -> tuple[DraftSchedule | None, int, int]:
    expected_draft = db.get(DraftSchedule, expected_draft_schedule_id)
    session = db.get(DraftSession, session_id)
    if expected_draft is None:
        raise StaleDraftError(None)
    if session is None or session.draft_schedule_id != expected_draft_schedule_id:
        raise StaleDraftError(expected_draft.revision)

    draft = get_draft_schedule(db, session.course_id, expected_draft.semester_id)
    if draft is None or draft.id != expected_draft_schedule_id:
        raise StaleDraftError(None)
    _claim_draft_revision(db, draft, expected_revision)
    course_id = draft.course_id
    semester_id = draft.semester_id
    if len(draft.sessions) == 1:
        db.delete(draft)
        db.flush()
        return None, course_id, semester_id

    db.delete(session)
    db.flush()
    db.expire(draft, ["sessions"])
    surviving = get_draft_schedule(db, course_id, semester_id)
    if surviving is None:
        raise PlanningInputNotFoundError("Draft Schedule not found after session deletion.")
    return surviving, course_id, semester_id


def clear_course_draft(
    db: Session,
    course_id: int,
    semester_id: int,
    *,
    expected_draft_schedule_id: int,
    expected_revision: int,
) -> tuple[int, int]:
    draft = get_draft_schedule(db, course_id, semester_id)
    if draft is None or draft.id != expected_draft_schedule_id:
        raise StaleDraftError(draft.revision if draft is not None else None)
    _claim_draft_revision(db, draft, expected_revision)
    db.delete(draft)
    db.flush()
    return course_id, semester_id


def _claim_draft_revision(db: Session, draft: DraftSchedule, expected_revision: int) -> None:
    claimed = db.execute(
        update(DraftSchedule)
        .where(DraftSchedule.id == draft.id, DraftSchedule.revision == expected_revision)
        .values(revision=expected_revision + 1),
        execution_options={"synchronize_session": False},
    )
    if claimed.rowcount != 1:
        db.expire_all()
        current = db.get(DraftSchedule, draft.id)
        raise StaleDraftError(current.revision if current is not None else None)
    draft.revision = expected_revision + 1


def update_draft_session(
    db: Session,
    session_id: int,
    *,
    date,
    start_time,
    end_time,
    lecturer_id: int | None = None,
    room_id: int,
) -> DraftSchedule:
    session = db.get(DraftSession, session_id)
    if session is None:
        raise PlanningInputNotFoundError("Draft Session not found.")

    draft = db.get(DraftSchedule, session.draft_schedule_id)
    if draft is None:
        raise PlanningInputNotFoundError("Draft Schedule not found.")

    if date < draft.semester_start_date_snapshot or date > draft.semester_end_date_snapshot:
        raise DraftSessionEditValidationError(
            "INVALID_SESSION_DATE",
            "Session date must be inside the selected semester.",
        )
    if end_time <= start_time:
        raise DraftSessionEditValidationError(
            "INVALID_SESSION_TIME_RANGE",
            "Session end time must be later than start time.",
        )

    duplicate = (
        db.execute(
            select(DraftSession).where(
                DraftSession.draft_schedule_id == session.draft_schedule_id,
                DraftSession.date == date,
                DraftSession.id != session.id,
            )
        )
        .scalars()
        .first()
    )
    if duplicate is not None:
        raise DraftSessionEditValidationError(
            "DUPLICATE_SESSION_DATE",
            "Another Draft Session in this draft schedule already uses that date.",
        )

    requested_lecturer_id = session.lecturer_id if lecturer_id is None else lecturer_id
    if requested_lecturer_id != session.lecturer_id:
        lecturer_link = db.get(CourseEligibleLecturer, (session.course_id, requested_lecturer_id))
        lecturer = db.get(Lecturer, requested_lecturer_id)
        if lecturer_link is None or lecturer is None or not lecturer.is_active:
            raise DraftSessionEditValidationError(
                "LECTURER_INELIGIBLE",
                "The selected Lecturer is inactive or outside the current Course eligibility set.",
            )
        lecturer_periods = list(
            db.execute(
                select(ResourceUnavailabilityPeriod)
                .where(ResourceUnavailabilityPeriod.lecturer_id == requested_lecturer_id)
                .options(selectinload(ResourceUnavailabilityPeriod.weekdays))
            ).scalars()
        )
        if resource_is_unavailable(lecturer_periods, date, start_time, end_time):
            raise DraftSessionEditValidationError("LECTURER_UNAVAILABLE", "The selected Lecturer is unavailable during this session.")

    if room_id != session.room_id:
        room = db.get(Room, room_id)
        if room is None:
            raise PlanningInputNotFoundError("Room not found.")
        course = db.get(Course, session.course_id)
        cohort = db.get(Cohort, course.cohort_id) if course is not None else None
        if cohort is None:
            raise PlanningInputNotFoundError("Course planning input is incomplete.")
        room_link = db.get(CourseEligibleRoom, (session.course_id, room_id))
        if room_link is None or not room.is_active:
            raise DraftSessionEditValidationError(
                "ROOM_INELIGIBLE",
                "The selected Room is inactive or outside the current Course eligibility set.",
            )
        if room.capacity < cohort.student_count:
            raise DraftSessionEditValidationError(
                "INSUFFICIENT_ROOM_CAPACITY",
                f"Room capacity {room.capacity} is lower than Cohort size {cohort.student_count}.",
            )
        room_periods = list(
            db.execute(
                select(ResourceUnavailabilityPeriod)
                .where(ResourceUnavailabilityPeriod.room_id == room_id)
                .options(selectinload(ResourceUnavailabilityPeriod.weekdays))
            ).scalars()
        )
        if resource_is_unavailable(room_periods, date, start_time, end_time):
            raise DraftSessionEditValidationError("ROOM_UNAVAILABLE", "The selected Room is unavailable during this session.")

    session.date = date
    session.start_time = start_time
    session.end_time = end_time
    session.lecturer_id = requested_lecturer_id
    session.room_id = room_id
    draft.revision += 1
    db.flush()
    db.expire(draft, ["sessions"])

    updated = get_draft_schedule(db, session.course_id, draft.semester_id)
    if updated is None:
        raise PlanningInputNotFoundError("Draft Schedule not found.")
    return updated


def _constraints_match(
    existing: GenerationConstraintSet,
    planning_period: PlanningPeriodPlan,
    allowed_windows: list[TimeWindowPlan],
) -> bool:
    if (
        existing.planning_start_date != planning_period.start_date
        or existing.planning_end_date != planning_period.end_date
        or len(existing.windows) != len(allowed_windows)
    ):
        return False
    return all(
        saved.source_time_window_id == incoming.id
        and saved.weekday == incoming.weekday
        and saved.start_time == incoming.start_time
        and saved.end_time == incoming.end_time
        and saved.sort_order == index
        for index, (saved, incoming) in enumerate(zip(existing.windows, allowed_windows))
    )


def list_draft_schedules_by_semester(db: Session, semester_id: int) -> list[DraftSchedule]:
    return list(
        db.execute(
            select(DraftSchedule)
            .where(DraftSchedule.semester_id == semester_id)
            .options(
                selectinload(DraftSchedule.sessions),
                selectinload(DraftSchedule.course).selectinload(Course.eligible_lecturers).selectinload(CourseEligibleLecturer.lecturer),
                selectinload(DraftSchedule.course).selectinload(Course.cohort),
                selectinload(DraftSchedule.course).selectinload(Course.eligible_rooms).selectinload(CourseEligibleRoom.room),
                selectinload(DraftSchedule.course).selectinload(Course.study_type),
            )
            .order_by(DraftSchedule.course_id)
        )
        .scalars()
        .all()
    )
