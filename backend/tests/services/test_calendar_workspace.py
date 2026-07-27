from copy import deepcopy
from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.models.planning import (
    InstitutionHoliday,
    Lecturer,
    ScheduleRevision,
    StudyTypeTimeWindow,
)
from app.services import calendar_workspace
from app.services.calendar_workspace import (
    CalendarWorkspaceError,
    get_calendar_workspace,
)
from app.services.planning_outcomes import retain_planning_outcome
from app.services.schedule_lifecycle import (
    create_working_revision,
    get_lifecycle_overview,
    prepare_publication,
    transition_revision,
)
from tests.schedule_lifecycle_fixtures import seed_lifecycle_semester


def _db():
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    initialize_database(engine)
    return Session(engine)


def test_no_revision_is_explicit_and_contains_no_revision_owned_records():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=False)

        workspace = get_calendar_workspace(db, 1)

        assert workspace["workspaceState"] == "no_revision"
        assert workspace["selectedRevision"] is None
        assert workspace["courses"] == []
        assert workspace["occurrences"] == []
        assert workspace["holidays"] == []
        assert workspace["filterFacets"]["courses"] == []
        assert {
            metric["availability"] for metric in workspace["summary"].values()
        } == {"not_applicable"}
        assert {
            metric["scope"] for metric in workspace["summary"].values()
        } == {"no_revision"}


def test_working_default_has_traceable_remaining_work_and_outcome_coverage():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        revision_id = created["activeWorkingRevision"]["revisionId"]
        retain_planning_outcome(
            db,
            schedule_revision_id=revision_id,
            course_id=1,
            operation_kind="single_course_generation",
            classification="failed",
            source_status="no_feasible_slot",
            result_payload={"errors": [{"code": "NO_FEASIBLE_SLOT"}]},
            completed_at=datetime(2026, 9, 1, tzinfo=timezone.utc),
        )
        db.commit()

        workspace = get_calendar_workspace(db, 1)

        assert workspace["selectedRevision"]["designation"] == "active_working"
        assert workspace["selectedRevision"]["readOnly"] is False
        assert {row["kind"] for row in workspace["occurrences"]} == {
            "teaching",
            "exam",
        }
        exam = next(
            row for row in workspace["occurrences"] if row["kind"] == "exam"
        )
        assert exam["requiredCapacity"] == 30
        assert exam["assignedRoomName"] == "Room 1"
        assert exam["currentRoomCapacity"] == 40
        unscheduled = workspace["summary"]["unscheduledWork"]
        assert unscheduled["remainingTeachingUnits"] == 2
        assert unscheduled["remainingInstructionalMinutes"] == 90
        assert unscheduled["contributorRefs"] == ["course:1"]
        failures = workspace["summary"]["planningFailures"]
        assert failures["availability"] == "available"
        assert failures["failedOutcomeCount"] == 1
        assert failures["contributorRefs"] == ["outcome:1"]
        assert workspace["summary"]["needsReview"]["contributorRefs"] == [
            "course:1"
        ]
        assert any(
            row["details"].get("issueCode") == "VALIDATION_DATA_MISSING"
            for row in workspace["validationFindings"]
        )
        assert workspace["sectionStatus"]["validationFindings"][
            "availability"
        ] == "partial"


def test_working_default_preserves_study_type_window_validation_code():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        db.add(
            StudyTypeTimeWindow(
                study_type_id=1,
                weekday=0,
                start_time=time(13),
                end_time=time(14),
                sort_order=0,
            )
        )
        initial = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, initial["stateToken"])
        db.commit()

        workspace = get_calendar_workspace(db, 1)
        issue_codes = {
            row["details"].get("issueCode")
            for row in workspace["validationFindings"]
            if row["category"] == "other"
        }

        assert "GENERATION_CONSTRAINT_VIOLATION" in issue_codes
        assert "STUDY_TYPE_WINDOW_VIOLATION" in issue_codes
        assert "VALIDATION_DATA_MISSING" not in issue_codes


