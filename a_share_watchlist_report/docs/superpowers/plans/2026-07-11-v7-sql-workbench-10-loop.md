# V7 SQL Workbench 10-Loop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn the current SQLite-backed table browser into a usable A-share research review workbench with pagination, sorting, filtering, and stock detail drill-down.

**Architecture:** Keep `run_report.py` as the data producer and SQLite as the application read model. Backend APIs read SQLite snapshots first and expose query parameters; frontend becomes a review queue UI that asks investment-review questions rather than merely displaying CSV files.

**Tech Stack:** Python, SQLite, FastAPI, pandas, React, TypeScript, CSS, Vitest, pytest.

---

### Loop 1: Table Query Contract
- Add backend tests for `limit`, `offset`, `search`, `sort_by`, `sort_dir`.
- Extend SQLite table repository to return `filtered_count`, `offset`, and `limit`.

### Loop 2: Table API Parameters
- Wire FastAPI query parameters into the table service.
- Preserve CSV fallback for missing SQLite snapshots.

### Loop 3: Frontend API Types
- Extend TypeScript types for pagination metadata.
- Let `fetchTable()` accept query options.

### Loop 4: Stock Detail Backend Contract
- Add a stock-detail service that collects rows for one symbol from key tables.
- Include summary fields: symbol, name, latest review label, risk flags, and sections.

### Loop 5: Stock Detail API Route
- Add `/api/report/securities/{symbol}`.
- Test success and empty detail behavior.

### Loop 6: Workbench Table Controls
- Add search input, page controls, and active sort state.
- Reload the active table when controls change.

### Loop 7: Sortable Table Headers
- Make table headers clickable.
- Keep stable button dimensions and clear sort indicator.

### Loop 8: Stock Detail Panel
- Clicking a row with `symbol` opens a side panel.
- Panel shows review, limit-up history, holding risk, exclusion reason, and dragon-tiger rows.

### Loop 9: UI Polish For Research Workflow
- Reframe labels as review workflow: “复核队列”, “筛选”, “排序”, “个股证据”.
- Keep dense operational style; no marketing hero.

### Loop 10: Full Verification And Upload
- Run Python compile, pytest, frontend tests, frontend build, report generation.
- Confirm backend reads `source=sqlite`.
- Push to GitHub.

---

### Self-Review
- The plan keeps trading outputs forbidden: no BUY, SELL, target price, orders, broker APIs, AI analysis, or automation.
- Static HTML remains export output, not the app source of truth.
- SQLite becomes the backend read model for the application.
