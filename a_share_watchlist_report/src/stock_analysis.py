from pathlib import Path
from typing import Any

import pandas as pd

from backend.repositories.sqlite_repo import StrategyRepository
from src.cli.json_contract import FORBIDDEN_OUTPUTS
from src.sector_echelon import build_sector_echelons


def build_stock_analysis(symbol: str, output_dir: Path, db_path: Path) -> dict[str, Any]:
    normalized_symbol = str(symbol).zfill(6)
    limit_up_pool = _read_csv(Path(output_dir) / "limit_up_pool.csv")
    limit_up_review = _read_csv(Path(output_dir) / "limit_up_strategy_review.csv")
    excluded = _read_csv(Path(output_dir) / "excluded_stocks.csv")
    dragon_tiger = _read_csv(Path(output_dir) / "dragon_tiger.csv")

    stock_limit_events = _filter_symbol(limit_up_pool, normalized_symbol)
    stock_reviews = _filter_symbol(limit_up_review, normalized_symbol)
    stock_excluded = _filter_symbol(excluded, normalized_symbol)
    stock_dragon_tiger = _filter_symbol(dragon_tiger, normalized_symbol)
    identity = _identity(normalized_symbol, stock_limit_events, stock_reviews, stock_excluded)
    sector_echelon = _sector_context(limit_up_pool, stock_limit_events)
    strategy_detail = StrategyRepository(Path(db_path)).inspect_symbol(normalized_symbol) if Path(db_path).exists() else {
        "symbol": normalized_symbol,
        "exists": False,
        "candidates": [],
        "evidence": [],
    }
    data_quality = _data_quality(stock_excluded, strategy_detail)
    event_timeline = _event_timeline(stock_limit_events)
    sector_position = _sector_position(sector_echelon, identity)

    return {
        "identity": identity,
        "data_quality": data_quality,
        "data_availability": _data_availability(
            stock_limit_events,
            stock_reviews,
            stock_excluded,
            stock_dragon_tiger,
            strategy_detail,
            sector_position,
        ),
        "review_brief": _review_brief(identity, stock_limit_events, stock_reviews, data_quality, sector_echelon),
        "event_timeline": event_timeline,
        "sector_position": sector_position,
        "limit_up_events": _records(_sort_by_trade_date(stock_limit_events)),
        "limit_up_reviews": _records(_sort_by_trade_date(stock_reviews)),
        "sector_echelon": sector_echelon,
        "strategy": strategy_detail,
        "dragon_tiger": _records(_sort_by_trade_date(stock_dragon_tiger)),
        "review_checklist": _review_checklist(stock_limit_events, stock_excluded, strategy_detail, sector_echelon),
        "safety": {
            "analysis_only": True,
            "forbidden_outputs": FORBIDDEN_OUTPUTS,
        },
    }


def _data_availability(
    limit_up_events: pd.DataFrame,
    stock_reviews: pd.DataFrame,
    excluded: pd.DataFrame,
    dragon_tiger: pd.DataFrame,
    strategy_detail: dict[str, Any],
    sector_position: dict[str, Any],
) -> dict[str, Any]:
    price_history_available = not _has_exclude_reason(excluded, "no price data")
    missing_notes: list[str] = []
    if not price_history_available:
        missing_notes.append("价格历史缺失，无法计算 MA、动量、回撤。")
    if limit_up_events.empty:
        missing_notes.append("涨停池没有该股事件，无法复核板位、炸板和封单。")

    return {
        "price_history_available": price_history_available,
        "limit_up_event_count": int(len(limit_up_events)),
        "sector_event_count": _int_value(sector_position.get("limit_up_count", 0)),
        "strategy_candidate_count": int(len(strategy_detail.get("candidates", []))),
        "review_record_count": int(len(stock_reviews)),
        "dragon_tiger_count": int(len(dragon_tiger)),
        "missing_notes": missing_notes,
    }


