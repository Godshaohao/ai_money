import json
from pathlib import Path

import pandas as pd

from backend.repositories.sqlite_repo import CliAuditRepository
from src.cli.strategy import main


def _write_strategy_inputs(output_dir: Path) -> None:
    output_dir.mkdir()
    pd.DataFrame(
        [
            {
                "symbol": "002115",
                "name": "三维通信",
                "review_score": 82,
                "review_label": "WATCH_REVIEW",
                "red_flags": "",
                "reason": "涨停复核",
            }
        ]
    ).to_csv(output_dir / "limit_up_strategy_review.csv", index=False)
    pd.DataFrame([{"symbol": "600519", "name": "贵州茅台", "rank": 1, "reason": "进入观察"}]).to_csv(
        output_dir / "watchlist.csv", index=False
    )
    pd.DataFrame(
        [{"symbol": "300750", "name": "宁德时代", "above_ma200": False, "reason": "持仓风险复核"}]
    ).to_csv(output_dir / "holding_risk.csv", index=False)


def test_strategy_cli_runs_lists_inspects_and_exports(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"
    db_path = tmp_path / "workbench.sqlite"
    export_path = tmp_path / "candidates.csv"
    _write_strategy_inputs(output_dir)

    assert main(["run", "all", "--output-dir", str(output_dir), "--db", str(db_path)]) == 0
    run_output = capsys.readouterr().out
    assert "策略复核完成" in run_output
    assert "候选 3" in run_output

    assert main(["list-runs", "--db", str(db_path)]) == 0
    list_output = capsys.readouterr().out
    assert "all" in list_output
    assert "SUCCESS" in list_output

    assert main(["inspect", "300750", "--db", str(db_path)]) == 0
    inspect_output = capsys.readouterr().out
    assert "300750" in inspect_output
    assert "持仓风险复核" in inspect_output

    assert main(["export", "--db", str(db_path), "--path", str(export_path)]) == 0
    export_output = capsys.readouterr().out
    assert "已导出" in export_output
    exported = pd.read_csv(export_path, dtype="string")
    assert list(exported["symbol"]) == ["600519", "002115", "300750"]


def test_strategy_cli_can_run_single_module(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    db_path = tmp_path / "workbench.sqlite"
    _write_strategy_inputs(output_dir)

    assert main(["run", "watchlist", "--output-dir", str(output_dir), "--db", str(db_path)]) == 0
    export_path = tmp_path / "watchlist.csv"
    assert main(["export", "--db", str(db_path), "--path", str(export_path)]) == 0
    exported = pd.read_csv(export_path, dtype="string")

    assert list(exported["module"]) == ["watchlist"]


def test_strategy_cli_json_mode_is_ai_readable_and_audited(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"
    db_path = tmp_path / "workbench.sqlite"
    export_path = tmp_path / "candidates.csv"
    _write_strategy_inputs(output_dir)

    assert main(["run", "all", "--output-dir", str(output_dir), "--db", str(db_path), "--json"]) == 0
    run_payload = json.loads(capsys.readouterr().out)
    assert run_payload["ok"] is True
    assert run_payload["command"] == "strategy.run"
    assert run_payload["data"]["metrics"]["candidate_count"] == 3

    assert main(["list-runs", "--db", str(db_path), "--json"]) == 0
    list_payload = json.loads(capsys.readouterr().out)
    assert list_payload["command"] == "strategy.list_runs"
    assert list_payload["data"]["runs"][0]["status"] == "SUCCESS"

    assert main(["inspect", "300750", "--db", str(db_path), "--json"]) == 0
    inspect_payload = json.loads(capsys.readouterr().out)
    assert inspect_payload["command"] == "strategy.inspect"
    assert inspect_payload["data"]["detail"]["symbol"] == "300750"
    assert inspect_payload["data"]["detail"]["evidence"][0]["title"] == "持仓风险证据"

    assert main(["export", "--db", str(db_path), "--path", str(export_path), "--json"]) == 0
    export_payload = json.loads(capsys.readouterr().out)
    assert export_payload["command"] == "strategy.export"
    assert export_payload["data"]["path"] == str(export_path)
    assert export_payload["data"]["row_count"] == 3

    audit_calls = CliAuditRepository(db_path).list_calls(limit=10)
    assert {call["tool_name"] for call in audit_calls} >= {
        "strategy.run",
        "strategy.list_runs",
        "strategy.inspect",
        "strategy.export",
    }
