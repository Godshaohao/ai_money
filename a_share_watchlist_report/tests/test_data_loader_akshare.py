import pandas as pd

from src import data_loader_akshare


class _FakeAkshare:
    def __init__(self) -> None:
        self.symbols: list[str] = []
        self.stock_calls: list[dict] = []

    def stock_zh_index_daily(self, symbol: str) -> pd.DataFrame:
        self.symbols.append(symbol)
        return pd.DataFrame(
            [
                {"date": "2024-01-01", "open": 1.0, "high": 1.0, "low": 1.0, "close": 100.0, "volume": 1},
                {"date": "2024-01-02", "open": 1.0, "high": 1.0, "low": 1.0, "close": 101.0, "volume": 1},
            ]
        )

    def stock_zh_a_hist(
        self,
        symbol: str,
        period: str,
        start_date: str,
        end_date: str,
        adjust: str,
    ) -> pd.DataFrame:
        self.symbols.append(symbol)
        self.stock_calls.append(
            {
                "symbol": symbol,
                "period": period,
                "start_date": start_date,
                "end_date": end_date,
                "adjust": adjust,
            }
        )
        return pd.DataFrame(
            [
                {"日期": "2024-01-01", "开盘": 1.0, "最高": 1.0, "最低": 1.0, "收盘": 10.0, "成交额": 1000.0},
                {"日期": "2024-01-02", "开盘": 1.0, "最高": 1.0, "最低": 1.0, "收盘": 11.0, "成交额": 1200.0},
            ]
        )


def test_fetch_stock_daily_uses_raw_six_digit_stock_code(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    result = data_loader_akshare.fetch_stock_daily("600519", "20240101", "20240102")

    assert fake.symbols == ["600519"]
    assert fake.stock_calls == [
        {
            "symbol": "600519",
            "period": "daily",
            "start_date": "20240101",
            "end_date": "20240102",
            "adjust": "qfq",
        }
    ]
    assert list(result.columns) == ["date", "symbol", "close", "amount"]
    assert result.iloc[-1]["symbol"] == "600519"
    assert result.iloc[-1]["close"] == 11.0


def test_fetch_stock_daily_does_not_prefix_300_codes(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    data_loader_akshare.fetch_stock_daily("300750", "20240101", "20240102")

    assert fake.symbols == ["300750"]


def test_fetch_index_daily_uses_market_prefixed_index_code(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    result = data_loader_akshare.fetch_index_daily("000300", "沪深300", "20240101", "20240102")

    assert fake.symbols == ["sh000300"]
    assert list(result.columns) == ["date", "index_name", "index_code", "close"]
    assert result.iloc[-1]["index_name"] == "沪深300"
    assert result.iloc[-1]["index_code"] == "000300"


def test_fetch_index_daily_uses_sz_prefix_for_399_codes(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    data_loader_akshare.fetch_index_daily("399006", "创业板指", "20240101", "20240102")

    assert fake.symbols == ["sz399006"]
