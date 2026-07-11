from datetime import datetime
from pathlib import Path

import pandas as pd

from src.operations import (
    build_artifact_catalog,
    build_operations_check,
    build_run_metrics,
    write_run_manifest,
)


def test_build_operations_check_reports_complete_outputs_and_cache_warning(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    for filename in ["watchlist.csv", "market_regime.csv", "data_quality_status.json"]:
        (output_dir / filename).write_text("x\n", encoding="utf-8")
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "limit_up_strategy_review.csv", index=False)
    pd.DataFrame(columns=["symbol"]).to_csv(output_dir / "portfolio_review.csv", index=False)

    checks = build_operations_check(
        output_dir,
        [
            "watchlist.csv",
            "market_regime.csv",
            "data_quality_status.json",
            "limit_up_strategy_review.csv",
            "portfolio_review.csv",
        ],
        {
            "ok": True,
            "errors": [],
            "warnings": ["live data fetch failed; using existing local cache"],
        },
    )

    assert list(checks.columns) == ["check_name", "status", "severity", "detail"]
    assert checks.loc[checks["check_name"] == "输出文件完整性", "status"].item() == "PASS"
    assert checks.loc[checks["check_name"] == "数据质量", "status"].item() == "PASS"
    assert checks.loc[checks["check_name"] == "缓存使用", "status"].item() == "WARN"
    assert checks.loc[checks["check_name"] == "涨停复核可用性", "status"].item() == "PASS"
    assert checks.loc[checks["check_name"] == "组合复核可用性", "status"].item() == "WARN"


def test_write_run_manifest_records_status_inventory_and_row_counts(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    (output_dir / "report.html").write_text("<html></html>", encoding="utf-8")

    manifest = write_run_manifest(
        output_dir / "run_manifest.json",
        datetime(2026, 7, 10, 9, 0, 0),
        datetime(2026, 7, 10, 9, 0, 2),
        {"ok": False, "errors": ["synthetic failure"], "warnings": []},
        ["report.html", "watchlist.csv"],
        output_dir,
    )

    assert manifest["status"] == "DATA_ISSUE"
    assert manifest["duration_seconds"] == 2.0
    assert manifest["row_counts"]["watchlist.csv"] == 1
    assert manifest["outputs"][0]["filename"] == "report.html"
    assert (output_dir / "run_manifest.json").exists()


def test_build_artifact_catalog_records_file_sizes_and_row_counts(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519"}]).to_csv(output_dir / "watchlist.csv", index=False)
    (output_dir / "run_metrics.json").write_text('{"status":"OK"}', encoding="utf-8")

    catalog = build_artifact_catalog(output_dir, ["watchlist.csv", "run_metrics.json", "missing.csv"])

    assert list(catalog.columns) == ["artifact_name", "filename", "exists", "size_bytes", "row_count", "updated_at"]
    watchlist = catalog.loc[catalog["filename"] == "watchlist.csv"].iloc[0]
    assert watchlist["artifact_name"] == "watchlist"
    assert watchlist["exists"] is True
    assert watchlist["row_count"] == 1
    missing = catalog.loc[catalog["filename"] == "missing.csv"].iloc[0]
    assert missing["exists"] is False
    assert missing["row_count"] == -1


def test_build_run_metrics_summarizes_quality_checks_and_artifacts(tmp_path: Path) -> None:
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    pd.DataFrame([{"symbol": "600519"}, {"symbol": "300750"}]).to_csv(output_dir / "watchlist.csv", index=False)
    pd.DataFrame([{"check_name": "数据质量", "status": "PASS"}, {"check_name": "缓存使用", "status": "WARN"}]).to_csv(
        output_dir / "operations_check.csv", index=False
    )
    pd.DataFrame([{"filename": "watchlist.csv"}]).to_csv(output_dir / "artifact_catalog.csv", index=False)

    metrics = build_run_metrics(
        output_dir,
        {"ok": True, "errors": [], "warnings": ["using existing local cache"]},
        ["watchlist.csv", "operations_check.csv", "artifact_catalog.csv", "missing.csv"],
    )

    assert metrics["status"] == "OK"
    assert metrics["data_source_state"] == "CACHE_USED"
    assert metrics["watchlist_count"] == 2
    assert metrics["operations_warn_count"] == 1
    assert metrics["missing_file_count"] == 1
    assert metrics["artifact_file_count"] == 3
