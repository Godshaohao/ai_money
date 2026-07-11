from pathlib import Path

from backend.repositories.sqlite_repo import ReportTableRepository


DETAIL_TABLES = [
    "limit_up_strategy_review",
    "limit_up_pool",
    "dragon_tiger",
    "holding_risk",
    "portfolio_review",
    "excluded_stocks",
    "watchlist",
]


def read_security_detail(db_path: Path, symbol: str) -> dict:
    normalized_symbol = str(symbol).strip().zfill(6)
    repo = ReportTableRepository(db_path)
    sections: dict[str, list[dict]] = {}
    first_row: dict | None = None
    latest_review: dict | None = None

    for table_name in DETAIL_TABLES:
        table = repo.read_table(table_name, limit=5000)
        if not table["exists"]:
            continue
        rows = [row for row in table["rows"] if str(row.get("symbol", "")).zfill(6) == normalized_symbol]
        if not rows:
            continue
        sections[table_name] = rows
        first_row = first_row or rows[0]
        if table_name == "limit_up_strategy_review":
            latest_review = rows[0]

    return {
        "symbol": normalized_symbol,
        "exists": bool(sections),
        "name": (first_row or {}).get("name", ""),
        "latest_review_label": (latest_review or {}).get("review_label", ""),
        "latest_review_score": (latest_review or {}).get("review_score", ""),
        "risk_flags": (latest_review or first_row or {}).get("red_flags", (first_row or {}).get("risk_flags", "")),
        "sections": sections,
    }
