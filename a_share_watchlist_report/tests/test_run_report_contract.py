import json
from pathlib import Path

import pandas as pd

import run_report
from src.data.dragon_tiger import empty_dragon_tiger_frame
from src.data.limit_up_pool import empty_limit_up_pool_frame
from src.limit_up_strategy import LIMIT_UP_REVIEW_COLUMNS
from src.portfolio_review import PORTFOLIO_REVIEW_COLUMNS
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
    monkeypatch.setattr(run_report, "fetch_recent_limit_up_pool", lambda: empty_limit_up_pool_frame())

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
        "portfolio_review.csv",
        "market_regime.csv",
        "dragon_tiger.csv",
        "limit_up_pool.csv",
        "limit_up_strategy_review.csv",
        "operations_check.csv",
        "run_manifest.json",
        "artifact_catalog.csv",
        "run_metrics.json",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    assert (output_dir / "watchlist.csv").read_text(encoding="utf-8") == ",".join(WATCHLIST_COLUMNS) + "\n"
    assert (output_dir / "limit_up_strategy_review.csv").read_text(encoding="utf-8") == ",".join(
        LIMIT_UP_REVIEW_COLUMNS
    ) + "\n"
    assert (output_dir / "portfolio_review.csv").read_text(encoding="utf-8") == ",".join(
        PORTFOLIO_REVIEW_COLUMNS
    ) + "\n"

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is False
    manifest = json.loads((output_dir / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["status"] == "DATA_ISSUE"
    run_metrics = json.loads((output_dir / "run_metrics.json").read_text(encoding="utf-8"))
    assert run_metrics["status"] == "DATA_ISSUE"
    operations_check = pd.read_csv(output_dir / "operations_check.csv")
    assert operations_check.loc[operations_check["check_name"] == "数据质量", "status"].item() == "FAIL"
    artifact_catalog = pd.read_csv(output_dir / "artifact_catalog.csv")
    assert "watchlist.csv" in artifact_catalog["filename"].tolist()

    assert (tmp_path / "data" / "cache" / "daily_bars.parquet").exists()
    coverage = json.loads((tmp_path / "data" / "reports" / "data_coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["cached_symbols"] == 0
    assert coverage["failed_symbols"] == ["600519"]

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert "DATA_ISSUE" in report_html
    assert "运行审计" in report_html
    assert "指标快照" in report_html
    assert "产物目录" in report_html
