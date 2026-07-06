from dataclasses import dataclass
from pathlib import Path
import json

import numpy as np
import pandas as pd


EXCLUDED_COLUMNS = [
    "symbol",
    "name",
    "industry",
    "exclude_reason",
    "last_price_date",
    "avg_amount_20d",
    "history_days",
]


@dataclass
class DataQualityResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    excluded: pd.DataFrame


def _empty_excluded() -> pd.DataFrame:
    return pd.DataFrame(columns=EXCLUDED_COLUMNS)


def _has_st_name(name: object) -> bool:
    normalized = str(name).strip().upper().replace(" ", "")
    return normalized.startswith("ST") or normalized.startswith("*ST")


def run_data_quality_checks(
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    config: dict,
) -> DataQualityResult:
    """Return global quality status and per-stock exclusions."""
    errors: list[str] = []
    warnings: list[str] = []
    required = {"date", "symbol", "close", "amount"}
    missing = sorted(required.difference(prices.columns))
    if missing:
        errors.append(f"prices missing required columns: {', '.join(missing)}")
        return DataQualityResult(False, errors, warnings, _empty_excluded())

    if prices.empty:
        errors.append("prices cache is empty")

    normalized = prices.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = normalized["symbol"].astype(str).str.zfill(6)
    latest_cache_date = normalized["date"].max() if not normalized.empty else pd.NaT
    global_dates = set(normalized["date"].dropna().unique())

    excluded_rows: list[dict] = []
    for row in universe.to_dict("records"):
        symbol = str(row["symbol"]).zfill(6)
        stock = normalized.loc[normalized["symbol"] == symbol].sort_values("date")
        reasons: list[str] = []
        if _has_st_name(row["name"]):
            reasons.append("ST name")

        if stock.empty:
            reasons.append("no price data")
            excluded_rows.append(
                {
                    "symbol": symbol,
                    "name": row["name"],
                    "industry": row["industry"],
                    "exclude_reason": "; ".join(reasons),
                    "last_price_date": "",
                    "avg_amount_20d": np.nan,
                    "history_days": 0,
                }
            )
            continue

        last_price_date = stock["date"].max()
        first_price_date = stock["date"].min()
        history_days = int(stock["date"].nunique())
        avg_amount_20d = float(stock["amount"].tail(20).mean())
        latest_close = float(stock["close"].iloc[-1])
        comparable_dates = {date for date in global_dates if first_price_date <= date <= last_price_date}
        missing_days = len(comparable_dates.difference(set(stock["date"].unique())))

        if history_days < int(config["min_listing_days"]):
            reasons.append("short history")
        if latest_close <= 0:
            reasons.append("latest close <= 0")
        if missing_days > int(config["max_missing_days"]):
            reasons.append("too many missing days")
        if avg_amount_20d < float(config["min_avg_amount_20d"]):
            reasons.append("low 20-day average amount")
        if pd.notna(latest_cache_date) and last_price_date < latest_cache_date:
            reasons.append("suspected suspension")

        if reasons:
            excluded_rows.append(
                {
                    "symbol": symbol,
                    "name": row["name"],
                    "industry": row["industry"],
                    "exclude_reason": "; ".join(dict.fromkeys(reasons)),
                    "last_price_date": last_price_date.strftime("%Y-%m-%d"),
                    "avg_amount_20d": avg_amount_20d,
                    "history_days": history_days,
                }
            )

    excluded = pd.DataFrame(excluded_rows, columns=EXCLUDED_COLUMNS)
    if len(excluded) == len(universe) and len(universe) > 0:
        errors.append("all universe stocks are excluded")
    elif not excluded.empty:
        warnings.append(f"{len(excluded)} stocks excluded by data quality checks")

    return DataQualityResult(ok=not errors, errors=errors, warnings=warnings, excluded=excluded)


def write_data_quality_status(result: DataQualityResult, output_path: str | Path) -> None:
    """Write output/data_quality_status.json."""
    status = {
        "ok": result.ok,
        "errors": result.errors,
        "warnings": result.warnings,
        "excluded_count": int(len(result.excluded)),
    }
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
