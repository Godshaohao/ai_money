# V11 Sector Workbench And Stock Detail Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Promote sector/theme echelon review to the first workflow and make stock detail a structured review panel.

**Architecture:** Keep the current single data source and SQLite-backed app. Add analysis API endpoints that wrap existing CSV artifacts and strategy database evidence, then update the React workbench to render sector cards before generic tables.

**Tech Stack:** Python, FastAPI, pandas, SQLite, React, TypeScript, Vitest.

## Global Constraints

- Do not add a second market data source.
- Do not add BUY, SELL, target price, broker orders, or automated trading outputs.
- Keep algorithm output explainable: rule summaries, table grouping, and evidence links only.
- Keep UI copy in Chinese except established technical labels such as CLI, JSON, DATA_GAP.

---

### Task 1: Analysis API Contract

**Files:**
- Create: `backend/services/analysis.py`
- Create: `backend/routes/analysis.py`
- Modify: `backend/app.py`
- Test: `tests/test_backend_analysis_api.py`

**Interfaces:**
- Produces: `build_sector_workbench(output_dir: Path) -> dict`
- Produces: `build_stock_review(output_dir: Path, db_path: Path, symbol: str) -> dict`
- Produces: `GET /api/analysis/sectors`
- Produces: `GET /api/analysis/stocks/{symbol}`

- [ ] Write failing backend API tests for sector cards and stock detail.
- [ ] Implement analysis service by reusing `src.sector_echelon.build_sector_echelons()` and `src.stock_analysis.build_stock_analysis()`.
- [ ] Register the analysis router in `backend/app.py`.
- [ ] Run `pytest tests/test_backend_analysis_api.py -q`.

### Task 2: Frontend Data Contract

**Files:**
- Modify: `frontend/src/types.ts`
- Modify: `frontend/src/api.ts`
- Modify: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `GET /api/analysis/sectors`
- Consumes: `GET /api/analysis/stocks/{symbol}`
- Produces: `fetchSectorWorkbench()`
- Produces: `fetchStockAnalysis(symbol)`

- [ ] Add TypeScript types for sector cards and stock analysis.
- [ ] Add API client functions.
- [ ] Update App test fixtures to include sector workbench responses.
- [ ] Run `npm run test -- --run` and confirm the frontend test fails before UI implementation.

### Task 3: Sector Workbench UI

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `SectorWorkbench`
- Produces: first-screen sector card grid with board ladder, leaders, risk, and click-to-review.

- [ ] Render “题材梯队工作台” above the generic strategy/table sections.
- [ ] Show latest trade date, sector count, limit-up count, broken-board count, and high-board count.
- [ ] Render card fields: industry, echelon summary, amount, leader names, risk flags.
- [ ] Make leader symbols clickable to open stock detail.
- [ ] Run `npm run test -- --run`.

### Task 4: Structured Stock Detail UI

**Files:**
- Modify: `frontend/src/App.tsx`
- Modify: `frontend/src/styles.css`
- Test: `frontend/src/App.test.tsx`

**Interfaces:**
- Consumes: `StockAnalysis`
- Produces: drawer sections for data quality, latest event, sector echelon, strategy labels, checklist.

- [ ] Replace the new stock analysis drawer content with Chinese structured sections.
- [ ] Keep existing raw security detail drawer for generic table clicks.
- [ ] Ensure no BUY/SELL/target price wording appears.
- [ ] Run `npm run test -- --run`.

### Task 5: Verification

**Files:**
- No new files.

- [ ] Run `python -m compileall .`.
- [ ] Run `pytest -q`.
- [ ] Run `python run_report.py`.
- [ ] Run `python -m src.cli.strategy run all --json`.
- [ ] Run `npm run test -- --run` in `frontend`.
- [ ] Run `npm run build` in `frontend`.
