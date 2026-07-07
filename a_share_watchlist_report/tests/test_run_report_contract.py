import json
from pathlib import Path

import pandas as pd

import run_report
from src.data.dragon_tiger import empty_dragon_tiger_frame
from src.stock_ranking import WATCHLIST_COLUMNS


def _write_minimal_inputs(root: Path) -> None:
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
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "universe.csv").write_text(
        "symbol,name,industry\n600519,贵州茅台,食品饮料\n",
        encoding="utf-8",
    )
    (root / "holdings.csv").write_text(
        "symbol,shares,cost_basis\n",
        encoding="utf-8",
    )


def test_data_fetch_failure_writes_complete_fail_closed_outputs(tmp_path: Path, monkeypatch) -> None:
    _write_minimal_inputs(tmp_path)
    monkeypatch.setattr(run_report, "ROOT", tmp_path)
    monkeypatch.setattr(run_report, "DATA_DIR", tmp_path / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", tmp_path / "output")
    monkeypatch.setattr(run_report, "fetch_today_dragon_tiger", lambda: empty_dragon_tiger_frame())

    def fail_price_fetch(
        universe: pd.DataFrame,
        config: dict,
        output_path: str | Path,
        daily_bar_output_path: str | Path | None = None,
    ) -> pd.DataFrame:
        raise RuntimeError("synthetic data fetch failure")

    monkeypatch.setattr(run_report, "build_price_cache", fail_price_fetch)

    assert run_report.main() == 0

    output_dir = tmp_path / "output"
    for filename in [
        "report.html",
        "watchlist.csv",
        "excluded_stocks.csv",
        "holding_risk.csv",
        "market_regime.csv",
        "dragon_tiger.csv",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    assert (output_dir / "watchlist.csv").read_text(encoding="utf-8") == ",".join(WATCHLIST_COLUMNS) + "\n"

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is False

    assert (tmp_path / "data" / "cache" / "daily_bars.parquet").exists()
    coverage = json.loads((tmp_path / "data" / "reports" / "data_coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["cached_symbols"] == 0
    assert coverage["failed_symbols"] == ["600519"]

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert "DATA_ISSUE" in report_html
