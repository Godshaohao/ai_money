from pathlib import Path
from typing import Any

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from src.sector_echelon import SECTOR_ECHELON_COLUMNS, build_sector_echelons
from src.stock_analysis import build_stock_analysis


class AnalysisCache:
    def __init__(self) -> None:
        self.sector_key: tuple[Any, ...] | None = None
        self.sector_value: dict[str, Any] | None = None
        self.stock_values: dict[tuple[Any, ...], dict[str, Any]] = {}


def build_sector_workbench(output_dir: Path, cache: AnalysisCache | None = None) -> dict[str, Any]:
    cache_key = ("sectors", _file_stamp(Path(output_dir) / "limit_up_pool.csv"))
    if cache is not None and cache.sector_key == cache_key and cache.sector_value is not None:
        return cache.sector_value

    limit_up_pool = _read_limit_up_pool(Path(output_dir))
    echelons = build_sector_echelons(limit_up_pool)
    if echelons.empty:
        result = {
            "latest_trade_date": "",
            "summary": {
                "sector_count": 0,
                "limit_up_count": 0,
                "broken_count": 0,
                "high_board_count": 0,
            },
            "cards": [],
            "errors": [] if (Path(output_dir) / "limit_up_pool.csv").exists() else ["Missing limit_up_pool.csv"],
        }
        if cache is not None:
            cache.sector_key = cache_key
            cache.sector_value = result
        return result

    latest_trade_date = str(echelons.iloc[0]["trade_date"])
    latest = echelons.loc[echelons["trade_date"].astype(str) == latest_trade_date].copy()
    cards = [_sector_card(row) for row in latest.to_dict(orient="records")]
    result = {
        "latest_trade_date": latest_trade_date,
        "summary": {
            "sector_count": int(len(latest)),
            "limit_up_count": int(latest["limit_up_count"].sum()),
            "broken_count": int(latest["broken_count"].sum()),
            "high_board_count": int(latest["high_board_count"].sum()),
        },
        "cards": cards,
        "errors": [],
    }
    if cache is not None:
        cache.sector_key = cache_key
        cache.sector_value = result
    return result


def build_stock_review(output_dir: Path, db_path: Path, symbol: str, cache: AnalysisCache | None = None) -> dict[str, Any]:
    normalized_symbol = str(symbol).zfill(6)
    output_path = Path(output_dir)
    database_path = Path(db_path)
    cache_key = (
        "stock",
        normalized_symbol,
        _file_stamp(output_path / "limit_up_pool.csv"),
        _file_stamp(output_path / "limit_up_strategy_review.csv"),
        _file_stamp(output_path / "excluded_stocks.csv"),
        _file_stamp(output_path / "dragon_tiger.csv"),
        _file_stamp(database_path),
    )
    if cache is not None and cache_key in cache.stock_values:
        return cache.stock_values[cache_key]

    result = {"analysis": build_stock_analysis(normalized_symbol, output_dir=output_path, db_path=database_path)}
    if cache is not None:
        cache.stock_values[cache_key] = result
    return result


def _read_limit_up_pool(output_dir: Path) -> pd.DataFrame:
    path = output_dir / "limit_up_pool.csv"
    if not path.exists():
        return pd.DataFrame(columns=SECTOR_ECHELON_COLUMNS)
    try:
        return pd.read_csv(path, dtype={"symbol": "string"})
    except (EmptyDataError, ParserError, UnicodeDecodeError, OSError):
        return pd.DataFrame(columns=SECTOR_ECHELON_COLUMNS)


def _sector_card(row: dict[str, Any]) -> dict[str, Any]:
    leader_symbols = _split_csv(row.get("leader_symbols"))
    leader_names = _split_csv(row.get("leader_names"))
    leaders = [
        {"symbol": symbol, "name": leader_names[index] if index < len(leader_names) else symbol}
        for index, symbol in enumerate(leader_symbols)
    ]
    broken_count = int(row.get("broken_count") or 0)
    high_board_count = int(row.get("high_board_count") or 0)
    risk_flags = []
    if broken_count > 0:
        risk_flags.append(f"炸板 {broken_count}")
    if high_board_count == 0:
        risk_flags.append("无高标")

    return {
        "trade_date": str(row.get("trade_date") or ""),
        "industry": str(row.get("industry") or "未分类"),
        "limit_up_count": int(row.get("limit_up_count") or 0),
        "first_board_count": int(row.get("first_board_count") or 0),
        "second_board_count": int(row.get("second_board_count") or 0),
        "high_board_count": high_board_count,
        "max_streak_count": int(row.get("max_streak_count") or 0),
        "broken_count": broken_count,
        "total_amount": float(row.get("total_amount") or 0),
        "leader_symbols": leader_symbols,
        "leader_names": leader_names,
        "leaders": leaders,
        "echelon_summary": str(row.get("echelon_summary") or ""),
        "risk_flags": risk_flags,
    }


def _split_csv(value: Any) -> list[str]:
    if value is None:
        return []
    text = str(value).strip()
    if not text or text.lower() == "nan":
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _file_stamp(path: Path) -> tuple[bool, int, int]:
    try:
        stat = path.stat()
    except OSError:
        return (False, 0, 0)
    return (True, int(stat.st_mtime_ns), int(stat.st_size))
