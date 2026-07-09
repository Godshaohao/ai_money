# A-share Backend Foundation V2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a local FastAPI + SQLite backend around the existing static A-share report pipeline while preserving the current CLI smoke check and output contract.

**Architecture:** Keep `run_report.py` as the canonical report generator. Add a thin backend layer that can initialize a local SQLite database, trigger a report run, record run metadata, and expose generated CSV/JSON/HTML artifact summaries through HTTP APIs. SQLite stores application state and run history only; Parquet remains the daily bar cache.

**Tech Stack:** Python, FastAPI, SQLite from the standard library, pandas, pytest, existing AKShare pipeline.

---

## Guardrails

- Keep `python run_report.py` working exactly as a standalone local report command.
- Keep existing P0 outputs: `report.html`, `watchlist.csv`, `excluded_stocks.csv`, `holding_risk.csv`, `market_regime.csv`, `data_quality_status.json`.
- Do not add broker APIs, order generation, BUY/SELL labels, target prices, account login, ML, AI commentary, or backtesting.
- Do not replace AKShare/EastMoney current data path in this phase.
- Do not build the React frontend in V2; V2 only prepares backend contracts for V3.
- Generated SQLite files live under `a_share_watchlist_report/data/` and stay out of git.

## File Structure

- Modify `a_share_watchlist_report/requirements.txt`
  - Add `fastapi` and `uvicorn`.
- Modify `a_share_watchlist_report/requirements-dev.txt`
  - Add `httpx`, required by FastAPI `TestClient`.
- Modify `a_share_watchlist_report/.gitignore`
  - Ignore `data/*.sqlite`, `data/*.sqlite3`, and SQLite sidecar files.
- Create `a_share_watchlist_report/backend/__init__.py`
  - Package marker.
- Create `a_share_watchlist_report/backend/db/__init__.py`
  - Package marker.
- Create `a_share_watchlist_report/backend/db/schema.py`
  - Own SQLite connection and schema initialization.
- Create `a_share_watchlist_report/backend/repositories/__init__.py`
  - Package marker.
- Create `a_share_watchlist_report/backend/repositories/sqlite_repo.py`
  - Persist and read report run history.
- Create `a_share_watchlist_report/backend/services/__init__.py`
  - Package marker.
- Create `a_share_watchlist_report/backend/services/artifacts.py`
  - Read current output artifacts safely.
- Create `a_share_watchlist_report/backend/services/report_runner.py`
  - Wrap `run_report.main()` and record run status.
- Create `a_share_watchlist_report/backend/routes/__init__.py`
  - Package marker.
- Create `a_share_watchlist_report/backend/routes/health.py`
  - `GET /health`.
- Create `a_share_watchlist_report/backend/routes/report.py`
  - `GET /api/report/summary`, `GET /api/report/runs`, `POST /api/report/run`.
- Create `a_share_watchlist_report/backend/app.py`
  - FastAPI app factory and default app.
- Add `a_share_watchlist_report/tests/test_backend_repository.py`
  - Unit tests for schema and run history persistence.
- Add `a_share_watchlist_report/tests/test_backend_artifacts.py`
  - Unit tests for output artifact summary parsing.
- Add `a_share_watchlist_report/tests/test_backend_api.py`
  - API contract tests with `TestClient`.
- Modify `a_share_watchlist_report/README.md`
  - Document V2 backend commands and database location.

## Task 1: SQLite Run History

**Files:**
- Create: `a_share_watchlist_report/backend/__init__.py`
- Create: `a_share_watchlist_report/backend/db/__init__.py`
- Create: `a_share_watchlist_report/backend/db/schema.py`
- Create: `a_share_watchlist_report/backend/repositories/__init__.py`
- Create: `a_share_watchlist_report/backend/repositories/sqlite_repo.py`
- Test: `a_share_watchlist_report/tests/test_backend_repository.py`

- [ ] **Step 1: Write failing repository tests**

