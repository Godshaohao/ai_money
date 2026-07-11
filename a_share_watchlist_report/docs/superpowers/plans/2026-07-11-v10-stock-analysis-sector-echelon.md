# V10 Stock Analysis And Sector Echelon Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade AI-callable single-stock analysis from raw strategy evidence into a richer review report with sector echelon context.

**Architecture:** Build a pure analysis service from existing local outputs (`limit_up_pool.csv`, `limit_up_strategy_review.csv`, `excluded_stocks.csv`, `dragon_tiger.csv`) and existing SQLite strategy records. Expose it through a JSON CLI command for local AI agents; do not add a new data source or trading output.

**Tech Stack:** Python, pandas, SQLite repository, argparse CLI, pytest.

## Global Constraints

- Use only existing local outputs and SQLite state.
- Treat `industry` from `limit_up_pool.csv` as the first P0 sector/theme proxy.
- No BUY, SELL, target price, broker API, automated order, or trading recommendation.
- Output must be deterministic JSON for AI agents.
- Analysis must include a human review checklist instead of conclusions framed as orders.

---

## Task 1: Sector Echelon Builder

**Files:**
- Create: `a_share_watchlist_report/src/sector_echelon.py`
- Create: `a_share_watchlist_report/tests/test_sector_echelon.py`

**Interfaces:**
- Produces: `build_sector_echelons(limit_up_pool: pd.DataFrame) -> pd.DataFrame`
- Columns: `trade_date`, `industry`, `limit_up_count`, `first_board_count`, `second_board_count`, `high_board_count`, `max_streak_count`, `broken_count`, `total_amount`, `leader_symbols`, `leader_names`, `echelon_summary`

- [ ] Write failing tests for first/second/high board counts and leader sorting.
- [ ] Verify failure.
- [ ] Implement builder.
- [ ] Verify pass.

## Task 2: Single Stock Analysis Service

**Files:**
- Create: `a_share_watchlist_report/src/stock_analysis.py`
- Create: `a_share_watchlist_report/tests/test_stock_analysis.py`

**Interfaces:**
- Produces: `build_stock_analysis(symbol: str, output_dir: Path, db_path: Path) -> dict`
- Output sections: `identity`, `data_quality`, `limit_up_events`, `sector_echelon`, `strategy`, `dragon_tiger`, `review_checklist`, `safety`

- [ ] Write failing tests using fixture CSVs and strategy SQLite records.
- [ ] Verify failure.
- [ ] Implement service.
- [ ] Verify pass.

## Task 3: AI-Callable Analysis CLI

**Files:**
- Create: `a_share_watchlist_report/src/cli/analysis.py`
- Modify: `a_share_watchlist_report/src/cli/ai.py`
- Create: `a_share_watchlist_report/tests/test_analysis_cli.py`
- Modify: `a_share_watchlist_report/tests/test_ai_manifest_cli.py`

**Interfaces:**
- Produces: `python -m src.cli.analysis stock 603538 --json`
- Adds manifest tool: `analysis.stock`

- [ ] Write failing CLI and manifest tests.
- [ ] Verify failure.
- [ ] Implement CLI and manifest entry.
- [ ] Verify pass.

## Task 4: Verification And README

**Files:**
- Modify: `a_share_watchlist_report/README.md`

**Commands:**
- `python -m compileall .`
- `pytest -q`
- `python run_report.py`
- `python -m src.cli.strategy run all --json`
- `python -m src.cli.analysis stock 603538 --json`

- [ ] Add README examples.
- [ ] Run smoke commands.
- [ ] Confirm output is analysis-only and includes sector echelon.
