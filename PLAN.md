# PLAN.md — `a_share_watchlist_report` P0

> Send this file to Codex as the implementation brief.  
> Goal: build the smallest useful A-share self-selected-stock observation report.  
> Do **not** turn this into a trading platform, factor platform, stock recommendation engine, or broker automation tool.

---

## 0. PD Vibe Guard Task Header

```text
Target user:
A personal investor using this locally for their own A-share watchlist review.

Main judgement:
Is the current A-share market suitable for increasing risk exposure? Which watchlist stocks deserve manual review? Which existing holdings require risk review?

Allowed input:
- universe.csv: manually maintained A-share watchlist, <= 100 stocks
- holdings.csv: current holdings, may be empty
- config.yaml: small static config, <= 30 lines
- AKShare daily stock/index data

Allowed output:
- output/report.html
- output/watchlist.csv
- output/excluded_stocks.csv
- output/holding_risk.csv
- output/market_regime.csv
- output/data_quality_status.json
- data/prices.parquet
- data/index_prices.parquet

Forbidden expansions:
- full A-share market scanner
- BUY/SELL/STRONG_BUY/target price output
- broker API, auto order, live trading, account login
- realtime quote dashboard, minute data, limit-up/board-hitting strategy
- AI/LLM stock commentary, news sentiment, policy interpretation agent
- multi-factor platform, ML prediction, parameter optimizer
- database, service, scheduler, cloud deploy, multi-user, auth system
- Streamlit or multi-page dashboard in P0
```

---

## 1. P0 Product Statement

Build a local static report generator:

```text
a_share_watchlist_report
```

It reads a manually maintained A-share watchlist and holdings file, pulls daily data using AKShare, applies transparent rule-based filters, and generates:

1. market regime: `RISK_ON / NEUTRAL / RISK_OFF`
2. excluded stocks with explicit exclusion reasons
3. Top 20 observation candidates, not trade orders
4. current holding risk review list
5. a static `report.html` for 30-second review

This project is **not** investment advice and must not output direct trading instructions.

---

## 2. Open-Source Libraries to Use

### Runtime dependencies

Create `requirements.txt`:

```txt
akshare
pandas
numpy
pyarrow
pyyaml
jinja2
```

### Dev/test dependencies

Create `requirements-dev.txt`:

```txt
pytest
```

### Why these libraries are allowed

- `akshare`: only data source for A-share and index daily data.
- `pandas`: tabular data loading, cleaning, calculations, CSV/Parquet IO.
- `numpy`: numeric calculations such as momentum, drawdown, NaN handling.
- `pyarrow`: enables Parquet read/write through pandas.
- `pyyaml`: reads `config.yaml`.
- `jinja2`: renders a static HTML report from a template.
- `pytest`: minimal tests only.

### Libraries explicitly not allowed in P0

Do not add:

```text
streamlit
fastapi
flask
sqlalchemy
duckdb
scikit-learn
statsmodels
xgboost
lightgbm
plotly
backtrader
vectorbt
qlib
freqtrade
vnpy
apscheduler
celery
openai
langchain
```

Reason: these trigger dashboard/platform/ML/agent/scheduler/live-trading expansion before the first useful report.

---

## 3. Repository Structure to Create

```text
a_share_watchlist_report/
  README.md
  PLAN.md
  requirements.txt
  requirements-dev.txt
  config.yaml
  universe.csv
  holdings.csv
  run_report.py

  src/
    __init__.py
    config_loader.py
    input_validation.py
    data_loader_akshare.py
    data_quality.py
    market_regime.py
    stock_filters.py
    stock_ranking.py
    holding_risk.py
    report_html.py
    schemas.py

  templates/
    report.html.j2

  data/
    .gitkeep

  output/
    .gitkeep

  tests/
    test_input_validation.py
    test_data_quality.py
    test_market_regime.py
    test_stock_ranking.py
    test_holding_risk.py
```

Do not create `broker.py`, `agent.py`, `database.py`, `scheduler.py`, `strategy_platform.py`, or `streamlit_app.py`.

---

## 4. Default Input Files

### `config.yaml`

Keep it small. Do not exceed 30 meaningful config lines.

