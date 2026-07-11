from pathlib import Path
from typing import Any

import yaml


REQUIRED_KEYS = {
    "max_universe_size",
    "top_n_watchlist",
    "market_indices",
    "start_date",
    "trend_ma_days",
    "short_trend_days",
    "momentum_12m_days",
    "momentum_6m_days",
    "max_drawdown_days",
    "min_listing_days",
    "min_avg_amount_20d",
    "max_missing_days",
}


def load_config(path: str | Path) -> dict[str, Any]:
    """Load config.yaml and validate required keys exist."""
    config_path = Path(path)
    with config_path.open("r", encoding="utf-8") as handle:
        config = yaml.safe_load(handle) or {}

    if not isinstance(config, dict):
        raise ValueError("config.yaml must contain a mapping")

    missing = sorted(REQUIRED_KEYS.difference(config))
    if missing:
        raise ValueError(f"config.yaml missing required keys: {', '.join(missing)}")

    if not isinstance(config["market_indices"], dict) or not config["market_indices"]:
        raise ValueError("market_indices must be a non-empty mapping")

    return config
