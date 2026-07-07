import time

import pandas as pd

try:
    from curl_cffi import requests as curl_requests
except ImportError:  # pragma: no cover - covered by dependency smoke checks
    curl_requests = None


class EastMoneyRequestError(RuntimeError):
    """Raised when the same-source EastMoney HTTP client cannot return usable data."""


def _market_code(symbol: str) -> int:
    return 1 if str(symbol).startswith("6") else 0


def parse_stock_hist_payload(payload: dict, symbol: str) -> pd.DataFrame:
    data = payload.get("data") if isinstance(payload, dict) else None
    klines = data.get("klines") if isinstance(data, dict) else None
    if not klines:
        raise EastMoneyRequestError(f"EastMoney stock data for {str(symbol).zfill(6)} missing kline data")

    frame = pd.DataFrame([str(item).split(",") for item in klines])
    frame["股票代码"] = str(symbol).zfill(6)
    frame.columns = [
        "日期",
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
        "股票代码",
    ]
    frame["日期"] = pd.to_datetime(frame["日期"], errors="coerce").dt.date
    for column in ["开盘", "收盘", "最高", "最低", "成交量", "成交额", "振幅", "涨跌幅", "涨跌额", "换手率"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame[
        [
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
    ]


def fetch_stock_hist_eastmoney(
    symbol: str,
    period: str,
    start_date: str,
    end_date: str,
    adjust: str,
    retries: int = 2,
    timeout: int = 15,
) -> pd.DataFrame:
    if curl_requests is None:
        raise EastMoneyRequestError("curl_cffi is not installed; install requirements.txt before running the report")

    symbol = str(symbol).strip().zfill(6)
    adjust_dict = {"qfq": "1", "hfq": "2", "": "0"}
    period_dict = {"daily": "101", "weekly": "102", "monthly": "103"}
    if adjust not in adjust_dict:
        raise EastMoneyRequestError(f"unsupported adjust mode: {adjust}")
    if period not in period_dict:
        raise EastMoneyRequestError(f"unsupported period: {period}")

    params = {
        "fields1": "f1,f2,f3,f4,f5,f6",
        "fields2": "f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61,f116",
        "ut": "7eea3edcaed734bea9cbfc24409ed989",
        "klt": period_dict[period],
        "fqt": adjust_dict[adjust],
        "secid": f"{_market_code(symbol)}.{symbol}",
        "beg": start_date,
        "end": end_date,
    }
    url = "https://push2his.eastmoney.com/api/qt/stock/kline/get"
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            response = curl_requests.get(url, params=params, timeout=timeout, impersonate="chrome")
            response.raise_for_status()
            return parse_stock_hist_payload(response.json(), symbol)
        except Exception as exc:  # noqa: BLE001 - convert transport/parser errors into fail-closed message
            last_error = exc
            if attempt < retries:
                time.sleep(0.5)

    raise EastMoneyRequestError(f"EastMoney stock data fetch failed for {symbol}: {last_error}") from last_error