def _event_timeline(limit_up_events: pd.DataFrame) -> list[dict[str, Any]]:
    if limit_up_events.empty:
        return []
    frame = _sort_by_trade_date(limit_up_events).copy()
    records = _records(frame)
    timeline: list[dict[str, Any]] = []
    for index, row in enumerate(records):
        previous = records[index + 1] if index + 1 < len(records) else None
        change_from_previous = _close_change_pct(row, previous)
        break_count = _int_value(row.get("break_count", 0))
        first_time = _format_limit_time(row.get("first_limit_time"))
        last_time = _format_limit_time(row.get("last_limit_time"))
        timeline.append(
            {
                "trade_date": _text_value(row.get("trade_date")),
                "event_profile": _event_profile(break_count, first_time, last_time),
                "streak_count": _int_value(row.get("streak_count", 0)),
                "break_count": break_count,
                "first_limit_time": first_time,
                "last_limit_time": last_time,
                "close": _float_value(row.get("close")),
                "change_pct": _float_value(row.get("change_pct")),
                "change_pct_text": _pct_text(row.get("change_pct")),
                "turnover_rate": _float_value(row.get("turnover_rate")),
                "turnover_rate_text": _pct_text(row.get("turnover_rate")),
                "amount": _float_value(row.get("amount")),
                "amount_text": _amount_text(row.get("amount")),
                "seal_amount": _float_value(row.get("seal_amount")),
                "seal_amount_text": _amount_text(row.get("seal_amount")),
                "limit_up_stats": _text_value(row.get("limit_up_stats")),
                "close_change_from_previous_event_pct": change_from_previous,
                "close_change_from_previous_event_text": _pct_text(change_from_previous)
                if change_from_previous is not None
                else "无上一条记录",
            }
        )
    return timeline


def _sector_position(sector_echelon: list[dict[str, Any]], identity: dict[str, str]) -> dict[str, Any]:
    if not sector_echelon:
        return {
            "industry": identity.get("industry", ""),
            "position_summary": "暂无题材梯队记录。",
            "leader_names": [],
            "stock_is_leader": False,
            "broken_ratio_pct": 0.0,
            "limit_up_count": 0,
        }
    latest = sector_echelon[0]
    leader_symbols = _split_csv_text(latest.get("leader_symbols"))
    leader_names = _split_csv_text(latest.get("leader_names"))
    limit_up_count = _int_value(latest.get("limit_up_count", 0))
    broken_count = _int_value(latest.get("broken_count", 0))
    broken_ratio = round(broken_count / limit_up_count * 100, 1) if limit_up_count else 0.0
    industry = _text_value(latest.get("industry")) or identity.get("industry", "")
    return {
        "trade_date": _text_value(latest.get("trade_date")),
        "industry": industry,
        "position_summary": (
            f"{industry} 当日涨停 {limit_up_count} 只，炸板 {broken_count} 只，"
            f"最高 {_int_value(latest.get('max_streak_count', 0))} 连板。"
        ),
        "limit_up_count": limit_up_count,
        "first_board_count": _int_value(latest.get("first_board_count", 0)),
        "second_board_count": _int_value(latest.get("second_board_count", 0)),
        "high_board_count": _int_value(latest.get("high_board_count", 0)),
        "max_streak_count": _int_value(latest.get("max_streak_count", 0)),
        "broken_count": broken_count,
        "broken_ratio_pct": broken_ratio,
        "leader_symbols": leader_symbols,
        "leader_names": leader_names,
        "stock_is_leader": identity.get("symbol", "") in leader_symbols,
    }


