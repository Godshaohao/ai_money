from pathlib import Path
import json

import pandas as pd

from src.data.coverage_report import build_data_coverage_report, write_data_coverage_report
from src.schemas import DATA_COVERAGE_KEYS


def _universe() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "symbol": ["600519", "300750", "000001"],
            "name": ["贵州茅台", "宁德时代", "平安银行"],
            "industry": ["食品饮料", "电力设备", "银行"],
        }
    )


def test_build_data_coverage_report_tracks_missing_and_stale_symbols() -> None:
    daily_bars = pd.DataFrame(
        {
            "symbol": ["600519", "600519", "300750", "999999"],
            "date": ["2025-01-01", "2025-01-03", "2025-01-02", "2025-01-04"],
        }
    )

    report = build_data_coverage_report(_universe(), daily_bars, failed_symbols=["000001"])

    assert list(report.keys()) == DATA_COVERAGE_KEYS
    assert report["total_symbols"] == 3
    assert report["cached_symbols"] == 2
    assert report["latest_date"] == "2025-01-03"
    assert report["missing_symbols"] == ["000001"]
    assert report["stale_symbols"] == ["300750"]
    assert report["failed_symbols"] == ["000001"]


def test_build_data_coverage_report_ignores_malformed_dates_and_extra_symbols() -> None:
    daily_bars = pd.DataFrame(
        {
            "symbol": ["600519", "300750", "999999"],
            "date": ["not-a-date", "2025-01-02", "2025-01-03"],
        }
    )

    report = build_data_coverage_report(_universe(), daily_bars)

    assert report["cached_symbols"] == 1
    assert report["latest_date"] == "2025-01-02"
    assert report["missing_symbols"] == ["600519", "000001"]
    assert report["stale_symbols"] == []


def test_write_data_coverage_report_preserves_key_order(tmp_path: Path) -> None:
    report = build_data_coverage_report(_universe(), pd.DataFrame(columns=["symbol", "date"]))
    path = tmp_path / "data_coverage_report.json"

    write_data_coverage_report(report, path)

    loaded = json.loads(path.read_text(encoding="utf-8"))
    assert list(loaded.keys()) == DATA_COVERAGE_KEYS

