from __future__ import annotations

from datetime import datetime
import json
from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError


OPERATIONS_CHECK_COLUMNS = ["check_name", "status", "severity", "detail"]
ARTIFACT_CATALOG_COLUMNS = ["artifact_name", "filename", "exists", "size_bytes", "row_count", "updated_at"]


def build_output_inventory(output_dir: Path, expected_files: list[str]) -> list[dict[str, Any]]:
    output_dir = Path(output_dir)
    inventory = []
    for filename in expected_files:
        path = output_dir / filename
        inventory.append(
            {
                "filename": filename,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
            }
        )
    return inventory


def build_artifact_catalog(output_dir: Path, expected_files: list[str]) -> pd.DataFrame:
    output_dir = Path(output_dir)
    rows = []
    for filename in expected_files:
        path = output_dir / filename
        rows.append(
            {
                "artifact_name": Path(filename).stem,
                "filename": filename,
                "exists": path.exists(),
                "size_bytes": path.stat().st_size if path.exists() else 0,
                "row_count": _csv_row_count(path) if path.exists() and filename.endswith(".csv") else -1,
                "updated_at": datetime.fromtimestamp(path.stat().st_mtime).isoformat(timespec="seconds")
                if path.exists()
                else "",
            }
        )
    catalog = pd.DataFrame(rows, columns=ARTIFACT_CATALOG_COLUMNS)
    catalog["exists"] = catalog["exists"].astype(object)
    return catalog


def build_operations_check(
    output_dir: Path,
    expected_files: list[str],
    data_quality_status: dict[str, Any],
) -> pd.DataFrame:
    output_dir = Path(output_dir)
    rows = [
        _output_completeness_check(output_dir, expected_files),
        _data_quality_check(data_quality_status),
        _cache_usage_check(data_quality_status),
        _table_availability_check(output_dir, "limit_up_strategy_review.csv", "涨停复核可用性"),
        _table_availability_check(output_dir, "portfolio_review.csv", "组合复核可用性"),
    ]
    return pd.DataFrame(rows, columns=OPERATIONS_CHECK_COLUMNS)


def build_run_metrics(
    output_dir: Path,
    data_quality_status: dict[str, Any],
    expected_files: list[str],
) -> dict[str, Any]:
    output_dir = Path(output_dir)
    errors = list(data_quality_status.get("errors") or [])
    warnings = [str(warning) for warning in data_quality_status.get("warnings") or []]
    operations = _read_csv_if_exists(output_dir / "operations_check.csv")
    check_statuses = operations["status"].astype(str).tolist() if not operations.empty and "status" in operations else []
    existing_files = [filename for filename in expected_files if (output_dir / filename).exists()]
    missing_files = [filename for filename in expected_files if not (output_dir / filename).exists()]
    row_counts = _csv_row_counts(output_dir, expected_files)
    total_size = sum((output_dir / filename).stat().st_size for filename in existing_files)
    status = "OK" if data_quality_status.get("ok") is True and not errors else "DATA_ISSUE"
    return {
        "status": status,
        "data_quality_ok": bool(data_quality_status.get("ok")),
        "data_source_state": _data_source_state(errors, warnings),
        "artifact_file_count": len(existing_files),
        "missing_file_count": len(missing_files),
        "total_output_size_bytes": int(total_size),
        "watchlist_count": int(row_counts.get("watchlist.csv", 0)),
        "excluded_count": int(row_counts.get("excluded_stocks.csv", 0)),
        "holding_risk_count": int(row_counts.get("holding_risk.csv", 0)),
        "portfolio_review_count": int(row_counts.get("portfolio_review.csv", 0)),
        "limit_up_review_count": int(row_counts.get("limit_up_strategy_review.csv", 0)),
        "operations_pass_count": check_statuses.count("PASS"),
        "operations_warn_count": check_statuses.count("WARN"),
        "operations_fail_count": check_statuses.count("FAIL"),
        "warning_count": len(warnings),
        "error_count": len(errors),
    }


def write_run_metrics(output_path: Path, metrics: dict[str, Any]) -> None:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(metrics, ensure_ascii=False, indent=2), encoding="utf-8")


