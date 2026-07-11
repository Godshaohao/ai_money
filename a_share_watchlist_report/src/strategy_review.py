from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass(frozen=True)
class StrategyRecords:
    candidates: list[dict[str, Any]]
    evidence: list[dict[str, Any]]
    metrics: dict[str, int]


def build_strategy_records(
    limit_up_review: pd.DataFrame,
    watchlist: pd.DataFrame,
    holding_risk: pd.DataFrame,
    modules: list[str],
) -> StrategyRecords:
    enabled = set(modules)
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []

    if "limit_up" in enabled:
        limit_candidates, limit_evidence = _from_limit_up(limit_up_review)
        candidates.extend(limit_candidates)
        evidence.extend(limit_evidence)
    if "watchlist" in enabled:
        watch_candidates, watch_evidence = _from_watchlist(watchlist)
        candidates.extend(watch_candidates)
        evidence.extend(watch_evidence)
    if "holding_risk" in enabled:
        risk_candidates, risk_evidence = _from_holding_risk(holding_risk)
        candidates.extend(risk_candidates)
        evidence.extend(risk_evidence)

    return StrategyRecords(
        candidates=candidates,
        evidence=evidence,
        metrics={
            "candidate_count": len(candidates),
            "limit_up_count": _count_module(candidates, "limit_up"),
            "watchlist_count": _count_module(candidates, "watchlist"),
            "holding_risk_count": _count_module(candidates, "holding_risk"),
            "risk_count": sum(1 for item in candidates if item["label"] in {"RISK_REVIEW", "DATA_REVIEW", "DATA_GAP"}),
        },
    )


def _from_limit_up(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for row in _records(frame):
        symbol = _symbol(row.get("symbol"))
        score = _float(row.get("review_score"))
        label = str(row.get("review_label") or "WATCH_REVIEW")
        risk_flags = str(row.get("red_flags") or "")
        reason = str(row.get("reason") or "涨停复核")
        candidates.append(
            _candidate(
                module="limit_up",
                symbol=symbol,
                name=str(row.get("name") or ""),
                score=score,
                label=label,
                risk_flags=risk_flags,
                reason=reason,
                source_table="limit_up_strategy_review",
                source_row=row,
            )
        )
        evidence.append(
            _evidence(
                symbol=symbol,
                module="limit_up",
                evidence_type="limit_up",
                title="涨停复核证据",
                detail=f"复核分 {score:.0f}，标签 {label}",
                payload=row,
            )
        )
    return candidates, evidence


def _from_watchlist(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for row in _records(frame):
        symbol = _symbol(row.get("symbol"))
        rank = max(int(_float(row.get("rank")) or 1), 1)
        score = max(0.0, 100.0 - (rank - 1) * 5.0)
        label = "CORE_REVIEW" if rank == 1 else "WATCH_REVIEW"
        reason = str(row.get("reason") or "观察池复核")
        candidates.append(
            _candidate(
                module="watchlist",
                symbol=symbol,
                name=str(row.get("name") or ""),
                score=score,
                label=label,
                risk_flags="",
                reason=reason,
                source_table="watchlist",
                source_row=row,
            )
        )
        evidence.append(
            _evidence(
                symbol=symbol,
                module="watchlist",
                evidence_type="watchlist",
                title="观察池证据",
                detail=_watchlist_detail(row, rank),
                payload=row,
            )
        )
    return candidates, evidence


def _from_holding_risk(frame: pd.DataFrame) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    candidates: list[dict[str, Any]] = []
    evidence: list[dict[str, Any]] = []
    for row in _records(frame):
        symbol = _symbol(row.get("symbol"))
        risk_flags = _holding_risk_flags(row)
        score = 40.0 if risk_flags else 70.0
        label = "RISK_REVIEW" if risk_flags else "WATCH_REVIEW"
        reason = str(row.get("reason") or "持仓风险复核")
        candidates.append(
            _candidate(
                module="holding_risk",
                symbol=symbol,
                name=str(row.get("name") or ""),
                score=score,
                label=label,
                risk_flags=risk_flags,
                reason=reason,
                source_table="holding_risk",
                source_row=row,
            )
        )
        evidence.append(
            _evidence(
                symbol=symbol,
                module="holding_risk",
                evidence_type="holding_risk",
                title="持仓风险证据",
                detail=f"{reason}；风险标签 {risk_flags or '未触发'}",
                payload=row,
            )
        )
    return candidates, evidence


def _candidate(
    module: str,
    symbol: str,
    name: str,
    score: float,
    label: str,
    risk_flags: str,
    reason: str,
    source_table: str,
    source_row: dict[str, Any],
) -> dict[str, Any]:
    return {
        "module": module,
        "symbol": symbol,
        "name": name,
        "score": float(score),
        "label": label,
        "risk_flags": risk_flags,
        "reason": reason,
        "source_table": source_table,
        "source_row": source_row,
    }


def _evidence(
    symbol: str,
    module: str,
    evidence_type: str,
    title: str,
    detail: str,
    payload: dict[str, Any],
) -> dict[str, Any]:
    return {
        "symbol": symbol,
        "module": module,
        "evidence_type": evidence_type,
        "title": title,
        "detail": detail,
        "payload": payload,
    }


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    safe = frame.where(pd.notna(frame), None)
    return [_json_safe(row) for row in safe.to_dict("records")]


def _json_safe(row: dict[str, Any]) -> dict[str, Any]:
    safe: dict[str, Any] = {}
    for key, value in row.items():
        if pd.isna(value):
            safe[key] = None
        elif hasattr(value, "item"):
            safe[key] = value.item()
        else:
            safe[key] = value
    return safe


def _symbol(value: Any) -> str:
    return str(value or "").zfill(6)


def _float(value: Any) -> float:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return 0.0
    return float(number)


def _count_module(candidates: list[dict[str, Any]], module: str) -> int:
    return sum(1 for item in candidates if item["module"] == module)


def _watchlist_detail(row: dict[str, Any], rank: int) -> str:
    return (
        f"观察池排名 {rank}；12M 动量 {row.get('momentum_12m', 'N/A')}；"
        f"6M 动量 {row.get('momentum_6m', 'N/A')}；60 日回撤 {row.get('max_drawdown_60d', 'N/A')}"
    )


def _holding_risk_flags(row: dict[str, Any]) -> str:
    flags: list[str] = []
    if row.get("above_ma200") is False:
        flags.append("BELOW_MA200")
    return ",".join(flags)
