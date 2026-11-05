"""Standalone real-process owner-loss probe; runnable in Windows and Linux images."""
import ctypes
import multiprocessing
import os
from pathlib import Path
import time

from app.services.optimization_worker import DetachedOptimizationInput, SolverProcess
from tests.optimization_fixtures import optimization_course


def abrupt_parent(pipe):
    problem = DetachedOptimizationInput(
        courses=tuple(optimization_course(i, total_units=80, lecturer_ids=(1, 2), room_ids=(1, 2))
                      for i in range(1, 21)),
        fixed_sessions=(), unavailable_dates=(), holidays={}, deadline=time.monotonic() + 90)
    worker = SolverProcess(problem)
    end = time.monotonic() + 20
    while time.monotonic() < end:
        if any(message.get('phase') == 'optimizing' for message in worker.receive()):
            pipe.send(worker._process.pid)
            pipe.close()
            os._exit(0)  # Bypass Python's normal daemon cleanup deliberately.
        time.sleep(.02)
    worker.close()
    os._exit(2)


def running(pid):
    if os.name == 'nt':
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_ulong]
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        handle = kernel.OpenProcess(0x00100000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 258
        finally:
            kernel.CloseHandle(handle)
    stat = Path(f'/proc/{pid}/stat')
    return stat.exists() and stat.read_text().split(') ')[1][0] != 'Z'


def run_probe():
    context = multiprocessing.get_context('spawn')
    reader, writer = context.Pipe(duplex=False)
    parent = context.Process(target=abrupt_parent, args=(writer,))
    parent.start()
    writer.close()
    try:
        assert reader.poll(25), 'probe parent did not start native search'
        child_pid = reader.recv()
        parent.join(5)
        assert parent.exitcode == 0
        end = time.monotonic() + 10
        while running(child_pid) and time.monotonic() < end:
            time.sleep(.05)
        assert not running(child_pid), f'orphan solver {child_pid} survived owner loss'
        return {'platform': os.name, 'abruptParentExit': True, 'solverExited': True}
    finally:
        reader.close()
        if parent.is_alive():
            parent.terminate()
            parent.join(5)


if __name__ == '__main__':
    import json
    print(json.dumps(run_probe()))
