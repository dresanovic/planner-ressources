from copy import deepcopy
from datetime import date, datetime, time, timezone

import pytest
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.db.schema import initialize_database
from app.models.planning import (
    DraftSession,
    GenerationConstraintSet,
    GenerationConstraintWindow,
    InstitutionHoliday,
    Lecturer,
    Room,
    ScheduleRevision,
    CohortCalendarTimeWindow,
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


def test_time_grid_projects_source_hours_every_date_and_never_writes():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    with _db() as db:
        seed_time_grid_workspace(db)
        before = list(db.connection().connection.iterdump())
        workspace = get_calendar_workspace(db, 1)
        context = workspace["teachingWindowContexts"][0]
        assert context["calendarRef"] == "calendar:1"
        assert workspace["courses"][0]["cohortCalendarRef"] == "calendar:1"
        assert context["basis"] == "current_working"
        assert len(context["days"]) == 31  # June plus the saved exam outside June
        saturday = next(day for day in context["days"] if day["date"] == "2027-06-26")
        assert saturday["applicableWindowRefs"] == [context["windows"][0]["windowRef"]]
        assert context["windows"][0]["startTime"] == "08:00"
        assert context["windows"][0]["endTime"] == "16:00"
        assert any(f["details"].get("issueCode") == "COHORT_CALENDAR_WINDOW_VIOLATION"
                   for f in workspace["validationFindings"])
        assert before == list(db.connection().connection.iterdump())


def test_time_grid_keeps_zero_session_courses_and_known_empty_hours():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    with _db() as db:
        seed_time_grid_workspace(db)
        for session in db.scalars(select(DraftSession)):
            db.delete(session)
        for window in db.scalars(select(CohortCalendarTimeWindow)):
            db.delete(window)
        db.commit()
        context = get_calendar_workspace(db, 1)["teachingWindowContexts"][0]
        assert context["availability"] == "available"
        assert context["windows"] == []
        assert all(day["applicableWindowRefs"] == [] for day in context["days"])


def test_time_grid_separates_calendars_even_with_duplicate_names_and_empty_course():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    from app.models.planning import CohortCalendar
    with _db() as db:
        seed_time_grid_workspace(db, second_calendar=True)
        db.get(CohortCalendar, 2).name = 'Calendar A'
        db.commit()
        workspace = get_calendar_workspace(db, 1)
        a, b = workspace['teachingWindowContexts']
        assert a['calendarLabel'] == b['calendarLabel']
        assert a['calendarRef'] != b['calendarRef']
        assert (a['windows'][0]['startTime'], b['windows'][0]['startTime']) == ('08:00', '10:00')
        assert workspace['courses'][1]['occurrenceRefs'] == []


def test_time_grid_keeps_actual_saved_intervals_and_existing_findings():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace, time_grid_reference_intervals
    with _db() as db:
        seed_time_grid_workspace(db)
        session = db.scalar(select(DraftSession))
        for name, start, end in time_grid_reference_intervals():
            session.start_time, session.end_time = time.fromisoformat(start), time.fromisoformat(end)
            db.commit()
            workspace = get_calendar_workspace(db, 1)
            occurrence = next(o for o in workspace['occurrences'] if o['kind'] == 'teaching')
            assert (occurrence['startTime'], occurrence['endTime']) == (start, end)
            has_window_finding = any(f['details'].get('issueCode') == 'COHORT_CALENDAR_WINDOW_VIOLATION'
                for f in workspace['validationFindings'])
            assert has_window_finding == (name in {'overrun', 'outside', 'early', 'late'})


def test_time_grid_dated_intensive_precedence_period_bounds_and_token():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    from app.models.planning import CohortCalendar
    with _db() as db:
        seed_time_grid_workspace(db)
        db.add_all([
            CohortCalendarTimeWindow(cohort_calendar_id=1, weekday=0,
                start_time=time(8), end_time=time(16), sort_order=1),
            CohortCalendarTimeWindow(cohort_calendar_id=1, kind="dated", weekday=None,
                date=date(2027, 6, 7), is_intensive=True,
                start_time=time(10), end_time=time(12), sort_order=2),
        ])
        db.commit()
        first = get_calendar_workspace(db, 1)
        ctx = first["teachingWindowContexts"][0]
        by_ref = {w["windowRef"]: w for w in ctx["windows"]}
        days = {d["date"]: d for d in ctx["days"]}
        assert [by_ref[r]["kind"] for r in days['2027-06-07']['applicableWindowRefs']] == ['dated']
        assert [by_ref[r]["kind"] for r in days['2027-06-14']['applicableWindowRefs']] == ['weekly']
        assert days['2026-12-10']['periodStatus'] == 'outside_period'
        assert days['2026-12-10']['applicableWindowRefs'] == []
        window = db.scalar(select(CohortCalendarTimeWindow).where(CohortCalendarTimeWindow.kind == 'dated'))
        window.is_intensive = False
        db.commit()
        second = get_calendar_workspace(db, 1)
        assert second['workspaceToken'] != first['workspaceToken']
        db.get(CohortCalendar, 1).start_date = date(2027, 6, 10)
        db.commit()
        bounded = get_calendar_workspace(db, 1)['teachingWindowContexts'][0]
        assert next(d for d in bounded['days'] if d['date'] == '2027-06-07')['applicableWindowRefs'] == []


def test_time_grid_retains_adjacent_source_boundaries_custom_bounds_and_hour_token():
    from tests.calendar_workspace_fixtures import seed_time_grid_workspace
    with _db() as db:
        seed_time_grid_workspace(db)
        first = db.scalar(select(CohortCalendarTimeWindow))
        first.end_time = time(13)
        db.add(CohortCalendarTimeWindow(cohort_calendar_id=1, weekday=5,
            start_time=time(13), end_time=time(18), sort_order=1))
        db.add(GenerationConstraintSet(course_id=1, semester_id=1,
            planning_start_date=date(2027, 6, 10), planning_end_date=date(2027, 6, 30), revision=2))
        db.commit()
        before = get_calendar_workspace(db, 1)
        context = before['teachingWindowContexts'][0]
        assert context['isCustom'] is True
        assert context['sourceRevision'] == 2
        assert context['planningStartDate'] == '2027-06-10'
        assert len(context['windows']) == 2
        assert len(next(d for d in context['days'] if d['date'] == '2027-06-26')['applicableWindowRefs']) == 2
        assert any(f['details'].get('issueCode') == 'COHORT_CALENDAR_WINDOW_VIOLATION' for f in before['validationFindings'])
        first.start_time = time(8, 30)
        db.commit()
        after = get_calendar_workspace(db, 1)
        assert before['workspaceToken'] != after['workspaceToken']
        assert before['validationFindings'] == after['validationFindings']


def test_time_grid_mixed_legacy_capture_has_partial_context_and_no_live_identity_fallback():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        created = create_working_revision(db, 1, get_lifecycle_overview(db, 1)['stateToken'])
        revision = created['activeWorkingRevision']
        prepared = prepare_publication(db, revision['revisionId'], revision['revisionVersion'], created['stateToken'])
        transition_revision(db, revision['revisionId'], action='publish',
            expected_revision_version=revision['revisionVersion'], expected_state_token=created['stateToken'],
            confirmed=True, publication_token=prepared['preparationToken'])
        row = db.get(ScheduleRevision, revision['revisionId'])
        snapshot = deepcopy(row.snapshot_document)
        legacy = deepcopy(snapshot['courses'][0])
        legacy['sourceCourseId'] = 999
        legacy.pop('constraintProfile', None)
        legacy['cohortCalendar'].pop('sourceId', None)
        legacy['teachingSessions'] = []
        snapshot['courses'].append(legacy)
        row.snapshot_document = snapshot
        db.commit()
        before = deepcopy(row.snapshot_document)
        workspace = get_calendar_workspace(db, 1)
        assert workspace['sectionStatus']['teachingWindows']['availability'] == 'partial'
        known, unknown = workspace['teachingWindowContexts']
        assert known['basis'] == 'captured_published'
        assert unknown['calendarRef'] is None
        assert unknown['basis'] == 'unavailable'
        assert unknown['windows'] == unknown['days'] == []
        assert workspace['courses'][1]['cohortCalendarRef'] is None
        assert workspace['selectedRevision']['validationBasis'] == 'current'
        assert row.snapshot_document == before


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


def test_lecturer_filter_facet_uses_the_resource_name():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        lecturer = db.get(Lecturer, 1)
        lecturer.name = "Ada Lovelace"
        db.get(Room, 1).reference_code = "CAMPUS-055"
        initial = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, initial["stateToken"])
        db.commit()

        workspace = get_calendar_workspace(db, 1)

        assert workspace["filterFacets"]["lecturers"] == [
            {"value": "lecturer:1", "label": "Ada Lovelace"}
        ]
        assert workspace["filterFacets"]["rooms"] == [
            {"value": "room:1", "label": "CAMPUS-055"}
        ]