def _review_brief(
    identity: dict[str, str],
    limit_up_events: pd.DataFrame,
    stock_reviews: pd.DataFrame,
    data_quality: dict[str, Any],
    sector_echelon: list[dict[str, Any]],
) -> dict[str, Any]:
    latest_event = _sort_by_trade_date(limit_up_events).iloc[0] if not limit_up_events.empty else {}
    latest_review = _sort_by_trade_date(stock_reviews).iloc[0] if not stock_reviews.empty else {}
    latest_sector = sector_echelon[0] if sector_echelon else {}
    latest_timeline = _event_timeline(limit_up_events)
    latest_event_detail = latest_timeline[0] if latest_timeline else {}
    sector_position = _sector_position(sector_echelon, identity)
    break_count = _int_value(latest_event.get("break_count", 0))
    streak_count = _int_value(latest_event.get("streak_count", 0))
    review_score = _int_value(latest_review.get("review_score", 0))
    review_state = _review_state(data_quality, break_count, review_score)
    name = identity.get("name") or identity.get("symbol") or "该股票"
    industry = identity.get("industry") or "未分类板块"
    event_text = f"{streak_count} 连板" if streak_count else "暂无连板记录"
    break_text = f"炸板 {break_count} 次" if break_count else "未记录炸板"
    event_detail_text = ""
    if latest_event_detail:
        event_detail_text = (
            f"，首封 {latest_event_detail.get('first_limit_time')}，末封 {latest_event_detail.get('last_limit_time')}，"
            f"封单 {latest_event_detail.get('seal_amount_text')}，成交额 {latest_event_detail.get('amount_text')}"
        )
    quality_text = "，但存在数据质量缺口" if not data_quality.get("ok", True) else ""
    headline = (
        f"{name} 属于 {industry}，最新涨停为 {event_text}、{break_text}{event_detail_text}"
        f"{quality_text}，应先做复核而非直接下结论。"
    )

    evidence_metrics = [
        {"label": "最新板位", "value": event_text, "note": _text_value(latest_event.get("trade_date"))},
        {"label": "炸板情况", "value": break_text, "note": "回封稳定性是主要复核点" if break_count else "封板过程相对干净"},
        {"label": "复核分", "value": str(review_score or "-"), "note": _text_value(latest_review.get("review_label"))},
    ]
    if latest_sector:
        evidence_metrics.append(
            {
                "label": "板块梯队",
                "value": _text_value(latest_sector.get("echelon_summary")),
                "note": _text_value(latest_sector.get("trade_date")),
            }
        )

    risk_notes: list[str] = []
    if break_count >= 3:
        risk_notes.append(f"最新涨停炸板 {break_count} 次，说明盘中分歧较大，需要复核回封时间和封单变化。")
    close_change_text = _text_value(latest_event_detail.get("close_change_from_previous_event_text"))
    if close_change_text and close_change_text != "无上一条记录":
        risk_notes.append(f"较上一条涨停收盘变化 {close_change_text}，需要复核连板断裂后的承接情况。")
    if not data_quality.get("ok", True):
        risk_notes.append(f"数据质量待复核：{'，'.join(data_quality.get('flags', []))}。")
    if sector_position.get("limit_up_count"):
        risk_notes.append(
            f"所属板块炸板占比 {sector_position['broken_ratio_pct']}%，"
            f"代表股包括 {'，'.join(sector_position.get('leader_names', [])[:3]) or '暂无'}。"
        )
    if latest_sector and _int_value(latest_sector.get("high_board_count", 0)) == 0:
        risk_notes.append("所属板块当前无高标，梯队高度不足，不能只看个股涨停。")
    if not risk_notes:
        risk_notes.append("当前风险标签较少，但仍需核对原始涨停事件和策略证据。")

    next_actions = [
        "先核对数据质量缺口，确认日线、涨停池和策略证据是否一致。",
        "复核最新涨停的炸板原因、回封时间、封单金额和成交额变化。",
        "对照所属题材梯队，确认该股是板块核心、跟风还是掉队。"
    ]

    return {
        "review_state": review_state,
        "headline": headline,
        "evidence_metrics": evidence_metrics,
        "risk_notes": risk_notes,
        "next_actions": next_actions,
    }


def _review_state(data_quality: dict[str, Any], break_count: int, review_score: int) -> str:
    if not data_quality.get("ok", True):
        return "风险优先复核"
    if break_count >= 3:
        return "分歧优先复核"
    if review_score >= 85:
        return "重点复核"
    return "常规复核"


def _sector_context(limit_up_pool: pd.DataFrame, stock_limit_events: pd.DataFrame) -> list[dict[str, Any]]:
    if limit_up_pool.empty or stock_limit_events.empty:
        return []
    echelons = build_sector_echelons(limit_up_pool)
    pairs = stock_limit_events[["trade_date", "industry"]].drop_duplicates()
    matched = echelons.merge(pairs, on=["trade_date", "industry"], how="inner")
    return _records(matched.sort_values("trade_date", ascending=False))


def _identity(symbol: str, *frames: pd.DataFrame) -> dict[str, str]:
    for frame in frames:
        if not frame.empty:
            row = frame.iloc[0]
            return {
                "symbol": symbol,
                "name": str(row.get("name", "")),
                "industry": str(row.get("industry", "")),
            }
    return {"symbol": symbol, "name": "", "industry": ""}


def _data_quality(excluded: pd.DataFrame, strategy_detail: dict[str, Any]) -> dict[str, Any]:
    flags = []
    if not excluded.empty and "exclude_reason" in excluded.columns:
        flags.extend(str(value) for value in excluded["exclude_reason"].dropna().unique())
    for candidate in strategy_detail.get("candidates", []):
        risk_flags = str(candidate.get("risk_flags", ""))
        flags.extend(
            flag
            for flag in risk_flags.split(",")
            if flag and ("GAP" in flag or "DATA" in flag)
        )
    return {
        "ok": len(flags) == 0,
        "flags": list(dict.fromkeys(flags)),
    }


