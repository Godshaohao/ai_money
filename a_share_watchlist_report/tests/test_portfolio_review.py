import pandas as pd

from src.portfolio_review import PORTFOLIO_REVIEW_COLUMNS, build_portfolio_review, empty_portfolio_review_frame


def test_build_portfolio_review_adds_position_diagnostics() -> None:
    holding_risk = pd.DataFrame(
        [
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "shares": 100,
                "cost_basis": 90.0,
                "latest_close": 110.0,
                "drawdown_from_cost": 110.0 / 90.0 - 1,
                "above_ma200": True,
                "max_drawdown_60d": -0.05,
                "avg_amount_20d": 100_000_000.0,
                "risk_action": "WATCH",
                "reason": "未触发明显风险规则，继续观察。",
            },
            {
                "symbol": "000001",
                "name": "平安银行",
                "shares": 1000,
                "cost_basis": 10.0,
                "latest_close": 8.0,
                "drawdown_from_cost": -0.2,
                "above_ma200": False,
                "max_drawdown_60d": -0.2,
                "avg_amount_20d": 1_000_000.0,
                "risk_action": "REDUCE_REVIEW",
                "reason": "价格低于 MA200，进入风险敞口复核。",
            },
        ]
    )
    universe = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "000001", "name": "平安银行", "industry": "银行"},
        ]
    )

    review = build_portfolio_review(holding_risk, universe)

    assert list(review.columns) == PORTFOLIO_REVIEW_COLUMNS
    assert review.loc[0, "symbol"] == "600519"
    assert review.loc[0, "position_value"] == 11_000
    assert review.loc[0, "cost_value"] == 9_000
    assert review.loc[0, "unrealized_pnl"] == 2_000
    assert review.loc[0, "portfolio_weight"] == 11_000 / 19_000
    assert "CONCENTRATED_WEIGHT" in review.loc[0, "risk_flags"]

    weak = review.loc[review["symbol"] == "000001"].iloc[0]
    assert weak["unrealized_return"] == -0.2
    assert "ACTION_REVIEW" in weak["risk_flags"]
    assert "UNDER_COST" in weak["risk_flags"]
    assert "DRAWDOWN_60D_15" in weak["risk_flags"]
    assert "LOW_LIQUIDITY" in weak["risk_flags"]
    assert "BUY" not in ",".join(review.astype(str).to_numpy().ravel())
    assert "SELL" not in ",".join(review.astype(str).to_numpy().ravel())


def test_empty_portfolio_review_frame_has_contract_columns() -> None:
    frame = empty_portfolio_review_frame()

    assert list(frame.columns) == PORTFOLIO_REVIEW_COLUMNS
    assert frame.empty
