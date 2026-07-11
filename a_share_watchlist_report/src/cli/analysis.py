import argparse
from pathlib import Path
from typing import Sequence

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import CliAuditRepository
from src.cli.json_contract import build_cli_response, emit_cli_response
from src.stock_analysis import build_stock_analysis


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="个股复盘分析 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    stock_parser = subparsers.add_parser("stock", help="生成单股复盘分析")
    stock_parser.add_argument("symbol")
    stock_parser.add_argument("--output-dir", default="output")
    stock_parser.add_argument("--db", default="data/workbench.sqlite")
    stock_parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    if args.command == "stock":
        db_path = Path(args.db)
        initialize_database(db_path)
        analysis = build_stock_analysis(args.symbol, output_dir=Path(args.output_dir), db_path=db_path)
        response = build_cli_response(
            command="analysis.stock",
            ok=True,
            data={
                "message": f"{analysis['identity']['symbol']} 个股复盘分析",
                "analysis": analysis,
            },
        )
        CliAuditRepository(db_path).record_call(
            tool_name="analysis.stock",
            status="SUCCESS",
            started_at="",
            finished_at="",
            args={"symbol": args.symbol, "output_dir": str(args.output_dir)},
            result=response,
        )
        emit_cli_response(response, as_json=args.as_json)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
