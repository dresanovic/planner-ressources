from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.planning import Course, PlanningOutcome, ScheduleRevision


OPERATION_KINDS = {
    "single_course_generation",
    "multi_course_generation",
    "semester_optimization",
    "exam_generation",
}
CLASSIFICATIONS = {"successful", "failed", "stale", "unchanged", "skipped"}
WRITABLE_REVISION_STATES = {"draft", "ready_for_review"}


class StalePlanningOutcomeError(RuntimeError):
    """Raised when a completed operation targets a revision that is no longer active."""


def retain_planning_outcome(
    db: Session,
    *,
    schedule_revision_id: int,
    course_id: int,
    operation_kind: str,
    classification: str,
    source_status: str,
    result_payload: dict[str, Any],
    completed_at: datetime,
) -> PlanningOutcome:
    if operation_kind not in OPERATION_KINDS:
        raise ValueError(f"Unsupported planning operation kind: {operation_kind}")
    if classification not in CLASSIFICATIONS:
        raise ValueError(f"Unsupported planning outcome classification: {classification}")
    if not source_status.strip():
        raise ValueError("Planning outcome source status is required.")
    if completed_at.tzinfo is None:
        raise ValueError("Planning outcome completion time must be timezone-aware.")

    revision = db.get(ScheduleRevision, schedule_revision_id)
    if revision is None or revision.state not in WRITABLE_REVISION_STATES:
        raise StalePlanningOutcomeError(
            "The completed operation no longer targets an active Working revision."
        )
    active_id = db.scalar(
        select(ScheduleRevision.id).where(
            ScheduleRevision.semester_id == revision.semester_id,
            ScheduleRevision.state.in_(WRITABLE_REVISION_STATES),
        )
    )
    if active_id != schedule_revision_id:
        raise StalePlanningOutcomeError(
            "The completed operation no longer targets the current Working revision."
        )
    if db.get(Course, course_id) is None:
        raise ValueError("Planning outcome course does not exist.")

    outcome = db.scalar(
        select(PlanningOutcome).where(
            PlanningOutcome.schedule_revision_id == schedule_revision_id,
            PlanningOutcome.course_id == course_id,
            PlanningOutcome.operation_kind == operation_kind,
        )
    )
    if outcome is not None and _as_utc(outcome.completed_at) >= _as_utc(completed_at):
        return outcome
    if outcome is None:
        outcome = PlanningOutcome(
            schedule_revision_id=schedule_revision_id,
            course_id=course_id,
            operation_kind=operation_kind,
        )
        db.add(outcome)
    outcome.classification = classification
    outcome.source_status = source_status
    outcome.result_payload = dict(result_payload)
    outcome.completed_at = completed_at
    db.flush()
    return outcome


def list_planning_outcomes(
    db: Session, schedule_revision_id: int
) -> list[PlanningOutcome]:
    return list(
        db.scalars(
            select(PlanningOutcome)
            .where(PlanningOutcome.schedule_revision_id == schedule_revision_id)
            .order_by(
                PlanningOutcome.course_id,
                PlanningOutcome.operation_kind,
            )
        )
    )


def _as_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)
