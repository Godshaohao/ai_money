import json
from pathlib import Path

import pandas as pd

from backend.services.artifacts import build_report_summary


def test_build_report_summary_reads_existing_outputs(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "report.html").write_text("<html>RISK_ON</html>", encoding="utf-8")
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "holding_risk.csv", index=False)
    pd.DataFrame([{"status": "POSITIVE"}]).to_csv(output_dir / "market_regime.csv", index=False)
    (output_dir / "data_quality_status.json").write_text(
        json.dumps({"ok": True, "warnings": []}),
        encoding="utf-8",
    )

    summary = build_report_summary(output_dir)

    assert summary["exists"] is True
    assert summary["data_quality"]["ok"] is True
    assert summary["row_counts"]["watchlist"] == 1
    assert summary["row_counts"]["excluded_stocks"] == 0
    assert summary["row_counts"]["holding_risk"] == 1
    assert summary["row_counts"]["market_regime"] == 1
    assert summary["artifacts"]["report_html"].endswith("report.html")


def test_build_report_summary_reports_missing_outputs(tmp_path: Path) -> None:
    summary = build_report_summary(tmp_path / "output")

    assert summary["exists"] is False
    assert summary["data_quality"]["ok"] is False
    assert summary["missing_files"]


def test_build_report_summary_reports_malformed_data_quality_json(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    (output_dir / "report.html").write_text("<html>RISK_ON</html>", encoding="utf-8")
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "excluded_stocks.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "holding_risk.csv", index=False)
    pd.DataFrame(columns=["status"]).to_csv(output_dir / "market_regime.csv", index=False)
    (output_dir / "data_quality_status.json").write_text("{bad json", encoding="utf-8")

    summary = build_report_summary(output_dir)

    assert summary["exists"] is True
    assert summary["data_quality"]["ok"] is False
    assert summary["data_quality"]["errors"]
