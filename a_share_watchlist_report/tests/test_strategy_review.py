import pandas as pd

from src.strategy_review import build_strategy_records


def test_build_strategy_records_combines_limit_up_watchlist_and_holding_risk() -> None:
    limit_up = pd.DataFrame(
        [
            {
                "symbol": "002115",
                "name": "三维通信",
                "review_score": 82,
                "review_label": "DATA_REVIEW",
                "red_flags": "HISTORY_GAP,BROKEN_BOARD_RISK",
                "hard_flags": "HISTORY_GAP,BROKEN_BOARD_RISK",
                "reason": "涨停复核",
            }
        ]
    )
    watchlist = pd.DataFrame(
        [
            {
                "symbol": "600519",
                "name": "贵州茅台",
                "rank": 2,
                "momentum_12m": 0.28,
                "momentum_6m": 0.12,
                "max_drawdown_60d": -0.08,
                "avg_amount_20d": 1_200_000_000,
                "reason": "进入观察",
            }
        ]
    )
    holding_risk = pd.DataFrame(
        [
            {
                "symbol": "300750",
                "name": "宁德时代",
                "drawdown_from_cost": -0.18,
                "above_ma200": False,
                "risk_action": "REDUCE_EXPOSURE_REVIEW",
                "reason": "持仓风险复核",
            }
        ]
    )

    result = build_strategy_records(
        limit_up_review=limit_up,
        watchlist=watchlist,
        holding_risk=holding_risk,
        modules=["limit_up", "watchlist", "holding_risk"],
    )

    assert result.metrics == {
        "candidate_count": 3,
        "limit_up_count": 1,
        "watchlist_count": 1,
        "holding_risk_count": 1,
        "risk_count": 2,
    }
    assert [candidate["module"] for candidate in result.candidates] == [
        "limit_up",
        "watchlist",
        "holding_risk",
    ]
    assert result.candidates[0]["score"] == 82.0
    assert result.candidates[0]["label"] == "DATA_REVIEW"
    assert result.candidates[1]["label"] == "WATCH_REVIEW"
    assert result.candidates[2]["label"] == "RISK_REVIEW"
    assert result.candidates[2]["risk_flags"] == "BELOW_MA200"
    assert {item["evidence_type"] for item in result.evidence} == {
        "limit_up",
        "watchlist",
        "holding_risk",
    }


def test_build_strategy_records_can_limit_modules() -> None:
    watchlist = pd.DataFrame([{"symbol": "600519", "name": "贵州茅台", "rank": 1, "reason": "进入观察"}])
    holding_risk = pd.DataFrame([{"symbol": "300750", "name": "宁德时代", "reason": "持仓风险复核"}])

    result = build_strategy_records(
        limit_up_review=pd.DataFrame(),
        watchlist=watchlist,
        holding_risk=holding_risk,
        modules=["watchlist"],
    )

    assert [candidate["module"] for candidate in result.candidates] == ["watchlist"]
    assert result.metrics["candidate_count"] == 1
    assert result.metrics["holding_risk_count"] == 0
