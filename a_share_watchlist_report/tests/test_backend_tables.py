from pathlib import Path

import pandas as pd
import pytest

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportTableRepository
from backend.services.tables import read_report_table


def test_read_report_table_returns_rows_and_columns(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "score": 1.25},
            {"symbol": "300750", "name": "宁德时代", "score": None},
        ]
    ).to_csv(output_dir / "watchlist.csv", index=False)

    table = read_report_table(output_dir, "watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is True
    assert table["columns"] == ["symbol", "name", "score"]
    assert table["row_count"] == 2
    assert table["rows"][0]["symbol"] == "600519"
    assert table["rows"][1]["score"] is None


def test_read_report_table_prefers_sqlite_snapshot_when_available(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "CSV_ONLY", "name": "旧文件"}]).to_csv(output_dir / "watchlist.csv", index=False)
    db_path = tmp_path / "data" / "workbench.sqlite"
    initialize_database(db_path)
    ReportTableRepository(db_path).replace_table(
        "watchlist",
        columns=["symbol", "name"],
        rows=[{"symbol": "DB_ONLY", "name": "数据库"}],
        updated_at="2026-07-11T13:00:00+08:00",
    )

    table = read_report_table(output_dir, "watchlist", db_path=db_path)

    assert table["exists"] is True
    assert table["source"] == "sqlite"
    assert table["rows"][0]["symbol"] == "DB_ONLY"


def test_read_report_table_passes_query_options_to_sqlite(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "data" / "workbench.sqlite"
    initialize_database(db_path)
    ReportTableRepository(db_path).replace_table(
        "watchlist",
        columns=["symbol", "name", "score"],
        rows=[
            {"symbol": "600519", "name": "贵州茅台", "score": "70"},
            {"symbol": "002115", "name": "三维通信", "score": "89"},
        ],
        updated_at="2026-07-11T13:00:00+08:00",
    )

    table = read_report_table(output_dir, "watchlist", limit=1, offset=0, search="通信", sort_by="score", sort_dir="desc", db_path=db_path)

    assert table["source"] == "sqlite"
    assert table["filtered_count"] == 1
    assert table["rows"][0]["symbol"] == "002115"


def test_read_report_table_reports_missing_file(tmp_path: Path) -> None:
    table = read_report_table(tmp_path / "output", "watchlist")

    assert table["name"] == "watchlist"
    assert table["exists"] is False
    assert table["rows"] == []
    assert table["errors"]


def test_read_report_table_rejects_unknown_table(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown report table"):
        read_report_table(tmp_path / "output", "orders")


def test_read_report_table_supports_limit_up_strategy_review(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519", "review_label": "CORE_REVIEW"}]).to_csv(
        output_dir / "limit_up_strategy_review.csv", index=False
    )

    table = read_report_table(output_dir, "limit_up_strategy_review")

    assert table["exists"] is True
    assert table["rows"][0]["review_label"] == "CORE_REVIEW"


def test_read_report_table_supports_portfolio_review(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519", "portfolio_weight": 0.45}]).to_csv(
        output_dir / "portfolio_review.csv", index=False
    )

    table = read_report_table(output_dir, "portfolio_review")

    assert table["exists"] is True
    assert table["rows"][0]["symbol"] == "600519"


def test_read_report_table_supports_operations_check(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"check_name": "数据质量", "status": "PASS", "severity": "P0", "detail": "通过"}]).to_csv(
        output_dir / "operations_check.csv", index=False
    )

    table = read_report_table(output_dir, "operations_check")

    assert table["exists"] is True
    assert table["rows"][0]["check_name"] == "数据质量"


def test_read_report_table_supports_artifact_catalog(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"artifact_name": "watchlist", "filename": "watchlist.csv"}]).to_csv(
        output_dir / "artifact_catalog.csv", index=False
    )

    table = read_report_table(output_dir, "artifact_catalog")

    assert table["exists"] is True
    assert table["rows"][0]["filename"] == "watchlist.csv"
