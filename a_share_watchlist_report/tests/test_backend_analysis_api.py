import asyncio
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

from backend.app import create_app
from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository
from backend.services import analysis as analysis_service


def _call_json(app: FastAPI, method: str, path: str) -> tuple[int, dict]:
    messages: list[dict] = []
    sent = False

    async def receive() -> dict:
        nonlocal sent
        if sent:
            return {"type": "http.disconnect"}
        sent = True
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message: dict) -> None:
        messages.append(message)

    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": method,
        "path": path,
        "raw_path": path.encode("ascii"),
        "root_path": "",
        "scheme": "http",
        "query_string": b"",
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return int(start["status"]), json.loads(body.decode("utf-8"))


def _seed_analysis_fixture(root: Path, db_path: Path) -> None:
    output_dir = root / "output"
    output_dir.mkdir()
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
                "symbol": "002115",
                "name": "三维通信",
                "trade_date": "2026-07-10",
                "close": 8,
                "change_pct": 10,
                "amount": 500_000_000,
                "turnover_rate": 8,
                "seal_amount": 90_000_000,
                "first_limit_time": "093000",
                "last_limit_time": "093000",
                "break_count": 0,
                "limit_up_stats": "1/1",
                "streak_count": 1,
                "industry": "通信设备",
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


def test_analysis_api_returns_sector_workbench_and_stock_review(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    _seed_analysis_fixture(tmp_path, db_path)
    app = create_app(root=tmp_path, db_path=db_path)

    status_code, sectors = _call_json(app, "GET", "/api/analysis/sectors")

    assert status_code == 200
    assert sectors["latest_trade_date"] == "2026-07-10"
    assert sectors["summary"]["sector_count"] == 2
    assert sectors["summary"]["limit_up_count"] == 3
    assert sectors["cards"][0]["industry"] == "化学制药"
    assert sectors["cards"][0]["leader_symbols"] == ["600276", "603538"]
    assert "炸板 1" in sectors["cards"][0]["risk_flags"]

    status_code, detail = _call_json(app, "GET", "/api/analysis/stocks/603538")

    assert status_code == 200
    assert detail["analysis"]["identity"]["name"] == "美诺华"
    assert detail["analysis"]["sector_echelon"][0]["industry"] == "化学制药"
    assert detail["analysis"]["review_brief"]["review_state"] == "风险优先复核"
    assert any("复核" in item for item in detail["analysis"]["review_checklist"])


def test_analysis_stock_review_uses_cache_until_inputs_change(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    _seed_analysis_fixture(tmp_path, db_path)
    cache = analysis_service.AnalysisCache()
    calls = {"count": 0}

    def fake_build_stock_analysis(symbol: str, output_dir: Path, db_path: Path) -> dict:
        calls["count"] += 1
        return {
            "identity": {"symbol": symbol, "name": "缓存样本", "industry": "化学制药"},
            "review_brief": {"headline": f"调用 {calls['count']}"},
        }

    monkeypatch.setattr(analysis_service, "build_stock_analysis", fake_build_stock_analysis)

    first = analysis_service.build_stock_review(tmp_path / "output", db_path, "603538", cache=cache)
    second = analysis_service.build_stock_review(tmp_path / "output", db_path, "603538", cache=cache)

    assert first == second
    assert calls["count"] == 1
