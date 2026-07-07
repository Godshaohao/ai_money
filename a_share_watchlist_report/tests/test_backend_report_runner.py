from pathlib import Path

from backend.services.report_runner import ReportRunner


def test_report_runner_has_internal_lock(tmp_path: Path) -> None:
    runner = ReportRunner(tmp_path)

    assert runner._lock.acquire(blocking=False)
    try:
        assert not runner._lock.acquire(blocking=False)
    finally:
        runner._lock.release()