```yaml
max_universe_size: 100
top_n_watchlist: 20

market_indices:
  沪深300: "000300"
  中证500: "000905"
  创业板指: "399006"

start_date: "20180101"
trend_ma_days: 200
short_trend_days: 20
momentum_12m_days: 252
momentum_6m_days: 126
max_drawdown_days: 60

min_listing_days: 250
min_avg_amount_20d: 50000000
max_missing_days: 5
```

### `universe.csv`

```csv
symbol,name,industry
600519,贵州茅台,食品饮料
000001,平安银行,银行
300750,宁德时代,电力设备
```

### `holdings.csv`

```csv
symbol,shares,cost_basis
600519,100,1500
000001,1000,10
```

`holdings.csv` may be empty except for the header.

---

## 5. Module-by-Module Implementation Plan

## M0 — Empty Project Skeleton

### Goal

Make the project runnable before adding data logic.

### Implement

- `run_report.py`
- output directory creation
- placeholder `output/report.html`
- placeholder `output/data_quality_status.json`

### Expected command

```bash
python run_report.py
```

### Acceptance

After running, these files exist:

```text
output/report.html
output/data_quality_status.json
```

The report should show:

```text
Data status: N/A
Market regime: N/A
Watchlist: N/A
Holding risk: N/A
```

### Do not implement yet

- AKShare calls
- ranking logic
- market regime logic
- holdings risk logic

---

## M1 — Input Protocol and Validation

### Goal

Freeze inputs so the project does not grow into a platform.

### Files

- `config.yaml`
- `universe.csv`
- `holdings.csv`
- `src/config_loader.py`
- `src/input_validation.py`

### Required imports

```python
from pathlib import Path
from typing import Any
import yaml
import pandas as pd
```

### Implement

`src/config_loader.py`

```python
def load_config(path: str | Path) -> dict[str, Any]:
    """Load config.yaml and validate required keys exist."""
```

`src/input_validation.py`

```python
def load_universe(path: str | Path, max_size: int) -> pd.DataFrame:
    """Load universe.csv and validate symbol/name/industry columns."""


def load_holdings(path: str | Path) -> pd.DataFrame:
    """Load holdings.csv. Empty holdings are allowed if header exists."""
```

### Validation rules

`universe.csv`:

- required columns: `symbol,name,industry`
- `symbol` must be non-empty string-like code
- row count must be `<= max_universe_size`
- duplicate symbols are not allowed

`holdings.csv`:

- required columns: `symbol,shares,cost_basis`
- empty file with only headers is allowed
- `shares >= 0`
- `cost_basis >= 0`

### Acceptance

- invalid universe size fails early
- missing required columns fail early
- empty holdings header passes
- no AKShare call is required for M1 tests

---

## M2 — AKShare Data Loader

### Goal

Fetch daily stock and index data from AKShare, normalize columns, and cache to Parquet.

### File

- `src/data_loader_akshare.py`

### Required imports

```python
from pathlib import Path
from datetime import datetime
import time
import pandas as pd
import akshare as ak
```

### Implement

```python
def fetch_stock_daily(symbol: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one A-share stock daily history through AKShare.

    Return normalized columns:
    date, symbol, close, amount
    """


def fetch_index_daily(index_code: str, index_name: str, start_date: str, end_date: str) -> pd.DataFrame:
    """Fetch one A-share index daily history through AKShare.

    Return normalized columns:
    date, index_name, index_code, close
    """


def build_price_cache(universe: pd.DataFrame, config: dict, output_path: str | Path) -> pd.DataFrame:
    """Fetch all universe stocks and write data/prices.parquet."""


def build_index_price_cache(config: dict, output_path: str | Path) -> pd.DataFrame:
    """Fetch configured market indices and write data/index_prices.parquet."""
```

### AKShare guidance

Use AKShare as the only data source in P0. Keep the API call isolated inside this module so API changes do not leak into business logic.

Suggested stock call pattern:

```python
ak.stock_zh_a_hist(
    symbol=symbol,
    period="daily",
    start_date=start_date,
    end_date=end_date,
    adjust="qfq",
)
```

