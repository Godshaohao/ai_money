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
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "portfolio_review.csv", index=False)
    pd.DataFrame([{"status": "POSITIVE"}]).to_csv(output_dir / "market_regime.csv", index=False)
    pd.DataFrame([{"check_name": "数据质量", "status": "PASS"}]).to_csv(
        output_dir / "operations_check.csv", index=False
    )
    pd.DataFrame([{"artifact_name": "watchlist", "filename": "watchlist.csv"}]).to_csv(
        output_dir / "artifact_catalog.csv", index=False
    )
    (output_dir / "run_manifest.json").write_text(
        json.dumps({"status": "OK"}),
        encoding="utf-8",
    )
    (output_dir / "run_metrics.json").write_text(
        json.dumps({"status": "OK", "artifact_file_count": 9}),
        encoding="utf-8",
    )
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
    assert summary["row_counts"]["portfolio_review"] == 1
    assert summary["row_counts"]["market_regime"] == 1
    assert summary["row_counts"]["operations_check"] == 1
    assert summary["row_counts"]["artifact_catalog"] == 1
    assert summary["run_metrics"]["status"] == "OK"
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
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "portfolio_review.csv", index=False)
    pd.DataFrame(columns=["status"]).to_csv(output_dir / "market_regime.csv", index=False)
    pd.DataFrame(columns=["check_name", "status"]).to_csv(output_dir / "operations_check.csv", index=False)
    pd.DataFrame(columns=["artifact_name", "filename"]).to_csv(output_dir / "artifact_catalog.csv", index=False)
    (output_dir / "run_manifest.json").write_text("{}", encoding="utf-8")
    (output_dir / "run_metrics.json").write_text("{}", encoding="utf-8")
    (output_dir / "data_quality_status.json").write_text("{bad json", encoding="utf-8")

    summary = build_report_summary(output_dir)

    assert summary["exists"] is True
    assert summary["data_quality"]["ok"] is False
    assert summary["data_quality"]["errors"]
