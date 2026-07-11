import argparse
from typing import Sequence

from src.cli.json_contract import build_cli_response, emit_cli_response


TOOLS = [
    {
        "name": "app.status",
        "argv": ["python", "-m", "src.cli.app", "status", "--json"],
        "description": "读取本地应用、数据质量、报告产物和策略运行状态。",
        "output": "CLI JSON envelope with data.status, data.data_quality, data.strategy_latest_run",
    },
    {
        "name": "report.summary",
        "argv": ["python", "-m", "src.cli.report", "summary", "--json"],
        "description": "读取最新静态报告摘要和核心输出文件状态。",
        "output": "CLI JSON envelope with report summary data",
    },
    {
        "name": "report.run",
        "argv": ["python", "-m", "src.cli.report", "run", "--json"],
        "description": "运行本地报告生成流程。",
        "output": "CLI JSON envelope with generated output inventory",
    },
    {
        "name": "strategy.run",
        "argv": ["python", "-m", "src.cli.strategy", "run", "all", "--json"],
        "description": "运行本地策略复核，生成候选和证据。",
        "output": "CLI JSON envelope with run_id and candidate metrics",
    },
    {
        "name": "strategy.inspect",
        "argv": ["python", "-m", "src.cli.strategy", "inspect", "<symbol>", "--json"],
        "description": "读取单只股票的策略候选和证据。",
        "output": "CLI JSON envelope with candidates and evidence",
    },
    {
        "name": "strategy.export",
        "argv": ["python", "-m", "src.cli.strategy", "export", "--path", "output/strategy_candidates.csv", "--json"],
        "description": "导出最新策略候选表。",
        "output": "CLI JSON envelope with export path and row count",
    },
    {
        "name": "analysis.stock",
        "argv": ["python", "-m", "src.cli.analysis", "stock", "<symbol>", "--json"],
        "description": "生成单股复盘分析，包含涨停事件、板块梯队、策略证据和人工复核清单。",
        "output": "CLI JSON envelope with data.analysis sections",
    },
]


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="AI Agent 工具清单 CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)
    manifest_parser = subparsers.add_parser("manifest", help="输出 AI 可调用 CLI 工具清单")
    manifest_parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)
    if args.command == "manifest":
        response = build_cli_response(
            command="ai.manifest",
            ok=True,
            data={
                "tools": TOOLS,
                "notes": [
                    "所有工具只输出投研复核数据和证据。",
                    "AI Agent 不应把输出解释为交易指令。",
                ],
            },
        )
        emit_cli_response(response, as_json=args.as_json)
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
