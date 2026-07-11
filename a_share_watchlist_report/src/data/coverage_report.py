from pathlib import Path
import json

import pandas as pd

from src.schemas import DATA_COVERAGE_KEYS


def _symbol_series(frame: pd.DataFrame) -> pd.Series:
    return frame["symbol"].astype(str).str.strip().str.zfill(6)


def build_data_coverage_report(
    universe: pd.DataFrame,
    daily_bars: pd.DataFrame,
    failed_symbols: list[str] | None = None,
) -> dict:
    expected_symbols = list(dict.fromkeys(_symbol_series(universe).tolist()))
    expected_set = set(expected_symbols)
    failed = sorted({str(symbol).strip().zfill(6) for symbol in (failed_symbols or []) if str(symbol).strip()})

    if daily_bars.empty or "symbol" not in daily_bars.columns or "date" not in daily_bars.columns:
        report = {
            "total_symbols": len(expected_symbols),
            "cached_symbols": 0,
            "latest_date": "",
            "missing_symbols": expected_symbols,
            "stale_symbols": [],
            "failed_symbols": failed,
        }
        return {key: report[key] for key in DATA_COVERAGE_KEYS}

    normalized = daily_bars.copy()
    normalized["symbol"] = _symbol_series(normalized)
    normalized = normalized.loc[normalized["symbol"].isin(expected_set)].copy()
    normalized["date"] = pd.to_datetime(
        normalized["date"].astype(str).str.slice(0, 10),
        errors="coerce",
        format="%Y-%m-%d",
    )
    normalized = normalized.dropna(subset=["date"])

    if normalized.empty:
        latest_date = ""
        cached_symbols: list[str] = []
        stale_symbols: list[str] = []
    else:
        latest_ts = normalized["date"].max()
        latest_date = latest_ts.strftime("%Y-%m-%d")
        latest_by_symbol = normalized.groupby("symbol")["date"].max()
        cached_symbols = sorted(latest_by_symbol.index.tolist())
        stale_symbols = sorted(latest_by_symbol.loc[latest_by_symbol < latest_ts].index.tolist())

    missing_symbols = [symbol for symbol in expected_symbols if symbol not in set(cached_symbols)]
    report = {
        "total_symbols": len(expected_symbols),
        "cached_symbols": len(cached_symbols),
        "latest_date": latest_date,
        "missing_symbols": missing_symbols,
        "stale_symbols": stale_symbols,
        "failed_symbols": failed,
    }
    return {key: report[key] for key in DATA_COVERAGE_KEYS}


def write_data_coverage_report(report: dict, output_path: str | Path) -> None:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {key: report[key] for key in DATA_COVERAGE_KEYS}
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2), encoding="utf-8")
