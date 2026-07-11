from pathlib import Path

import pandas as pd

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportTableRepository
from src.storage.report_table_store import write_report_tables_to_sqlite


def test_write_report_tables_to_sqlite_persists_csv_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "data" / "workbench.sqlite"
    initialize_database(db_path)
    pd.DataFrame([{"symbol": "600519", "name": "贵州茅台"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame([{"symbol": "002115", "review_label": "WATCH_REVIEW"}]).to_csv(
        output_dir / "limit_up_strategy_review.csv", index=False
    )

    written = write_report_tables_to_sqlite(
        output_dir=output_dir,
        db_path=db_path,
        table_files={
            "watchlist": "watchlist.csv",
            "limit_up_strategy_review": "limit_up_strategy_review.csv",
            "missing_table": "missing.csv",
        },
        updated_at="2026-07-11T12:00:00+08:00",
    )

    repo = ReportTableRepository(db_path)
    watchlist = repo.read_table("watchlist")
    review = repo.read_table("limit_up_strategy_review")
    missing = repo.read_table("missing_table")
    assert written == ["watchlist", "limit_up_strategy_review"]
    assert watchlist["rows"][0]["symbol"] == "600519"
    assert review["rows"][0]["review_label"] == "WATCH_REVIEW"
    assert missing["exists"] is False
