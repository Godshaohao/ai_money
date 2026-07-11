from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import ReportTableRepository
from backend.services.security_detail import read_security_detail


def test_read_security_detail_collects_symbol_rows_from_key_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = ReportTableRepository(db_path)
    repo.replace_table(
        "limit_up_strategy_review",
        columns=["symbol", "name", "review_label", "review_score", "red_flags"],
        rows=[{"symbol": "002115", "name": "三维通信", "review_label": "WATCH_REVIEW", "review_score": "89", "red_flags": "HISTORY_GAP"}],
        updated_at="2026-07-11T14:00:00+08:00",
    )
    repo.replace_table(
        "limit_up_pool",
        columns=["symbol", "trade_date", "limit_up_stats"],
        rows=[{"symbol": "002115", "trade_date": "2026-07-10", "limit_up_stats": "1天1板"}],
        updated_at="2026-07-11T14:00:00+08:00",
    )

    detail = read_security_detail(db_path, "2115")

    assert detail["exists"] is True
    assert detail["symbol"] == "002115"
    assert detail["name"] == "三维通信"
    assert detail["latest_review_label"] == "WATCH_REVIEW"
    assert detail["risk_flags"] == "HISTORY_GAP"
    assert detail["sections"]["limit_up_strategy_review"][0]["review_score"] == "89"
    assert detail["sections"]["limit_up_pool"][0]["limit_up_stats"] == "1天1板"


def test_read_security_detail_returns_empty_contract_for_unknown_symbol(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)

    detail = read_security_detail(db_path, "600000")

    assert detail["exists"] is False
    assert detail["symbol"] == "600000"
    assert detail["sections"] == {}
