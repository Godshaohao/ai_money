from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import CliAuditRepository


def test_cli_audit_repository_records_and_lists_tool_calls(tmp_path: Path) -> None:
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = CliAuditRepository(db_path)

    call_id = repo.record_call(
        tool_name="strategy.inspect",
        status="SUCCESS",
        started_at="2026-07-11T15:00:00+08:00",
        finished_at="2026-07-11T15:00:01+08:00",
        args={"symbol": "002115"},
        result={"ok": True, "symbol": "002115"},
    )

    calls = repo.list_calls()

    assert calls[0]["id"] == call_id
    assert calls[0]["tool_name"] == "strategy.inspect"
    assert calls[0]["status"] == "SUCCESS"
    assert calls[0]["args"] == {"symbol": "002115"}
    assert calls[0]["result"] == {"ok": True, "symbol": "002115"}
