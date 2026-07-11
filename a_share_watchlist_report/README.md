# a_share_watchlist_report

A local static report generator for a manually maintained A-share watchlist. It reads `universe.csv`, `holdings.csv`, and `config.yaml`, fetches daily market data through AKShare, applies transparent rules, and writes CSV outputs plus `output/report.html`.

## What This Tool Does

- Classifies the configured A-share market indices as `RISK_ON`, `NEUTRAL`, or `RISK_OFF`.
- Excludes stocks with explicit data quality reasons.
- Creates a Top 20 observation watchlist for manual review.
- Reviews recent limit-up stocks from AKShare/EastMoney as observation candidates only.
- Flags current holdings for risk review using only allowed actions: `WATCH`, `HOLD_REVIEW`, `REDUCE_REVIEW`, `DATA_ISSUE`.
- Adds a portfolio review table with position value, unrealized P/L, portfolio weight, liquidity days, and manual review flags.
- Adds V5 run audit files for output completeness, data quality state, cache fallback visibility, and review-table availability.
- Adds V6 run metrics and an artifact catalog for local run inspection.
- Writes a static HTML report that opens without a web service.
- Optionally exposes the latest local report and run history through a local FastAPI backend.

## What This Tool Does Not Do

- It does not generate trading orders or investment recommendations.
- It does not output `BUY`, `SELL`, target prices, or expected returns.
- It does not connect to brokers, accounts, realtime quotes, schedulers, ML models, or agent systems.
- Its SQLite database is local run-history storage only, not an account, order, or trading database.

## Install

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

## Edit `universe.csv`

Keep at most 100 rows:

```csv
symbol,name,industry
600519,贵州茅台,食品饮料
000001,平安银行,银行
```

## Edit `holdings.csv`

Holdings may be empty except for the header:

```csv
symbol,shares,cost_basis
600519,100,1500
```

## Run

```bash
python run_report.py
```

Open `output/report.html` after the command finishes.

## Local Backend API

V2 adds an optional local FastAPI backend around the existing report generator:

```bash
python -m uvicorn backend.app:app --reload
```

Useful local endpoints:

- `GET /health`
- `GET /api/report/summary`
- `POST /api/report/run`
- `GET /api/report/runs`

The backend writes run history to `data/workbench.sqlite`. The original CLI remains supported:

```bash
python run_report.py
```

## Local Frontend Workbench

V3 adds an optional local React workbench that reads the existing report outputs through the local backend.

Start the backend:

```bash
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8000
```

Start the frontend:

```bash
cd frontend
npm install
npm run dev
```

Open `http://127.0.0.1:5173`.

The frontend does not generate trading orders, target prices, automated actions, or investment recommendations.

## Local Smoke Check

```bash
python -m compileall .
pytest
python run_report.py
```

Frontend smoke check:

```bash
cd frontend
npm run test
npm run build
```

## Local Data Artifacts

The run also writes local-only data foundation artifacts:

- `data/cache/daily_bars.parquet`
- `data/reports/data_coverage_report.json`

These files are generated from the same AKShare pull used by the report and are ignored by git.

The report output directory includes event-driven review tables:

- `output/dragon_tiger.csv`
- `output/limit_up_pool.csv`
- `output/limit_up_strategy_review.csv`
- `output/portfolio_review.csv`
- `output/operations_check.csv`
- `output/run_manifest.json`
- `output/artifact_catalog.csv`
- `output/run_metrics.json`

`limit_up_strategy_review.csv` scores recent limit-up stocks for manual review with labels such as `CORE_REVIEW`, `WATCH_REVIEW`, `RISK_REVIEW`, and `DATA_GAP`. It does not output `BUY`, `SELL`, target prices, position sizes, broker actions, or automated orders.

`portfolio_review.csv` summarizes current holdings for manual review. It uses existing holding risk data to calculate position value, unrealized P/L, portfolio weight, and liquidity days. It does not recommend position sizes or trading actions.

`operations_check.csv` is the V5 operations audit table. It records local checks such as output file completeness, data quality, cache fallback, limit-up review availability, and portfolio review availability.

`run_manifest.json` records the run id, timestamps, duration, final status, output inventory, CSV row counts, warnings, and errors.

`run_metrics.json` is the V6 metrics snapshot. It summarizes status, data source state, output file count, missing file count, key row counts, and operations check counts.

`artifact_catalog.csv` is the V6 artifact catalog. It lists local output files, file sizes, CSV row counts, and update times so the frontend and static report can inspect outputs consistently.

## 如何阅读报告

- `市场状态` 汇总配置指数是否支持更高风险敞口。
- `观察池 Top 20` 只列出观察候选，不是交易指令。
- `涨停复核` 展示近期涨停股票的人工复核信号。
- `排除股票` 解释股票在排序前被硬过滤的原因。
- `持仓风险复核` 展示需要人工复核的持仓。
- `组合复核` 展示当前持仓的市值、盈亏、权重、流动性和风险标签。
- `运行审计` 展示本次本地运行是否完整生成核心产物。
- `指标快照` 展示本次运行的核心机器可读指标。
- `产物目录` 展示本次运行生成的本地输出文件。
- `数据质量状态` 展示当前数据是否被流水线信任。

## Data Source Limitations

AKShare remains the first data entry for market data. For EastMoney-backed endpoints that are important to the local workflow, the project also includes direct EastMoney HTTP fallbacks adapted from the Apache-2.0 `simonlin1212/a-stock-data` request pattern: shared session, serial throttling, jitter, bounded retry, and explicit schema normalization.

The current direct fallback scope is intentionally narrow:

- stock daily K-line fallback through EastMoney `push2his`
- recent limit-up pool fallback through EastMoney `push2ex`

If both AKShare and the direct same-source fallback fail or return incompatible fields, the report fails closed and records a data issue instead of producing a false watchlist.

## Disclaimer

This project is a personal research and review tool. It is not investment advice, does not predict returns, and does not generate trading orders. All outputs require manual review.
