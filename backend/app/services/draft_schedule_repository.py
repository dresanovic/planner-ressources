from sqlalchemy import delete, select
from sqlalchemy.orm import Session, selectinload

from app.models.planning import (
    Cohort,
    Course,
    DraftSchedule,
    DraftSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    Room,
    Semester,
    StudyTypeTimeWindow,
)
from app.services.schedule_generation import (
    CoursePlan,
    GeneratedSession,
    PlanningPeriodPlan,
    SemesterPlan,
    TimeWindowPlan,
)

_UNSET = object()


class PlanningInputNotFoundError(ValueError):
    pass


class DraftSessionEditValidationError(ValueError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


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
    course = db.get(Course, course_id)
    if course is None:
        raise PlanningInputNotFoundError("Course not found.")
    cohort = db.get(Cohort, course.cohort_id)
    room = db.get(Room, course.room_id)
    if cohort is None or room is None:
        raise PlanningInputNotFoundError("Course planning input is incomplete.")
    return CoursePlan(
        id=course.id,
        total_units=course.total_units,
        min_session_units=course.min_session_units,
        max_session_units=course.max_session_units,
        lecturer_id=course.lecturer_id,
        cohort_id=course.cohort_id,
        room_id=course.room_id,
        study_type_id=course.study_type_id,
        cohort_size=cohort.student_count,
        room_capacity=room.capacity,
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
        draft = DraftSchedule(
            course_id=course_plan.id,
            semester_id=semester_id,
            selected_time_window_id=None,
            status="generated",
            revision=1,
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
            lecturer_id=course_plan.lecturer_id,
            cohort_id=course_plan.cohort_id,
            room_id=course_plan.room_id,
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
                selectinload(DraftSchedule.course).selectinload(Course.lecturer),
                selectinload(DraftSchedule.course).selectinload(Course.cohort),
                selectinload(DraftSchedule.course).selectinload(Course.room),
                selectinload(DraftSchedule.course).selectinload(Course.study_type),
            )
        )
        .scalars()
        .one_or_none()
    )


def update_draft_session(
    db: Session,
    session_id: int,
    *,
    date,
    start_time,
    end_time,
    room_id: int,
) -> DraftSchedule:
    session = db.get(DraftSession, session_id)
    if session is None:
        raise PlanningInputNotFoundError("Draft Session not found.")

    draft = db.get(DraftSchedule, session.draft_schedule_id)
    if draft is None:
        raise PlanningInputNotFoundError("Draft Schedule not found.")

    semester = db.get(Semester, draft.semester_id)
    if semester is None:
        raise PlanningInputNotFoundError("Semester not found.")

    if date < semester.start_date or date > semester.end_date:
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

    room = db.get(Room, room_id)
    if room is None:
        raise PlanningInputNotFoundError("Room not found.")
    cohort = db.get(Cohort, session.cohort_id)
    if cohort is None:
        raise PlanningInputNotFoundError("Cohort not found.")
    if room.capacity < cohort.student_count:
        raise DraftSessionEditValidationError(
            "INSUFFICIENT_ROOM_CAPACITY",
            f"Room capacity {room.capacity} is lower than Cohort size {cohort.student_count}.",
        )

    session.date = date
    session.start_time = start_time
    session.end_time = end_time
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
                selectinload(DraftSchedule.course).selectinload(Course.lecturer),
                selectinload(DraftSchedule.course).selectinload(Course.cohort),
                selectinload(DraftSchedule.course).selectinload(Course.room),
                selectinload(DraftSchedule.course).selectinload(Course.study_type),
            )
            .order_by(DraftSchedule.course_id)
        )
        .scalars()
        .all()
    )
