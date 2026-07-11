from pathlib import Path

import numpy as np
import pandas as pd


ELIGIBLE_COLUMNS = [
    "symbol",
    "name",
    "industry",
    "close",
    "ma200",
    "above_ma200",
    "avg_amount_20d",
    "history_days",
]


def build_eligible_stocks(
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    excluded: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Return per-stock latest indicators after hard exclusions."""
    excluded_symbols = set(excluded["symbol"].astype(str).str.zfill(6)) if not excluded.empty else set()
    normalized = prices.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = normalized["symbol"].astype(str).str.zfill(6)
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")
    normalized["amount"] = pd.to_numeric(normalized["amount"], errors="coerce")

    rows: list[dict] = []
    trend_days = int(config["trend_ma_days"])
    for info in universe.to_dict("records"):
        symbol = str(info["symbol"]).zfill(6)
        if symbol in excluded_symbols:
            continue
        stock = normalized.loc[normalized["symbol"] == symbol].sort_values("date")
        if stock.empty:
            continue

        close = float(stock["close"].iloc[-1])
        ma200 = float(stock["close"].tail(trend_days).mean()) if len(stock) >= trend_days else np.nan
        avg_amount_20d = float(stock["amount"].tail(20).mean())
        rows.append(
            {
                "symbol": symbol,
                "name": info["name"],
                "industry": info["industry"],
                "close": close,
                "ma200": ma200,
                "above_ma200": bool(close > ma200) if not np.isnan(ma200) else False,
                "avg_amount_20d": avg_amount_20d,
                "history_days": int(stock["date"].nunique()),
            }
        )

    return pd.DataFrame(rows, columns=ELIGIBLE_COLUMNS)