For index history, use the appropriate AKShare index historical endpoint available in the installed AKShare version. Keep this wrapper small and fail closed if the endpoint fails.

### Column normalization

AKShare often returns Chinese column names. Normalize them immediately:

```text
日期 -> date
收盘 -> close
成交额 -> amount
```

If required columns are missing, raise a clear exception and stop report generation.

### Acceptance

Generated files:

```text
data/prices.parquet
data/index_prices.parquet
```

Normalized schemas:

```text
prices.parquet:
date, symbol, close, amount

index_prices.parquet:
date, index_name, index_code, close
```

### Expansion guard

Do not add fallback data sources. If AKShare fails, stop and produce a data issue report.

---

## M3 — Data Quality and Exclusion Reasons

### Goal

Never output a watchlist from bad or incomplete data.

### File

- `src/data_quality.py`

### Required imports

```python
from dataclasses import dataclass
from pathlib import Path
import json
import pandas as pd
import numpy as np
```

### Implement

```python
@dataclass
class DataQualityResult:
    ok: bool
    errors: list[str]
    warnings: list[str]
    excluded: pd.DataFrame


def run_data_quality_checks(
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    config: dict,
) -> DataQualityResult:
    """Return global quality status and per-stock exclusions."""


def write_data_quality_status(result: DataQualityResult, output_path: str | Path) -> None:
    """Write output/data_quality_status.json."""
```

### Required checks

Per stock:

- no price data
- latest date too old versus latest date in the cache
- listing/history length `< min_listing_days`
- latest `close <= 0`
- missing days count `> max_missing_days`
- 20-day average amount `< min_avg_amount_20d`
- suspected suspension: no recent rows while other stocks have recent rows

### Output

`output/excluded_stocks.csv`:

```text
symbol,name,industry,exclude_reason,last_price_date,avg_amount_20d,history_days
```

### Acceptance

- every excluded stock has `exclude_reason`
- if global data is unusable, `ok=false`
- if `ok=false`, pipeline must not generate `watchlist.csv`

### Expansion guard

Do not add complex anomaly detection or AI data-quality judgement.

---

## M4 — Market Regime

### Goal

Classify market state using only configured indices and transparent rules.

### File

- `src/market_regime.py`

### Required imports

```python
from pathlib import Path
import pandas as pd
import numpy as np
```

### Implement

```python
def calculate_market_regime(index_prices: pd.DataFrame, config: dict) -> tuple[str, pd.DataFrame]:
    """Return regime and evidence table.

    regime in: RISK_ON, NEUTRAL, RISK_OFF
    evidence columns:
    index_name, close, ma200, above_ma200, return_20d, status
    """
```

### P0 rule

- `RISK_ON`: at least 2/3 configured indices are above MA200 and have positive 20-day return
- `RISK_OFF`: at least 2/3 configured indices are below MA200 and have negative 20-day return
- else: `NEUTRAL`

### Output

`output/market_regime.csv`

### Acceptance

The report can show:

```text
Market regime: RISK_ON / NEUTRAL / RISK_OFF
Evidence: index-level MA200 and 20-day return
```

### Expansion guard

Do not add macro, news, policy, northbound capital, or sector rotation in P0.

---

## M5 — Stock Filters and Watchlist Ranking

### Goal

Generate Top 20 observation candidates from eligible stocks.

### Files

- `src/stock_filters.py`
- `src/stock_ranking.py`

### Required imports

```python
from pathlib import Path
import pandas as pd
import numpy as np
```

### Implement filters

`src/stock_filters.py`

```python
def build_eligible_stocks(
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    excluded: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Return per-stock latest indicators after hard exclusions."""
```

Required output columns:

```text
symbol,name,industry,close,ma200,above_ma200,avg_amount_20d,history_days
```

### Implement ranking

`src/stock_ranking.py`

```python
def build_watchlist(
    prices: pd.DataFrame,
    eligible: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Build Top N observation list using trend and momentum."""
```

Calculate:

- 12M momentum: `latest_close / close_252d_ago - 1`
- 6M momentum: `latest_close / close_126d_ago - 1`
- MA200 status
- 60-day max drawdown
- 20-day average amount

