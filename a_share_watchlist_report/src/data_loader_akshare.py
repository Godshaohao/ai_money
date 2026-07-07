from pathlib import Path
from datetime import datetime
import time

import pandas as pd

try:
    import akshare as ak
except ImportError:  # pragma: no cover - exercised in environments without runtime deps
    ak = None

from src.data.data_cache import write_daily_bar_cache
from src.data.data_normalizer import empty_daily_bar_frame, normalize_stock_hist_frame
from src.data.eastmoney_client import fetch_stock_hist_eastmoney
from src.schemas import DAILY_BAR_COLUMNS, INDEX_PRICE_COLUMNS, PRICE_COLUMNS


def _normalize_stock_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    daily_bars = normalize_stock_hist_frame(frame, symbol)
    return daily_bars[PRICE_COLUMNS].copy()


def _normalize_index_frame(frame: pd.DataFrame, index_code: str, index_name: str) -> pd.DataFrame:
    renamed = frame.rename(columns={"日期": "date", "收盘": "close"})
    missing = [column for column in ["date", "close"] if column not in renamed.columns]
    if missing:
        raise ValueError(f"AKShare index data for {index_name} missing columns: {', '.join(missing)}")

    normalized = renamed[["date", "close"]].copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["index_name"] = index_name
    normalized["index_code"] = str(index_code)
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")
    return normalized[INDEX_PRICE_COLUMNS].sort_values(["index_name", "date"]).reset_index(drop=True)


def _prefixed_index_symbol(index_code: str) -> str:
    code = str(index_code).strip()
    if code.startswith(("sh", "sz")):
        return code
    if code.startswith("399"):
        return f"sz{code}"
    return f"sh{code}"


def fetch_stock_daily(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one A-share stock daily history through AKShare."""
    daily_bars = fetch_stock_daily_bar(symbol, "", "", start_date, end_date)
    return daily_bars[PRICE_COLUMNS].copy()


def fetch_stock_daily_bar(
    symbol: str,
    name: str,
    industry: str,
    start_date: str,
    end_date: str,
) -> pd.DataFrame:
    """Fetch one A-share stock daily history with V1 cache columns."""
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    stock_symbol = str(symbol).strip().zfill(6)
    try:
        raw = ak.stock_zh_a_hist(
            symbol=stock_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
    except Exception:
        raw = fetch_stock_hist_eastmoney(
            symbol=stock_symbol,
            period="daily",
            start_date=start_date,
            end_date=end_date,
            adjust="qfq",
        )
    return normalize_stock_hist_frame(raw, symbol, name, industry, adjust="qfq")


def fetch_index_daily(index_code: str, index_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one A-share index daily history through AKShare."""
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    try:
        raw = ak.stock_zh_index_daily(symbol=_prefixed_index_symbol(index_code))
    except Exception as exc:
        raise RuntimeError(f"AKShare index fetch failed for {index_name}({index_code}): {exc}") from exc
    normalized = _normalize_index_frame(raw, index_code, index_name)
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    return normalized.loc[(normalized["date"] >= start) & (normalized["date"] <= end)].reset_index(drop=True)


def build_price_cache(
    universe: pd.DataFrame,
    config: dict,
    output_path: str | Path,
    daily_bar_output_path: str | Path | None = None,
) -> pd.DataFrame:
    """Fetch all universe stocks and write data/prices.parquet."""
    end_date = datetime.today().strftime("%Y%m%d")
    daily_bar_frames = []
    for row in universe.to_dict("records"):
        daily_bar_frames.append(
            fetch_stock_daily_bar(
                str(row["symbol"]),
                str(row.get("name", "")),
                str(row.get("industry", "")),
                config["start_date"],
                end_date,
            )
        )
        time.sleep(0.2)

    daily_bars = pd.concat(daily_bar_frames, ignore_index=True) if daily_bar_frames else empty_daily_bar_frame()
    daily_bars = daily_bars[DAILY_BAR_COLUMNS].copy()
    prices = daily_bars[PRICE_COLUMNS].copy()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output, index=False)
    if daily_bar_output_path is not None:
        write_daily_bar_cache(daily_bars, daily_bar_output_path)
    return prices


def build_index_price_cache(config: dict, output_path: str | Path) -> pd.DataFrame:
    """Fetch configured market indices and write data/index_prices.parquet."""
    end_date = datetime.today().strftime("%Y%m%d")
    frames = []
    for index_name, index_code in config["market_indices"].items():
        frames.append(fetch_index_daily(str(index_code), str(index_name), config["start_date"], end_date))
        time.sleep(0.2)

    index_prices = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=INDEX_PRICE_COLUMNS)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    index_prices.to_parquet(output, index=False)
    return index_prices