def test_exported_validation_derivation_receives_the_complete_revision(
    monkeypatch,
):
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        initial = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        original = calendar_workspace.derive_calendar_validation_findings
        received: list[set[str]] = []

        def capture(db_session, courses, occurrences, holidays):
            received.append(
                {occurrence["occurrenceRef"] for occurrence in occurrences}
            )
            return original(db_session, courses, occurrences, holidays)

        monkeypatch.setattr(
            calendar_workspace,
            "derive_calendar_validation_findings",
            capture,
        )

        workspace = get_calendar_workspace(db, 1)

        assert received == [
            {row["occurrenceRef"] for row in workspace["occurrences"]}
        ]
        assert {row["kind"] for row in workspace["occurrences"]} == {
            "teaching",
            "exam",
        }


def test_working_default_preserves_cohort_calendar_window_validation_code():
    with _db() as db:
        seed_lifecycle_semester(db, with_schedule=True)
        db.add(
            CohortCalendarTimeWindow(
                cohort_calendar_id=1,
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

        assert "GENERATION_CONSTRAINT_VIOLATION" not in issue_codes
        assert "COHORT_CALENDAR_WINDOW_VIOLATION" in issue_codes
        assert "VALIDATION_DATA_MISSING" not in issue_codes


def test_calendar_revalidates_saved_teaching_against_live_windows_without_moving_it():
    with _db() as db:
        semester, _course = seed_lifecycle_semester(db, with_schedule=True)
        db.add_all(
            [
                CohortCalendarTimeWindow(
                    cohort_calendar_id=1,
                    weekday=1,
                    start_time=time(9),
                    end_time=time(11),
                    sort_order=0,
                ),
                GenerationConstraintSet(
                    course_id=1,
                    semester_id=1,
                    planning_start_date=semester.start_date,
                    planning_end_date=semester.end_date,
                    windows=[
                        GenerationConstraintWindow(
                            weekday=0,
                            start_time=time(9),
                            end_time=time(11),
                            sort_order=0,
                        )
                    ],
                ),
            ]
        )
        initial = get_lifecycle_overview(db, 1)
        create_working_revision(db, 1, initial["stateToken"])
        db.commit()
        source = db.scalar(select(DraftSession).where(DraftSession.course_id == 1))
        original_interval = (source.date, source.start_time, source.end_time)

        workspace = get_calendar_workspace(db, 1)

        issue_codes = {
            row["details"].get("issueCode")
            for row in workspace["validationFindings"]
            if row["category"] == "other"
        }
        assert "GENERATION_CONSTRAINT_VIOLATION" not in issue_codes
        assert "COHORT_CALENDAR_WINDOW_VIOLATION" in issue_codes
        db.refresh(source)
        assert (source.date, source.start_time, source.end_time) == original_interval


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
        assert before["filterFacets"]["rooms"] == [
            {"value": "room:1", "label": "R-1"}
        ]
        db.get(Room, 1).reference_code = "RENAMED-ROOM"
        db.get(Lecturer, 1).name = "Renamed Lecturer"
        db.add(InstitutionHoliday(date=date(2026, 10, 5), name="New closure"))
        db.get(Lecturer, 1).is_active = False
        db.commit()
        after = get_calendar_workspace(db, 1)
        assert after["filterFacets"]["rooms"] == before["filterFacets"]["rooms"]
        assert after["filterFacets"]["lecturers"] == before["filterFacets"]["lecturers"]

        assert before["selectedRevision"]["designation"] == "current_published"
        assert before["selectedRevision"]["snapshotSchemaVersion"] == 2
        assert before['teachingWindowContexts'][0]['basis'] == 'captured_published'
        assert after['teachingWindowContexts'] == before['teachingWindowContexts']
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
        assert workspace['teachingWindowContexts'][0]['availability'] == 'unavailable'
        assert workspace['teachingWindowContexts'][0]['windows'] == []
        assert workspace['teachingWindowContexts'][0]['basis'] == 'unavailable'
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
            "cohortCalendar": "Full-time",
            "occurrenceRefs": ["teaching:1"],
            "findingRefs": [],
        },
        {
            "courseRef": "course:2",
            "name": "Stale unscheduled",
            "cohort": "C2",
            "cohortCalendar": "Part-time",
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
            "cohortCalendar": "Full-time",
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
