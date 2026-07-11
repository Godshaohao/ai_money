import argparse
from datetime import datetime
from pathlib import Path
from typing import Sequence

import pandas as pd

from backend.db.schema import initialize_database
from backend.repositories.sqlite_repo import CliAuditRepository, StrategyRepository
from src.cli.json_contract import build_cli_response, emit_cli_response
from src.strategy_review import build_strategy_records


MODULES_BY_COMMAND = {
    "all": ["limit_up", "watchlist", "holding_risk"],
    "limit-up": ["limit_up"],
    "watchlist": ["watchlist"],
    "holding-risk": ["holding_risk"],
}


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    command = args.command.replace("-", "_")
    return int(globals()[f"_command_{command}"](args))


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="A 股策略复核 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="运行策略复核")
    run_parser.add_argument("module", choices=sorted(MODULES_BY_COMMAND.keys()))
    run_parser.add_argument("--output-dir", default="output")
    run_parser.add_argument("--db", default="data/workbench.sqlite")
    run_parser.add_argument("--json", action="store_true", dest="as_json")

    list_parser = subparsers.add_parser("list-runs", help="查看策略运行历史")
    list_parser.add_argument("--db", default="data/workbench.sqlite")
    list_parser.add_argument("--limit", type=int, default=10)
    list_parser.add_argument("--json", action="store_true", dest="as_json")

    inspect_parser = subparsers.add_parser("inspect", help="查看个股策略证据")
    inspect_parser.add_argument("symbol")
    inspect_parser.add_argument("--db", default="data/workbench.sqlite")
    inspect_parser.add_argument("--json", action="store_true", dest="as_json")

    export_parser = subparsers.add_parser("export", help="导出最新策略候选")
    export_parser.add_argument("--db", default="data/workbench.sqlite")
    export_parser.add_argument("--path", default="output/strategy_candidates.csv")
    export_parser.add_argument("--module", default="")
    export_parser.add_argument("--json", action="store_true", dest="as_json")

    return parser


def _command_run(args: argparse.Namespace) -> int:
    db_path = Path(args.db)
    initialize_database(db_path)
    repo = StrategyRepository(db_path)
    started_at = _now()
    modules = MODULES_BY_COMMAND[args.module]
    run_id = repo.create_run(
        strategy_name=args.module,
        status="RUNNING",
        started_at=started_at,
        params={"modules": modules, "output_dir": str(args.output_dir)},
    )
    try:
        output_dir = Path(args.output_dir)
        records = build_strategy_records(
            limit_up_review=_read_csv(output_dir / "limit_up_strategy_review.csv"),
            watchlist=_read_csv(output_dir / "watchlist.csv"),
            holding_risk=_read_csv(output_dir / "holding_risk.csv"),
            modules=modules,
        )
        repo.replace_candidates(run_id, records.candidates)
        repo.replace_evidence(run_id, records.evidence)
        repo.replace_metrics(run_id, records.metrics)
        repo.finish_run(run_id, "SUCCESS", _now(), "策略复核完成")
        response = build_cli_response(
            command="strategy.run",
            ok=True,
            data={
                "message": (
                    f"策略复核完成：run_id {run_id}，候选 {records.metrics['candidate_count']}，"
                    f"风险 {records.metrics['risk_count']}"
                ),
                "run_id": run_id,
                "strategy_name": args.module,
                "metrics": records.metrics,
            },
        )
        _audit(db_path, "strategy.run", "SUCCESS", started_at, {"module": args.module}, response)
        emit_cli_response(response, as_json=args.as_json)
        return 0
    except Exception as exc:
        repo.finish_run(run_id, "FAILED", _now(), str(exc))
        response = build_cli_response(
            command="strategy.run",
            ok=False,
            data={"run_id": run_id, "strategy_name": args.module},
            errors=[str(exc)],
        )
        _audit(db_path, "strategy.run", "FAILED", started_at, {"module": args.module}, response)
        emit_cli_response(response, as_json=args.as_json)
        return 1


def _command_list_runs(args: argparse.Namespace) -> int:
    initialize_database(Path(args.db))
    repo = StrategyRepository(Path(args.db))
    runs = repo.list_runs(limit=max(int(args.limit), 1))
    response = build_cli_response(
        command="strategy.list_runs",
        ok=True,
        data={"runs": runs, "message": f"策略运行记录 {len(runs)} 条"},
    )
    _audit(Path(args.db), "strategy.list_runs", "SUCCESS", _now(), {"limit": args.limit}, response)
    if args.as_json:
        emit_cli_response(response, as_json=True)
        return 0
    if not runs:
        print("暂无策略运行记录")
        return 0
    for run in runs:
        metrics = run["metrics"]
        print(
            f"{run['id']}\t{run['strategy_name']}\t{run['status']}\t"
            f"候选 {metrics.get('candidate_count', 0)}\t风险 {metrics.get('risk_count', 0)}"
        )
    return 0


def _command_inspect(args: argparse.Namespace) -> int:
    initialize_database(Path(args.db))
    repo = StrategyRepository(Path(args.db))
    detail = repo.inspect_symbol(args.symbol)
    response = build_cli_response(
        command="strategy.inspect",
        ok=True,
        data={"detail": detail, "message": f"{detail['symbol']} 策略证据"},
    )
    _audit(Path(args.db), "strategy.inspect", "SUCCESS", _now(), {"symbol": args.symbol}, response)
    if args.as_json:
        emit_cli_response(response, as_json=True)
        return 0
    if not detail["exists"]:
        print(f"{detail['symbol']} 暂无策略证据")
        return 0
    print(f"{detail['symbol']} 策略证据")
    for candidate in detail["candidates"]:
        print(
            f"- {candidate['module']}：{candidate['label']}，"
            f"复核分 {candidate['score']:.0f}，{candidate['reason']}"
        )
    for evidence in detail["evidence"]:
        print(f"  · {evidence['title']}：{evidence['detail']}")
    return 0


def _command_export(args: argparse.Namespace) -> int:
    initialize_database(Path(args.db))
    repo = StrategyRepository(Path(args.db))
    candidates = repo.list_candidates(module=args.module, limit=10000, offset=0)
    frame = pd.DataFrame(candidates["rows"])
    path = Path(args.path)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(path, index=False)
    response = build_cli_response(
        command="strategy.export",
        ok=True,
        data={"path": str(path), "row_count": len(frame), "message": f"已导出 {len(frame)} 行到 {path}"},
    )
    _audit(Path(args.db), "strategy.export", "SUCCESS", _now(), {"path": str(path), "module": args.module}, response)
    if args.as_json:
        emit_cli_response(response, as_json=True)
        return 0
    print(f"已导出 {len(frame)} 行到 {path}")
    return 0


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _now() -> str:
    return datetime.now().astimezone().isoformat(timespec="seconds")


def _audit(db_path: Path, tool_name: str, status: str, started_at: str, args: dict, result: dict) -> None:
    CliAuditRepository(db_path).record_call(
        tool_name=tool_name,
        status=status,
        started_at=started_at,
        finished_at=_now(),
        args=args,
        result=result,
    )


if __name__ == "__main__":
    raise SystemExit(main())
