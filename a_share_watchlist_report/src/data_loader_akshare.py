from pathlib import Path
from datetime import datetime
import time

import pandas as pd

try:
    import akshare as ak
except ImportError:  # pragma: no cover - exercised in environments without runtime deps
    ak = None

from src.schemas import INDEX_PRICE_COLUMNS, PRICE_COLUMNS


def _normalize_stock_frame(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    renamed = frame.rename(columns={"日期": "date", "收盘": "close", "成交额": "amount"})
    missing = [column for column in ["date", "close", "amount"] if column not in renamed.columns]
    if missing:
        raise ValueError(f"AKShare stock data for {symbol} missing columns: {', '.join(missing)}")

    normalized = renamed[["date", "close", "amount"]].copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["symbol"] = str(symbol).zfill(6)
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")
    normalized["amount"] = pd.to_numeric(normalized["amount"], errors="coerce")
    return normalized[PRICE_COLUMNS].sort_values(["symbol", "date"]).reset_index(drop=True)


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


def _prefixed_stock_symbol(symbol: str) -> str:
    code = str(symbol).strip().zfill(6)
    if code.startswith(("0", "3")):
        return f"sz{code}"
    return f"sh{code}"


def fetch_stock_daily(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one A-share stock daily history through AKShare."""
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    raw = ak.stock_zh_a_daily(
        symbol=_prefixed_stock_symbol(symbol),
        start_date=start_date,
        end_date=end_date,
        adjust="qfq",
    )
    return _normalize_stock_frame(raw, symbol)


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


def build_price_cache(universe: pd.DataFrame, config: dict, output_path: str | Path) -> pd.DataFrame:
    """Fetch all universe stocks and write data/prices.parquet."""
    end_date = datetime.today().strftime("%Y%m%d")
    frames = []
    for symbol in universe["symbol"].astype(str):
        frames.append(fetch_stock_daily(symbol, config["start_date"], end_date))
        time.sleep(0.2)

    prices = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=PRICE_COLUMNS)
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    prices.to_parquet(output, index=False)
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
