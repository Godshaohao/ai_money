from pathlib import Path

import pandas as pd
import pytest

from src.data.data_cache import read_daily_bar_cache, write_daily_bar_cache
from src.schemas import DAILY_BAR_COLUMNS


def _daily_bars() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "date": pd.Timestamp("2024-01-01"),
                "symbol": "600519",
                "name": "贵州茅台",
                "industry": "食品饮料",
                "open": 10.0,
                "high": 11.0,
                "low": 9.0,
                "close": 10.5,
                "amount": 1_000_000.0,
                "volume": 1200.0,
                "source": "akshare",
                "adjust": "qfq",
                "updated_at": "2026-01-01T00:00:00+00:00",
            }
        ]
    )


def test_write_and_read_daily_bar_cache_preserves_schema(tmp_path: Path) -> None:
    path = tmp_path / "data" / "cache" / "daily_bars.parquet"

    write_daily_bar_cache(_daily_bars(), path)
    loaded = read_daily_bar_cache(path)

    assert path.exists()
    assert list(loaded.columns) == DAILY_BAR_COLUMNS
    assert loaded.loc[0, "symbol"] == "600519"


def test_write_daily_bar_cache_fails_closed_on_missing_schema_column(tmp_path: Path) -> None:
    broken = _daily_bars().drop(columns=["amount"])

    with pytest.raises(ValueError, match="daily bar cache missing columns: amount"):
        write_daily_bar_cache(broken, tmp_path / "daily_bars.parquet")

