from pathlib import Path

import pandas as pd
import pytest

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
