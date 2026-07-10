from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


REPORT_TABLES = {
    "watchlist": "watchlist.csv",
    "excluded_stocks": "excluded_stocks.csv",
    "holding_risk": "holding_risk.csv",
    "portfolio_review": "portfolio_review.csv",
    "market_regime": "market_regime.csv",
    "dragon_tiger": "dragon_tiger.csv",
    "limit_up_pool": "limit_up_pool.csv",
    "limit_up_strategy_review": "limit_up_strategy_review.csv",
    "operations_check": "operations_check.csv",
    "artifact_catalog": "artifact_catalog.csv",
}


def read_report_table(output_dir: Path, table_name: str, limit: int = 200) -> dict[str, Any]:
    if table_name not in REPORT_TABLES:
        raise ValueError(f"unknown report table: {table_name}")

    path = Path(output_dir) / REPORT_TABLES[table_name]
    if not path.exists():
        return {
            "name": table_name,
            "exists": False,
            "columns": [],
            "row_count": 0,
            "rows": [],
            "errors": [f"Missing {path.name}"],
        }

    try:
        frame = pd.read_csv(path, dtype="string")
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError) as exc:
        return {
            "name": table_name,
            "exists": False,
            "columns": [],
            "row_count": 0,
            "rows": [],
            "errors": [f"Malformed {path.name}: {exc}"],
        }

    limited = frame.head(limit)
    rows = limited.where(pd.notna(limited), None).to_dict(orient="records")
    return {
        "name": table_name,
        "exists": True,
        "columns": list(frame.columns),
        "row_count": int(len(frame)),
        "rows": rows,
        "errors": [],
    }