Ranking:

1. keep only `above_ma200 == True`
2. sort by `momentum_12m` descending
3. tie-break by `momentum_6m` descending
4. take `top_n_watchlist`

### Output

`output/watchlist.csv`:

```text
symbol,name,industry,close,momentum_12m,momentum_6m,above_ma200,max_drawdown_60d,avg_amount_20d,rank,reason
```

### Reason template

```text
进入观察：价格在 MA200 上方，12M 动量排名第 {rank}，20 日平均成交额达标。
```

### Acceptance

- only Top 20 by default
- every candidate has a deterministic `reason`
- no `BUY`, `SELL`, `target_price`, or expected return fields

### Expansion guard

Do not add multi-factor scoring, ML ranking, clustering, recommendation, or optimizer.

---

## M6 — Holding Risk Review

### Goal

Review existing holdings for risk flags without generating trade instructions.

### File

- `src/holding_risk.py`

### Required imports

```python
from pathlib import Path
import pandas as pd
import numpy as np
```

### Implement

```python
def build_holding_risk(
    holdings: pd.DataFrame,
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    excluded: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Return holding risk review table."""
```

### Allowed risk actions

```text
WATCH
HOLD_REVIEW
REDUCE_REVIEW
DATA_ISSUE
```

### Suggested rules

- `DATA_ISSUE`: symbol excluded due to data issue or no current price
- `REDUCE_REVIEW`: below MA200 or drawdown from cost below a risk threshold if added to config later
- `HOLD_REVIEW`: above MA200 but recent max drawdown is large
- `WATCH`: no obvious issue

Do not add direct trading verbs.

### Output

`output/holding_risk.csv`:

```text
symbol,name,shares,cost_basis,latest_close,drawdown_from_cost,above_ma200,max_drawdown_60d,avg_amount_20d,risk_action,reason
```

### Acceptance

- no direct `SELL` or `BUY` output
- unknown holdings not in universe are allowed but must be flagged for review
- every row has a `reason`

### Expansion guard

Do not add target weights, auto stop-loss execution, or broker integration.

---

## M7 — Static HTML Report

### Goal

Create a static report that answers the main judgement within 30 seconds.

### Files

- `src/report_html.py`
- `templates/report.html.j2`

### Required imports

```python
from pathlib import Path
from datetime import datetime
import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape
```

### Implement

```python
def render_report(
    output_path: str | Path,
    market_regime: str,
    market_evidence: pd.DataFrame,
    watchlist: pd.DataFrame | None,
    excluded: pd.DataFrame,
    holding_risk: pd.DataFrame,
    data_quality_status: dict,
) -> None:
    """Render output/report.html using templates/report.html.j2."""
```

### First screen must include

```text
Market regime: RISK_ON / NEUTRAL / RISK_OFF / DATA_ISSUE
Risk exposure review: YES / NO / REVIEW
Watchlist candidate count
Excluded stock count
Holding risk count
Largest risk warning
```

### Sections

1. Summary
2. Market regime evidence
3. Watchlist Top 20
4. Excluded stocks
5. Holding risk review
6. Data quality status

### Acceptance

Opening `output/report.html` answers:

```text
现在市场环境怎么样？
有哪些股票值得人工看？
哪些股票被排除？
我的持仓哪里有风险？
```

### Expansion guard

Do not add Streamlit, login, auto-refresh, filters, charts, or multi-page navigation in P0.

---

## 6. Pipeline Orchestration

### File

- `run_report.py`

### Required imports

```python
from pathlib import Path
from datetime import datetime
import json
import pandas as pd

from src.config_loader import load_config
from src.input_validation import load_universe, load_holdings
from src.data_loader_akshare import build_price_cache, build_index_price_cache
from src.data_quality import run_data_quality_checks, write_data_quality_status
from src.market_regime import calculate_market_regime
from src.stock_filters import build_eligible_stocks
from src.stock_ranking import build_watchlist
from src.holding_risk import build_holding_risk
from src.report_html import render_report
```

### Pipeline order

