# A-share Portfolio Review V4 Implementation Plan

## Goal

Add a local portfolio review layer on top of the existing holding risk table. V4 improves manual holding diagnostics without changing the project into a trading, recommendation, or broker system.

## Guardrails

- Keep `python run_report.py` working.
- Keep all existing output files and API routes working.
- Use only existing local inputs and AKShare-derived price data.
- Do not add BUY, SELL, target price, position-size advice, broker orders, account login, AI commentary, ML, or backtesting.
- Keep generated CSV/JSON/HTML/SQLite/Parquet artifacts out of git.

## Scope

1. Add `output/portfolio_review.csv`.
2. Build portfolio diagnostics from existing `holding_risk.csv` fields:
   - position value
   - cost value
   - unrealized P/L
   - unrealized return
   - portfolio weight
   - liquidity days based on 20-day average amount
   - risk flags
   - manual review note
3. Render Portfolio Review in static `output/report.html`.
4. Expose the table through the local backend table API.
5. Add a Portfolio Review section to the React workbench.
6. Preserve fail-closed behavior by writing an empty header on data issues.

## Acceptance

```bash
cd a_share_watchlist_report
python -m compileall .
pytest
python run_report.py
cd frontend
npm run test
npm run build
```

Expected outputs include:

- `output/portfolio_review.csv`
- `output/report.html` with `Portfolio Review`
- backend table key `portfolio_review`
- frontend navigation item `Portfolio Review`
