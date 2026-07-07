import pandas as pd
import pytest

from src.data.eastmoney_client import EastMoneyRequestError, parse_stock_hist_payload


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

