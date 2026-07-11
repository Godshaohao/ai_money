import asyncio
import json
from pathlib import Path

from fastapi import FastAPI

from backend.app import create_app
from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository


def _call_json(app: FastAPI, method: str, path: str, query_string: bytes = b"") -> tuple[int, dict]:
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
        "query_string": query_string,
        "headers": [],
        "client": ("testclient", 50000),
        "server": ("testserver", 80),
    }
    asyncio.run(app(scope, receive, send))
    start = next(message for message in messages if message["type"] == "http.response.start")
    body = b"".join(message.get("body", b"") for message in messages if message["type"] == "http.response.body")
    return int(start["status"]), json.loads(body.decode("utf-8"))


def _seed_strategy(db_path: Path) -> int:
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    run_id = repo.create_run("all", "RUNNING", "2026-07-11T10:00:00+08:00", {"modules": ["watchlist"]})
    repo.replace_candidates(
        run_id,
        [
            {
                "module": "watchlist",
                "symbol": "600519",
                "name": "贵州茅台",
                "score": 100,
                "label": "CORE_REVIEW",
                "risk_flags": "",
                "reason": "观察池复核",
                "source_table": "watchlist",
                "source_row": {"rank": 1},
            }
        ],
    )
    repo.replace_evidence(
        run_id,
        [
            {
                "symbol": "600519",
                "module": "watchlist",
                "evidence_type": "watchlist",
                "title": "观察池证据",
                "detail": "观察池排名 1",
                "payload": {"rank": 1},
            }
        ],
    )
    repo.replace_metrics(run_id, {"candidate_count": 1, "risk_count": 0})
    repo.finish_run(run_id, "SUCCESS", "2026-07-11T10:01:00+08:00", "策略复核完成")
    return run_id


def test_strategy_api_returns_runs_candidates_and_symbol_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    run_id = _seed_strategy(db_path)
    app = create_app(root=tmp_path, db_path=db_path)

    status_code, runs = _call_json(app, "GET", "/api/strategy/runs")
    assert status_code == 200
    assert runs["runs"][0]["id"] == run_id
    assert runs["runs"][0]["metrics"]["candidate_count"] == 1

    status_code, candidates = _call_json(app, "GET", "/api/strategy/candidates", b"module=watchlist")
    assert status_code == 200
    assert candidates["rows"][0]["symbol"] == "600519"
    assert candidates["rows"][0]["label"] == "CORE_REVIEW"

    status_code, detail = _call_json(app, "GET", "/api/strategy/securities/600519")
    assert status_code == 200
    assert detail["exists"] is True
    assert detail["evidence"][0]["title"] == "观察池证据"
