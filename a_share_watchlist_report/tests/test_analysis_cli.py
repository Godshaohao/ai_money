import json
from pathlib import Path

import pandas as pd

from src.cli.analysis import main


def test_analysis_cli_outputs_stock_analysis_json(tmp_path: Path, capsys) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    db_path = tmp_path / "workbench.sqlite"
    pd.DataFrame(
        [
            {
                "symbol": "603538",
                "name": "美诺华",
                "trade_date": "2026-07-10",
                "amount": 2_134_658_736,
                "break_count": 9,
                "streak_count": 1,
                "industry": "化学制药",
            }
        ]
    ).to_csv(output_dir / "limit_up_pool.csv", index=False)

    assert main(["stock", "603538", "--output-dir", str(output_dir), "--db", str(db_path), "--json"]) == 0

    payload = json.loads(capsys.readouterr().out)
    assert payload["ok"] is True
    assert payload["command"] == "analysis.stock"
    assert payload["data"]["analysis"]["identity"]["symbol"] == "603538"
    assert payload["data"]["analysis"]["sector_echelon"][0]["industry"] == "化学制药"
    assert payload["safety"]["analysis_only"] is True