def test_same_revision_lifecycle_change_during_read_returns_conflict(monkeypatch):
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        revision_id = created["activeWorkingRevision"]["revisionId"]
        db.commit()
        original_token = calendar_workspace._token

        def transition_before_final_check(response):
            revision = db.get(ScheduleRevision, revision_id)
            revision.state = "ready_for_review"
            revision.row_version += 1
            db.flush()
            return original_token(response)

        monkeypatch.setattr(
            calendar_workspace,
            "_token",
            transition_before_final_check,
        )

        with pytest.raises(CalendarWorkspaceError) as caught:
            get_calendar_workspace(db, 1)

        assert caught.value.status_code == 409


def test_published_content_stays_captured_while_current_holiday_validation_changes():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        revision = created["activeWorkingRevision"]
        prepared = prepare_publication(
            db,
            revision["revisionId"],
            revision["revisionVersion"],
            created["stateToken"],
        )
        transition_revision(
            db,
            revision["revisionId"],
            action="publish",
            expected_revision_version=revision["revisionVersion"],
            expected_state_token=created["stateToken"],
            confirmed=True,
            publication_token=prepared["preparationToken"],
        )
        db.commit()

        before = get_calendar_workspace(db, 1)
        db.add(InstitutionHoliday(date=date(2026, 10, 5), name="New closure"))
        db.get(Lecturer, 1).is_active = False
        db.commit()
        after = get_calendar_workspace(db, 1)

        assert before["selectedRevision"]["designation"] == "current_published"
        assert before["selectedRevision"]["snapshotSchemaVersion"] == 2
        assert [
            {key: value for key, value in row.items() if key != "findingRefs"}
            for row in before["occurrences"]
        ] == [
            {key: value for key, value in row.items() if key != "findingRefs"}
            for row in after["occurrences"]
        ]
        assert any(
            row["category"] == "holiday"
            and row["affectedOccurrenceRefs"] == ["teaching:1"]
            for row in after["validationFindings"]
        )
        assert any(
            row["category"] == "other"
            and row["details"]["issueCode"] == "LECTURER_INELIGIBLE"
            and row["affectedOccurrenceRefs"] == ["teaching:1"]
            for row in after["validationFindings"]
        )


def test_legacy_publication_marks_only_constraint_dependent_validation_incomplete():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        created = create_working_revision(db, 1, initial["stateToken"])
        revision = created["activeWorkingRevision"]
        prepared = prepare_publication(
            db,
            revision["revisionId"],
            revision["revisionVersion"],
            created["stateToken"],
        )
        transition_revision(
            db,
            revision["revisionId"],
            action="publish",
            expected_revision_version=revision["revisionVersion"],
            expected_state_token=created["stateToken"],
            confirmed=True,
            publication_token=prepared["preparationToken"],
        )
        row = db.get(ScheduleRevision, revision["revisionId"])
        snapshot = deepcopy(row.snapshot_document)
        snapshot["schemaVersion"] = 1
        for course in snapshot["courses"]:
            course.pop("constraintProfile", None)
        row.snapshot_schema_version = 1
        row.snapshot_document = snapshot
        db.commit()

        workspace = get_calendar_workspace(db, 1)

        assert workspace["workspaceState"] == "loaded"
        assert workspace["sectionStatus"]["validationFindings"][
            "availability"
        ] == "partial"
        assert workspace["summary"]["needsReview"]["availability"] == "partial"
        assert workspace["summary"]["conflicts"]["availability"] == "available"
        assert any(
            finding["details"].get("issueCode") == "VALIDATION_DATA_MISSING"
            and finding["details"].get("subjectRef") == "constraint_profile"
            and finding["affectedOccurrenceRefs"] == ["teaching:1"]
            for finding in workspace["validationFindings"]
        )


