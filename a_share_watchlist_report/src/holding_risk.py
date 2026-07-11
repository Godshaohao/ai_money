from pathlib import Path

import numpy as np
import pandas as pd

from src.schemas import ALLOWED_RISK_ACTIONS


HOLDING_RISK_COLUMNS = [
    "symbol",
    "name",
    "shares",
    "cost_basis",
    "latest_close",
    "drawdown_from_cost",
    "above_ma200",
    "max_drawdown_60d",
    "avg_amount_20d",
    "risk_action",
    "reason",
]


def _stock_metrics(stock: pd.DataFrame, config: dict) -> dict:
    stock = stock.sort_values("date").dropna(subset=["close"])
    if stock.empty:
        return {
            "latest_close": np.nan,
            "above_ma200": False,
            "max_drawdown_60d": np.nan,
            "avg_amount_20d": np.nan,
        }

    latest_close = float(stock["close"].iloc[-1])
    trend_days = int(config["trend_ma_days"])
    ma200 = float(stock["close"].tail(trend_days).mean()) if len(stock) >= trend_days else np.nan
    peak_60d = float(stock["close"].tail(int(config["max_drawdown_days"])).max())
    return {
        "latest_close": latest_close,
        "above_ma200": bool(latest_close > ma200) if not np.isnan(ma200) else False,
        "max_drawdown_60d": latest_close / peak_60d - 1 if peak_60d > 0 else np.nan,
        "avg_amount_20d": float(stock["amount"].tail(20).mean()) if "amount" in stock.columns else np.nan,
    }


def build_holding_risk(
    holdings: pd.DataFrame,
    prices: pd.DataFrame,
    universe: pd.DataFrame,
    excluded: pd.DataFrame,
    config: dict,
) -> pd.DataFrame:
    """Return holding risk review table."""
    if holdings.empty:
        return pd.DataFrame(columns=HOLDING_RISK_COLUMNS)

    normalized = prices.copy()
    if not normalized.empty:
        normalized["date"] = pd.to_datetime(normalized["date"])
        normalized["symbol"] = normalized["symbol"].astype(str).str.zfill(6)
        normalized["close"] = pd.to_numeric(normalized["close"], errors="coerce")
        normalized["amount"] = pd.to_numeric(normalized["amount"], errors="coerce")

    universe_by_symbol = {
        str(row["symbol"]).zfill(6): row for row in universe.to_dict("records")
    }
    excluded_by_symbol = {
        str(row["symbol"]).zfill(6): row.get("exclude_reason", "data quality issue")
        for row in excluded.to_dict("records")
    } if not excluded.empty else {}

    rows: list[dict] = []
    for holding in holdings.to_dict("records"):
        symbol = str(holding["symbol"]).zfill(6)
        name = universe_by_symbol.get(symbol, {}).get("name", "")
        shares = float(holding["shares"])
        cost_basis = float(holding["cost_basis"])
        stock = normalized.loc[normalized["symbol"] == symbol] if not normalized.empty else pd.DataFrame()
        metrics = _stock_metrics(stock, config)
        latest_close = metrics["latest_close"]
        drawdown_from_cost = latest_close / cost_basis - 1 if cost_basis > 0 and not np.isnan(latest_close) else np.nan

        if symbol not in universe_by_symbol:
            action = "DATA_ISSUE"
            reason = "持仓不在 universe.csv 中，需要人工核对基础信息。"
        elif symbol in excluded_by_symbol:
            action = "DATA_ISSUE"
            reason = f"持仓数据质量异常：{excluded_by_symbol[symbol]}。"
        elif np.isnan(latest_close):
            action = "DATA_ISSUE"
            reason = "持仓缺少当前价格数据，需要人工复核。"
        elif not metrics["above_ma200"]:
            action = "REDUCE_REVIEW"
            reason = "价格低于 MA200，进入风险敞口复核。"
        elif metrics["max_drawdown_60d"] <= -0.15:
            action = "HOLD_REVIEW"
            reason = "价格仍在 MA200 上方，但 60 日回撤较大，需要复核。"
        else:
            action = "WATCH"
            reason = "未触发明显风险规则，继续观察。"

        if action not in ALLOWED_RISK_ACTIONS:
            raise ValueError(f"invalid risk action: {action}")

        rows.append(
            {
                "symbol": symbol,
                "name": name,
                "shares": shares,
                "cost_basis": cost_basis,
                "latest_close": latest_close,
                "drawdown_from_cost": drawdown_from_cost,
                "above_ma200": metrics["above_ma200"],
                "max_drawdown_60d": metrics["max_drawdown_60d"],
                "avg_amount_20d": metrics["avg_amount_20d"],
                "risk_action": action,
                "reason": reason,
            }
        )

    return pd.DataFrame(rows, columns=HOLDING_RISK_COLUMNS)
