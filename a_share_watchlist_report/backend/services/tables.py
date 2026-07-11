from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from backend.repositories.sqlite_repo import ReportTableRepository


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


def read_report_table(
    output_dir: Path,
    table_name: str,
    limit: int = 200,
    offset: int = 0,
    search: str = "",
    sort_by: str = "",
    sort_dir: str = "asc",
    db_path: Path | None = None,
) -> dict[str, Any]:
    if table_name not in REPORT_TABLES:
        raise ValueError(f"unknown report table: {table_name}")

    if db_path is not None and Path(db_path).exists():
        sqlite_table = ReportTableRepository(Path(db_path)).read_table(
            table_name,
            limit=limit,
            offset=offset,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
        )
        if sqlite_table["exists"]:
            return sqlite_table

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

    filtered = _filter_frame(frame, search)
    sorted_frame = _sort_frame(filtered, sort_by, sort_dir)
    limited = sorted_frame.iloc[max(offset, 0) : max(offset, 0) + max(limit, 0)]
    rows = limited.where(pd.notna(limited), None).to_dict(orient="records")
    return {
        "name": table_name,
        "exists": True,
        "columns": list(frame.columns),
        "row_count": int(len(frame)),
        "filtered_count": int(len(filtered)),
        "rows": rows,
        "errors": [],
        "source": "csv",
        "limit": limit,
        "offset": offset,
    }


def _filter_frame(frame: pd.DataFrame, search: str) -> pd.DataFrame:
    query = search.strip().lower()
    if not query:
        return frame
    mask = frame.astype("string").fillna("").agg(" ".join, axis=1).str.lower().str.contains(query, regex=False)
    return frame.loc[mask].reset_index(drop=True)


def _sort_frame(frame: pd.DataFrame, sort_by: str, sort_dir: str) -> pd.DataFrame:
    if sort_by not in frame.columns:
        return frame
    sorted_values = frame.copy()
    numeric = pd.to_numeric(sorted_values[sort_by], errors="coerce")
    if numeric.notna().any():
        sorted_values["_sort_key"] = numeric
    else:
        sorted_values["_sort_key"] = sorted_values[sort_by].astype("string")
    return sorted_values.sort_values("_sort_key", ascending=sort_dir.lower() != "desc").drop(columns=["_sort_key"])
