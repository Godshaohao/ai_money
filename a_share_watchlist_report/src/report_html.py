from pathlib import Path
from datetime import datetime

import pandas as pd
from jinja2 import Environment, FileSystemLoader, select_autoescape


def _records(frame: pd.DataFrame | None) -> list[dict]:
    if frame is None or frame.empty:
        return []
    cleaned = frame.copy()
    return cleaned.where(pd.notna(cleaned), "").to_dict("records")


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


def render_report(
    output_path: str | Path,
    market_regime: str,
    market_evidence: pd.DataFrame,
    watchlist: pd.DataFrame | None,
    excluded: pd.DataFrame,
    holding_risk: pd.DataFrame,
    data_quality_status: dict,
) -> None:
    """Render output/report.html using templates/report.html.j2."""
    template_dir = Path(__file__).resolve().parents[1] / "templates"
    env = Environment(
        loader=FileSystemLoader(template_dir),
        autoescape=select_autoescape(["html", "xml"]),
    )
    template = env.get_template("report.html.j2")
    html = template.render(
        generated_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        market_regime=market_regime,
        risk_exposure_review=_risk_exposure_review(market_regime, holding_risk),
        watchlist_count=0 if watchlist is None else len(watchlist),
        excluded_count=len(excluded),
        holding_risk_count=0 if holding_risk.empty else int((holding_risk["risk_action"] != "WATCH").sum()),
        largest_risk_warning=_largest_risk_warning(holding_risk, data_quality_status),
        market_evidence=_records(market_evidence),
        watchlist=_records(watchlist),
        excluded=_records(excluded),
        holding_risk=_records(holding_risk),
        data_quality_status=data_quality_status,
    )
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
