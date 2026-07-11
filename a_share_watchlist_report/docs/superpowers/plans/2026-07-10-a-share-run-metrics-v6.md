# A Share Run Metrics V6 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a V6 run metrics and artifact catalog layer so each local report run can be inspected like a small experiment/run record without adding trading scope or a new data source.

**Architecture:** Extend the existing `src.operations` module. V5 already writes operational checks and a run manifest; V6 derives a compact `run_metrics.json` and tabular `artifact_catalog.csv` from those same local outputs, then exposes them in static HTML, backend summary/table APIs, and the React workbench.

**Tech Stack:** Python, pandas, Jinja2, FastAPI service helpers, React/Vite, pytest, Vitest.

---

### Open-Source Lessons Absorbed

- MLflow: track each run with metrics and artifacts, but keep this local and dependency-free.
- Evidently: make report quality checks exportable as JSON/HTML/table data.
- Superset: make generated datasets browsable from the workbench instead of buried as files.
- OpenBB: keep one data foundation and expose it consistently to multiple surfaces.

### V6 Scope

- [x] Add `output/run_metrics.json`.
- [x] Add `output/artifact_catalog.csv`.
- [x] Include V6 outputs on success and fail-closed paths.
- [x] Surface metrics in `output/report.html` under `指标快照`.
- [x] Surface `artifact_catalog` through backend table API and frontend navigation as `产物目录`.
- [x] Add backend summary field `run_metrics`.
- [x] Keep all UI labels Chinese except professional tokens like AKShare, EastMoney, OK, DATA_ISSUE.

### Guardrails

- [x] Do not add Streamlit, Docker, GitHub Actions, broker APIs, BUY/SELL, target prices, auto trading, AI/LLM analysis, backtesting, or a second data source.
- [x] Do not change stock scoring or strategy semantics.
- [x] Do not copy third-party code into the repository.
- [x] Keep all V6 metrics derived from local files already produced by the report run.

### Validation

- [x] `python -m compileall .`
- [x] `pytest -q`
- [x] `npm run test`
- [x] `npm run build`
- [x] `python run_report.py`
