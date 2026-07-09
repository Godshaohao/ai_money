import json
from pathlib import Path

import pandas as pd

import run_report
from src.data.data_cache import write_daily_bar_cache
from src.data.dragon_tiger import empty_dragon_tiger_frame
from src.data.limit_up_pool import empty_limit_up_pool_frame


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


def _daily_bars(symbol: str = "600519") -> pd.DataFrame:
    prices = _stock_prices(symbol)
    return pd.DataFrame(
        {
            "date": prices["date"],
            "symbol": prices["symbol"],
            "name": "贵州茅台",
            "industry": "食品饮料",
            "open": prices["close"],
            "high": prices["close"],
            "low": prices["close"],
            "close": prices["close"],
            "amount": prices["amount"],
            "volume": [1_000_000.0 for _ in range(len(prices))],
            "source": "akshare",
            "adjust": "qfq",
            "updated_at": "2026-01-01T00:00:00+00:00",
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


def _disable_event_pools(monkeypatch) -> None:
    monkeypatch.setattr(run_report, "fetch_today_dragon_tiger", lambda: empty_dragon_tiger_frame())
    monkeypatch.setattr(run_report, "fetch_recent_limit_up_pool", lambda: empty_limit_up_pool_frame())


def test_data_issue_path_writes_empty_watchlist_csv(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root)
    _disable_event_pools(monkeypatch)

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fail_fetch(
        universe: pd.DataFrame,
        config: dict,
        output_path: str | Path,
        daily_bar_output_path: str | Path | None = None,
    ) -> pd.DataFrame:
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
        "dragon_tiger.csv",
        "limit_up_pool.csv",
        "limit_up_strategy_review.csv",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    watchlist_path = output_dir / "watchlist.csv"
    assert watchlist_path.exists()
    assert watchlist_path.read_text(encoding="utf-8").startswith("symbol,name,industry,close")

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is False

    coverage = json.loads((root / "data" / "reports" / "data_coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["cached_symbols"] == 0
    assert coverage["failed_symbols"] == ["600519"]
    assert (root / "data" / "cache" / "daily_bars.parquet").exists()

    report_html = (output_dir / "report.html").read_text(encoding="utf-8")
    assert "DATA_ISSUE" in report_html


def test_success_path_writes_observation_report(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root, "symbol,shares,cost_basis\n600519,100,90\n")
    _disable_event_pools(monkeypatch)

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fake_build_price_cache(
        universe: pd.DataFrame,
        config: dict,
        output_path: str | Path,
        daily_bar_output_path: str | Path | None = None,
    ) -> pd.DataFrame:
        prices = _stock_prices()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        prices.to_parquet(output_path, index=False)
        if daily_bar_output_path is not None:
            write_daily_bar_cache(_daily_bars(), daily_bar_output_path)
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
        "dragon_tiger.csv",
        "limit_up_pool.csv",
        "limit_up_strategy_review.csv",
        "data_quality_status.json",
    ]:
        assert (output_dir / filename).exists()

    status = json.loads((output_dir / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is True

    coverage = json.loads((root / "data" / "reports" / "data_coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["total_symbols"] == 1
    assert coverage["cached_symbols"] == 1
    assert (root / "data" / "cache" / "daily_bars.parquet").exists()

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
        "Dragon Tiger List",
        "Data Quality Status",
    ]:
        assert label in report_html
    assert "DATA_ISSUE" not in report_html


def test_live_fetch_failure_uses_existing_local_cache(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root, "symbol,shares,cost_basis\n600519,100,90\n")
    _disable_event_pools(monkeypatch)
    data_dir = root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    _stock_prices().to_parquet(data_dir / "prices.parquet", index=False)
    _index_prices().to_parquet(data_dir / "index_prices.parquet", index=False)

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", data_dir)
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")

    def fail_live_fetch(
        universe: pd.DataFrame,
        config: dict,
        output_path: str | Path,
        daily_bar_output_path: str | Path | None = None,
    ) -> pd.DataFrame:
        raise RuntimeError("synthetic live fetch failure")

    monkeypatch.setattr(run_report, "build_price_cache", fail_live_fetch)

    assert run_report.main() == 0

    status = json.loads((root / "output" / "data_quality_status.json").read_text(encoding="utf-8"))
    assert status["ok"] is True
    assert "using existing local cache" in status["warnings"][0]

    coverage = json.loads((root / "data" / "reports" / "data_coverage_report.json").read_text(encoding="utf-8"))
    assert coverage["cached_symbols"] == 1
    assert coverage["missing_symbols"] == []
    assert (root / "data" / "cache" / "daily_bars.parquet").exists()

    report_html = (root / "output" / "report.html").read_text(encoding="utf-8")
    assert "DATA_ISSUE" not in report_html
    assert "Watchlist Top 20" in report_html


def test_success_path_adds_dragon_tiger_symbols_to_universe(tmp_path: Path, monkeypatch) -> None:
    root = tmp_path
    _write_inputs(root)

    monkeypatch.setattr(run_report, "ROOT", root)
    monkeypatch.setattr(run_report, "DATA_DIR", root / "data")
    monkeypatch.setattr(run_report, "OUTPUT_DIR", root / "output")
    monkeypatch.setattr(
        run_report,
        "fetch_today_dragon_tiger",
        lambda: pd.DataFrame(
            [
                {
                    "symbol": "000001",
                    "name": "平安银行",
                    "trade_date": "2026-07-07",
                    "close": 12.34,
                    "change_pct": 10.0,
                    "net_buy_amount": 1_000_000.0,
                    "buy_amount": 2_000_000.0,
                    "sell_amount": 1_000_000.0,
                    "deal_amount": 3_000_000.0,
                    "turnover_rate": 8.8,
                    "reason": "日涨幅偏离值达7%",
                    "source": "akshare_eastmoney_lhb",
                }
            ]
        ),
    )
    monkeypatch.setattr(run_report, "fetch_recent_limit_up_pool", lambda: empty_limit_up_pool_frame())

    seen_symbols: list[str] = []

    def fake_build_price_cache(
        universe: pd.DataFrame,
        config: dict,
        output_path: str | Path,
        daily_bar_output_path: str | Path | None = None,
    ) -> pd.DataFrame:
        seen_symbols.extend(universe["symbol"].astype(str).tolist())
        prices = pd.concat([_stock_prices("600519"), _stock_prices("000001")], ignore_index=True)
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        prices.to_parquet(output_path, index=False)
        if daily_bar_output_path is not None:
            daily_bars = pd.concat([_daily_bars("600519"), _daily_bars("000001")], ignore_index=True)
            write_daily_bar_cache(daily_bars, daily_bar_output_path)
        return prices

    def fake_build_index_price_cache(config: dict, output_path: str | Path) -> pd.DataFrame:
        index_prices = _index_prices()
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        index_prices.to_parquet(output_path, index=False)
        return index_prices

    monkeypatch.setattr(run_report, "build_price_cache", fake_build_price_cache)
    monkeypatch.setattr(run_report, "build_index_price_cache", fake_build_index_price_cache)

    assert run_report.main() == 0

    assert seen_symbols == ["600519", "000001"]
    dragon_tiger = pd.read_csv(root / "output" / "dragon_tiger.csv", dtype={"symbol": "string"})
    assert dragon_tiger.loc[0, "symbol"] == "000001"
    assert "平安银行" in (root / "output" / "report.html").read_text(encoding="utf-8")
