import numpy as np
import pandas as pd


PORTFOLIO_REVIEW_COLUMNS = [
    "symbol",
    "name",
    "industry",
    "shares",
    "cost_basis",
    "latest_close",
    "position_value",
    "cost_value",
    "unrealized_pnl",
    "unrealized_return",
    "portfolio_weight",
    "max_drawdown_60d",
    "avg_amount_20d",
    "liquidity_days",
    "risk_action",
    "risk_flags",
    "review_note",
]


def empty_portfolio_review_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=PORTFOLIO_REVIEW_COLUMNS)


def build_portfolio_review(holding_risk: pd.DataFrame, universe: pd.DataFrame) -> pd.DataFrame:
    if holding_risk.empty:
        return empty_portfolio_review_frame()

    frame = holding_risk.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    for column in ["shares", "cost_basis", "latest_close", "max_drawdown_60d", "avg_amount_20d"]:
        frame[column] = pd.to_numeric(frame[column], errors="coerce") if column in frame.columns else np.nan

    frame["position_value"] = frame["shares"] * frame["latest_close"]
    frame["cost_value"] = frame["shares"] * frame["cost_basis"]
    frame["unrealized_pnl"] = frame["position_value"] - frame["cost_value"]
    frame["unrealized_return"] = np.where(
        frame["cost_value"] > 0,
        frame["unrealized_pnl"] / frame["cost_value"],
        np.nan,
    )
    total_value = float(frame["position_value"].dropna().sum())
    frame["portfolio_weight"] = frame["position_value"] / total_value if total_value > 0 else np.nan
    frame["liquidity_days"] = np.where(
        frame["avg_amount_20d"] > 0,
        frame["position_value"] / frame["avg_amount_20d"],
        np.nan,
    )

    industries = _industry_map(universe)
    rows: list[dict] = []
    for row in frame.to_dict("records"):
        flags = _risk_flags(row)
        rows.append(
            {
                "symbol": row["symbol"],
                "name": row.get("name", ""),
                "industry": industries.get(row["symbol"], ""),
                "shares": row.get("shares", np.nan),
                "cost_basis": row.get("cost_basis", np.nan),
                "latest_close": row.get("latest_close", np.nan),
                "position_value": row.get("position_value", np.nan),
                "cost_value": row.get("cost_value", np.nan),
                "unrealized_pnl": row.get("unrealized_pnl", np.nan),
                "unrealized_return": row.get("unrealized_return", np.nan),
                "portfolio_weight": row.get("portfolio_weight", np.nan),
                "max_drawdown_60d": row.get("max_drawdown_60d", np.nan),
                "avg_amount_20d": row.get("avg_amount_20d", np.nan),
                "liquidity_days": row.get("liquidity_days", np.nan),
                "risk_action": row.get("risk_action", ""),
                "risk_flags": ",".join(flags),
                "review_note": _review_note(flags, row),
            }
        )

    return pd.DataFrame(rows, columns=PORTFOLIO_REVIEW_COLUMNS).sort_values(
        ["portfolio_weight", "risk_action"], ascending=[False, True]
    ).reset_index(drop=True)


def _industry_map(universe: pd.DataFrame) -> dict[str, str]:
    if universe.empty or "symbol" not in universe.columns:
        return {}
    return {
        str(row["symbol"]).zfill(6): str(row.get("industry", ""))
        for row in universe.to_dict("records")
    }


def _risk_flags(row: dict) -> list[str]:
    flags: list[str] = []
    action = str(row.get("risk_action", ""))
    latest_close = _number(row.get("latest_close"))
    unrealized_return = _number(row.get("unrealized_return"))
    max_drawdown = _number(row.get("max_drawdown_60d"))
    avg_amount = _number(row.get("avg_amount_20d"))
    weight = _number(row.get("portfolio_weight"))

    if action == "DATA_ISSUE" or np.isnan(latest_close):
        flags.append("DATA_ISSUE")
    if action and action != "WATCH":
        flags.append("ACTION_REVIEW")
    if not np.isnan(unrealized_return) and unrealized_return < 0:
        flags.append("UNDER_COST")
    if not np.isnan(max_drawdown) and max_drawdown <= -0.15:
        flags.append("DRAWDOWN_60D_15")
    if not np.isnan(avg_amount) and avg_amount < 50_000_000:
        flags.append("LOW_LIQUIDITY")
    if not np.isnan(weight) and weight >= 0.40:
        flags.append("CONCENTRATED_WEIGHT")
    return flags


def _review_note(flags: list[str], row: dict) -> str:
    if "DATA_ISSUE" in flags:
        return "组合复核：持仓数据不完整，先核对基础数据。"
    if flags:
        return "组合复核：触发 " + ",".join(flags) + "，需要人工复核风险敞口。"
    return "组合复核：未触发组合层面风险标签，继续观察。"


def _number(value: object) -> float:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return np.nan
    return float(number)
