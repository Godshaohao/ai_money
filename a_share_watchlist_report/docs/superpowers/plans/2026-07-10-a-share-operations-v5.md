# A Share Operations V5 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a V5 operations audit layer so every local report run exposes output completeness, data quality state, cache usage, and review-table availability in CSV, JSON, static HTML, and the local frontend.

**Architecture:** Keep the existing AKShare/EastMoney single-source data pipeline and static report contract. Add a small `src.operations` module that derives operational metadata from files already produced by `run_report.py`, then surface it through the Jinja report, backend table registry, and React table shell.

**Tech Stack:** Python, pandas, Jinja2, FastAPI backend services, React/Vite frontend, pytest, Vitest.

---

### Open-Source Lessons Absorbed

- Dagster-style asset thinking: treat generated report files as observable assets with completeness checks.
- Great Expectations-style data contracts: make data quality status and failures visible without adding a new validation framework.
- Qlib-style loose coupling: keep operations audit independent from stock ranking and strategy review logic.
- vn.py-style engineering discipline: keep quality checks local and testable, without expanding into brokerage or trading scope.

### V5 Scope

- [ ] Add `operations_check.csv` with columns `check_name,status,severity,detail`.
- [ ] Add `run_manifest.json` with run id, timestamps, duration, status, output inventory, row counts, warnings, and errors.
- [ ] Generate both files on success and fail-closed paths.
- [ ] Show `运行审计` in `output/report.html`.
- [ ] Expose `operations_check` through the backend table API and React UI.
- [ ] Keep HTML/React display Chinese except professional terms such as AKShare, EastMoney, DATA_ISSUE, OK.

### Guardrails

- [ ] Do not add Streamlit, Docker, GitHub Actions, database changes, broker APIs, target prices, BUY/SELL, AI/LLM, backtesting, or a second data source.
- [ ] Do not change ranking or strategy scoring semantics.
- [ ] Do not copy third-party source code into the repository.
- [ ] Keep the new module deterministic and testable with local temporary directories.

### Validation

- [ ] `python -m compileall .`
- [ ] `pytest -q`
- [ ] `npm run test`
- [ ] `npm run build`
- [ ] `python run_report.py`