1. create `data/` and `output/`
2. load config
3. load universe and holdings
4. fetch/cache stock prices
5. fetch/cache index prices
6. run data quality
7. write `data_quality_status.json`
8. always write `excluded_stocks.csv`
9. if data quality fails globally:
   - do not build watchlist
   - render report with `DATA_ISSUE`
   - exit successfully with clear message
10. calculate market regime
11. build eligible stocks
12. build watchlist
13. build holding risk
14. write all CSVs
15. render report

### Console output

At the end, print:

```text
Generated output/report.html
Generated output/watchlist.csv
Generated output/excluded_stocks.csv
Generated output/holding_risk.csv
Generated output/market_regime.csv
Generated output/data_quality_status.json
```

---

## 7. Minimal Tests

Use synthetic DataFrames. Do not call AKShare in tests.

### `tests/test_input_validation.py`

Test:

- universe over 100 fails
- missing columns fail
- empty holdings header passes

### `tests/test_data_quality.py`

Test:

- no price data excludes stock
- low amount excludes stock
- short history excludes stock
- close <= 0 excludes stock

### `tests/test_market_regime.py`

Test:

- 2/3 above MA200 and 20d positive -> `RISK_ON`
- 2/3 below MA200 and 20d negative -> `RISK_OFF`
- mixed -> `NEUTRAL`

### `tests/test_stock_ranking.py`

Test:

- below MA200 stock not in watchlist
- Top N respected
- reason is non-empty
- no BUY/SELL columns

### `tests/test_holding_risk.py`

Test:

- holdings not in universe flagged
- excluded holding becomes `DATA_ISSUE`
- below MA200 becomes review action
- no BUY/SELL actions appear

---

## 8. README Requirements

Create `README.md` with:

```text
What this tool does
What this tool does not do
Install instructions
How to edit universe.csv
How to edit holdings.csv
How to run python run_report.py
How to read report.html
Data source limitations
Not investment advice disclaimer
```

Mandatory disclaimer:

```text
This project is a personal research and review tool. It is not investment advice, does not predict returns, and does not generate trading orders. All outputs require manual review.
```

---

## 9. Codex Execution Rules

When implementing this plan:

1. Implement milestones in order: M0 -> M1 -> M2 -> M3 -> M4 -> M5 -> M6 -> M7.
2. Do not introduce libraries outside `requirements.txt` and `requirements-dev.txt`.
3. Do not create database, API server, scheduler, Streamlit app, agent, broker integration, or ML model.
4. Keep each module small and testable.
5. If AKShare API behavior differs, update only `src/data_loader_akshare.py`.
6. If data quality fails, fail closed: no watchlist, no false confidence.
7. Use CSV/Parquet files only.
8. Do not output `BUY`, `SELL`, `target_price`, or `expected_return`.
9. Every excluded stock, watchlist stock, and holding risk row must have a human-readable reason.
10. Prefer clear deterministic rules over clever abstractions.

---

## 10. P0 Acceptance Checklist

The P0 is complete only when all are true:

```text
[ ] python run_report.py runs locally
[ ] requirements.txt has only approved runtime dependencies
[ ] universe.csv <= 100 rows is enforced
[ ] AKShare data is normalized to expected schemas
[ ] data/prices.parquet is generated
[ ] data/index_prices.parquet is generated
[ ] output/data_quality_status.json is generated
[ ] output/excluded_stocks.csv is generated with reasons
[ ] output/market_regime.csv is generated
[ ] output/watchlist.csv is generated only when data quality passes
[ ] output/watchlist.csv has Top 20 max by default
[ ] output/watchlist.csv has no BUY/SELL/target price fields
[ ] output/holding_risk.csv uses only allowed risk actions
[ ] output/report.html opens without external service
[ ] tests do not call AKShare
[ ] README states this is not investment advice
[ ] no database/API/server/scheduler/agent/broker code exists
```

---

## 11. Explicitly Deferred to P0.5 or Later

Do not implement these in P0:

```text
sanity backtest
industry distribution report
valuation metrics
financial statement filters
northbound capital
volume trend dashboard
Streamlit UI
email notification
scheduled execution
Tushare fallback
full A-share scanner
factor platform
```

If any of these become necessary later, write a separate plan and re-run the PD Vibe Guard task header first.
