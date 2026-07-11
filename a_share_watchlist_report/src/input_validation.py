from pathlib import Path

import pandas as pd

from src.schemas import HOLDING_COLUMNS, UNIVERSE_COLUMNS


def _missing_columns(frame: pd.DataFrame, required: list[str]) -> list[str]:
    return [column for column in required if column not in frame.columns]


def load_universe(path: str | Path, max_size: int) -> pd.DataFrame:
    """Load universe.csv and validate symbol/name/industry columns."""
    frame = pd.read_csv(path, dtype={"symbol": "string", "name": "string", "industry": "string"})
    missing = _missing_columns(frame, UNIVERSE_COLUMNS)
    if missing:
        raise ValueError(f"universe.csv missing required columns: {', '.join(missing)}")

    frame = frame[UNIVERSE_COLUMNS].copy()
    frame["symbol"] = frame["symbol"].astype("string").str.strip()
    frame["name"] = frame["name"].astype("string").str.strip()
    frame["industry"] = frame["industry"].astype("string").str.strip()

    if len(frame) > max_size:
        raise ValueError(f"universe.csv row count exceeds max_universe_size={max_size}")
    if frame["symbol"].isna().any() or (frame["symbol"] == "").any():
        raise ValueError("universe.csv symbol must be non-empty")
    if frame["symbol"].duplicated().any():
        duplicated = sorted(frame.loc[frame["symbol"].duplicated(), "symbol"].astype(str).unique())
        raise ValueError(f"universe.csv duplicate symbols: {', '.join(duplicated)}")

    return frame


def load_holdings(path: str | Path) -> pd.DataFrame:
    """Load holdings.csv. Empty holdings are allowed if header exists."""
    frame = pd.read_csv(path, dtype={"symbol": "string"})
    missing = _missing_columns(frame, HOLDING_COLUMNS)
    if missing:
        raise ValueError(f"holdings.csv missing required columns: {', '.join(missing)}")

    frame = frame[HOLDING_COLUMNS].copy()
    frame["symbol"] = frame["symbol"].astype("string").str.strip()
    frame["shares"] = pd.to_numeric(frame["shares"], errors="raise")
    frame["cost_basis"] = pd.to_numeric(frame["cost_basis"], errors="raise")

    if frame["shares"].lt(0).any():
        raise ValueError("holdings.csv shares must be >= 0")
    if frame["cost_basis"].lt(0).any():
        raise ValueError("holdings.csv cost_basis must be >= 0")

    return frame
