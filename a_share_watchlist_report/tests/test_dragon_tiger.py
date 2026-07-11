import pandas as pd

from src.data import dragon_tiger
from src.data.dragon_tiger import (
    DRAGON_TIGER_COLUMNS,
    fetch_today_dragon_tiger,
    merge_dragon_tiger_universe,
    normalize_dragon_tiger_frame,
)


def _raw_lhb() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "代码": "000001",
                "名称": "平安银行",
                "上榜日": "2026-07-07",
                "收盘价": "12.34",
                "涨跌幅": "10.0",
                "龙虎榜净买额": "1000000",
                "龙虎榜买入额": "2000000",
                "龙虎榜卖出额": "1000000",
                "龙虎榜成交额": "3000000",
                "换手率": "8.8",
                "上榜原因": "日涨幅偏离值达7%",
            }
        ]
    )


def test_normalize_dragon_tiger_frame_outputs_contract_columns() -> None:
    normalized = normalize_dragon_tiger_frame(_raw_lhb())

    assert list(normalized.columns) == DRAGON_TIGER_COLUMNS
    assert normalized.loc[0, "symbol"] == "000001"
    assert normalized.loc[0, "name"] == "平安银行"
    assert normalized.loc[0, "trade_date"] == "2026-07-07"
    assert normalized.loc[0, "close"] == 12.34
    assert normalized.loc[0, "net_buy_amount"] == 1_000_000
    assert normalized.loc[0, "source"] == "akshare_eastmoney_lhb"


def test_merge_dragon_tiger_universe_preserves_existing_and_adds_lhb_symbols() -> None:
    universe = pd.DataFrame({"symbol": ["600519"], "name": ["贵州茅台"], "industry": ["食品饮料"]})
    dragon_tiger = normalize_dragon_tiger_frame(_raw_lhb())

    merged = merge_dragon_tiger_universe(universe, dragon_tiger, max_size=100)

    assert merged["symbol"].tolist() == ["600519", "000001"]
    assert merged.loc[1, "industry"] == "龙虎榜"


def test_merge_dragon_tiger_universe_respects_max_size() -> None:
    universe = pd.DataFrame({"symbol": ["600519"], "name": ["贵州茅台"], "industry": ["食品饮料"]})
    dragon_tiger = normalize_dragon_tiger_frame(_raw_lhb())

    merged = merge_dragon_tiger_universe(universe, dragon_tiger, max_size=1)

    assert merged["symbol"].tolist() == ["600519"]


def test_fetch_today_dragon_tiger_returns_empty_on_weekend(monkeypatch) -> None:
    class FakeAk:
        @staticmethod
        def stock_lhb_detail_em(start_date: str, end_date: str) -> pd.DataFrame:
            raise AssertionError("weekend should not call AKShare")

    monkeypatch.setattr(dragon_tiger, "ak", FakeAk())

    frame = fetch_today_dragon_tiger("20260711")

    assert frame.empty
    assert list(frame.columns) == DRAGON_TIGER_COLUMNS
