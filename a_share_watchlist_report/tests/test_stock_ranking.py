import pandas as pd

from src.stock_ranking import build_watchlist


def _prices(symbol: str, latest: float) -> list[dict]:
    rows = []
    for day in range(260):
        close = 10.0
        if day == 134:
            close = latest / 1.1
        if day == 8:
            close = latest / 1.2
        if day == 259:
            close = latest
        rows.append({"date": f"2024-01-{(day % 28) + 1:02d}", "symbol": symbol, "close": close, "amount": 1000.0})
    return rows


def test_ranking_excludes_below_ma200_and_respects_top_n() -> None:
    prices = pd.DataFrame(_prices("600519", 20.0) + _prices("000001", 15.0) + _prices("300750", 18.0))
    eligible = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料", "close": 20.0, "ma200": 11.0, "above_ma200": True, "avg_amount_20d": 1000.0, "history_days": 260},
            {"symbol": "000001", "name": "平安银行", "industry": "银行", "close": 15.0, "ma200": 16.0, "above_ma200": False, "avg_amount_20d": 1000.0, "history_days": 260},
            {"symbol": "300750", "name": "宁德时代", "industry": "电力设备", "close": 18.0, "ma200": 11.0, "above_ma200": True, "avg_amount_20d": 1000.0, "history_days": 260},
        ]
    )

    watchlist = build_watchlist(prices, eligible, {"top_n_watchlist": 1, "momentum_12m_days": 252, "momentum_6m_days": 126, "max_drawdown_days": 60})

    assert len(watchlist) == 1
    assert watchlist.iloc[0]["symbol"] == "600519"
    assert watchlist.iloc[0]["reason"]
    forbidden = {"BUY", "SELL", "target_price", "expected_return"}
    assert forbidden.isdisjoint(set(watchlist.columns))
