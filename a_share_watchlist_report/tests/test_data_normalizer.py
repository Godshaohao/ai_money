import pandas as pd
import pytest

from src.data.data_normalizer import normalize_stock_hist_frame
from src.schemas import DAILY_BAR_COLUMNS


def _raw_hist_frame() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "日期": "2024-01-01",
                "开盘": "10.0",
                "最高": "11.0",
                "最低": "9.5",
                "收盘": "10.5",
                "成交额": "1000000",
                "成交量": "1200",
            }
        ]
    )


def test_normalize_stock_hist_frame_outputs_daily_bar_schema() -> None:
    normalized = normalize_stock_hist_frame(
        _raw_hist_frame(),
        "600519",
        "贵州茅台",
        "食品饮料",
        updated_at="2026-01-01T00:00:00+00:00",
    )

    assert list(normalized.columns) == DAILY_BAR_COLUMNS
    assert normalized.loc[0, "symbol"] == "600519"
    assert normalized.loc[0, "name"] == "贵州茅台"
    assert normalized.loc[0, "industry"] == "食品饮料"
    assert normalized.loc[0, "close"] == 10.5
    assert normalized.loc[0, "amount"] == 1_000_000
    assert normalized.loc[0, "source"] == "akshare"
    assert normalized.loc[0, "adjust"] == "qfq"


def test_normalize_stock_hist_frame_allows_missing_optional_volume() -> None:
    raw = _raw_hist_frame().drop(columns=["成交量"])

    normalized = normalize_stock_hist_frame(raw, "1", updated_at="2026-01-01T00:00:00+00:00")

    assert list(normalized.columns) == DAILY_BAR_COLUMNS
    assert normalized.loc[0, "symbol"] == "000001"
    assert pd.isna(normalized.loc[0, "volume"])


def test_normalize_stock_hist_frame_fails_closed_on_missing_required_column() -> None:
    raw = _raw_hist_frame().drop(columns=["成交额"])

    with pytest.raises(ValueError, match="missing columns: 成交额"):
        normalize_stock_hist_frame(raw, "600519")

