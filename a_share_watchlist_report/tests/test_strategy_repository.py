from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository


def test_strategy_repository_records_runs_candidates_and_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = StrategyRepository(db_path)

    run_id = repo.create_run(
        strategy_name="all",
        status="RUNNING",
        started_at="2026-07-11T09:30:00+08:00",
        params={"modules": ["limit_up", "watchlist", "holding_risk"]},
    )
    repo.replace_candidates(
        run_id,
        [
            {
                "module": "limit_up",
                "symbol": "002115",
                "name": "三维通信",
                "score": 82,
                "label": "WATCH_REVIEW",
                "risk_flags": "BROKEN_BOARD_RISK",
                "reason": "涨停复核",
                "source_table": "limit_up_strategy_review",
                "source_row": {"review_score": 82},
            },
            {
                "module": "holding_risk",
                "symbol": "600519",
                "name": "贵州茅台",
                "score": 45,
                "label": "RISK_REVIEW",
                "risk_flags": "DRAWDOWN",
                "reason": "持仓风险复核",
                "source_table": "holding_risk",
                "source_row": {"holding_risk": "HIGH"},
            },
        ],
    )
    repo.replace_evidence(
        run_id,
        [
            {
                "symbol": "002115",
                "module": "limit_up",
                "evidence_type": "limit_up",
                "title": "涨停证据",
                "detail": "复核分 82",
                "payload": {"review_label": "WATCH_REVIEW"},
            }
        ],
    )
    repo.replace_metrics(run_id, {"candidate_count": 2, "risk_count": 1})
    repo.finish_run(
        run_id,
        status="SUCCESS",
        finished_at="2026-07-11T09:31:00+08:00",
        message="策略复核完成",
    )

    runs = repo.list_runs()
    candidates = repo.list_candidates(run_id=run_id, module="limit_up")
    detail = repo.inspect_symbol("002115")

    assert runs[0]["id"] == run_id
    assert runs[0]["strategy_name"] == "all"
    assert runs[0]["metrics"]["candidate_count"] == 2
    assert candidates["filtered_count"] == 1
    assert candidates["rows"][0]["symbol"] == "002115"
    assert candidates["rows"][0]["source_row"] == {"review_score": 82}
    assert detail["symbol"] == "002115"
    assert detail["exists"] is True
    assert detail["candidates"][0]["label"] == "WATCH_REVIEW"
    assert detail["evidence"][0]["title"] == "涨停证据"


def test_strategy_repository_filters_sorts_and_paginates_candidates(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    run_id = repo.create_run("all", "RUNNING", "2026-07-11T09:30:00+08:00", {})
    repo.replace_candidates(
        run_id,
        [
            {
                "module": "watchlist",
                "symbol": "600519",
                "name": "贵州茅台",
                "score": 72,
                "label": "WATCH_REVIEW",
                "risk_flags": "",
                "reason": "观察池复核",
                "source_table": "watchlist",
                "source_row": {},
            },
            {
                "module": "watchlist",
                "symbol": "300750",
                "name": "宁德时代",
                "score": 88,
                "label": "CORE_REVIEW",
                "risk_flags": "",
                "reason": "观察池复核",
                "source_table": "watchlist",
                "source_row": {},
            },
            {
                "module": "holding_risk",
                "symbol": "000001",
                "name": "平安银行",
                "score": 40,
                "label": "RISK_REVIEW",
                "risk_flags": "DRAWDOWN",
                "reason": "持仓风险复核",
                "source_table": "holding_risk",
                "source_row": {},
            },
        ],
    )

    page = repo.list_candidates(
        run_id=run_id,
        module="watchlist",
        search="观察池",
        sort_by="score",
        sort_dir="asc",
        limit=1,
        offset=1,
    )

    assert page["row_count"] == 3
    assert page["filtered_count"] == 2
    assert page["rows"] == [
        {
            "id": page["rows"][0]["id"],
            "run_id": run_id,
            "module": "watchlist",
            "symbol": "300750",
            "name": "宁德时代",
            "score": 88.0,
            "label": "CORE_REVIEW",
            "risk_flags": "",
            "reason": "观察池复核",
            "source_table": "watchlist",
            "source_row": {},
        }
    ]


def test_strategy_repository_reads_latest_successful_run_when_newer_run_is_running(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    success_id = repo.create_run("all", "RUNNING", "2026-07-11T09:30:00+08:00", {})
    repo.replace_candidates(
        success_id,
        [
            {
                "module": "limit_up",
                "symbol": "002115",
                "name": "三维通信",
                "score": 89,
                "label": "WATCH_REVIEW",
                "risk_flags": "HISTORY_GAP",
                "reason": "涨停复核",
                "source_table": "limit_up_strategy_review",
                "source_row": {},
            }
        ],
    )
    repo.finish_run(success_id, "SUCCESS", "2026-07-11T09:31:00+08:00", "完成")
    running_id = repo.create_run("all", "RUNNING", "2026-07-11T09:32:00+08:00", {})

    candidates = repo.list_candidates()
    detail = repo.inspect_symbol("002115")

    assert running_id > success_id
    assert candidates["run_id"] == success_id
    assert candidates["rows"][0]["symbol"] == "002115"
    assert detail["exists"] is True