```python
from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportRunRepository


def test_initialize_database_creates_report_runs_table(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"

    initialize_database(db_path)

    repo = ReportRunRepository(db_path)
    assert repo.list_runs() == []


def test_report_run_repository_records_and_lists_runs_newest_first(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportRunRepository(db_path)

    first_id = repo.create_run(status="RUNNING", started_at="2026-07-07T01:00:00+00:00")
    repo.finish_run(first_id, status="SUCCESS", finished_at="2026-07-07T01:01:00+00:00", message="ok")
    second_id = repo.create_run(status="RUNNING", started_at="2026-07-07T02:00:00+00:00")
    repo.finish_run(second_id, status="FAILED", finished_at="2026-07-07T02:01:00+00:00", message="boom")

    runs = repo.list_runs()
    assert [run["id"] for run in runs] == [second_id, first_id]
    assert runs[0]["status"] == "FAILED"
    assert runs[0]["message"] == "boom"
    assert runs[1]["status"] == "SUCCESS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_repository.py -q`

Expected: FAIL because `backend.db.schema` does not exist.

- [ ] **Step 3: Implement SQLite schema and repository**

Create `backend/db/schema.py` with `initialize_database(db_path: Path) -> None`. It creates parent directories and a `report_runs` table with columns: `id`, `status`, `started_at`, `finished_at`, `message`.

Create `backend/repositories/sqlite_repo.py` with `ReportRunRepository` methods:
- `create_run(status: str, started_at: str) -> int`
- `finish_run(run_id: int, status: str, finished_at: str, message: str) -> None`
- `list_runs(limit: int = 20) -> list[dict]`

- [ ] **Step 4: Run repository tests**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_repository.py -q`

Expected: PASS.

## Task 2: Artifact Summary Service

**Files:**
- Create: `a_share_watchlist_report/backend/services/__init__.py`
- Create: `a_share_watchlist_report/backend/services/artifacts.py`
- Test: `a_share_watchlist_report/tests/test_backend_artifacts.py`

- [ ] **Step 1: Write failing artifact tests**

```python
import json
from pathlib import Path

import pandas as pd

from backend.services.artifacts import build_report_summary


def test_build_report_summary_reads_existing_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "report.html").write_text("<html>RISK_ON</html>", encoding="utf-8")
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "holding_risk.csv", index=False)
    pd.DataFrame([{"status": "POSITIVE"}]).to_csv(output_dir / "market_regime.csv", index=False)
    (output_dir / "data_quality_status.json").write_text(json.dumps({"ok": True, "warnings": []}), encoding="utf-8")

    summary = build_report_summary(output_dir)

    assert summary["exists"] is True
    assert summary["data_quality"]["ok"] is True
    assert summary["row_counts"]["watchlist"] == 1
    assert summary["row_counts"]["excluded_stocks"] == 0
    assert summary["row_counts"]["holding_risk"] == 1
    assert summary["row_counts"]["market_regime"] == 1
    assert summary["artifacts"]["report_html"].endswith("report.html")


def test_build_report_summary_reports_missing_outputs(tmp_path: Path) -> None:
    summary = build_report_summary(tmp_path / "output")

    assert summary["exists"] is False
    assert summary["data_quality"]["ok"] is False
    assert summary["missing_files"]
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_artifacts.py -q`

Expected: FAIL because `backend.services.artifacts` does not exist.

- [ ] **Step 3: Implement artifact summary**

`build_report_summary(output_dir: Path) -> dict` must:
- Require the six P0 files.
- Return `exists`, `missing_files`, `data_quality`, `row_counts`, and `artifacts`.
- Count CSV rows with pandas.
- Treat missing or malformed JSON as `{"ok": False, "errors": [...]}`.

- [ ] **Step 4: Run artifact tests**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_artifacts.py -q`

Expected: PASS.

## Task 3: FastAPI Report API

**Files:**
- Modify: `a_share_watchlist_report/requirements.txt`
- Modify: `a_share_watchlist_report/requirements-dev.txt`
- Modify: `a_share_watchlist_report/.gitignore`
- Create: `a_share_watchlist_report/backend/routes/__init__.py`
- Create: `a_share_watchlist_report/backend/routes/health.py`
- Create: `a_share_watchlist_report/backend/routes/report.py`
- Create: `a_share_watchlist_report/backend/services/report_runner.py`
- Create: `a_share_watchlist_report/backend/app.py`
- Test: `a_share_watchlist_report/tests/test_backend_api.py`

- [ ] **Step 1: Write failing API tests**

