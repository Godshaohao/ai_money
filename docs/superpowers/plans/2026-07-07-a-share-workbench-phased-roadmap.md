# A-share Research Workbench Phased Roadmap

## Goal

Build a personal A-share research workbench in phases while preserving the current P0 static report contract.

## Guardrails

- Keep P0 outputs runnable at every phase.
- Use AKShare as the single market data source until a later explicit data-source decision.
- Do not emit BUY, SELL, target price, broker order, or automated trading output.
- Keep generated data artifacts out of git.

## Phases

1. V1 data foundation: normalized daily bars, local parquet cache, coverage report, and tests.
2. V2 market scan: broaden scan logic behind explicit local controls after V1 is stable.
3. V3 research views: add richer review pages without changing the P0 output contract.
4. V4 portfolio review: improve holding diagnostics while keeping manual review language.
5. V5 operations: add local run discipline, logs, and documentation.

## Current Phase

V1 data foundation.

