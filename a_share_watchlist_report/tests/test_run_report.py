import json
from pathlib import Path

import pandas as pd

import run_report


def _write_inputs(root: Path, holdings_text: str = "symbol,shares,cost_basis\n") -> None:
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
    (root / "holdings.csv").write_text(holdings_text, encoding="utf-8")


def _stock_prices(symbol: str = "600519") -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=260, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "close": [100.0 + day * 0.2 for day in range(260)],
            "amount": [100_000_000.0 for _ in range(260)],
        }
    )


def _index_prices(index_name: str = "沪深300", index_code: str = "000300") -> pd.DataFrame:
    dates = pd.date_range("2025-01-01", periods=220, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "index_name": index_name,
            "index_code": index_code,
            "close": [100.0 + day * 0.1 for day in range(220)],
        }
    )


def test_data_issue_path_writes_empty_watchlist_csv(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root)

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fail_fetch(universe: pd.DataFrame, config: dict, output_path: str | Path) -> pd.DataFrame:
        raise RuntimeError("synthetic fetch failure")

    monkeypatch.setattr(run_report, "build_price_cache", fail_fetch)

    assert run_report.main() == 0

    output_dir = root / "output"
    for filename in [
        "report.html",
        "watchlist.csv",
        "excluded_stocks.csv",
        "holding_risk.csv",
        "market_regime.csv",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    watchlist_path = output_dir / "watchlist.csv"
    assert watchlist_path.exists()
    assert watchlist_path.read_text(encoding="utf-8").startswith("symbol,name,industry,close")

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is False

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert "DATA_ISSUE" in report_html


def test_success_path_writes_observation_report(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root, "symbol,shares,cost_basis\n600519,100,90\n")

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fake_build_price_cache(universe: pd.DataFrame, config: dict, output_path: str | Path) -> pd.DataFrame:
        prices = _stock_prices()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        prices.to_parquet(output_path, index=False)
        return prices

    def fake_build_index_price_cache(config: dict, output_path: str | Path) -> pd.DataFrame:
        index_prices = _index_prices()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        index_prices.to_parquet(output_path, index=False)
        return index_prices

    monkeypatch.setattr(run_report, "build_price_cache", fake_build_price_cache)
    monkeypatch.setattr(run_report, "build_index_price_cache", fake_build_index_price_cache)

    assert run_report.main() == 0

    output_dir = root / "output"
    for filename in [
        "report.html",
        "watchlist.csv",
        "excluded_stocks.csv",
        "holding_risk.csv",
        "market_regime.csv",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is True

    watchlist = pd.read_csv(output_dir / "watchlist.csv", dtype={"symbol": "string"})
    assert watchlist.loc[0, "symbol"] == "600519"
    assert "12M 动量" in watchlist.loc[0, "reason"]
    assert "20 日平均成交额" in watchlist.loc[0, "reason"]

    market_regime = pd.read_csv(output_dir / "market_regime.csv")
    assert market_regime.loc[0, "status"] == "POSITIVE"

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    for label in [
        "Market regime",
        "Risk exposure review",
        "Watchlist Top 20",
        "Excluded Stocks",
        "Holding Risk Review",
        "Data Quality Status",
    ]:
        assert label in report_html
    assert "DATA_ISSUE" not in report_html
