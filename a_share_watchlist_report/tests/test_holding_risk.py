import pandas as pd

from src.holding_risk import build_holding_risk


def _prices(symbol: str, latest: float) -> list[dict]:
    start = pd.Timestamp("2024-01-01")
    rows = []
    for day in range(220):
        close = 20.0
        if day == 219:
            close = latest
        rows.append({"date": (start + pd.Timedelta(days=day)).strftime("%Y-%m-%d"), "symbol": symbol, "close": close, "amount": 1000.0})
    return rows


def test_holding_risk_flags_unknown_excluded_and_below_ma200() -> None:
    holdings = pd.DataFrame(
        [
            {"symbol": "UNKNOWN", "shares": 1, "cost_basis": 10.0},
            {"symbol": "600519", "shares": 100, "cost_basis": 10.0},
            {"symbol": "000001", "shares": 100, "cost_basis": 10.0},
        ]
    )
    universe = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "000001", "name": "平安银行", "industry": "银行"},
        ]
    )
    excluded = pd.DataFrame(
        [{"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料", "exclude_reason": "no price data"}]
    )
    prices = pd.DataFrame(_prices("000001", 10.0))

    risk = build_holding_risk(holdings, prices, universe, excluded, {"trend_ma_days": 200, "max_drawdown_days": 60})

    actions = dict(zip(risk["symbol"], risk["risk_action"], strict=False))
    assert actions["UNKNOWN"] == "DATA_ISSUE"
    assert actions["600519"] == "DATA_ISSUE"
    assert actions["000001"] == "REDUCE_REVIEW"
    assert set(risk["risk_action"]).issubset({"WATCH", "HOLD_REVIEW", "REDUCE_REVIEW", "DATA_ISSUE"})
    assert not {"BUY", "SELL"}.intersection(set(risk["risk_action"]))
    assert risk["reason"].str.len().min() > 0
