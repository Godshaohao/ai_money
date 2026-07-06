from pathlib import Path

import numpy as np
import pandas as pd


WATCHLIST_COLUMNS = [
    "symbol",
    "name",
    "industry",
    "close",
    "momentum_12m",
    "momentum_6m",
    "above_ma200",
    "max_drawdown_60d",
    "avg_amount_20d",
    "rank",
    "reason",
]


def _momentum(group: pd.DataFrame, days: int) -> float:
    if len(group) <= days:
        return np.nan
    latest = float(group["close"].iloc[-1])
    base = float(group["close"].iloc[-days - 1])
    return latest / base - 1 if base > 0 else np.nan


def _max_drawdown(group: pd.DataFrame, days: int) -> float:
    window = group["close"].tail(days)
    if window.empty:
        return np.nan
    peak = float(window.max())
    latest = float(window.iloc[-1])
    return latest / peak - 1 if peak > 0 else np.nan


def _format_percent(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    return f"{value:.2%}"


def _format_amount(value: float) -> str:
    if pd.isna(value):
        return "N/A"
    if abs(value) >= 100_000_000:
        return f"{value / 100_000_000:.2f} 亿"
    if abs(value) >= 10_000:
        return f"{value / 10_000:.2f} 万"
    return f"{value:.2f}"


def build_watchlist(
    prices: pd.DataFrame,
    eligible: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Build Top N observation list using trend and momentum."""
    if eligible.empty:
        return pd.DataFrame(columns=WATCHLIST_COLUMNS)

    normalized = prices.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = normalized["symbol"].astype(str).str.zfill(6)
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")

    rows: list[dict] = []
    eligible_above = eligible.loc[eligible["above_ma200"] == True].copy()
    for stock_info in eligible_above.to_dict("records"):
        symbol = str(stock_info["symbol"]).zfill(6)
        stock = normalized.loc[normalized["symbol"] == symbol].sort_values("date").dropna(subset=["close"])
        if stock.empty:
            continue
        rows.append(
            {
                "symbol": symbol,
                "name": stock_info["name"],
                "industry": stock_info["industry"],
                "close": float(stock_info["close"]),
                "momentum_12m": _momentum(stock, int(config["momentum_12m_days"])),
                "momentum_6m": _momentum(stock, int(config["momentum_6m_days"])),
                "above_ma200": bool(stock_info["above_ma200"]),
                "max_drawdown_60d": _max_drawdown(stock, int(config["max_drawdown_days"])),
                "avg_amount_20d": float(stock_info["avg_amount_20d"]),
            }
        )

    ranked = pd.DataFrame(rows)
    if ranked.empty:
        return pd.DataFrame(columns=WATCHLIST_COLUMNS)

    ranked = ranked.sort_values(["momentum_12m", "momentum_6m"], ascending=[False, False], na_position="last")
    ranked = ranked.head(int(config["top_n_watchlist"])).reset_index(drop=True)
    ranked["rank"] = ranked.index + 1
    ranked["reason"] = ranked.apply(
        lambda row: (
            "进入观察：价格在 MA200 上方，"
            f"12M 动量 {_format_percent(row['momentum_12m'])}，"
            f"6M 动量 {_format_percent(row['momentum_6m'])}，"
            f"60 日回撤 {_format_percent(row['max_drawdown_60d'])}，"
            f"20 日平均成交额 {_format_amount(row['avg_amount_20d'])}。"
        ),
        axis=1,
    )
    return ranked[WATCHLIST_COLUMNS]
