# V8 Strategy CLI Workbench Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a SQLite-backed strategy review loop that can run limit-up, watchlist, and holding-risk analysis from CLI, expose the results through FastAPI, and present them in a Chinese review workbench.

**Architecture:** Keep strategy logic in pure Python services, persist normalized run/candidate/evidence rows in SQLite, expose read-only API endpoints, and render a dense React review interface. The system remains analysis-only: no BUY/SELL labels, target prices, broker API, AI/ML, or auto trading.

**Tech Stack:** Python stdlib argparse, pandas, SQLite, FastAPI, React/Vite, Vitest, pytest.

---

## Engineering Boundaries

- Source of truth: `src/`, `backend/`, `frontend/src/`, `tests/`.
- Generated artifacts: `output/`, `frontend/dist/`, `data/workbench.sqlite`.
- CLI output is review text and persisted analysis only.
- Strategy modules may read existing CSV/report data and SQLite snapshots; they must not add new data sources.
- UI text should be Chinese except stable professional terms such as CLI, SQLite, API.

## Loop 1: Strategy SQLite Contract

**Files:**
- Modify: `a_share_watchlist_report/backend/db/schema.py`
- Modify: `a_share_watchlist_report/backend/repositories/sqlite_repo.py`
- Create: `a_share_watchlist_report/tests/test_strategy_repository.py`

- [ ] Write failing tests for creating strategy runs, replacing candidates/evidence, listing runs, and inspecting a symbol.
- [ ] Run the new test and verify it fails because the repository does not exist.
- [ ] Implement `StrategyRepository` and strategy tables.
- [ ] Run the new test and verify it passes.

## Loop 2: Unified Strategy Builder

**Files:**
- Create: `a_share_watchlist_report/src/strategy_review.py`
- Create: `a_share_watchlist_report/tests/test_strategy_review.py`

- [ ] Write failing tests that build candidates from limit-up review, watchlist, and holding-risk frames.
- [ ] Verify failure.
- [ ] Implement normalized candidate/evidence records.
- [ ] Verify pass.

## Loop 3: CLI Strategy Runner

**Files:**
- Create: `a_share_watchlist_report/src/cli/__init__.py`
- Create: `a_share_watchlist_report/src/cli/strategy.py`
- Create: `a_share_watchlist_report/tests/test_strategy_cli.py`

- [ ] Write failing CLI tests for `run all`, `list-runs`, `inspect SYMBOL`, and `export`.
- [ ] Verify failure.
- [ ] Implement argparse CLI using existing output CSVs and SQLite.
- [ ] Verify pass.

## Loop 4: Backend Strategy API

**Files:**
- Create: `a_share_watchlist_report/backend/services/strategy.py`
- Create: `a_share_watchlist_report/backend/routes/strategy.py`
- Modify: `a_share_watchlist_report/backend/app.py`
- Create: `a_share_watchlist_report/tests/test_backend_strategy_api.py`

- [ ] Write failing API tests for runs, candidates, and symbol evidence.
- [ ] Verify failure.
- [ ] Implement API service and route.
- [ ] Verify pass.

## Loop 5: Frontend Strategy Workbench

**Files:**
- Modify: `a_share_watchlist_report/frontend/src/types.ts`
- Modify: `a_share_watchlist_report/frontend/src/api.ts`
- Modify: `a_share_watchlist_report/frontend/src/App.tsx`
- Modify: `a_share_watchlist_report/frontend/src/styles.css`
- Modify: `a_share_watchlist_report/frontend/src/App.test.tsx`

- [ ] Write failing frontend test that expects the strategy workbench labels and candidate rows.
- [ ] Verify failure.
- [ ] Add strategy API calls, module filter, candidate table, and evidence drawer copy in Chinese.
- [ ] Verify pass.

## Loop 6: Smoke And Contract Verification

**Commands:**
- `cd a_share_watchlist_report && python -m compileall .`
- `cd a_share_watchlist_report && pytest -q`
- `cd a_share_watchlist_report/frontend && npm run test`
- `cd a_share_watchlist_report/frontend && npm run build`
- `cd a_share_watchlist_report && python run_report.py`
- `cd a_share_watchlist_report && python -m src.cli.strategy run all`
- `cd a_share_watchlist_report && python -m src.cli.strategy list-runs`

- [ ] Run all commands fresh.
- [ ] Inspect CLI output for analysis-only wording.
- [ ] Report exact pass/fail evidence.
