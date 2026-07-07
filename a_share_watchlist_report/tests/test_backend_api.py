import asyncio
import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi import FastAPI

from backend.app import create_app
from backend.repositories.sqlite_repo import ReportRunRepository


def _write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.html").write_text("<html>NEUTRAL</html>", encoding="utf-8")
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "holding_risk.csv", index=False)
    pd.DataFrame([{"status": "NEUTRAL"}]).to_csv(output_dir / "market_regime.csv", index=False)
    (output_dir / "data_quality_status.json").write_text(
        json.dumps({"ok": True, "warnings": []}),
        encoding="utf-8",
    )


def _call_json(app: FastAPI, method: str, path: str) -> tuple[int, dict]:
    messages: list[dict] = []
    body_sent = False

    async def receive() -> dict:
        nonlocal body_sent
        if body_sent:
            return {"type": "http.disconnect"}
        body_sent = True
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


def test_health_endpoint_returns_ok(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/health")

    assert status_code == 200
    assert body["status"] == "ok"


def test_report_summary_endpoint_returns_artifact_summary(tmp_path: Path) -> None:
    _write_outputs(tmp_path / "output")
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/summary")

    assert status_code == 200
    assert body["exists"] is True
    assert body["row_counts"]["watchlist"] == 1


def test_report_run_endpoint_records_successful_run(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"

    def fake_runner() -> int:
        _write_outputs(tmp_path / "output")
        return 0

    app = create_app(root=tmp_path, db_path=db_path, runner=fake_runner)

    status_code, response = _call_json(app, "POST", "/api/report/run")

    assert status_code == 200
    assert response["status"] == "SUCCESS"
    runs = ReportRunRepository(db_path).list_runs()
    assert len(runs) == 1
    assert runs[0]["status"] == "SUCCESS"


def test_report_runs_endpoint_lists_history(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    app = create_app(root=tmp_path, db_path=db_path, runner=lambda: 0)
    _call_json(app, "POST", "/api/report/run")

    status_code, response = _call_json(app, "GET", "/api/report/runs")

    assert status_code == 200
    assert response["runs"][0]["status"] == "SUCCESS"


def test_report_run_endpoint_rejects_concurrent_run(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite", runner=lambda: 0)
    assert app.state.run_lock.acquire(blocking=False)

    try:
        status_code, body = _call_json(app, "POST", "/api/report/run")
    finally:
        app.state.run_lock.release()

    assert status_code == 409
    assert body["detail"] == "report run already in progress"


def test_report_run_endpoint_releases_lock_when_database_fails(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite", runner=lambda: 0)

    def fail_database() -> None:
        raise RuntimeError("synthetic database failure")

    app.state.ensure_database = fail_database

    with pytest.raises(RuntimeError, match="synthetic database failure"):
        _call_json(app, "POST", "/api/report/run")

    assert app.state.run_lock.acquire(blocking=False)
    app.state.run_lock.release()


def test_importing_backend_app_does_not_create_default_database() -> None:
    import backend.app as backend_app

    assert backend_app.app.state.initialize_on_create is False


def test_report_summary_endpoint_handles_malformed_csv(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    _write_outputs(output_dir)
    (output_dir / "watchlist.csv").write_text("", encoding="utf-8")
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")

    status_code, body = _call_json(app, "GET", "/api/report/summary")

    assert status_code == 200
    assert body["exists"] is False
    assert body["data_quality"]["ok"] is False
    assert "watchlist.csv" in body["data_quality"]["errors"][0]
