import asyncio
import json
from pathlib import Path

import pandas as pd
from fastapi import FastAPI

from backend.app import create_app


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


def test_table_endpoint_returns_watchlist_rows(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519", "name": "贵州茅台"}]).to_csv(output_dir / "watchlist.csv", index=False)
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/tables/watchlist")

    assert status_code == 200
    assert body["name"] == "watchlist"
    assert body["rows"][0]["symbol"] == "600519"


def test_table_endpoint_rejects_unknown_table(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/tables/orders")

    assert status_code == 404
    assert body["detail"] == "unknown report table"
