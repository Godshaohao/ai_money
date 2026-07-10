# A-share UI Localization V4.1 Plan

## Goal

Localize the visible HTML and local workbench UI to Chinese while preserving professional terms, enum labels, and data contracts.

## Scope

1. Static `output/report.html` template uses Chinese labels, section titles, table headers, and empty states.
2. React workbench uses Chinese navigation, status labels, buttons, metric labels, and table headers.
3. CSV column names and API payloads remain unchanged.
4. Keep professional terms such as `AKShare`, `EastMoney`, `MA200`, `Top 20`, `DATA_ISSUE`, and `RISK_ON`.

## Guardrails

- Do not change strategy logic.
- Do not change generated CSV schemas.
- Do not add trading instructions, target prices, broker actions, AI commentary, or new data sources.
- Keep existing smoke checks passing.

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

The rendered static report and frontend shell should show Chinese interface text except for professional terms and enum values.
