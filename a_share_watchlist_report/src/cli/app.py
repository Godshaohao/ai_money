import argparse
import json
from pathlib import Path
from typing import Sequence

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import StrategyRepository
from src.cli.json_contract import build_cli_response, emit_cli_response


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="本地投研应用状态 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    status_parser = subparsers.add_parser("status", help="读取本地应用状态")
    status_parser.add_argument("--output-dir", default="output")
    status_parser.add_argument("--db", default="data/workbench.sqlite")
    status_parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    if args.command == "status":
        response = build_cli_response(
            command="app.status",
            ok=True,
            data=_status(Path(args.output_dir), Path(args.db)),
        )
        emit_cli_response(response, as_json=args.as_json)
        return 0
    return 1


def _status(output_dir: Path, db_path: Path) -> dict:
    quality_path = output_dir / "data_quality_status.json"
    data_quality = _read_json(quality_path, default={"ok": False, "errors": ["missing data_quality_status.json"]})
    latest_strategy_run = None
    if db_path.exists():
        initialize_database(db_path)
        runs = StrategyRepository(db_path).list_runs(limit=1)
        latest_strategy_run = runs[0] if runs else None
    return {
        "status": "READY" if data_quality.get("ok") else "DATA_ISSUE",
        "output_dir": str(output_dir),
        "database": str(db_path),
        "data_quality": data_quality,
        "strategy_latest_run": latest_strategy_run,
    }


def _read_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"ok": False, "errors": [f"malformed {path.name}"]}


if __name__ == "__main__":
    raise SystemExit(main())
