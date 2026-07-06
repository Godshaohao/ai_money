from pathlib import Path
from datetime import datetime
import json

import pandas as pd

from src.config_loader import load_config
from src.input_validation import load_holdings, load_universe
from src.data_loader_akshare import build_index_price_cache, build_price_cache
from src.data_quality import DataQualityResult, run_data_quality_checks, write_data_quality_status
from src.market_regime import calculate_market_regime
from src.stock_filters import build_eligible_stocks
from src.stock_ranking import WATCHLIST_COLUMNS, build_watchlist
from src.holding_risk import build_holding_risk
from src.report_html import render_report


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _status_dict(result: DataQualityResult) -> dict:
    return {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "excluded_count": int(len(result.excluded)),
    }


def _render_data_issue(status: DataQualityResult, excluded: pd.DataFrame | None = None) -> None:
    excluded_frame = excluded if excluded is not None else status.excluded
    write_data_quality_status(status, OUTPUT_DIR / "data_quality_status.json")
    excluded_frame.to_csv(OUTPUT_DIR / "excluded_stocks.csv", index=False)
    _empty_frame(["index_name", "close", "ma200", "above_ma200", "return_20d", "status"]).to_csv(
        OUTPUT_DIR / "market_regime.csv", index=False
    )
    _empty_frame(WATCHLIST_COLUMNS).to_csv(OUTPUT_DIR / "watchlist.csv", index=False)
    _empty_frame(
        [
            "symbol",
            "name",
            "shares",
            "cost_basis",
            "latest_close",
            "drawdown_from_cost",
            "above_ma200",
            "max_drawdown_60d",
            "avg_amount_20d",
            "risk_action",
            "reason",
        ]
    ).to_csv(OUTPUT_DIR / "holding_risk.csv", index=False)
    render_report(
        OUTPUT_DIR / "report.html",
        "DATA_ISSUE",
        _empty_frame(["index_name", "close", "ma200", "above_ma200", "return_20d", "status"]),
        None,
        excluded_frame,
        _empty_frame(["risk_action", "reason"]),
        _status_dict(status),
    )


def main() -> int:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = load_config(ROOT / "config.yaml")
    universe = load_universe(ROOT / "universe.csv", int(config["max_universe_size"]))
    holdings = load_holdings(ROOT / "holdings.csv")

    try:
        prices = build_price_cache(universe, config, DATA_DIR / "prices.parquet")
        index_prices = build_index_price_cache(config, DATA_DIR / "index_prices.parquet")
    except Exception as exc:
        status = DataQualityResult(False, [f"data fetch failed: {exc}"], [], _empty_frame(
            ["symbol", "name", "industry", "exclude_reason", "last_price_date", "avg_amount_20d", "history_days"]
        ))
        _render_data_issue(status)
        print("Generated output/report.html")
        print("Generated output/watchlist.csv")
        print("Generated output/excluded_stocks.csv")
        print("Generated output/holding_risk.csv")
        print("Generated output/market_regime.csv")
        print("Generated output/data_quality_status.json")
        return 0

    data_quality = run_data_quality_checks(prices, universe, config)
    write_data_quality_status(data_quality, OUTPUT_DIR / "data_quality_status.json")
    data_quality.excluded.to_csv(OUTPUT_DIR / "excluded_stocks.csv", index=False)

    if not data_quality.ok:
        _render_data_issue(data_quality, data_quality.excluded)
        print("Generated output/report.html")
        print("Generated output/watchlist.csv")
        print("Generated output/excluded_stocks.csv")
        print("Generated output/holding_risk.csv")
        print("Generated output/market_regime.csv")
        print("Generated output/data_quality_status.json")
        return 0

    market_regime, market_evidence = calculate_market_regime(index_prices, config)
    market_evidence.to_csv(OUTPUT_DIR / "market_regime.csv", index=False)

    eligible = build_eligible_stocks(prices, universe, data_quality.excluded, config)
    watchlist = build_watchlist(prices, eligible, config)
    watchlist.to_csv(OUTPUT_DIR / "watchlist.csv", index=False)

    holding_risk = build_holding_risk(holdings, prices, universe, data_quality.excluded, config)
    holding_risk.to_csv(OUTPUT_DIR / "holding_risk.csv", index=False)

    render_report(
        OUTPUT_DIR / "report.html",
        market_regime,
        market_evidence,
        watchlist,
        data_quality.excluded,
        holding_risk,
        _status_dict(data_quality),
    )

    print("Generated output/report.html")
    print("Generated output/watchlist.csv")
    print("Generated output/excluded_stocks.csv")
    print("Generated output/holding_risk.csv")
    print("Generated output/market_regime.csv")
    print("Generated output/data_quality_status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
