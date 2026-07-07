# a_share_watchlist_report

A local static report generator for a manually maintained A-share watchlist. It reads `universe.csv`, `holdings.csv`, and `config.yaml`, fetches daily market data through AKShare, applies transparent rules, and writes CSV outputs plus `output/report.html`.

## What This Tool Does

- Classifies the configured A-share market indices as `RISK_ON`, `NEUTRAL`, or `RISK_OFF`.
- Excludes stocks with explicit data quality reasons.
- Creates a Top 20 observation watchlist for manual review.
- Flags current holdings for risk review using only allowed actions: `WATCH`, `HOLD_REVIEW`, `REDUCE_REVIEW`, `DATA_ISSUE`.
- Writes a static HTML report that opens without a web service.

## What This Tool Does Not Do

- It does not generate trading orders or investment recommendations.
- It does not output `BUY`, `SELL`, target prices, or expected returns.
- It does not connect to brokers, accounts, realtime quotes, databases, APIs, schedulers, ML models, or agent systems.

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

## Local Smoke Check

```bash
python -m compileall .
pytest
python run_report.py
```

## Local Data Artifacts

The run also writes local-only data foundation artifacts:

- `data/cache/daily_bars.parquet`
- `data/reports/data_coverage_report.json`

These files are generated from the same AKShare pull used by the report and are ignored by git.

## How To Read The Report

- `Market regime` summarizes whether configured indices support more risk exposure.
- `Watchlist Top 20` lists observation candidates only, not trade orders.
- `Excluded Stocks` explains why a stock was removed before ranking.
- `Holding Risk Review` shows holdings that deserve manual review.
- `Data Quality Status` shows whether the pipeline trusted the current data.

## Data Source Limitations

AKShare is the only data source in P0. If AKShare fails or changes its returned schema, the report fails closed and records a data issue instead of producing a false watchlist.

## Disclaimer

This project is a personal research and review tool. It is not investment advice, does not predict returns, and does not generate trading orders. All outputs require manual review.