def test_summary_availability_and_outcome_coverage_matrix_is_exact():
    empty = calendar_workspace._summary([], [], [], [])
    assert {metric["availability"] for metric in empty.values()} == {
        "not_applicable"
    }
    assert empty["planningFailures"]["coverage"] == {
        "eligibleCourseCount": 0,
        "coveredCourseCount": 0,
        "coverageComplete": False,
    }

    courses = [
        {
            "courseRef": "course:1",
            "planningEligible": True,
            "remainingTeachingUnits": 0,
            "remainingInstructionalMinutes": 0,
            "needsReviewReasonRefs": [],
        },
        {
            "courseRef": "course:2",
            "planningEligible": True,
            "remainingTeachingUnits": 2,
            "remainingInstructionalMinutes": 90,
            "needsReviewReasonRefs": ["remaining:course:2", "finding:other:2"],
        },
    ]
    uncovered = calendar_workspace._summary(courses, [], [], [])
    assert uncovered["planningFailures"]["availability"] == "unavailable"
    assert uncovered["planningFailures"]["coverage"] == {
        "eligibleCourseCount": 2,
        "coveredCourseCount": 0,
        "coverageComplete": False,
    }
    assert "failedOutcomeCount" not in uncovered["planningFailures"]

    partial = calendar_workspace._summary(
        courses,
        [],
        [],
        [
            {
                "outcomeRef": "outcome:1",
                "courseRef": "course:1",
                "classification": "failed",
            }
        ],
    )
    assert partial["planningFailures"] == {
        "availability": "partial",
        "scope": "complete_revision",
        "coverage": {
            "eligibleCourseCount": 2,
            "coveredCourseCount": 1,
            "coverageComplete": False,
        },
        "failedOutcomeCount": 1,
        "staleOutcomeCount": 0,
        "unchangedOutcomeCount": 0,
        "contributorRefs": ["outcome:1"],
    }

    available = calendar_workspace._summary(
        courses,
        [],
        [],
        [
            {
                "outcomeRef": "outcome:1",
                "courseRef": "course:1",
                "classification": "failed",
            },
            {
                "outcomeRef": "outcome:2",
                "courseRef": "course:2",
                "classification": "successful",
            },
        ],
    )
    assert available["planningFailures"]["availability"] == "available"
    assert available["planningFailures"]["coverage"]["coverageComplete"] is True
    assert available["planningFailures"]["failedOutcomeCount"] == 1
    assert available["planningFailures"]["contributorRefs"] == ["outcome:1"]


def test_planning_outcome_coverage_excludes_visible_ineligible_courses_and_outcomes():
    courses = [
        {
            "courseRef": "course:1",
            "planningEligible": True,
            "remainingTeachingUnits": 0,
            "remainingInstructionalMinutes": 0,
            "needsReviewReasonRefs": [],
        },
        {
            "courseRef": "course:2",
            "planningEligible": False,
            "remainingTeachingUnits": 2,
            "remainingInstructionalMinutes": 90,
            "needsReviewReasonRefs": ["remaining:course:2"],
        },
    ]
    outcomes = [
        {
            "outcomeRef": "outcome:1",
            "courseRef": "course:1",
            "classification": "successful",
        },
        {
            "outcomeRef": "outcome:2",
            "courseRef": "course:2",
            "classification": "failed",
        },
    ]

    mixed = calendar_workspace._summary(courses, [], [], outcomes)
    assert mixed["planningFailures"] == {
        "availability": "available",
        "scope": "complete_revision",
        "coverage": {
            "eligibleCourseCount": 1,
            "coveredCourseCount": 1,
            "coverageComplete": True,
        },
        "failedOutcomeCount": 0,
        "staleOutcomeCount": 0,
        "unchangedOutcomeCount": 0,
        "contributorRefs": [],
    }

    ineligible_only = calendar_workspace._summary([courses[1]], [], [], [outcomes[1]])
    assert ineligible_only["planningFailures"]["availability"] == "not_applicable"
    assert ineligible_only["planningFailures"]["coverage"] == {
        "eligibleCourseCount": 0,
        "coveredCourseCount": 0,
        "coverageComplete": False,
    }


