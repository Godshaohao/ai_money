# A-share Data Foundation V1

## Objective

Add a local data foundation for the existing static A-share watchlist report without changing the product scope.

## Tasks

1. Define daily bar and coverage report schemas.
2. Normalize AKShare `stock_zh_a_hist` data into daily bar columns.
3. Write and read a local `data/cache/daily_bars.parquet` cache.
4. Produce `data/reports/data_coverage_report.json`.
5. Add a small AKShare stock-list wrapper for future universe maintenance.
6. Keep `run_report.py` fail-closed and preserve the six P0 output files.
7. Document local artifacts and smoke checks.

## Acceptance

```bash
cd a_share_watchlist_report
python -m compileall .
pytest
python run_report.py
```

Expected generated files:

- `output/report.html`
- `output/watchlist.csv`
- `output/excluded_stocks.csv`
- `output/holding_risk.csv`
- `output/market_regime.csv`
- `output/data_quality_status.json`
- `data/cache/daily_bars.parquet`
- `data/reports/data_coverage_report.json`

