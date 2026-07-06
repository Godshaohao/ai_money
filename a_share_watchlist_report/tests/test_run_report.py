import json
from pathlib import Path

import pandas as pd

import run_report


def test_data_issue_path_writes_empty_watchlist_csv(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    (root / "config.yaml").write_text(
        "\n".join(
            [
                "max_universe_size: 100",
                "top_n_watchlist: 20",
                "market_indices:",
                '  沪深300: "000300"',
                'start_date: "20180101"',
                "trend_ma_days: 200",
                "short_trend_days: 20",
                "momentum_12m_days: 252",
                "momentum_6m_days: 126",
                "max_drawdown_days: 60",
                "min_listing_days: 250",
                "min_avg_amount_20d: 50000000",
                "max_missing_days: 5",
            ]
        ),
        encoding="utf-8",
    )
    (root / "universe.csv").write_text("symbol,name,industry\n600519,贵州茅台,食品饮料\n", encoding="utf-8")
    (root / "holdings.csv").write_text("symbol,shares,cost_basis\n", encoding="utf-8")

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fail_fetch(universe: pd.DataFrame, config: dict, output_path: str | Path) -> pd.DataFrame:
        raise RuntimeError("synthetic fetch failure")

    monkeypatch.setattr(run_report, "build_price_cache", fail_fetch)

    assert run_report.main() == 0

    watchlist_path = root / "output" / "watchlist.csv"
    assert watchlist_path.exists()
    assert watchlist_path.read_text(encoding="utf-8").startswith("symbol,name,industry,close")

    status = json.loads((root / "output" / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is False
