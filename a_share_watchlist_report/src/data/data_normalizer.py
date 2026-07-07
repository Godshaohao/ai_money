from datetime import datetime, timezone

import pandas as pd

from src.schemas import DAILY_BAR_COLUMNS


AKSHARE_STOCK_HIST_COLUMNS = {
    "日期": "date",
    "开盘": "open",
    "最高": "high",
    "最低": "low",
    "收盘": "close",
    "成交额": "amount",
    "成交量": "volume",
}
REQUIRED_AKSHARE_STOCK_HIST_COLUMNS = ["日期", "开盘", "最高", "最低", "收盘", "成交额"]
NUMERIC_DAILY_BAR_COLUMNS = ["open", "high", "low", "close", "amount", "volume"]


def _numeric_column(frame: pd.DataFrame, column: str) -> pd.Series:
    if column not in frame.columns:
        return pd.Series([pd.NA] * len(frame), dtype="Float64")
    return pd.to_numeric(frame[column], errors="coerce")


def empty_daily_bar_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=DAILY_BAR_COLUMNS)


def normalize_stock_hist_frame(
    frame: pd.DataFrame,
    symbol: str,
    name: str = "",
    industry: str = "",
    source: str = "akshare",
    adjust: str = "qfq",
    updated_at: str | None = None,
) -> pd.DataFrame:
    missing = [column for column in REQUIRED_AKSHARE_STOCK_HIST_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"AKShare stock data for {str(symbol).zfill(6)} missing columns: {', '.join(missing)}")

    renamed = frame.rename(columns=AKSHARE_STOCK_HIST_COLUMNS).copy()
    normalized = pd.DataFrame()
    normalized["date"] = pd.to_datetime(renamed["date"], errors="raise")
    normalized["symbol"] = str(symbol).strip().zfill(6)
    normalized["name"] = str(name or "")
    normalized["industry"] = str(industry or "")
    for column in NUMERIC_DAILY_BAR_COLUMNS:
        normalized[column] = _numeric_column(renamed, column)
    normalized["source"] = source
    normalized["adjust"] = adjust
    normalized["updated_at"] = updated_at or datetime.now(timezone.utc).isoformat()

    return normalized[DAILY_BAR_COLUMNS].sort_values(["symbol", "date"]).reset_index(drop=True)

