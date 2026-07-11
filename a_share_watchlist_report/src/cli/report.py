import argparse
import subprocess
import sys
from pathlib import Path
from typing import Callable, Sequence

from src.cli.json_contract import build_cli_response, emit_cli_response


REPORT_ARTIFACTS = [
    "report.html",
    "watchlist.csv",
    "excluded_stocks.csv",
    "holding_risk.csv",
    "market_regime.csv",
    "data_quality_status.json",
    "run_metrics.json",
    "artifact_catalog.csv",
    "strategy_candidates.csv",
]


def main(argv: Sequence[str] | None = None, runner: Callable[[], int] | None = None) -> int:
    parser = argparse.ArgumentParser(description="本地报告 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    summary_parser = subparsers.add_parser("summary", help="读取最新报告摘要")
    summary_parser.add_argument("--output-dir", default="output")
    summary_parser.add_argument("--json", action="store_true", dest="as_json")

    run_parser = subparsers.add_parser("run", help="运行报告生成")
    run_parser.add_argument("--output-dir", default="output")
    run_parser.add_argument("--json", action="store_true", dest="as_json")

    args = parser.parse_args(argv)
    if args.command == "summary":
        response = build_cli_response("report.summary", True, _summary(Path(args.output_dir)))
        emit_cli_response(response, as_json=args.as_json)
        return 0
    if args.command == "run":
        run = runner or _default_runner
        exit_code = int(run())
        response = build_cli_response(
            command="report.run",
            ok=exit_code == 0,
            data={"exit_code": exit_code, **_summary(Path(args.output_dir))},
            errors=[] if exit_code == 0 else [f"run_report.py exited {exit_code}"],
        )
        emit_cli_response(response, as_json=args.as_json)
        return 0 if exit_code == 0 else 1
    return 1


def _summary(output_dir: Path) -> dict:
    return {
        "output_dir": str(output_dir),
        "artifacts": {
            name: {
                "exists": (output_dir / name).exists(),
                "size_bytes": (output_dir / name).stat().st_size if (output_dir / name).exists() else 0,
            }
            for name in REPORT_ARTIFACTS
        },
    }


def _default_runner() -> int:
    return subprocess.run([sys.executable, "run_report.py"], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
