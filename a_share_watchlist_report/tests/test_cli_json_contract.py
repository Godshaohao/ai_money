import json

from src.cli.json_contract import build_cli_response, emit_cli_response


def test_build_cli_response_has_stable_ai_readable_shape() -> None:
    response = build_cli_response(
        command="strategy.inspect",
        ok=True,
        data={"symbol": "002115"},
        warnings=["人工复核"],
    )

    assert response["ok"] is True
    assert response["command"] == "strategy.inspect"
    assert response["data"] == {"symbol": "002115"}
    assert response["warnings"] == ["人工复核"]
    assert response["errors"] == []
    assert response["safety"]["analysis_only"] is True
    assert response["safety"]["forbidden_outputs"] == [
        "BUY",
        "SELL",
        "target_price",
        "broker_order",
        "automated_trading",
    ]


def test_emit_cli_response_prints_json_when_requested(capsys) -> None:
    response = build_cli_response("app.status", True, {"status": "OK"})

    emit_cli_response(response, as_json=True)

    printed = json.loads(capsys.readouterr().out)
    assert printed["command"] == "app.status"
    assert printed["data"]["status"] == "OK"
