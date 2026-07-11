from pathlib import Path
from datetime import datetime
import json

import pandas as pd

from backend.db.schema import initialize_database
from src.config_loader import load_config
from src.input_validation import load_holdings, load_universe
from src.data.coverage_report import build_data_coverage_report, write_data_coverage_report
from src.data.data_cache import read_daily_bar_cache, write_daily_bar_cache
from src.data.data_normalizer import empty_daily_bar_frame
from src.data.dragon_tiger import empty_dragon_tiger_frame, fetch_today_dragon_tiger, merge_dragon_tiger_universe
from src.data.limit_up_pool import empty_limit_up_pool_frame, fetch_recent_limit_up_pool, merge_limit_up_universe
from src.data_loader_akshare import build_index_price_cache, build_price_cache
from src.data_quality import DataQualityResult, run_data_quality_checks, write_data_quality_status
from src.market_regime import calculate_market_regime
from src.stock_filters import build_eligible_stocks
from src.stock_ranking import WATCHLIST_COLUMNS, build_watchlist
from src.holding_risk import build_holding_risk
from src.limit_up_strategy import build_limit_up_strategy_review, empty_limit_up_strategy_review_frame
from src.operations import build_artifact_catalog, build_operations_check, build_run_metrics, write_operations_artifacts
from src.portfolio_review import build_portfolio_review, empty_portfolio_review_frame
from src.report_html import render_report
from src.storage.report_table_store import write_report_tables_to_sqlite


ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
OUTPUT_DIR = ROOT / "output"
PRIMARY_OUTPUT_FILES = [
    "report.html",
    "watchlist.csv",
    "excluded_stocks.csv",
    "holding_risk.csv",
    "portfolio_review.csv",
    "market_regime.csv",
    "dragon_tiger.csv",
    "limit_up_pool.csv",
    "limit_up_strategy_review.csv",
    "data_quality_status.json",
]
REPORT_TABLE_FILES = {
    "watchlist": "watchlist.csv",
    "excluded_stocks": "excluded_stocks.csv",
    "holding_risk": "holding_risk.csv",
    "portfolio_review": "portfolio_review.csv",
    "market_regime": "market_regime.csv",
    "dragon_tiger": "dragon_tiger.csv",
    "limit_up_pool": "limit_up_pool.csv",
    "limit_up_strategy_review": "limit_up_strategy_review.csv",
    "operations_check": "operations_check.csv",
    "artifact_catalog": "artifact_catalog.csv",
}


def _empty_frame(columns: list[str]) -> pd.DataFrame:
    return pd.DataFrame(columns=columns)


def _status_dict(result: DataQualityResult) -> dict:
    return {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "excluded_count": int(len(result.excluded)),
    }


def _daily_bar_cache_path() -> Path:
    return DATA_DIR / "cache" / "daily_bars.parquet"


def _data_coverage_report_path() -> Path:
    return DATA_DIR / "reports" / "data_coverage_report.json"


def _workbench_db_path() -> Path:
    return DATA_DIR / "workbench.sqlite"


def _sync_report_tables_to_sqlite() -> list[str]:
    db_path = _workbench_db_path()
    initialize_database(db_path)
    return write_report_tables_to_sqlite(
        OUTPUT_DIR,
        db_path,
        REPORT_TABLE_FILES,
        datetime.now().isoformat(),
    )


def _write_v1_data_artifacts(
    universe: pd.DataFrame,
    daily_bars: pd.DataFrame,
    failed_symbols: list[str] | None = None,
    coverage_frame: pd.DataFrame | None = None,
) -> None:
    write_daily_bar_cache(daily_bars, _daily_bar_cache_path())
    coverage_source = coverage_frame if coverage_frame is not None else daily_bars
    coverage = build_data_coverage_report(universe, coverage_source, failed_symbols)
    write_data_coverage_report(coverage, _data_coverage_report_path())


def _write_empty_v1_data_artifacts_best_effort(universe: pd.DataFrame, status: DataQualityResult) -> None:
    try:
        _write_v1_data_artifacts(universe, empty_daily_bar_frame(), universe["symbol"].astype(str).tolist())
    except Exception as exc:
        status.warnings.append(f"V1 data artifact write failed: {exc}")


def _load_existing_local_cache() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    prices_path = DATA_DIR / "prices.parquet"
    index_prices_path = DATA_DIR / "index_prices.parquet"
    if not prices_path.exists() or not index_prices_path.exists():
        raise FileNotFoundError("local price cache is incomplete")

    prices = pd.read_parquet(prices_path)
    index_prices = pd.read_parquet(index_prices_path)
    daily_bars_path = _daily_bar_cache_path()
    daily_bars = read_daily_bar_cache(daily_bars_path) if daily_bars_path.exists() else empty_daily_bar_frame()
    return prices, index_prices, daily_bars


