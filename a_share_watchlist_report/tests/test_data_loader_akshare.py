import pandas as pd

from src import data_loader_akshare


class _FakeAkshare:
    def __init__(self) -> None:
        self.symbols: list[str] = []

    def stock_zh_index_daily(self, symbol: str) -> pd.DataFrame:
        self.symbols.append(symbol)
        return pd.DataFrame(
            [
                {"date": "2024-01-01", "open": 1.0, "high": 1.0, "low": 1.0, "close": 100.0, "volume": 1},
                {"date": "2024-01-02", "open": 1.0, "high": 1.0, "low": 1.0, "close": 101.0, "volume": 1},
            ]
        )

    def stock_zh_a_daily(self, symbol: str, start_date: str, end_date: str, adjust: str) -> pd.DataFrame:
        self.symbols.append(symbol)
        return pd.DataFrame(
            [
                {"date": "2024-01-01", "open": 1.0, "high": 1.0, "low": 1.0, "close": 10.0, "amount": 1000.0},
                {"date": "2024-01-02", "open": 1.0, "high": 1.0, "low": 1.0, "close": 11.0, "amount": 1200.0},
            ]
        )


def test_fetch_stock_daily_uses_market_prefixed_stock_code(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    result = data_loader_akshare.fetch_stock_daily("600519", "20240101", "20240102")

    assert fake.symbols == ["sh600519"]
    assert list(result.columns) == ["date", "symbol", "close", "amount"]
    assert result.iloc[-1]["symbol"] == "600519"
    assert result.iloc[-1]["close"] == 11.0


def test_fetch_stock_daily_uses_sz_prefix_for_000_and_300_codes(monkeypatch) -> None:
    fake = _FakeAkshare()
    monkeypatch.setattr(data_loader_akshare, "ak", fake)

    data_loader_akshare.fetch_stock_daily("300750", "20240101", "20240102")

    assert fake.symbols == ["sz300750"]


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
