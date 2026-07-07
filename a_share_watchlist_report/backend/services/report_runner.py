from collections.abc import Callable
from pathlib import Path
from threading import Lock

import run_report


class ReportRunner:
    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._lock = Lock()

    def __call__(self) -> int:
        with self._lock:
            return self._run_once()

    def _run_once(self) -> int:
        original_root = run_report.ROOT
        original_data_dir = run_report.DATA_DIR
        original_output_dir = run_report.OUTPUT_DIR
        try:
            run_report.ROOT = self.root
            run_report.DATA_DIR = self.root / "data"
            run_report.OUTPUT_DIR = self.root / "output"
            return run_report.main()
        finally:
            run_report.ROOT = original_root
            run_report.DATA_DIR = original_data_dir
            run_report.OUTPUT_DIR = original_output_dir


def resolve_runner(root: Path, runner: Callable[[], int] | None = None) -> Callable[[], int]:
    if runner is not None:
        return runner
    return ReportRunner(root)
