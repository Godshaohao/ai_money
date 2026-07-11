import asyncio
import json
from pathlib import Path

from fastapi import FastAPI

from backend.app import create_app
from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportTableRepository


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


def test_security_detail_endpoint_returns_symbol_evidence(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    initialize_database(db_path)
    ReportTableRepository(db_path).replace_table(
        "limit_up_strategy_review",
        columns=["symbol", "name", "review_label"],
        rows=[{"symbol": "002115", "name": "三维通信", "review_label": "WATCH_REVIEW"}],
        updated_at="2026-07-11T14:10:00+08:00",
    )
    app = create_app(root=tmp_path, db_path=db_path)

    status_code, body = _call_json(app, "GET", "/api/report/securities/002115")

    assert status_code == 200
    assert body["exists"] is True
    assert body["symbol"] == "002115"
    assert body["latest_review_label"] == "WATCH_REVIEW"
