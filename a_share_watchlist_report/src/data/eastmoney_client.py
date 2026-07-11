import pandas as pd

from src.data.eastmoney_http import EastMoneyHTTPError, em_get_json


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
    try:
        payload = em_get_json(
            url,
            params=params,
            headers={"Referer": "https://quote.eastmoney.com/"},
            timeout=timeout,
            impersonate="chrome",
        )
        return parse_stock_hist_payload(payload, symbol)
    except EastMoneyHTTPError as exc:
        raise EastMoneyRequestError(f"EastMoney stock data fetch failed for {symbol}: {exc}") from exc
    except Exception as exc:  # noqa: BLE001 - convert parser errors into fail-closed message
        raise EastMoneyRequestError(f"EastMoney stock data fetch failed for {symbol}: {exc}") from exc