def _write_operations_outputs(started_at: datetime, data_quality_status: dict) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    finished_at = datetime.now()
    display_files = [filename for filename in PRIMARY_OUTPUT_FILES if filename != "report.html"]
    operations_check = build_operations_check(OUTPUT_DIR, display_files, data_quality_status)
    write_operations_artifacts(OUTPUT_DIR, started_at, finished_at, data_quality_status, PRIMARY_OUTPUT_FILES)
    artifact_files = PRIMARY_OUTPUT_FILES + [
        "operations_check.csv",
        "run_manifest.json",
        "artifact_catalog.csv",
        "run_metrics.json",
    ]
    run_metrics = build_run_metrics(OUTPUT_DIR, data_quality_status, artifact_files)
    artifact_catalog = build_artifact_catalog(OUTPUT_DIR, artifact_files)
    return operations_check, run_metrics, artifact_catalog


def _render_data_issue(
    status: DataQualityResult,
    excluded: pd.DataFrame | None = None,
    started_at: datetime | None = None,
) -> None:
    excluded_frame = excluded if excluded is not None else status.excluded
    write_data_quality_status(status, OUTPUT_DIR / "data_quality_status.json")
    excluded_frame.to_csv(OUTPUT_DIR / "excluded_stocks.csv", index=False)
    empty_dragon_tiger_frame().to_csv(OUTPUT_DIR / "dragon_tiger.csv", index=False)
    empty_limit_up_pool_frame().to_csv(OUTPUT_DIR / "limit_up_pool.csv", index=False)
    empty_limit_up_strategy_review_frame().to_csv(OUTPUT_DIR / "limit_up_strategy_review.csv", index=False)
    empty_portfolio_review_frame().to_csv(OUTPUT_DIR / "portfolio_review.csv", index=False)
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
    operations_check, run_metrics, artifact_catalog = _write_operations_outputs(
        started_at or datetime.now(), _status_dict(status)
    )
    render_report(
        OUTPUT_DIR / "report.html",
        "DATA_ISSUE",
        _empty_frame(["index_name", "close", "ma200", "above_ma200", "return_20d", "status"]),
        None,
        excluded_frame,
        _empty_frame(["risk_action", "reason"]),
        _status_dict(status),
        empty_dragon_tiger_frame(),
        empty_limit_up_strategy_review_frame(),
        empty_portfolio_review_frame(),
        operations_check,
        run_metrics,
        artifact_catalog,
    )
    _sync_report_tables_to_sqlite()
    operations_check, run_metrics, artifact_catalog = _write_operations_outputs(
        started_at or datetime.now(), _status_dict(status)
    )
    render_report(
        OUTPUT_DIR / "report.html",
        "DATA_ISSUE",
        _empty_frame(["index_name", "close", "ma200", "above_ma200", "return_20d", "status"]),
        None,
        excluded_frame,
        _empty_frame(["risk_action", "reason"]),
        _status_dict(status),
        empty_dragon_tiger_frame(),
        empty_limit_up_strategy_review_frame(),
        empty_portfolio_review_frame(),
        operations_check,
        run_metrics,
        artifact_catalog,
    )
    _sync_report_tables_to_sqlite()