```python
import json
from pathlib import Path

import pandas as pd
from fastapi.testclient import TestClient

from backend.app import create_app
from backend.repositories.sqlite_repo import ReportRunRepository


def _write_outputs(output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "report.html").write_text("<html>NEUTRAL</html>", encoding="utf-8")
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "holding_risk.csv", index=False)
    pd.DataFrame([{"status": "NEUTRAL"}]).to_csv(output_dir / "market_regime.csv", index=False)
    (output_dir / "data_quality_status.json").write_text(json.dumps({"ok": True, "warnings": []}), encoding="utf-8")


def test_health_endpoint_returns_ok(tmp_path: Path) -> None:
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_report_summary_endpoint_returns_artifact_summary(tmp_path: Path) -> None:
    _write_outputs(tmp_path / "output")
    app = create_app(root=tmp_path, db_path=tmp_path / "data" / "workbench.sqlite")
    client = TestClient(app)

    response = client.get("/api/report/summary")

    assert response.status_code == 200
    body = response.json()
    assert body["exists"] is True
    assert body["row_counts"]["watchlist"] == 1


def test_report_run_endpoint_records_successful_run(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"

    def fake_runner() -> int:
        _write_outputs(tmp_path / "output")
        return 0

    app = create_app(root=tmp_path, db_path=db_path, runner=fake_runner)
    client = TestClient(app)

    response = client.post("/api/report/run")

    assert response.status_code == 200
    assert response.json()["status"] == "SUCCESS"
    runs = ReportRunRepository(db_path).list_runs()
    assert len(runs) == 1
    assert runs[0]["status"] == "SUCCESS"


def test_report_runs_endpoint_lists_history(tmp_path: Path) -> None:
    db_path = tmp_path / "data" / "workbench.sqlite"
    app = create_app(root=tmp_path, db_path=db_path, runner=lambda: 0)
    client = TestClient(app)
    client.post("/api/report/run")

    response = client.get("/api/report/runs")

    assert response.status_code == 200
    assert response.json()["runs"][0]["status"] == "SUCCESS"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_api.py -q`

Expected: FAIL before the API files and dependencies are implemented.

- [ ] **Step 3: Add dependencies**

`requirements.txt` must include:
- `fastapi`
- `uvicorn`

`requirements-dev.txt` must include:
- `httpx`

`.gitignore` must ignore:
- `data/*.sqlite`
- `data/*.sqlite3`
- `data/*.sqlite-wal`
- `data/*.sqlite-shm`

- [ ] **Step 4: Implement API**

`create_app(root: Path = ROOT, db_path: Path | None = None, runner: Callable[[], int] | None = None) -> FastAPI` must:
- Initialize SQLite during app creation.
- Store `root`, `output_dir`, `db_path`, and `runner` on `app.state`.
- Include health and report routers.

Endpoints:
- `GET /health` returns `{"status": "ok"}`.
- `GET /api/report/summary` returns `build_report_summary(output_dir)`.
- `GET /api/report/runs` returns `{"runs": repo.list_runs()}`.
- `POST /api/report/run` calls `run_report.main()` through `ReportRunner`, records `SUCCESS` for exit code `0`, otherwise `FAILED`, then returns run metadata plus current summary.

- [ ] **Step 5: Run API tests**

Run: `cd a_share_watchlist_report && pytest tests/test_backend_api.py -q`

Expected: PASS.

## Task 4: Documentation and Smoke Check

**Files:**
- Modify: `a_share_watchlist_report/README.md`

- [ ] **Step 1: Update README**

Add a `Local Backend API` section:

```markdown
## Local Backend API

V2 adds an optional local FastAPI backend around the existing report generator.

```bash
uvicorn backend.app:app --reload
```

Useful endpoints:

- `GET /health`
- `GET /api/report/summary`
- `POST /api/report/run`
- `GET /api/report/runs`

The backend writes run history to `data/workbench.sqlite`. The original CLI remains supported:

```bash
python run_report.py
```
```

- [ ] **Step 2: Run full verification**

Run:

```bash
cd a_share_watchlist_report
python -m compileall .
pytest -q
python run_report.py
```

Expected:
- compileall exits `0`.
- pytest exits `0`.
- `python run_report.py` exits `0`.
- Existing P0 output files still exist.

## Self-Review Checklist

- V2 backend does not remove or weaken the static report contract.
- SQLite stores run history only, not broker/account/order state.
- API endpoints expose report state and run control only.
- No BUY/SELL/target-price/trading-order language is introduced.
- Tests cover repository, artifact summary, and API contracts.
