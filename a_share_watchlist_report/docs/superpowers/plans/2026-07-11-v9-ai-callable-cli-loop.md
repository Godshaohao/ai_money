# V9 AI-Callable CLI Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the local A-share research application callable by Codex or other local AI agents through stable JSON CLI contracts.

**Architecture:** Add a small CLI contract layer shared by app/status, report, strategy, and AI manifest commands. Persist CLI calls into SQLite for auditability, keep outputs analysis-only, and leave the existing FastAPI/React workbench as the human interface.

**Tech Stack:** Python stdlib argparse/json/subprocess, pandas, SQLite, pytest, existing FastAPI/React app.

## Global Constraints

- AI-callable CLI means local shell commands with deterministic JSON output.
- No application chat UI in v9.
- No BUY, SELL, target price, broker API, automated order, or trading recommendation output.
- No new data source.
- CLI commands must be useful for both humans and AI agents.
- Generated files under `output/`, `data/`, and `frontend/dist/` are verification artifacts, not source of truth.

---

## Task 1: CLI JSON Contract And Audit Storage

**Files:**
- Create: `a_share_watchlist_report/src/cli/json_contract.py`
- Modify: `a_share_watchlist_report/backend/db/schema.py`
- Modify: `a_share_watchlist_report/backend/repositories/sqlite_repo.py`
- Create: `a_share_watchlist_report/tests/test_cli_json_contract.py`
- Create: `a_share_watchlist_report/tests/test_cli_audit_repository.py`

**Interfaces:**
- Produces: `build_cli_response(command: str, ok: bool, data: dict, warnings: list[str] | None = None, errors: list[str] | None = None) -> dict`
- Produces: `emit_cli_response(response: dict, as_json: bool) -> None`
- Produces: `CliAuditRepository.record_call(tool_name: str, status: str, started_at: str, finished_at: str, args: dict, result: dict) -> int`

- [ ] Write failing tests for deterministic JSON envelope and SQLite CLI audit rows.
- [ ] Run tests and verify failure.
- [ ] Implement JSON contract helper and `cli_tool_runs` table/repository.
- [ ] Run tests and verify pass.

## Task 2: AI Tool Manifest CLI

**Files:**
- Create: `a_share_watchlist_report/src/cli/ai.py`
- Create: `a_share_watchlist_report/tests/test_ai_manifest_cli.py`

**Interfaces:**
- Produces: `python -m src.cli.ai manifest --json`
- Produces tool entries for app status, report summary, report run, strategy run, strategy inspect, and strategy export.

- [ ] Write failing test that parses manifest JSON and checks safety notes.
- [ ] Run test and verify failure.
- [ ] Implement manifest command.
- [ ] Run test and verify pass.

## Task 3: App And Report CLI For Data Access

**Files:**
- Create: `a_share_watchlist_report/src/cli/app.py`
- Create: `a_share_watchlist_report/src/cli/report.py`
- Create: `a_share_watchlist_report/tests/test_app_report_cli.py`

**Interfaces:**
- Produces: `python -m src.cli.app status --json`
- Produces: `python -m src.cli.report summary --json`
- Produces: `python -m src.cli.report run --json`

- [ ] Write failing tests using temporary output/data directories.
- [ ] Run tests and verify failure.
- [ ] Implement status, summary, and run commands.
- [ ] Run tests and verify pass.

## Task 4: Strategy CLI JSON Mode

**Files:**
- Modify: `a_share_watchlist_report/src/cli/strategy.py`
- Modify: `a_share_watchlist_report/tests/test_strategy_cli.py`

**Interfaces:**
- Extends: `run`, `list-runs`, `inspect`, and `export` with `--json`.
- JSON output includes `ok`, `command`, `data`, `warnings`, `errors`, and `safety`.

- [ ] Add failing tests for JSON mode on strategy run/list/inspect/export.
- [ ] Run tests and verify failure.
- [ ] Implement JSON mode and CLI audit writes.
- [ ] Run tests and verify pass.

## Task 5: Smoke Verification And Docs

**Files:**
- Modify: `a_share_watchlist_report/README.md`

**Commands:**
- `cd a_share_watchlist_report && python -m compileall .`
- `cd a_share_watchlist_report && pytest -q`
- `cd a_share_watchlist_report && python run_report.py`
- `cd a_share_watchlist_report && python -m src.cli.ai manifest --json`
- `cd a_share_watchlist_report && python -m src.cli.app status --json`
- `cd a_share_watchlist_report && python -m src.cli.report summary --json`
- `cd a_share_watchlist_report && python -m src.cli.strategy run all --json`
- `cd a_share_watchlist_report && python -m src.cli.strategy inspect 002115 --json`

- [ ] Add README examples for local AI agents.
- [ ] Run all smoke commands fresh.
- [ ] Confirm JSON outputs do not contain BUY, SELL, target price, broker action, or automated order fields.
