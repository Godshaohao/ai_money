from pathlib import Path

import pandas as pd

from src.schemas import DAILY_BAR_COLUMNS


def _validate_daily_bar_schema(frame: pd.DataFrame) -> None:
    missing = [column for column in DAILY_BAR_COLUMNS if column not in frame.columns]
    if missing:
        raise ValueError(f"daily bar cache missing columns: {', '.join(missing)}")


def write_daily_bar_cache(frame: pd.DataFrame, output_path: str | Path) -> pd.DataFrame:
    _validate_daily_bar_schema(frame)
    normalized = frame[DAILY_BAR_COLUMNS].copy()
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    normalized.to_parquet(output, index=False)
    return normalized


def read_daily_bar_cache(input_path: str | Path) -> pd.DataFrame:
    frame = pd.read_parquet(input_path)
    _validate_daily_bar_schema(frame)
    return frame[DAILY_BAR_COLUMNS].copy()