def _has_exclude_reason(excluded: pd.DataFrame, reason: str) -> bool:
    if excluded.empty or "exclude_reason" not in excluded.columns:
        return False
    return excluded["exclude_reason"].fillna("").astype(str).str.contains(reason, case=False, regex=False).any()


def _review_checklist(
    limit_up_events: pd.DataFrame,
    excluded: pd.DataFrame,
    strategy_detail: dict[str, Any],
    sector_echelon: list[dict[str, Any]],
) -> list[str]:
    checklist: list[str] = []
    if not limit_up_events.empty:
        max_break = pd.to_numeric(limit_up_events.get("break_count"), errors="coerce").fillna(0).max()
        checklist.append(f"复核涨停事件数量 {len(limit_up_events)}，最高炸板次数 {int(max_break)}。")
        if max_break > 0:
            checklist.append("重点复核炸板原因、回封时间和封单稳定性。")
    if sector_echelon:
        latest = sector_echelon[0]
        checklist.append(
            f"复核所属板块 {latest['industry']} 梯队：{latest['echelon_summary']}。"
        )
    if not excluded.empty:
        checklist.append("先处理数据质量问题，再判断趋势、动量和回撤。")
    if strategy_detail.get("candidates"):
        checklist.append("对照策略候选的风险标签，逐条确认是否仍然有效。")
    if not checklist:
        checklist.append("本地证据不足，先补充数据后再复核。")
    return checklist


def _filter_symbol(frame: pd.DataFrame, symbol: str) -> pd.DataFrame:
    if frame.empty or "symbol" not in frame.columns:
        return pd.DataFrame()
    copy = frame.copy()
    copy["symbol"] = copy["symbol"].astype(str).str.zfill(6)
    return copy.loc[copy["symbol"] == symbol].reset_index(drop=True)


def _sort_by_trade_date(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty or "trade_date" not in frame.columns:
        return frame
    return frame.sort_values("trade_date", ascending=False)


def _read_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    if frame.empty:
        return []
    safe = frame.where(pd.notna(frame), None)
    records: list[dict[str, Any]] = []
    for row in safe.to_dict("records"):
        records.append({key: _json_value(value) for key, value in row.items()})
    return records


def _json_value(value: Any) -> Any:
    if hasattr(value, "item"):
        return value.item()
    return value


def _int_value(value: Any) -> int:
    try:
        if pd.isna(value):
            return 0
        return int(float(value))
    except (TypeError, ValueError):
        return 0


def _float_value(value: Any) -> float | None:
    try:
        if pd.isna(value):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _text_value(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except TypeError:
        pass
    return str(value)


def _split_csv_text(value: Any) -> list[str]:
    text = _text_value(value)
    if not text:
        return []
    return [item.strip() for item in text.split(",") if item.strip()]


def _format_limit_time(value: Any) -> str:
    text = _text_value(value).split(".")[0]
    if not text:
        return "-"
    digits = "".join(char for char in text if char.isdigit())
    if len(digits) > 6:
        digits = digits[-6:]
    if len(digits) < 6:
        digits = digits.zfill(6)
    if len(digits) != 6:
        return text
    return f"{digits[:2]}:{digits[2:4]}:{digits[4:]}"


def _amount_text(value: Any) -> str:
    amount = _float_value(value)
    if amount is None:
        return "-"
    if abs(amount) >= 100_000_000:
        return f"{amount / 100_000_000:.2f} 亿"
    if abs(amount) >= 10_000:
        return f"{amount / 10_000:.2f} 万"
    return f"{amount:.0f}"


def _pct_text(value: Any) -> str:
    number = _float_value(value)
    if number is None:
        return "-"
    return f"{number:.2f}%"


def _close_change_pct(current: dict[str, Any], previous: dict[str, Any] | None) -> float | None:
    if previous is None:
        return None
    current_close = _float_value(current.get("close"))
    previous_close = _float_value(previous.get("close"))
    if current_close is None or previous_close in (None, 0):
        return None
    return round((current_close / previous_close - 1) * 100, 2)


def _event_profile(break_count: int, first_time: str, last_time: str) -> str:
    if break_count >= 3:
        return "分歧回封"
    if break_count == 0 and first_time == last_time and first_time != "-":
        return "一字强封"
    if break_count == 0:
        return "稳定封板"
    return "温和分歧"
