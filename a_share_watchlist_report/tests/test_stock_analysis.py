from pathlib import Path

import pandas as pd

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository
from src.stock_analysis import build_stock_analysis


def test_build_stock_analysis_includes_sector_echelon_and_review_checklist(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "workbench.sqlite"
    pd.DataFrame(
        [
            {
                "symbol": "603538",
                "name": "美诺华",
                "trade_date": "2026-07-10",
                "close": 30.88,
                "change_pct": 10.01,
                "amount": 2_134_658_736,
                "turnover_rate": 21.23,
                "seal_amount": 55_938_471,
                "first_limit_time": "100758",
                "last_limit_time": "132658",
                "break_count": 9,
                "limit_up_stats": "1/1",
                "streak_count": 1,
                "industry": "化学制药",
                "source": "fixture",
            },
            {
                "symbol": "600276",
                "name": "恒瑞医药",
                "trade_date": "2026-07-10",
                "close": 60,
                "change_pct": 10,
                "amount": 800_000_000,
                "turnover_rate": 4,
                "seal_amount": 200_000_000,
                "first_limit_time": "092500",
                "last_limit_time": "092500",
                "break_count": 0,
                "limit_up_stats": "2/2",
                "streak_count": 2,
                "industry": "化学制药",
                "source": "fixture",
            },
            {
                "symbol": "603538",
                "name": "美诺华",
                "trade_date": "2026-07-09",
                "close": 39.39,
                "change_pct": 10.01,
                "amount": 1_500_000_000,
                "turnover_rate": 18.23,
                "seal_amount": 30_000_000,
                "first_limit_time": "103000",
                "last_limit_time": "143000",
                "break_count": 2,
                "limit_up_stats": "1/1",
                "streak_count": 1,
                "industry": "化学制药",
                "source": "fixture",
            },
        ]
    ).to_csv(output_dir / "limit_up_pool.csv", index=False)
    pd.DataFrame(
        [
            {
                "symbol": "603538",
                "name": "美诺华",
                "trade_date": "2026-07-10",
                "review_score": 69,
                "review_label": "WATCH_REVIEW",
                "red_flags": "HISTORY_GAP,BROKEN_BOARD_RISK",
                "reason": "近期涨停复核",
            }
        ]
    ).to_csv(output_dir / "limit_up_strategy_review.csv", index=False)
    pd.DataFrame(
        [{"symbol": "603538", "name": "美诺华", "industry": "近期涨停", "exclude_reason": "no price data"}]
    ).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame(columns=["symbol", "name", "trade_date", "net_buy_amount"]).to_csv(
        output_dir / "dragon_tiger.csv", index=False
    )
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    run_id = repo.create_run("all", "RUNNING", "2026-07-11T10:00:00+08:00", {})
    repo.replace_candidates(
        run_id,
        [
            {
                "module": "limit_up",
                "symbol": "603538",
                "name": "美诺华",
                "score": 69,
                "label": "WATCH_REVIEW",
                "risk_flags": "HISTORY_GAP,BROKEN_BOARD_RISK",
                "reason": "近期涨停复核",
                "source_table": "limit_up_strategy_review",
                "source_row": {},
            }
        ],
    )
    repo.finish_run(run_id, "SUCCESS", "2026-07-11T10:01:00+08:00", "完成")

    analysis = build_stock_analysis("603538", output_dir=output_dir, db_path=db_path)

    assert analysis["identity"]["symbol"] == "603538"
    assert analysis["identity"]["name"] == "美诺华"
    assert analysis["identity"]["industry"] == "化学制药"
    assert analysis["data_quality"]["flags"] == ["no price data", "HISTORY_GAP"]
    assert analysis["limit_up_events"][0]["break_count"] == 9
    assert analysis["sector_echelon"][0]["industry"] == "化学制药"
    assert analysis["sector_echelon"][0]["second_board_count"] == 1
    assert analysis["review_brief"]["review_state"] == "风险优先复核"
    assert "炸板 9 次" in analysis["review_brief"]["headline"]
    assert "首封 10:07:58" in analysis["review_brief"]["headline"]
    assert "封单 5593.85 万" in analysis["review_brief"]["headline"]
    assert any(item["label"] == "板块梯队" for item in analysis["review_brief"]["evidence_metrics"])
    assert any("数据质量" in item for item in analysis["review_brief"]["risk_notes"])
    assert any("较上一条涨停收盘变化 -21.60%" in item for item in analysis["review_brief"]["risk_notes"])
    assert any("炸板占比 50.0%" in item for item in analysis["review_brief"]["risk_notes"])
    assert any("回封" in item for item in analysis["review_brief"]["next_actions"])
    assert analysis["data_availability"]["limit_up_event_count"] == 2
    assert analysis["data_availability"]["price_history_available"] is False
    assert "无法计算 MA、动量、回撤" in analysis["data_availability"]["missing_notes"][0]
    assert analysis["data_availability"]["sector_event_count"] == 2
    assert analysis["event_timeline"][0]["event_profile"] == "分歧回封"
    assert analysis["event_timeline"][0]["first_limit_time"] == "10:07:58"
    assert analysis["event_timeline"][0]["seal_amount_text"] == "5593.85 万"
    assert analysis["event_timeline"][0]["amount_text"] == "21.35 亿"
    assert analysis["event_timeline"][0]["close_change_from_previous_event_pct"] < 0
    assert analysis["sector_position"]["industry"] == "化学制药"
    assert analysis["sector_position"]["broken_ratio_pct"] == 50.0
    assert analysis["sector_position"]["stock_is_leader"] is True
    assert analysis["strategy"]["candidates"][0]["label"] == "WATCH_REVIEW"
    assert any("炸板" in item for item in analysis["review_checklist"])
    assert analysis["safety"]["analysis_only"] is True
