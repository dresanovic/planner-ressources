from datetime import date, datetime, time

from sqlalchemy import Date, DateTime, ForeignKey, Integer, String, Time, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Lecturer(Base):
    __tablename__ = "lecturers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)


class Cohort(Base):
    __tablename__ = "cohorts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    student_count: Mapped[int] = mapped_column(Integer, nullable=False)


class Room(Base):
    __tablename__ = "rooms"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)


class StudyType(Base):
    __tablename__ = "study_types"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    time_windows: Mapped[list["StudyTypeTimeWindow"]] = relationship(
        back_populates="study_type",
        cascade="all, delete-orphan",
        order_by="StudyTypeTimeWindow.sort_order",
    )


class StudyTypeTimeWindow(Base):
    __tablename__ = "study_type_time_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    study_type_id: Mapped[int] = mapped_column(ForeignKey("study_types.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    study_type: Mapped[StudyType] = relationship(back_populates="time_windows")


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    total_units: Mapped[int] = mapped_column(Integer, nullable=False)
    min_session_units: Mapped[int] = mapped_column(Integer, nullable=False)
    max_session_units: Mapped[int] = mapped_column(Integer, nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), nullable=False)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    study_type_id: Mapped[int] = mapped_column(ForeignKey("study_types.id"), nullable=False)

    lecturer: Mapped[Lecturer] = relationship()
    cohort: Mapped[Cohort] = relationship()
    room: Mapped[Room] = relationship()
    study_type: Mapped[StudyType] = relationship()


class GenerationConstraintSet(Base):
    __tablename__ = "generation_constraint_sets"
    __table_args__ = (UniqueConstraint("course_id", "semester_id", name="uq_generation_constraint_course_semester"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    planning_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    planning_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    course: Mapped[Course] = relationship()
    semester: Mapped[Semester] = relationship()
    windows: Mapped[list["GenerationConstraintWindow"]] = relationship(
        back_populates="constraint_set",
        cascade="all, delete-orphan",
        order_by="GenerationConstraintWindow.sort_order",
    )


class GenerationConstraintWindow(Base):
    __tablename__ = "generation_constraint_windows"

    id: Mapped[int] = mapped_column(primary_key=True)
    constraint_set_id: Mapped[int] = mapped_column(
        ForeignKey("generation_constraint_sets.id"), nullable=False
    )
    source_time_window_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_type_time_windows.id"), nullable=True
    )
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    constraint_set: Mapped[GenerationConstraintSet] = relationship(back_populates="windows")


class DraftSchedule(Base):
    __tablename__ = "draft_schedules"
    __table_args__ = (
        UniqueConstraint("course_id", "semester_id", name="uq_draft_schedule_course_semester"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    selected_time_window_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_type_time_windows.id"), nullable=True
    )
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="generated")
    created_at: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    course: Mapped[Course] = relationship()
    sessions: Mapped[list["DraftSession"]] = relationship(
        back_populates="draft_schedule",
        cascade="all, delete-orphan",
        order_by=lambda: (DraftSession.date, DraftSession.start_time),
    )


class DraftSession(Base):
    __tablename__ = "draft_sessions"
    __table_args__ = (UniqueConstraint("draft_schedule_id", "date", name="uq_draft_session_day"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    draft_schedule_id: Mapped[int] = mapped_column(
        ForeignKey("draft_schedules.id"), nullable=False
    )
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), nullable=False)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    units: Mapped[int] = mapped_column(Integer, nullable=False)
    time_window_id: Mapped[int | None] = mapped_column(
        ForeignKey("study_type_time_windows.id"), nullable=True
    )
    constraint_window_index: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    draft_schedule: Mapped[DraftSchedule] = relationship(back_populates="sessions")
