import json
from typing import Any


FORBIDDEN_OUTPUTS = [
    "BUY",
    "SELL",
    "target_price",
    "broker_order",
    "automated_trading",
]


def build_cli_response(
    command: str,
    ok: bool,
    data: dict[str, Any],
    warnings: list[str] | None = None,
    errors: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "ok": ok,
        "command": command,
        "data": data,
        "warnings": warnings or [],
        "errors": errors or [],
        "safety": {
            "analysis_only": True,
            "forbidden_outputs": FORBIDDEN_OUTPUTS,
        },
    }


def emit_cli_response(response: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(response, ensure_ascii=False, sort_keys=True))
        return
    if response["ok"]:
        print(response["data"].get("message", "命令完成"))
    else:
        print("命令失败：" + "；".join(str(error) for error in response["errors"]))