def test_summary_deduplicated_finding_counts_and_capacity_coverage():
    courses = [
        {
            "courseRef": "course:1",
            "planningEligible": True,
            "remainingTeachingUnits": 0,
            "remainingInstructionalMinutes": 0,
            "needsReviewReasonRefs": [
                "finding:conflict:room:teaching:1:teaching:2",
                "finding:capacity:teaching:1",
            ],
        }
    ]
    occurrences = [
        {"occurrenceRef": "teaching:1"},
        {"occurrenceRef": "teaching:2"},
    ]
    findings = [
        {
            "findingRef": "finding:conflict:room:teaching:1:teaching:2",
            "category": "room_conflict",
            "affectedOccurrenceRefs": ["teaching:1", "teaching:2"],
            "details": {"kind": "conflict"},
        },
        {
            "findingRef": "finding:capacity:teaching:1",
            "category": "room_capacity",
            "affectedOccurrenceRefs": ["teaching:1"],
            "details": {"kind": "capacity"},
        },
        {
            "findingRef": "finding:missing:teaching:2",
            "category": "other",
            "affectedOccurrenceRefs": ["teaching:2"],
            "details": {
                "kind": "other",
                "issueCode": "VALIDATION_DATA_MISSING",
                "roomRef": "room:2",
            },
        },
    ]

    summary = calendar_workspace._summary(courses, occurrences, findings, [])

    assert summary["conflicts"]["distinctFindingCount"] == 1
    assert summary["conflicts"]["countByType"] == {
        "lecturer": 0,
        "room": 1,
        "cohort": 0,
    }
    assert summary["capacityIssues"]["availability"] == "partial"
    assert summary["capacityIssues"]["affectedOccurrenceCount"] == 1
    assert summary["capacityIssues"]["contributorRefs"] == ["teaching:1"]
    assert summary["needsReview"]["distinctCourseCount"] == 1


def test_validation_facets_reconcile_no_issue_with_course_outcomes():
    courses = [
        {
            "courseRef": "course:1",
            "name": "Failed scheduled",
            "cohort": "C1",
            "studyType": "Full-time",
            "occurrenceRefs": ["teaching:1"],
            "findingRefs": [],
        },
        {
            "courseRef": "course:2",
            "name": "Stale unscheduled",
            "cohort": "C2",
            "studyType": "Part-time",
            "occurrenceRefs": [],
            "findingRefs": [],
        },
    ]
    occurrences = [
        {
            "courseRef": "course:1",
            "kind": "teaching",
            "lecturerRefs": ["lecturer:1"],
            "roomRef": "room:1",
            "findingRefs": [],
        }
    ]
    outcomes = [
        {"courseRef": "course:1", "classification": "failed"},
        {"courseRef": "course:2", "classification": "stale"},
    ]

    affected_facets = calendar_workspace._facets(
        courses,
        occurrences,
        [],
        outcomes,
        "active_working",
        "draft",
    )
    affected_values = {
        row["value"] for row in affected_facets["validationCategories"]
    }

    assert affected_values == {"planning_failure", "stale_outcome"}

    courses.append(
        {
            "courseRef": "course:3",
            "name": "Clean unscheduled",
            "cohort": "C3",
            "studyType": "Full-time",
            "occurrenceRefs": [],
            "findingRefs": [],
        }
    )
    clean_facets = calendar_workspace._facets(
        courses,
        occurrences,
        [],
        outcomes,
        "active_working",
        "draft",
    )

    assert {
        row["value"] for row in clean_facets["validationCategories"]
    } == {"none", "planning_failure", "stale_outcome"}
