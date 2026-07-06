import pandas as pd

from src.market_regime import calculate_market_regime


def _index_rows(index_name: str, latest: float, old: float, ma_base: float) -> list[dict]:
    rows = []
    for day in range(220):
        close = ma_base
        if day == 199:
            close = old
        if day == 219:
            close = latest
        rows.append(
            {
                "date": f"2024-01-{(day % 28) + 1:02d}",
                "index_name": index_name,
                "index_code": index_name,
                "close": close,
            }
        )
    return rows


def test_two_of_three_positive_indices_is_risk_on() -> None:
    prices = pd.DataFrame(
        _index_rows("A", latest=120.0, old=100.0, ma_base=100.0)
        + _index_rows("B", latest=121.0, old=100.0, ma_base=100.0)
        + _index_rows("C", latest=80.0, old=100.0, ma_base=100.0)
    )

    regime, evidence = calculate_market_regime(prices, {"trend_ma_days": 200, "short_trend_days": 20})

    assert regime == "RISK_ON"
    assert len(evidence) == 3


def test_two_of_three_negative_indices_is_risk_off() -> None:
    prices = pd.DataFrame(
        _index_rows("A", latest=80.0, old=100.0, ma_base=100.0)
        + _index_rows("B", latest=79.0, old=100.0, ma_base=100.0)
        + _index_rows("C", latest=120.0, old=100.0, ma_base=100.0)
    )

    regime, _ = calculate_market_regime(prices, {"trend_ma_days": 200, "short_trend_days": 20})

    assert regime == "RISK_OFF"


def test_mixed_indices_are_neutral() -> None:
    prices = pd.DataFrame(
        _index_rows("A", latest=120.0, old=100.0, ma_base=100.0)
        + _index_rows("B", latest=80.0, old=100.0, ma_base=100.0)
        + _index_rows("C", latest=100.0, old=100.0, ma_base=100.0)
    )

    regime, _ = calculate_market_regime(prices, {"trend_ma_days": 200, "short_trend_days": 20})

    assert regime == "NEUTRAL"
