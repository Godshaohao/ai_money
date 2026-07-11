import json
from pathlib import Path

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository
from src.cli.app import main as app_main
from src.cli.report import main as report_main


def test_app_status_outputs_json_with_quality_and_strategy_state(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "data_quality_status.json").write_text(
        json.dumps({"ok": False, "errors": ["DATA_ISSUE"]}, ensure_ascii=False),
        encoding="utf-8",
    )
    db_path = tmp_path / "workbench.sqlite"
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    run_id = repo.create_run("all", "RUNNING", "2026-07-11T15:10:00+08:00", {})
    repo.replace_metrics(run_id, {"candidate_count": 3, "risk_count": 1})
    repo.finish_run(run_id, "SUCCESS", "2026-07-11T15:11:00+08:00", "策略复核完成")

    assert app_main(["status", "--output-dir", str(output_dir), "--db", str(db_path), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == "app.status"
    assert payload["data"]["data_quality"]["ok"] is False
    assert payload["data"]["strategy_latest_run"]["id"] == run_id


def test_report_summary_outputs_existing_artifacts(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "report.html").write_text("<html></html>", encoding="utf-8")
    (output_dir / "watchlist.csv").write_text("symbol,name\n600519,贵州茅台\n", encoding="utf-8")

    assert report_main(["summary", "--output-dir", str(output_dir), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "report.summary"
    assert payload["data"]["artifacts"]["report.html"]["exists"] is True
    assert payload["data"]["artifacts"]["watchlist.csv"]["exists"] is True


def test_report_run_can_use_injected_runner(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"

    def fake_runner() -> int:
        output_dir.mkdir()
        (output_dir / "report.html").write_text("<html>ok</html>", encoding="utf-8")
        return 0

    assert report_main(["run", "--output-dir", str(output_dir), "--json"], runner=fake_runner) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == "report.run"
    assert payload["data"]["exit_code"] == 0
    assert payload["data"]["artifacts"]["report.html"]["exists"] is True
