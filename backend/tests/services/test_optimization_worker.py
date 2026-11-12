"""Real Windows spawn and explicit cancellation; no live database access."""
import pickle
import time

from app.services.optimization_worker import DetachedOptimizationInput, SolverProcess
from tests.optimization_fixtures import optimization_course


def problem(*, seconds=30):
    return DetachedOptimizationInput(
        courses=(optimization_course(1, total_units=2),),
        fixed_sessions=(), unavailable_dates=(), holidays={},
        deadline=time.monotonic() + seconds,
    )


def test_input_is_detached_picklable_and_solver_process_returns_exact_result():
    value = pickle.loads(pickle.dumps(problem()))
    assert value.courses[0].course_id == 1
    worker = SolverProcess(value)
    try:
        messages = []
        end = time.monotonic() + 30
        while time.monotonic() < end:
            messages.extend(worker.receive())
            if any(item["kind"] in ("result", "failed", "timeout") for item in messages):
                break
            time.sleep(.02)
        result = next(item["result"] for item in messages if item["kind"] == "result")
        assert result.total_units == 2
        assert result.courses[0].scheduled_units == 2
        assert any(item.get("phase") == "optimizing" for item in messages)
    finally:
        worker.close()
    assert not worker.is_alive()


def test_spawned_continuation_receives_incumbent_and_skips_proven_prefix():
    from dataclasses import replace
    from app.services.semester_optimization import optimize_semester
    value = problem()
    incumbent = optimize_semester(value.courses, (), generated_only=True)
    incumbent = replace(incumbent, optimal=False, objectives=tuple(
        e if i < 4 else replace(e, proof_status='not_attempted')
        for i, e in enumerate(incumbent.objectives)))
    value = pickle.loads(pickle.dumps(replace(value, incumbent=incumbent)))
    worker = SolverProcess(value)
    try:
        messages = []
        end = time.monotonic() + 30
        while time.monotonic() < end:
            messages.extend(worker.receive())
            if any(item['kind'] in ('result', 'failed', 'timeout') for item in messages):
                break
            time.sleep(.02)
        result = next(item['result'] for item in messages if item['kind'] == 'result')
        assert result.total_units == incumbent.total_units
        stages = [m['objectiveKey'] for m in messages if m['kind'] == 'objective']
        assert stages[0] == 'schedule_shape'
        assert 'total_units' not in stages
    finally:
        worker.close()


def test_exhausted_deadline_never_starts_search():
    worker = SolverProcess(problem(seconds=-1))
    try:
        messages = []
        end = time.monotonic() + 15
        while time.monotonic() < end:
            messages.extend(worker.receive())
            if any(item["kind"] == "timeout" for item in messages):
                break
            time.sleep(.02)
        assert any(item["kind"] == "timeout" for item in messages)
        assert not any(item["kind"] == "result" for item in messages)
    finally:
        worker.close()


def test_cancel_stops_and_reaps_spawned_child():
    worker = SolverProcess(problem())
    worker.close()
    assert not worker.is_alive()
    worker.close()  # cleanup is idempotent


def test_control_channel_loss_stops_child_without_parent_cleanup():
    from dataclasses import replace
    value = replace(problem(seconds=60), courses=tuple(
        optimization_course(i, total_units=80, lecturer_ids=(1, 2), room_ids=(1, 2))
        for i in range(1, 21)))
    worker = SolverProcess(value)
    try:
        worker._control_writer.close()
        end = time.monotonic() + 10
        while worker.is_alive() and time.monotonic() < end:
            worker.receive()
            time.sleep(.02)
        assert not worker.is_alive(), 'lost control channel must stop native search'
    finally:
        worker.close()


def test_abrupt_spawned_parent_exit_stops_solver_child():
    from tests.optimization_parent_probe import run_probe
    assert run_probe()['solverExited']


def test_no_candidate_transports_available_german_reasons():
    from dataclasses import replace
    from tests.optimization_fixtures import fixed_session
    from app.services.schedule_generation import PlanningPeriodPlan
    value = problem()
    course = replace(value.courses[0], planning_period=PlanningPeriodPlan(
        value.courses[0].planning_period.start_date, value.courses[0].planning_period.start_date))
    value = replace(value, courses=(course,), fixed_sessions=(fixed_session(cohort_id=1, lecturer_id=1, room_id=1),))
    worker = SolverProcess(value)
    try:
        messages=[];end=time.monotonic()+15
        while time.monotonic()<end:
            messages.extend(worker.receive())
            if any(m['kind']=='timeout' for m in messages):break
            time.sleep(.02)
        timeout=next(m for m in messages if m['kind']=='timeout')
        assert timeout['errors']
        assert any('belegt' in error['message'] for error in timeout['errors'])
    finally:worker.close()


def test_holiday_evidence_message_is_german_for_provisional_and_no_candidate_transport():
    from app.services.holiday_calendar import HolidayReference
    from app.services.semester_optimization import generate_candidates
    value=problem()
    day=value.courses[0].planning_period.start_date
    evidence=generate_candidates(
        value.courses[0],(),frozenset(),{day:HolidayReference(1,day,'Osterferien',1)})
    holiday=next(e for e in evidence.evidence if e.code=='INSTITUTION_HOLIDAY')
    assert 'ausgeschlossen' in holiday.message
    assert day.strftime('%d.%m.%Y') in holiday.message
    assert 'removed an otherwise' not in holiday.message and day.isoformat() not in holiday.message
def test_intensive_detached_input_preserves_exact_windows_and_fixed_teaching_without_orm():
    import pickle
    from datetime import date, time
    from app.services.schedule_generation import TimeWindowPlan
    from app.services.semester_optimization import FixedSession
    from app.services.optimization_worker import DetachedOptimizationInput
    marker = TimeWindowPlan(1,None,time(9),time(12),kind='dated',date=date(2026,9,7),is_intensive=True)
    fixed = FixedSession(99,1,99,99,date(2026,9,7),time(9),time(9,45),units=1,cohort_calendar_id=2,marked_windows=(marker,))
    problem = DetachedOptimizationInput((),(fixed,),(),{},123.0)
    copied = pickle.loads(pickle.dumps(problem))
    assert copied == problem
    assert copied.fixed_sessions[0].marked_windows[0].is_intensive is True

