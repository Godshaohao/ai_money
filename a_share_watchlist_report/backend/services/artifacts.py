import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


REQUIRED_ARTIFACTS = {
    "report_html": "report.html",
    "watchlist_csv": "watchlist.csv",
    "excluded_stocks_csv": "excluded_stocks.csv",
    "holding_risk_csv": "holding_risk.csv",
    "market_regime_csv": "market_regime.csv",
    "data_quality_status_json": "data_quality_status.json",
}

CSV_ROW_COUNT_KEYS = {
    "watchlist": "watchlist.csv",
    "excluded_stocks": "excluded_stocks.csv",
    "holding_risk": "holding_risk.csv",
    "market_regime": "market_regime.csv",
}


def build_report_summary(output_dir: Path) -> dict[str, Any]:
    output_dir = Path(output_dir)
    missing_files = [
        filename
        for filename in REQUIRED_ARTIFACTS.values()
        if not (output_dir / filename).exists()
    ]
    row_counts, read_errors = _count_csv_rows(output_dir)
    data_quality = _read_data_quality(output_dir / "data_quality_status.json")
    if read_errors:
        data_quality = dict(data_quality)
        data_quality["ok"] = False
        data_quality.setdefault("errors", [])
        data_quality["errors"].extend(read_errors)

    return {
        "exists": not missing_files and not read_errors,
        "missing_files": missing_files,
        "data_quality": data_quality,
        "row_counts": row_counts,
        "artifacts": {
            name: str(output_dir / filename)
            for name, filename in REQUIRED_ARTIFACTS.items()
        },
    }


def _read_data_quality(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"ok": False, "errors": [f"Missing {path.name}"]}

    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        return {"ok": False, "errors": [f"Malformed {path.name}: {exc.msg}"]}

    if not isinstance(data, dict):
        return {"ok": False, "errors": [f"Malformed {path.name}: expected object"]}

    return data


def _count_csv_rows(output_dir: Path) -> tuple[dict[str, int], list[str]]:
    row_counts: dict[str, int] = {}
    errors: list[str] = []
    for key, filename in CSV_ROW_COUNT_KEYS.items():
        path = output_dir / filename
        if path.exists():
            try:
                row_counts[key] = len(pd.read_csv(path))
            except (EmptyDataError, ParserError, UnicodeDecodeError, OSError) as exc:
                errors.append(f"Malformed {filename}: {exc}")
    return row_counts, errors
