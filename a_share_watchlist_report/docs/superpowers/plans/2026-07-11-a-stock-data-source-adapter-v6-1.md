# A-Stock-Data Source Adapter V6.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Absorb the mature EastMoney request and limit-up pool patterns from `simonlin1212/a-stock-data` into this project while preserving our existing report scope and schemas.

**Architecture:** Add a focused EastMoney HTTP helper with session reuse, serial throttling, jitter, and retry semantics adapted from `a-stock-data` under Apache-2.0 attribution. Route our direct EastMoney K-line fallback and a new push2ex limit-up fallback through the helper, while keeping AKShare as the first call path and preserving fail-closed data contracts.

**Tech Stack:** Python, pandas, curl_cffi, AKShare, pytest, Jinja/static HTML.

---

### Task 1: EastMoney HTTP Helper

**Files:**
- Create: `a_share_watchlist_report/src/data/eastmoney_http.py`
- Test: `a_share_watchlist_report/tests/test_eastmoney_http.py`

- [ ] **Step 1: Write tests**

Test a fake session that fails once with HTTP 500 and succeeds on retry, verifies JSON output, session headers, and sleeps when requests are too close together.

- [ ] **Step 2: Implement helper**

Implement `EastMoneyHTTPClient.get_json()` and module-level `em_get_json()`. Keep retries bounded, do not retry 403, and raise `EastMoneyHTTPError` with URL context.

- [ ] **Step 3: Verify**

Run: `pytest tests/test_eastmoney_http.py -q`

### Task 2: K-Line Fallback Uses Shared Helper

**Files:**
- Modify: `a_share_watchlist_report/src/data/eastmoney_client.py`
- Modify: `a_share_watchlist_report/tests/test_eastmoney_client.py`

- [ ] **Step 1: Add test coverage**

Patch `eastmoney_client.em_get_json` and assert `fetch_stock_hist_eastmoney()` parses the payload through the shared helper.

- [ ] **Step 2: Replace direct curl request**

Remove local curl session logic and call `em_get_json()` with the existing `push2his` URL and params.

- [ ] **Step 3: Verify**

Run: `pytest tests/test_eastmoney_client.py -q`

### Task 3: Direct Push2ex Limit-Up Fallback

**Files:**
- Modify: `a_share_watchlist_report/src/data/limit_up_pool.py`
- Modify: `a_share_watchlist_report/tests/test_limit_up_pool.py`

- [ ] **Step 1: Add parser tests**

Use an `a-stock-data` style `data.pool` payload with fields `c`, `n`, `p`, `zdp`, `amount`, `hs`, `fund`, `fbt`, `lbt`, `zbc`, `zttj`, `lbc`, `hybk`. Assert it normalizes to our `LIMIT_UP_POOL_COLUMNS`.

- [ ] **Step 2: Add fallback test**

Patch AKShare to raise and patch direct EastMoney fetch to return a valid frame. Assert `fetch_limit_up_pool_for_date()` still succeeds and source identifies direct EastMoney.

- [ ] **Step 3: Implement direct fallback**

Add `_fmt_zt_time()`, `parse_eastmoney_limit_up_payload()`, and `fetch_limit_up_pool_eastmoney_direct()`. Keep AKShare first; direct push2ex is fallback for the same EastMoney data family.

- [ ] **Step 4: Verify**

Run: `pytest tests/test_limit_up_pool.py -q`

### Task 4: Full Smoke Check

**Files:**
- No additional files expected.

- [ ] **Step 1: Compile**

Run: `python -m compileall .`

- [ ] **Step 2: Test**

Run: `pytest -q`

- [ ] **Step 3: Generate report**

Run: `python run_report.py`

- [ ] **Step 4: Inspect outputs**

Confirm `output/report.html`, `output/limit_up_pool.csv`, `output/limit_up_strategy_review.csv`, and `output/data_quality_status.json` exist. Confirm no BUY/SELL/target-price/trading-order output is introduced.

### Task 5: GitHub Upload

**Files:**
- Commit only source, tests, and plan docs.

- [ ] **Step 1: Use temp clone if root git is invalid**

Clone `https://github.com/Godshaohao/ai_money.git` under `/tmp`, sync source excluding cache, node_modules, dist, and generated output.

- [ ] **Step 2: Commit and push**

Commit with message `feat: adapt a-stock-data eastmoney helper` and push `main`.

---

### Self-Review

- Scope stays inside data-source robustness and 打板池 ingestion.
- No Streamlit, Docker, Actions, broker API, AI/LLM analysis, auto-trading, or target-price output.
- Direct-source reuse is limited to Apache-2.0-compatible helper patterns and field parsing, with attribution in code comments and docs.