def write_run_manifest(
    output_path: Path,
    started_at: datetime,
    finished_at: datetime,
    data_quality_status: dict[str, Any],
    expected_files: list[str],
    output_dir: Path,
) -> dict[str, Any]:
    output_path = Path(output_path)
    output_dir = Path(output_dir)
    duration = max((finished_at - started_at).total_seconds(), 0.0)
    errors = list(data_quality_status.get("errors") or [])
    warnings = list(data_quality_status.get("warnings") or [])
    manifest = {
        "run_id": started_at.strftime("%Y%m%d%H%M%S"),
        "started_at": started_at.isoformat(timespec="seconds"),
        "finished_at": finished_at.isoformat(timespec="seconds"),
        "duration_seconds": duration,
        "status": "OK" if data_quality_status.get("ok") is True and not errors else "DATA_ISSUE",
        "data_quality_ok": bool(data_quality_status.get("ok")),
        "errors": errors,
        "warnings": warnings,
        "outputs": build_output_inventory(output_dir, expected_files),
        "row_counts": _csv_row_counts(output_dir, expected_files),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def write_operations_artifacts(
    output_dir: Path,
    started_at: datetime,
    finished_at: datetime,
    data_quality_status: dict[str, Any],
    expected_files: list[str],
) -> tuple[pd.DataFrame, dict[str, Any]]:
    output_dir = Path(output_dir)
    check_files = [filename for filename in expected_files if filename != "report.html"]
    checks = build_operations_check(output_dir, check_files, data_quality_status)
    checks.to_csv(output_dir / "operations_check.csv", index=False)
    artifact_files = expected_files + ["operations_check.csv", "run_manifest.json", "artifact_catalog.csv", "run_metrics.json"]
    artifact_catalog = build_artifact_catalog(output_dir, artifact_files)
    artifact_catalog.to_csv(output_dir / "artifact_catalog.csv", index=False)
    run_metrics = build_run_metrics(output_dir, data_quality_status, artifact_files)
    write_run_metrics(output_dir / "run_metrics.json", run_metrics)
    manifest = write_run_manifest(
        output_dir / "run_manifest.json",
        started_at,
        finished_at,
        data_quality_status,
        artifact_files,
        output_dir,
    )
    artifact_catalog = build_artifact_catalog(output_dir, artifact_files)
    artifact_catalog.to_csv(output_dir / "artifact_catalog.csv", index=False)
    run_metrics = build_run_metrics(output_dir, data_quality_status, artifact_files)
    write_run_metrics(output_dir / "run_metrics.json", run_metrics)
    return checks, manifest


def _output_completeness_check(output_dir: Path, expected_files: list[str]) -> dict[str, str]:
    missing = [filename for filename in expected_files if not (output_dir / filename).exists()]
    if missing:
        return {
            "check_name": "输出文件完整性",
            "status": "FAIL",
            "severity": "P0",
            "detail": "缺少文件: " + ", ".join(missing),
        }
    return {
        "check_name": "输出文件完整性",
        "status": "PASS",
        "severity": "P0",
        "detail": "核心报告文件已生成",
    }


def _data_quality_check(data_quality_status: dict[str, Any]) -> dict[str, str]:
    errors = list(data_quality_status.get("errors") or [])
    if data_quality_status.get("ok") is not True or errors:
        return {
            "check_name": "数据质量",
            "status": "FAIL",
            "severity": "P0",
            "detail": "; ".join(str(error) for error in errors) or "data_quality_status.ok=false",
        }
    return {
        "check_name": "数据质量",
        "status": "PASS",
        "severity": "P0",
        "detail": "数据质量检查通过",
    }


def _cache_usage_check(data_quality_status: dict[str, Any]) -> dict[str, str]:
    warnings = [str(warning) for warning in data_quality_status.get("warnings") or []]
    cache_warnings = [
        warning
        for warning in warnings
        if "using existing local cache" in warning or "使用现有本地缓存" in warning
    ]
    if cache_warnings:
        return {
            "check_name": "缓存使用",
            "status": "WARN",
            "severity": "P2",
            "detail": "; ".join(cache_warnings),
        }
    return {
        "check_name": "缓存使用",
        "status": "PASS",
        "severity": "P2",
        "detail": "本次未触发本地缓存降级",
    }


def _table_availability_check(output_dir: Path, filename: str, check_name: str) -> dict[str, str]:
    path = output_dir / filename
    if not path.exists():
        return {
            "check_name": check_name,
            "status": "WARN",
            "severity": "P2",
            "detail": f"{filename} 未生成",
        }
    try:
        row_count = len(pd.read_csv(path))
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError) as exc:
        return {
            "check_name": check_name,
            "status": "WARN",
            "severity": "P2",
            "detail": f"{filename} 读取失败: {exc}",
        }
    if row_count == 0:
        return {
            "check_name": check_name,
            "status": "WARN",
            "severity": "P2",
            "detail": f"{filename} 当前为空表",
        }
    return {
        "check_name": check_name,
        "status": "PASS",
        "severity": "P2",
        "detail": f"{filename} 共 {row_count} 行",
    }


def _csv_row_counts(output_dir: Path, expected_files: list[str]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for filename in expected_files:
        if not filename.endswith(".csv"):
            continue
        path = output_dir / filename
        if not path.exists():
            continue
        counts[filename] = _csv_row_count(path)
    return counts


def _csv_row_count(path: Path) -> int:
    try:
        return len(pd.read_csv(path))
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError):
        return -1


def _read_csv_if_exists(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    try:
        return pd.read_csv(path)
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError):
        return pd.DataFrame()


def _data_source_state(errors: list[Any], warnings: list[str]) -> str:
    if errors:
        return "DATA_ISSUE"
    if any("using existing local cache" in warning or "使用现有本地缓存" in warning for warning in warnings):
        return "CACHE_USED"
    return "LIVE"
