import pandas as pd

from src.limit_up_strategy import build_limit_up_strategy_review, empty_limit_up_strategy_review_frame


def _prices(symbol: str = "600519") -> pd.DataFrame:
    dates = pd.date_range("2026-01-01", periods=90, freq="D")
    return pd.DataFrame(
        {
            "date": dates,
            "symbol": symbol,
            "close": [100.0 + index for index in range(len(dates))],
            "amount": [120_000_000.0 for _ in dates],
        }
    )


def test_build_limit_up_strategy_review_scores_recent_limit_up_stock() -> None:
    limit_up = pd.DataFrame(
        [
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "trade_date": "2026-07-08",
                "close": 1800.0,
                "change_pct": 10.01,
                "amount": 1_000_000_000,
                "turnover_rate": 3.2,
                "seal_amount": 90_000_000,
                "first_limit_time": "09:35:00",
                "last_limit_time": "10:02:00",
                "break_count": 0,
                "limit_up_stats": "1/1",
                "streak_count": 2,
                "industry": "食品饮料",
                "source": "test",
            }
        ]
    )
    market = pd.DataFrame([{"status": "POSITIVE"}])

    review = build_limit_up_strategy_review(limit_up, _prices(), market)

    assert review.loc[0, "symbol"] == "600519"
    assert review.loc[0, "review_label"] in {"CORE_REVIEW", "WATCH_REVIEW"}
    assert review.loc[0, "review_score"] > 70
    assert "近期涨停复核" in review.loc[0, "reason"]
    assert "BUY" not in ",".join(review.astype(str).iloc[0].tolist())
    assert "SELL" not in ",".join(review.astype(str).iloc[0].tolist())


def test_build_limit_up_strategy_review_uses_limit_up_pool_when_price_history_missing() -> None:
    limit_up = pd.DataFrame(
        [
            {
                "symbol": "300750",
                "name": "宁德时代",
                "trade_date": "2026-07-08",
                "close": 250.0,
                "change_pct": 10.1,
                "amount": 200_000_000,
                "turnover_rate": 0.5,
                "seal_amount": 80_000_000,
                "first_limit_time": "",
                "last_limit_time": "",
                "break_count": 0,
                "limit_up_stats": "2/2",
                "streak_count": 2,
                "industry": "电力设备",
                "source": "test",
            }
        ]
    )

    review = build_limit_up_strategy_review(limit_up, pd.DataFrame(columns=["date", "symbol", "close", "amount"]))

    assert review.loc[0, "review_label"] == "WATCH_REVIEW"
    assert review.loc[0, "review_score"] > 60
    assert "HISTORY_GAP" in review.loc[0, "red_flags"]
    assert "DATA_GAP" not in review.loc[0, "red_flags"]


def test_build_limit_up_strategy_review_marks_missing_limit_up_pool_fields_as_data_gap() -> None:
    limit_up = pd.DataFrame(
        [
            {
                "symbol": "300750",
                "name": "宁德时代",
                "trade_date": "2026-07-08",
                "close": 250.0,
                "change_pct": pd.NA,
                "amount": pd.NA,
                "turnover_rate": 0.5,
                "seal_amount": 0,
                "first_limit_time": "",
                "last_limit_time": "",
                "break_count": pd.NA,
                "limit_up_stats": "1/1",
                "streak_count": pd.NA,
                "industry": "电力设备",
                "source": "test",
            }
        ]
    )

    review = build_limit_up_strategy_review(limit_up, pd.DataFrame(columns=["date", "symbol", "close", "amount"]))

    assert review.loc[0, "review_label"] == "DATA_GAP"
    assert review.loc[0, "review_score"] <= 60
    assert "DATA_GAP" in review.loc[0, "red_flags"]


def test_empty_limit_up_strategy_review_frame_has_columns() -> None:
    frame = empty_limit_up_strategy_review_frame()

    assert "review_score" in frame.columns
    assert frame.empty
