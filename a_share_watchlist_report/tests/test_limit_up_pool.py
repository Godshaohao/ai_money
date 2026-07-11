from datetime import date

import pandas as pd
import pytest

from src.data import limit_up_pool
from src.data.limit_up_pool import (
    empty_limit_up_pool_frame,
    fetch_limit_up_pool_for_date,
    fetch_recent_limit_up_pool,
    merge_limit_up_universe,
    normalize_limit_up_pool_frame,
    parse_eastmoney_limit_up_payload,
)


def test_normalize_limit_up_pool_frame_maps_akshare_columns() -> None:
    raw = pd.DataFrame(
        [
            {
                "代码": "519",
                "名称": "贵州茅台",
                "最新价": 1800.5,
                "涨跌幅": 10.01,
                "成交额": 1_000_000_000,
                "换手率": 2.5,
                "封板资金": 80_000_000,
                "首次封板时间": "09:35:12",
                "最后封板时间": "10:02:01",
                "炸板次数": 0,
                "涨停统计": "1/1",
                "连板数": 1,
                "所属行业": "食品饮料",
            }
        ]
    )

    normalized = normalize_limit_up_pool_frame(raw, "20260708")

    assert normalized.loc[0, "symbol"] == "000519"
    assert normalized.loc[0, "trade_date"] == "2026-07-08"
    assert normalized.loc[0, "change_pct"] == pytest.approx(10.01)
    assert normalized.loc[0, "source"] == "akshare_eastmoney_zt_pool"


def test_fetch_recent_limit_up_pool_combines_available_days(monkeypatch) -> None:
    calls: list[str] = []

    def fake_fetch(day: str) -> pd.DataFrame:
        calls.append(day)
        if day == "20260707":
            return empty_limit_up_pool_frame()
        return pd.DataFrame(
            [
                {
                    "symbol": "600519",
                    "name": "贵州茅台",
                    "trade_date": "2026-07-08",
                    "close": 1800.0,
                    "change_pct": 10.0,
                    "amount": 1_000_000_000,
                    "turnover_rate": 2.0,
                    "seal_amount": 80_000_000,
                    "first_limit_time": "09:35:00",
                    "last_limit_time": "10:00:00",
                    "break_count": 0,
                    "limit_up_stats": "1/1",
                    "streak_count": 1,
                    "industry": "食品饮料",
                    "source": "test",
                }
            ]
        )

    monkeypatch.setattr(limit_up_pool, "fetch_limit_up_pool_for_date", fake_fetch)

    recent = fetch_recent_limit_up_pool(days=2, today=date(2026, 7, 8))

    assert calls == ["20260707", "20260708"]
    assert len(recent) == 1
    assert recent.loc[0, "symbol"] == "600519"


def test_fetch_recent_limit_up_pool_skips_weekends(monkeypatch) -> None:
    calls: list[str] = []

    def fake_fetch(day: str) -> pd.DataFrame:
        calls.append(day)
        return empty_limit_up_pool_frame()

    monkeypatch.setattr(limit_up_pool, "fetch_limit_up_pool_for_date", fake_fetch)

    recent = fetch_recent_limit_up_pool(days=2, today=date(2026, 7, 11))

    assert calls == ["20260709", "20260710"]
    assert recent.empty


def test_parse_eastmoney_limit_up_payload_maps_push2ex_pool() -> None:
    payload = {
        "data": {
            "pool": [
                {
                    "c": "002115",
                    "n": "三维通信",
                    "p": 12030,
                    "zdp": 10.03,
                    "amount": 911000000,
                    "hs": 13.21,
                    "fund": 82000000,
                    "fbt": 92500,
                    "lbt": 145700,
                    "zbc": 1,
                    "zttj": {"days": 3, "ct": 2},
                    "lbc": 2,
                    "hybk": "通信设备",
                }
            ]
        }
    }

    normalized = parse_eastmoney_limit_up_payload(payload, "20260710")

    assert normalized.loc[0, "symbol"] == "002115"
    assert normalized.loc[0, "name"] == "三维通信"
    assert normalized.loc[0, "close"] == pytest.approx(12.03)
    assert normalized.loc[0, "trade_date"] == "2026-07-10"
    assert normalized.loc[0, "first_limit_time"] == "09:25:00"
    assert normalized.loc[0, "last_limit_time"] == "14:57:00"
    assert normalized.loc[0, "limit_up_stats"] == "3天2板"
    assert normalized.loc[0, "streak_count"] == 2
    assert normalized.loc[0, "source"] == "eastmoney_push2ex_zt_pool"


def test_fetch_limit_up_pool_for_date_falls_back_to_direct_eastmoney(monkeypatch) -> None:
    fallback = pd.DataFrame(
        [
            {
                "symbol": "002115",
                "name": "三维通信",
                "trade_date": "2026-07-10",
                "close": 12.03,
                "change_pct": 10.03,
                "amount": 911000000,
                "turnover_rate": 13.21,
                "seal_amount": 82000000,
                "first_limit_time": "09:25:00",
                "last_limit_time": "14:57:00",
                "break_count": 1,
                "limit_up_stats": "3天2板",
                "streak_count": 2,
                "industry": "通信设备",
                "source": "eastmoney_push2ex_zt_pool",
            }
        ]
    )

    class FakeAk:
        @staticmethod
        def stock_zt_pool_em(date: str) -> pd.DataFrame:
            raise RuntimeError(f"akshare blocked {date}")

    monkeypatch.setattr(limit_up_pool, "ak", FakeAk())
    monkeypatch.setattr(limit_up_pool, "fetch_limit_up_pool_eastmoney_direct", lambda trade_date: fallback)

    frame = fetch_limit_up_pool_for_date("20260710")

    assert frame.loc[0, "symbol"] == "002115"
    assert frame.loc[0, "source"] == "eastmoney_push2ex_zt_pool"


def test_fetch_recent_limit_up_pool_raises_when_all_dates_fail(monkeypatch) -> None:
    def fake_fetch(day: str) -> pd.DataFrame:
        raise RuntimeError(f"boom {day}")

    monkeypatch.setattr(limit_up_pool, "fetch_limit_up_pool_for_date", fake_fetch)

    with pytest.raises(RuntimeError, match="limit-up pool fetch failed for all dates"):
        fetch_recent_limit_up_pool(days=2, today=date(2026, 7, 8))


def test_merge_limit_up_universe_adds_recent_symbols_until_max_size() -> None:
    universe = pd.DataFrame([{"symbol": "000001", "name": "平安银行", "industry": "银行"}])
    limit_up = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "300750", "name": "宁德时代", "industry": "电力设备"},
        ]
    )

    merged = merge_limit_up_universe(universe, limit_up, max_size=2)

    assert merged["symbol"].tolist() == ["000001", "600519"]
    assert merged.loc[1, "industry"] == "近期涨停"
