from pathlib import Path

import numpy as np
import pandas as pd


EVIDENCE_COLUMNS = ["index_name", "close", "ma200", "above_ma200", "return_20d", "status"]


def calculate_market_regime(index_prices: pd.DataFrame, config: dict) -> tuple[str, pd.DataFrame]:
    """Return regime and evidence table."""
    required = {"date", "index_name", "index_code", "close"}
    missing = sorted(required.difference(index_prices.columns))
    if missing:
        raise ValueError(f"index_prices missing required columns: {', '.join(missing)}")

    trend_days = int(config["trend_ma_days"])
    short_days = int(config["short_trend_days"])
    evidence_rows: list[dict] = []

    normalized = index_prices.copy()
    normalized["date"] = pd.to_datetime(normalized["date"])
    normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")

    for index_name, group in normalized.groupby("index_name"):
        group = group.sort_values("date").dropna(subset=["close"])
        if len(group) < max(trend_days, short_days) + 1:
            status = "INSUFFICIENT_DATA"
            close = float(group["close"].iloc[-1]) if not group.empty else np.nan
            ma200 = np.nan
            return_20d = np.nan
            above_ma200 = False
        else:
            close = float(group["close"].iloc[-1])
            ma200 = float(group["close"].tail(trend_days).mean())
            base = float(group["close"].iloc[-short_days - 1])
            return_20d = close / base - 1 if base > 0 else np.nan
            above_ma200 = bool(close > ma200)
            if above_ma200 and return_20d > 0:
                status = "POSITIVE"
            elif (not above_ma200) and return_20d < 0:
                status = "NEGATIVE"
            else:
                status = "MIXED"

        evidence_rows.append(
            {
                "index_name": index_name,
                "close": close,
                "ma200": ma200,
                "above_ma200": above_ma200,
                "return_20d": return_20d,
                "status": status,
            }
        )

    evidence = pd.DataFrame(evidence_rows, columns=EVIDENCE_COLUMNS)
    if evidence.empty:
        raise ValueError("no index evidence available")

    positive_count = int((evidence["status"] == "POSITIVE").sum())
    negative_count = int((evidence["status"] == "NEGATIVE").sum())
    threshold = int(np.ceil(len(evidence) * 2 / 3))
    if positive_count >= threshold:
        regime = "RISK_ON"
    elif negative_count >= threshold:
        regime = "RISK_OFF"
    else:
        regime = "NEUTRAL"

    return regime, evidence