def main() -> int:
    started_at = datetime.now()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    config = load_config(ROOT / "config.yaml")
    universe = load_universe(ROOT / "universe.csv", int(config["max_universe_size"]))
    holdings = load_holdings(ROOT / "holdings.csv")
    dragon_tiger_warnings: list[str] = []
    try:
        dragon_tiger = fetch_today_dragon_tiger()
    except Exception as exc:
        dragon_tiger = empty_dragon_tiger_frame()
        dragon_tiger_warnings.append(f"dragon tiger fetch failed: {exc}")
    dragon_tiger.to_csv(OUTPUT_DIR / "dragon_tiger.csv", index=False)
    universe = merge_dragon_tiger_universe(universe, dragon_tiger, int(config["max_universe_size"]))

    limit_up_warnings: list[str] = []
    try:
        limit_up_pool = fetch_recent_limit_up_pool()
    except Exception as exc:
        limit_up_pool = empty_limit_up_pool_frame()
        limit_up_warnings.append(f"limit-up pool fetch failed: {exc}")
    limit_up_pool.to_csv(OUTPUT_DIR / "limit_up_pool.csv", index=False)
    universe = merge_limit_up_universe(universe, limit_up_pool, int(config["max_universe_size"]))

    cache_warning = ""
    try:
        prices = build_price_cache(universe, config, DATA_DIR / "prices.parquet", _daily_bar_cache_path())
        daily_bars = read_daily_bar_cache(_daily_bar_cache_path())
        _write_v1_data_artifacts(universe, daily_bars)
        index_prices = build_index_price_cache(config, DATA_DIR / "index_prices.parquet")
    except Exception as exc:
        try:
            prices, index_prices, daily_bars = _load_existing_local_cache()
            coverage_frame = prices if daily_bars.empty else daily_bars
            _write_v1_data_artifacts(universe, daily_bars, coverage_frame=coverage_frame)
            cache_warning = f"live data fetch failed: {exc}; using existing local cache"
        except Exception:
            status = DataQualityResult(False, [f"data fetch failed: {exc}"], [], _empty_frame(
                ["symbol", "name", "industry", "exclude_reason", "last_price_date", "avg_amount_20d", "history_days"]
            ))
            _write_empty_v1_data_artifacts_best_effort(universe, status)
            _render_data_issue(status, started_at=started_at)
            print("Generated output/report.html")
            print("Generated output/watchlist.csv")
            print("Generated output/excluded_stocks.csv")
            print("Generated output/holding_risk.csv")
            print("Generated output/portfolio_review.csv")
            print("Generated output/market_regime.csv")
            print("Generated output/operations_check.csv")
            print("Generated output/run_manifest.json")
            print("Generated output/artifact_catalog.csv")
            print("Generated output/run_metrics.json")
            print("Generated output/data_quality_status.json")
            return 0

    data_quality = run_data_quality_checks(prices, universe, config)
    data_quality.warnings.extend(dragon_tiger_warnings)
    data_quality.warnings.extend(limit_up_warnings)
    if cache_warning:
        data_quality.warnings.append(cache_warning)
    write_data_quality_status(data_quality, OUTPUT_DIR / "data_quality_status.json")
    data_quality.excluded.to_csv(OUTPUT_DIR / "excluded_stocks.csv", index=False)

    if not data_quality.ok:
        _render_data_issue(data_quality, data_quality.excluded, started_at=started_at)
        print("Generated output/report.html")
        print("Generated output/watchlist.csv")
        print("Generated output/excluded_stocks.csv")
        print("Generated output/holding_risk.csv")
        print("Generated output/portfolio_review.csv")
        print("Generated output/market_regime.csv")
        print("Generated output/operations_check.csv")
        print("Generated output/run_manifest.json")
        print("Generated output/artifact_catalog.csv")
        print("Generated output/run_metrics.json")
        print("Generated output/data_quality_status.json")
        return 0

    market_regime, market_evidence = calculate_market_regime(index_prices, config)
    market_evidence.to_csv(OUTPUT_DIR / "market_regime.csv", index=False)

    limit_up_strategy_review = build_limit_up_strategy_review(limit_up_pool, prices, market_evidence)
    limit_up_strategy_review.to_csv(OUTPUT_DIR / "limit_up_strategy_review.csv", index=False)

    eligible = build_eligible_stocks(prices, universe, data_quality.excluded, config)
    watchlist = build_watchlist(prices, eligible, config)
    watchlist.to_csv(OUTPUT_DIR / "watchlist.csv", index=False)

    holding_risk = build_holding_risk(holdings, prices, universe, data_quality.excluded, config)
    holding_risk.to_csv(OUTPUT_DIR / "holding_risk.csv", index=False)

    portfolio_review = build_portfolio_review(holding_risk, universe)
    portfolio_review.to_csv(OUTPUT_DIR / "portfolio_review.csv", index=False)

    operations_check, run_metrics, artifact_catalog = _write_operations_outputs(started_at, _status_dict(data_quality))
    render_report(
        OUTPUT_DIR / "report.html",
        market_regime,
        market_evidence,
        watchlist,
        data_quality.excluded,
        holding_risk,
        _status_dict(data_quality),
        dragon_tiger,
        limit_up_strategy_review,
        portfolio_review,
        operations_check,
        run_metrics,
        artifact_catalog,
    )
    _sync_report_tables_to_sqlite()
    operations_check, run_metrics, artifact_catalog = _write_operations_outputs(started_at, _status_dict(data_quality))
    render_report(
        OUTPUT_DIR / "report.html",
        market_regime,
        market_evidence,
        watchlist,
        data_quality.excluded,
        holding_risk,
        _status_dict(data_quality),
        dragon_tiger,
        limit_up_strategy_review,
        portfolio_review,
        operations_check,
        run_metrics,
        artifact_catalog,
    )
    _sync_report_tables_to_sqlite()

    print("Generated output/report.html")
    print("Generated output/watchlist.csv")
    print("Generated output/excluded_stocks.csv")
    print("Generated output/holding_risk.csv")
    print("Generated output/portfolio_review.csv")
    print("Generated output/market_regime.csv")
    print("Generated output/operations_check.csv")
    print("Generated output/run_manifest.json")
    print("Generated output/artifact_catalog.csv")
    print("Generated output/run_metrics.json")
    print("Generated output/data_quality_status.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
