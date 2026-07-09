from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportRunRepository


def test_initialize_database_creates_report_runs_table(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"

    initialize_database(db_path)

    assert db_path.exists()
    repo = ReportRunRepository(db_path)
    assert repo.list_runs() == []


def test_report_run_repository_records_and_lists_runs_newest_first(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportRunRepository(db_path)

    first_id = repo.create_run(status="RUNNING", started_at="2026-07-07T01:00:00+00:00")
    repo.finish_run(
        first_id,
        status="SUCCESS",
        finished_at="2026-07-07T01:01:00+00:00",
        message="ok",
    )
    second_id = repo.create_run(status="RUNNING", started_at="2026-07-07T02:00:00+00:00")
    repo.finish_run(
        second_id,
        status="FAILED",
        finished_at="2026-07-07T02:01:00+00:00",
        message="boom",
    )

    runs = repo.list_runs()
    assert [run["id"] for run in runs] == [second_id, first_id]
    assert runs[0]["status"] == "FAILED"
    assert runs[0]["message"] == "boom"
    assert runs[1]["status"] == "SUCCESS"
