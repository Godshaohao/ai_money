from pathlib import Path
from datetime import datetime

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


PERCENT_COLUMNS = {"momentum_12m", "momentum_6m", "max_drawdown_60d", "return_20d"}
AMOUNT_COLUMNS = {
    "amount",
    "avg_amount_20d",
    "net_buy_amount",
    "buy_amount",
    "sell_amount",
    "deal_amount",
}


def _format_amount(value: object) -> str:
    if value == "" or pd.isna(value):
        return ""
    number = float(value)
    if abs(number) >= 100_000_000:
        return f"{number / 100_000_000:.2f} 亿"
    if abs(number) >= 10_000:
        return f"{number / 10_000:.2f} 万"
    return f"{number:,.2f}"


def _format_cell(column: str, value: object) -> object:
    if value == "" or pd.isna(value):
        return ""
    if column in PERCENT_COLUMNS:
        return f"{float(value):.2%}"
    if column == "change_pct" or column == "turnover_rate":
        return f"{float(value):.2f}%"
    if column in AMOUNT_COLUMNS:
        return _format_amount(value)
    if column in {"close", "ma200", "latest_close", "cost_basis", "drawdown_from_cost"}:
        return f"{float(value):,.2f}"
    return value


def _records(frame: pd.DataFrame | None) -> list[dict]:
    if frame is None or frame.empty:
        return []
    cleaned = frame.copy()
    cleaned = cleaned.where(pd.notna(cleaned), "")
    records = cleaned.to_dict("records")
    return [{key: _format_cell(key, value) for key, value in row.items()} for row in records]


def _risk_exposure_review(market_regime: str, holding_risk: pd.DataFrame) -> str:
    risky_holdings = 0 if holding_risk.empty else int((holding_risk["risk_action"] != "WATCH").sum())
    if market_regime == "DATA_ISSUE" or market_regime == "RISK_OFF":
        return "NO"
    if risky_holdings > 0 or market_regime == "NEUTRAL":
        return "REVIEW"
    return "YES"


def _largest_risk_warning(holding_risk: pd.DataFrame, data_quality_status: dict) -> str:
    if data_quality_status.get("errors"):
        return str(data_quality_status["errors"][0])
    if not holding_risk.empty:
        risky = holding_risk.loc[holding_risk["risk_action"] != "WATCH"]
        if not risky.empty:
            row = risky.iloc[0]
            return f"{row['symbol']} {row['risk_action']}: {row['reason']}"
    return "N/A"


def _data_source_status(data_quality_status: dict) -> str:
    if data_quality_status.get("errors"):
        return "DATA_ISSUE"
    warnings = data_quality_status.get("warnings") or []
    if any("using existing local cache" in str(warning) for warning in warnings):
        return "CACHE_USED"
    return "LIVE"


def _status_badge_kind(status: str) -> str:
    if status in {"LIVE", "RISK_ON", "POSITIVE", "YES", "WATCH"}:
        return "good"
    if status in {"DATA_ISSUE", "NO", "RISK_OFF"}:
        return "bad"
    return "warn"


def _latest_value(frame: pd.DataFrame | None, column: str) -> str:
    if frame is None or frame.empty or column not in frame.columns:
        return "N/A"
    values = frame[column].dropna()
    if values.empty:
        return "N/A"
    return str(values.max())


def render_report(
    output_path: str | Path,
    market_regime: str,
    market_evidence: pd.DataFrame,
    watchlist: pd.DataFrame | None,
    excluded: pd.DataFrame,
    holding_risk: pd.DataFrame,
    data_quality_status: dict,
    dragon_tiger: pd.DataFrame | None = None,
) -> None:
    """Render output/report.html using templates/report.html.j2."""
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    data_source_status = _data_source_status(data_quality_status)
    risk_exposure_review = _risk_exposure_review(market_regime, holding_risk)
    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        market_regime=market_regime,
        market_regime_kind=_status_badge_kind(market_regime),
        risk_exposure_review=risk_exposure_review,
        risk_exposure_kind=_status_badge_kind(risk_exposure_review),
        data_source_status=data_source_status,
        data_source_kind=_status_badge_kind(data_source_status),
        watchlist_count=0 if watchlist is None else len(watchlist),
        excluded_count=len(excluded),
        holding_risk_count=0 if holding_risk.empty else int((holding_risk["risk_action"] != "WATCH").sum()),
        dragon_tiger_count=0 if dragon_tiger is None else len(dragon_tiger),
        latest_dragon_tiger_date=_latest_value(dragon_tiger, "trade_date"),
        largest_risk_warning=_largest_risk_warning(holding_risk, data_quality_status),
        market_evidence=_records(market_evidence),
        watchlist=_records(watchlist),
        excluded=_records(excluded),
        holding_risk=_records(holding_risk),
        data_quality_status=data_quality_status,
        dragon_tiger=_records(dragon_tiger),
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
