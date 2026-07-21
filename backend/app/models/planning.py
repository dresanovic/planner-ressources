from datetime import date, datetime, time, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Time,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class InstitutionHoliday(Base):
    __tablename__ = "institution_holidays"
    __table_args__ = (
        UniqueConstraint("date", name="uq_institution_holidays_date"),
        CheckConstraint("revision > 0", name="ck_institution_holidays_revision_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    date: Mapped[date] = mapped_column(Date, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}


class Lecturer(Base):
    __tablename__ = "lecturers"
    __table_args__ = (
        UniqueConstraint(
            "normalized_reference_code",
            name="uq_lecturers_normalized_reference_code",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    reference_code: Mapped[str] = mapped_column(
        String(100), nullable=False, default=lambda: f"AUTO-{uuid4().hex}"
    )
    normalized_reference_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=lambda context: context.get_current_parameters()["reference_code"].strip().casefold(),
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    eligible_courses: Mapped[list["CourseEligibleLecturer"]] = relationship(
        back_populates="lecturer",
        cascade="all, delete-orphan",
    )
    unavailability_periods: Mapped[list["ResourceUnavailabilityPeriod"]] = relationship(
        back_populates="lecturer",
        cascade="all, delete-orphan",
    )


class Cohort(Base):
    __tablename__ = "cohorts"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_cohorts_normalized_name"),
        UniqueConstraint("normalized_name_key", name="uq_cohorts_normalized_name_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    normalized_name_key: Mapped[str] = mapped_column(String(260), nullable=False, default=lambda: uuid4().hex)
    name_repair_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    student_count: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)


class Room(Base):
    __tablename__ = "rooms"
    __table_args__ = (
        UniqueConstraint(
            "normalized_reference_code",
            name="uq_rooms_normalized_reference_code",
        ),
        CheckConstraint("capacity > 0", name="ck_rooms_capacity_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    reference_code: Mapped[str] = mapped_column(
        String(100), nullable=False, default=lambda: f"AUTO-{uuid4().hex}"
    )
    normalized_reference_code: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        default=lambda context: context.get_current_parameters()["reference_code"].strip().casefold(),
    )
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    eligible_courses: Mapped[list["CourseEligibleRoom"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )
    unavailability_periods: Mapped[list["ResourceUnavailabilityPeriod"]] = relationship(
        back_populates="room",
        cascade="all, delete-orphan",
    )


class Semester(Base):
    __tablename__ = "semesters"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_semesters_normalized_name"),
        UniqueConstraint("normalized_name_key", name="uq_semesters_normalized_name_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    normalized_name_key: Mapped[str] = mapped_column(String(260), nullable=False, default=lambda: uuid4().hex)
    name_repair_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    start_date: Mapped[date] = mapped_column(Date, nullable=False)
    end_date: Mapped[date] = mapped_column(Date, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    schedule_revisions: Mapped[list["ScheduleRevision"]] = relationship(
        back_populates="semester",
        cascade="all, delete-orphan",
        order_by="ScheduleRevision.revision_number",
    )


class ScheduleRevision(Base):
    __tablename__ = "schedule_revisions"
    __table_args__ = (
        UniqueConstraint(
            "semester_id", "revision_number", name="uq_schedule_revision_number"
        ),
        CheckConstraint(
            "revision_number > 0", name="ck_schedule_revision_number_positive"
        ),
        CheckConstraint("row_version > 0", name="ck_schedule_revision_version_positive"),
        CheckConstraint(
            "state IN ('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_state",
        ),
        CheckConstraint(
            "(state IN ('draft', 'ready_for_review') AND published_at IS NULL) OR "
            "(state IN ('published', 'superseded') AND published_at IS NOT NULL "
            "AND snapshot_schema_version IS NOT NULL AND snapshot_document IS NOT NULL) OR "
            "(state = 'abandoned' AND published_at IS NULL "
            "AND snapshot_schema_version IS NOT NULL AND snapshot_document IS NOT NULL)",
            name="ck_schedule_revision_state_content",
        ),
        Index(
            "uq_schedule_revision_active_working",
            "semester_id",
            unique=True,
            sqlite_where=text("state IN ('draft', 'ready_for_review')"),
        ),
        Index(
            "uq_schedule_revision_current_publication",
            "semester_id",
            unique=True,
            sqlite_where=text("state = 'published'"),
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    state: Mapped[str] = mapped_column(String(30), nullable=False)
    origin_revision_id: Mapped[int | None] = mapped_column(
        ForeignKey("schedule_revisions.id"), nullable=True
    )
    row_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    snapshot_schema_version: Mapped[int | None] = mapped_column(Integer, nullable=True)
    snapshot_document: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    state_changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )
    published_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now, onupdate=utc_now
    )
    __mapper_args__ = {"version_id_col": row_version, "version_id_generator": False}

    semester: Mapped[Semester] = relationship(back_populates="schedule_revisions")
    origin_revision: Mapped["ScheduleRevision | None"] = relationship(
        remote_side="ScheduleRevision.id", back_populates="successor_revisions"
    )
    successor_revisions: Mapped[list["ScheduleRevision"]] = relationship(
        back_populates="origin_revision"
    )
    events: Mapped[list["ScheduleRevisionEvent"]] = relationship(
        back_populates="schedule_revision",
        cascade="all, delete-orphan",
        order_by="ScheduleRevisionEvent.event_sequence",
    )


class ScheduleRevisionEvent(Base):
    __tablename__ = "schedule_revision_events"
    __table_args__ = (
        UniqueConstraint(
            "semester_id", "event_sequence", name="uq_schedule_revision_event_sequence"
        ),
        CheckConstraint(
            "event_sequence > 0", name="ck_schedule_revision_event_sequence_positive"
        ),
        CheckConstraint(
            "event_type IN ('created', 'marked_ready', 'returned_to_draft', 'published', "
            "'superseded', 'abandoned', 'restored')",
            name="ck_schedule_revision_event_type",
        ),
        CheckConstraint(
            "to_state IN ('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_event_to_state",
        ),
        CheckConstraint(
            "from_state IS NULL OR from_state IN "
            "('draft', 'ready_for_review', 'published', 'superseded', 'abandoned')",
            name="ck_schedule_revision_event_from_state",
        ),
        CheckConstraint(
            "(event_type = 'created' AND from_state IS NULL) OR "
            "(event_type <> 'created' AND from_state IS NOT NULL)",
            name="ck_schedule_revision_event_created_source",
        ),
        Index("ix_schedule_revision_events_revision", "schedule_revision_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    schedule_revision_id: Mapped[int] = mapped_column(
        ForeignKey("schedule_revisions.id", ondelete="CASCADE"), nullable=False
    )
    event_sequence: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String(30), nullable=False)
    from_state: Mapped[str | None] = mapped_column(String(30), nullable=True)
    to_state: Mapped[str] = mapped_column(String(30), nullable=False)
    occurred_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utc_now
    )

    schedule_revision: Mapped[ScheduleRevision] = relationship(back_populates="events")


class StudyType(Base):
    __tablename__ = "study_types"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_study_types_normalized_name"),
        UniqueConstraint("normalized_name_key", name="uq_study_types_normalized_name_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    normalized_name_key: Mapped[str] = mapped_column(String(260), nullable=False, default=lambda: uuid4().hex)
    name_repair_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    time_windows: Mapped[list["StudyTypeTimeWindow"]] = relationship(
        back_populates="study_type",
        order_by="StudyTypeTimeWindow.sort_order",
    )


class StudyTypeTimeWindow(Base):
    __tablename__ = "study_type_time_windows"
    __table_args__ = (
        UniqueConstraint(
            "study_type_id", "weekday", "start_time", "end_time",
            name="uq_study_type_time_window_exact",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    study_type_id: Mapped[int] = mapped_column(ForeignKey("study_types.id"), nullable=False)
    weekday: Mapped[int] = mapped_column(Integer, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    study_type: Mapped[StudyType] = relationship(back_populates="time_windows")


class Course(Base):
    __tablename__ = "courses"
    __table_args__ = (
        UniqueConstraint("normalized_name", name="uq_courses_normalized_name"),
        UniqueConstraint("normalized_name_key", name="uq_courses_normalized_name_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    normalized_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    normalized_name_key: Mapped[str] = mapped_column(String(260), nullable=False, default=lambda: uuid4().hex)
    name_repair_required: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    total_units: Mapped[int] = mapped_column(Integer, nullable=False)
    min_session_units: Mapped[int] = mapped_column(Integer, nullable=False)
    max_session_units: Mapped[int] = mapped_column(Integer, nullable=False)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), nullable=False)
    study_type_id: Mapped[int] = mapped_column(ForeignKey("study_types.id"), nullable=False)
    current_semester_id: Mapped[int | None] = mapped_column(
        ForeignKey("semesters.id"), nullable=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    cohort: Mapped[Cohort] = relationship()
    study_type: Mapped[StudyType] = relationship()
    current_semester: Mapped[Semester | None] = relationship()
    eligible_lecturers: Mapped[list["CourseEligibleLecturer"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseEligibleLecturer.lecturer_id",
    )
    eligible_rooms: Mapped[list["CourseEligibleRoom"]] = relationship(
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseEligibleRoom.room_id",
    )
    exam_configurations: Mapped[list["CourseExamConfiguration"]] = relationship(
        back_populates="course", cascade="all, delete-orphan"
    )
    exam_sessions: Mapped[list["ExamSession"]] = relationship(back_populates="course")

    @property
    def lecturer_id(self) -> int | None:
        return self.eligible_lecturers[0].lecturer_id if self.eligible_lecturers else None

    @property
    def room_id(self) -> int | None:
        return self.eligible_rooms[0].room_id if self.eligible_rooms else None

    @property
    def lecturer(self) -> Lecturer | None:
        return self.eligible_lecturers[0].lecturer if self.eligible_lecturers else None

    @property
    def room(self) -> Room | None:
        return self.eligible_rooms[0].room if self.eligible_rooms else None


class CourseEligibleLecturer(Base):
    __tablename__ = "course_eligible_lecturers"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    lecturer_id: Mapped[int] = mapped_column(
        ForeignKey("lecturers.id"),
        primary_key=True,
    )

    course: Mapped[Course] = relationship(back_populates="eligible_lecturers")
    lecturer: Mapped[Lecturer] = relationship(back_populates="eligible_courses")


class CourseEligibleRoom(Base):
    __tablename__ = "course_eligible_rooms"

    course_id: Mapped[int] = mapped_column(
        ForeignKey("courses.id", ondelete="CASCADE"),
        primary_key=True,
    )
    room_id: Mapped[int] = mapped_column(
        ForeignKey("rooms.id"),
        primary_key=True,
    )

    course: Mapped[Course] = relationship(back_populates="eligible_rooms")
    room: Mapped[Room] = relationship(back_populates="eligible_courses")


class ResourceUnavailabilityPeriod(Base):
    __tablename__ = "resource_unavailability_periods"
    __table_args__ = (
        CheckConstraint(
            "(lecturer_id IS NOT NULL AND room_id IS NULL) OR "
            "(lecturer_id IS NULL AND room_id IS NOT NULL)",
            name="ck_resource_unavailability_exactly_one_owner",
        ),
        CheckConstraint(
            "kind IN ('recurring', 'dated')",
            name="ck_resource_unavailability_kind",
        ),
        CheckConstraint(
            "(kind = 'recurring' AND start_date IS NULL AND end_date IS NULL AND end_time > start_time) OR "
            "(kind = 'dated' AND start_date IS NOT NULL AND end_date IS NOT NULL AND "
            "(end_date > start_date OR (end_date = start_date AND end_time > start_time)))",
            name="ck_resource_unavailability_shape",
        ),
        CheckConstraint("revision > 0", name="ck_resource_unavailability_revision_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    lecturer_id: Mapped[int | None] = mapped_column(
        ForeignKey("lecturers.id", ondelete="CASCADE"),
        nullable=True,
    )
    room_id: Mapped[int | None] = mapped_column(
        ForeignKey("rooms.id", ondelete="CASCADE"),
        nullable=True,
    )
    kind: Mapped[str] = mapped_column(String(20), nullable=False)
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    lecturer: Mapped[Lecturer | None] = relationship(back_populates="unavailability_periods")
    room: Mapped[Room | None] = relationship(back_populates="unavailability_periods")
    weekdays: Mapped[list["ResourceUnavailabilityWeekday"]] = relationship(
        back_populates="period",
        cascade="all, delete-orphan",
        order_by="ResourceUnavailabilityWeekday.weekday",
    )


class ResourceUnavailabilityWeekday(Base):
    __tablename__ = "resource_unavailability_weekdays"
    __table_args__ = (
        CheckConstraint("weekday >= 0 AND weekday <= 6", name="ck_resource_unavailability_weekday"),
    )

    period_id: Mapped[int] = mapped_column(
        ForeignKey("resource_unavailability_periods.id", ondelete="CASCADE"),
        primary_key=True,
    )
    weekday: Mapped[int] = mapped_column(Integer, primary_key=True)

    period: Mapped[ResourceUnavailabilityPeriod] = relationship(back_populates="weekdays")


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
    course_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    course_total_units_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    course_min_session_units_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    course_max_session_units_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    cohort_id_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    cohort_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    cohort_size_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    study_type_id_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    study_type_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    semester_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    semester_start_date_snapshot: Mapped[date] = mapped_column(Date, nullable=False)
    semester_end_date_snapshot: Mapped[date] = mapped_column(Date, nullable=False)

    course: Mapped[Course] = relationship()
    semester: Mapped[Semester] = relationship()
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


class CourseExamConfiguration(Base):
    __tablename__ = "course_exam_configurations"
    __table_args__ = (
        UniqueConstraint("course_id", "semester_id", name="uq_course_exam_configuration_course_semester"),
        CheckConstraint("duration_minutes IS NULL OR duration_minutes > 0", name="ck_exam_configuration_duration_positive"),
        CheckConstraint("required_capacity IS NULL OR required_capacity > 0", name="ck_exam_configuration_capacity_positive"),
        CheckConstraint("revision > 0", name="ck_exam_configuration_revision_positive"),
        CheckConstraint(
            "(recommended_start_override IS NULL AND recommended_end_override IS NULL) OR "
            "(recommended_start_override IS NOT NULL AND recommended_end_override IS NOT NULL AND recommended_end_override >= recommended_start_override)",
            name="ck_exam_configuration_recommendation_pair",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    identifier: Mapped[str | None] = mapped_column(String(200), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    recommended_start_override: Mapped[date | None] = mapped_column(Date, nullable=True)
    recommended_end_override: Mapped[date | None] = mapped_column(Date, nullable=True)
    required_capacity: Mapped[int | None] = mapped_column(Integer, nullable=True)
    exam_type: Mapped[str | None] = mapped_column(String(200), nullable=True)
    responsible_lecturer_id: Mapped[int | None] = mapped_column(ForeignKey("lecturers.id"), nullable=True)
    configuration_consumed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    course: Mapped[Course] = relationship(back_populates="exam_configurations")
    semester: Mapped[Semester] = relationship()
    responsible_lecturer: Mapped[Lecturer | None] = relationship()


class ExamSession(Base):
    __tablename__ = "exam_sessions"
    __table_args__ = (
        CheckConstraint("duration_minutes > 0", name="ck_exam_session_duration_positive"),
        CheckConstraint("required_capacity > 0", name="ck_exam_session_capacity_positive"),
        CheckConstraint("revision > 0", name="ck_exam_session_revision_positive"),
        CheckConstraint("end_time > start_time", name="ck_exam_session_interval"),
        CheckConstraint("source IN ('generated', 'manual')", name="ck_exam_session_source"),
        Index("ix_exam_session_course_semester_date", "course_id", "semester_id", "exam_date"),
        Index("ix_exam_session_lecturer_occupancy", "semester_id", "exam_date", "lecturer_id"),
        Index("ix_exam_session_room_occupancy", "semester_id", "exam_date", "room_id"),
        Index("ix_exam_session_cohort_occupancy", "semester_id", "exam_date", "cohort_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    course_id: Mapped[int] = mapped_column(ForeignKey("courses.id"), nullable=False)
    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id"), nullable=False)
    cohort_id: Mapped[int] = mapped_column(ForeignKey("cohorts.id"), nullable=False)
    lecturer_id: Mapped[int] = mapped_column(ForeignKey("lecturers.id"), nullable=False)
    room_id: Mapped[int] = mapped_column(ForeignKey("rooms.id"), nullable=False)
    exam_date: Mapped[date] = mapped_column(Date, nullable=False)
    start_time: Mapped[time] = mapped_column(Time, nullable=False)
    end_time: Mapped[time] = mapped_column(Time, nullable=False)
    source: Mapped[str] = mapped_column(String(20), nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    configuration_identifier: Mapped[str] = mapped_column(String(200), nullable=False)
    configuration_revision: Mapped[int] = mapped_column(Integer, nullable=False)
    duration_minutes: Mapped[int] = mapped_column(Integer, nullable=False)
    exam_type: Mapped[str] = mapped_column(String(200), nullable=False)
    required_capacity: Mapped[int] = mapped_column(Integer, nullable=False)
    recommended_start_date: Mapped[date] = mapped_column(Date, nullable=False)
    recommended_end_date: Mapped[date] = mapped_column(Date, nullable=False)
    recommendation_was_overridden: Mapped[bool] = mapped_column(Boolean, nullable=False)
    final_teaching_date: Mapped[date] = mapped_column(Date, nullable=False)
    final_teaching_end_time: Mapped[time] = mapped_column(Time, nullable=False)
    final_teaching_session_id_snapshot: Mapped[int] = mapped_column(Integer, nullable=False)
    course_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    semester_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    cohort_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    lecturer_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    lecturer_reference_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    room_name_snapshot: Mapped[str] = mapped_column(String(200), nullable=False)
    room_reference_snapshot: Mapped[str] = mapped_column(String(100), nullable=False)
    __mapper_args__ = {"version_id_col": revision, "version_id_generator": False}

    course: Mapped[Course] = relationship(back_populates="exam_sessions")
    semester: Mapped[Semester] = relationship()
    cohort: Mapped[Cohort] = relationship()
    lecturer: Mapped[Lecturer] = relationship()
    room: Mapped[Room] = relationship()
