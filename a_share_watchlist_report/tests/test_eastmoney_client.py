import pytest
import pandas as pd

from src.data import eastmoney_client
from src.data.eastmoney_client import EastMoneyRequestError, fetch_stock_hist_eastmoney, parse_stock_hist_payload


def test_parse_stock_hist_payload_returns_akshare_compatible_columns() -> None:
    payload = {
        "rc": 0,
        "data": {
            "klines": [
                "2026-07-01,1180.10,1193.01,1196.80,1166.33,42474,5033838236.00,2.57,0.63,7.52,0.34",
                "2026-07-02,1193.01,1203.00,1215.52,1190.00,42500,5100000000.00,2.14,0.84,9.99,0.35",
            ]
        },
    }

    frame = parse_stock_hist_payload(payload, "600519")

    assert list(frame.columns) == [
        "日期",
        "股票代码",
        "开盘",
        "收盘",
        "最高",
        "最低",
        "成交量",
        "成交额",
        "振幅",
        "涨跌幅",
        "涨跌额",
        "换手率",
    ]
    assert frame.loc[0, "股票代码"] == "600519"
    assert frame.loc[0, "收盘"] == 1193.01
    assert pd.api.types.is_numeric_dtype(frame["成交额"])


def test_parse_stock_hist_payload_fails_closed_on_missing_klines() -> None:
    with pytest.raises(EastMoneyRequestError, match="missing kline data"):
        parse_stock_hist_payload({"rc": 0, "data": {"klines": []}}, "600519")


def test_fetch_stock_hist_eastmoney_uses_shared_http_helper(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_em_get_json(
        url: str,
        params: dict,
        headers: dict | None = None,
        timeout: int = 15,
        **kwargs,
    ) -> dict:
        calls.append({"url": url, "params": params, "headers": headers, "timeout": timeout, "kwargs": kwargs})
        return {
            "rc": 0,
            "data": {
                "klines": [
                    "2026-07-01,1180.10,1193.01,1196.80,1166.33,42474,5033838236.00,2.57,0.63,7.52,0.34"
                ]
            },
        }

    monkeypatch.setattr(eastmoney_client, "em_get_json", fake_em_get_json)

    frame = fetch_stock_hist_eastmoney("600519", period="daily", start_date="20260701", end_date="20260707", adjust="qfq")

    assert calls[0]["url"] == "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    assert calls[0]["params"]["secid"] == "1.600519"
    assert calls[0]["params"]["klt"] == "101"
    assert calls[0]["params"]["fqt"] == "1"
    assert calls[0]["headers"]["Referer"] == "https://quote.eastmoney.com/"
    assert calls[0]["kwargs"]["impersonate"] == "chrome"
    assert frame.loc[0, "股票代码"] == "600519"
