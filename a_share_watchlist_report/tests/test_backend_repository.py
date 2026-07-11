from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportRunRepository, ReportTableRepository


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


def test_report_table_repository_replaces_table_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportTableRepository(db_path)

    repo.replace_table(
        "watchlist",
        columns=["symbol", "name", "score"],
        rows=[
            {"symbol": "600519", "name": "贵州茅台", "score": "1.25"},
            {"symbol": "300750", "name": "宁德时代", "score": None},
        ],
        updated_at="2026-07-11T10:00:00+08:00",
    )
    repo.replace_table(
        "watchlist",
        columns=["symbol", "name", "score"],
        rows=[{"symbol": "000001", "name": "平安银行", "score": "0.50"}],
        updated_at="2026-07-11T10:01:00+08:00",
    )

    table = repo.read_table("watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is True
    assert table["columns"] == ["symbol", "name", "score"]
    assert table["row_count"] == 1
    assert table["rows"] == [{"symbol": "000001", "name": "平安银行", "score": "0.50"}]
    assert table["source"] == "sqlite"


def test_report_table_repository_reports_missing_snapshot(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportTableRepository(db_path)

    table = repo.read_table("watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is False
    assert table["columns"] == []
    assert table["row_count"] == 0
    assert table["rows"] == []


def test_report_table_repository_filters_sorts_and_paginates_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportTableRepository(db_path)
    repo.replace_table(
        "limit_up_strategy_review",
        columns=["symbol", "name", "review_score", "review_label"],
        rows=[
            {"symbol": "600519", "name": "贵州茅台", "review_score": "70", "review_label": "RISK_REVIEW"},
            {"symbol": "002115", "name": "三维通信", "review_score": "89", "review_label": "WATCH_REVIEW"},
            {"symbol": "300750", "name": "宁德时代", "review_score": "80", "review_label": "WATCH_REVIEW"},
        ],
        updated_at="2026-07-11T10:02:00+08:00",
    )

    table = repo.read_table(
        "limit_up_strategy_review",
        limit=1,
        offset=1,
        search="WATCH",
        sort_by="review_score",
        sort_dir="desc",
    )

    assert table["row_count"] == 3
    assert table["filtered_count"] == 2
    assert table["limit"] == 1
    assert table["offset"] == 1
    assert table["rows"] == [
        {"symbol": "300750", "name": "宁德时代", "review_score": "80", "review_label": "WATCH_REVIEW"}
    ]
