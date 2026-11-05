"""Spawn-safe solver boundary. Only detached planning values cross this pipe."""
from dataclasses import dataclass
from datetime import date
import multiprocessing
from threading import Thread
from time import monotonic

from app.services.holiday_calendar import HolidayReference
from app.services.semester_optimization import (
    FixedSession, OptimizationCourse, OptimalResultNotProven,
    OptimizationModelInvalid, NoGeneratedAlternative, optimize_semester,
    OptimizationSearchControl, OptimizationCancelled,
)


@dataclass(frozen=True)
class DetachedOptimizationInput:
    courses: tuple[OptimizationCourse, ...]
    fixed_sessions: tuple[FixedSession, ...]
    unavailable_dates: tuple[date, ...]
    holidays: dict[date, HolidayReference]
    deadline: float
    generated_only: bool = True


def _solve(problem: DetachedOptimizationInput, output, stop, control):
    """No engine, session, ORM records or application callback supplied by parent."""
    def observe_owner():
        parent = multiprocessing.parent_process()
        while not stop.is_set():
            try:
                if control.poll(.05):
                    control.recv()
                if parent is not None and not parent.is_alive():
                    stop.set()
            except (EOFError, OSError):
                stop.set()
    Thread(target=observe_owner, daemon=True).start()
    try:
        remaining = problem.deadline - monotonic()
        if stop.is_set() or remaining <= 0:
            output.send({"kind": "timeout", "budgetExhausted": remaining <= 0})
            return
        output.send({"kind": "phase", "phase": "optimizing"})
        result = optimize_semester(
            problem.courses, problem.fixed_sessions, problem.unavailable_dates,
            holidays=problem.holidays, deadline_seconds=remaining,
            generated_only=problem.generated_only,
            allow_unproven=True,
            control=OptimizationSearchControl(
                deadline=problem.deadline, cancelled=stop.is_set,
                progress=lambda objective: output.send({"kind": "objective", "objectiveKey": objective}),
                checkpoint=lambda candidate: output.send({"kind": "checkpoint", "result": candidate}),
            ),
        )
        if not stop.is_set():
            output.send({"kind": "result", "result": result})
    except OptimizationCancelled:
        pass
    except NoGeneratedAlternative as exc:
        output.send({"kind": "timeout", "budgetExhausted": monotonic() >= problem.deadline,
            "errors": [{"code": reason.code, "message": f"Lehrveranstaltung #{course.course_id}: {reason.message}"}
                for course in exc.courses for reason in course.evidence]})
    except OptimalResultNotProven:
        output.send({"kind": "timeout", "budgetExhausted": monotonic() >= problem.deadline})
    except OptimizationModelInvalid:
        output.send({"kind": "failed", "code": "OPTIMIZATION_MODEL_INVALID"})
    except (BrokenPipeError, EOFError, OSError):
        pass
    except Exception:
        # Do not serialize exception text or arbitrary inputs across the boundary.
        try:
            output.send({"kind": "failed", "code": "OPTIMIZATION_OPERATION_FAILED"})
        except (BrokenPipeError, EOFError, OSError):
            pass
    finally:
        stop.set()
        control.close()
        output.close()


class SolverProcess:
    def __init__(self, problem: DetachedOptimizationInput):
        context = multiprocessing.get_context("spawn")
        self._reader, writer = context.Pipe(duplex=False)
        control_reader, self._control_writer = context.Pipe(duplex=False)
        self._stop = context.Event()
        self._closed = False
        self._process = context.Process(target=_solve, args=(problem, writer, self._stop, control_reader), daemon=True)
        try:
            self._process.start()
        except BaseException:
            self._reader.close()
            self._control_writer.close()
            raise
        finally:
            writer.close()
            control_reader.close()

    def receive(self) -> list[dict]:
        messages = []
        if self._closed:
            return messages
        try:
            while self._reader.poll():
                messages.append(self._reader.recv())
        except (EOFError, OSError):
            pass
        return messages

    def is_alive(self) -> bool:
        return self._process.is_alive()

    def close(self):
        if self._closed:
            return
        self._closed = True
        self._stop.set()
        self._control_writer.close()
        self._process.join(timeout=.2)
        if self._process.is_alive():
            self._process.terminate()
            self._process.join(timeout=2)
        if self._process.is_alive():
            self._process.kill()
            self._process.join(timeout=2)
        self._reader.close()
