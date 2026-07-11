import json

from src.cli.ai import main


def test_ai_manifest_cli_outputs_safe_tool_catalog(capsys) -> None:
    assert main(["manifest", "--json"]) == 0

    manifest = json.loads(capsys.readouterr().out)
    names = {tool["name"] for tool in manifest["data"]["tools"]}

    assert manifest["ok"] is True
    assert manifest["command"] == "ai.manifest"
    assert "app.status" in names
    assert "report.summary" in names
    assert "report.run" in names
    assert "strategy.run" in names
    assert "strategy.inspect" in names
    assert "strategy.export" in names
    assert "analysis.stock" in names
    assert manifest["safety"]["analysis_only"] is True
    assert "BUY" in manifest["safety"]["forbidden_outputs"]
    assert all("argv" in tool for tool in manifest["data"]["tools"])
