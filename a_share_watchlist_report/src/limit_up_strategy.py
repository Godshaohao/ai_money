import pandas as pd


LIMIT_UP_REVIEW_COLUMNS = [
    "symbol",
    "name",
    "trade_date",
    "review_score",
    "review_label",
    "red_flags",
    "hard_flags",
    "market_context",
    "data_confidence_score",
    "board_quality_score",
    "theme_position_score",
    "risk_penalty_score",
    "limit_up_strength",
    "streak_score",
    "board_quality",
    "liquidity_score",
    "overnight_risk",
    "data_quality_score",
    "score_explain",
    "reason",
]
LIMIT_UP_REQUIRED_FIELDS = ["change_pct", "amount", "break_count", "streak_count"]


def empty_limit_up_strategy_review_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=LIMIT_UP_REVIEW_COLUMNS)


def build_limit_up_strategy_review(
    limit_up_pool: pd.DataFrame,
    prices: pd.DataFrame,
    market_evidence: pd.DataFrame | None = None,
) -> pd.DataFrame:
    if limit_up_pool.empty:
        return empty_limit_up_strategy_review_frame()

    price_symbols = set(prices["symbol"].astype(str).str.zfill(6)) if "symbol" in prices.columns else set()
    _, market_state = _market_context_score(market_evidence)
    market_component = _market_component(market_state)
    theme_context = _theme_context(limit_up_pool)
    rows: list[dict] = []
    for row in limit_up_pool.to_dict("records"):
        symbol = str(row.get("symbol", "")).zfill(6)
        red_flags: list[str] = []
        hard_flags: list[str] = []
        if _is_st_name(str(row.get("name", ""))):
            red_flags.append("ST_NAME")
            hard_flags.append("ST_NAME")
        has_history = symbol in price_symbols
        has_pool_data_gap = _has_limit_up_pool_data_gap(row)
        if has_pool_data_gap:
            red_flags.append("DATA_GAP")
            hard_flags.append("DATA_GAP")
        elif not has_history:
            red_flags.append("HISTORY_GAP")
            hard_flags.append("HISTORY_GAP")

        change_pct = _number(row.get("change_pct"))
        amount = _number(row.get("amount"))
        break_count = int(_number(row.get("break_count")))
        streak_count = int(_number(row.get("streak_count")))
        seal_amount = _number(row.get("seal_amount"))

        if amount < 50_000_000:
            red_flags.append("LOW_LIQUIDITY")
            hard_flags.append("LOW_LIQUIDITY")
        if break_count > 0:
            red_flags.append("BROKEN_BOARD_RISK")
        if break_count >= 3:
            hard_flags.append("BROKEN_BOARD_RISK")
        if change_pct < 9:
            red_flags.append("WEAK_LIMIT_MOVE")
            hard_flags.append("WEAK_LIMIT_MOVE")

        limit_up_strength = 20 if change_pct >= 9.8 else 16 if change_pct >= 9 else 10
        streak_score = min(max(streak_count, 1) * 5, 15)
        board_quality = _board_quality_score(row, change_pct, amount, break_count, seal_amount)
        liquidity_score = 10 if amount >= 100_000_000 else 7 if amount >= 50_000_000 else 3
        overnight_risk = 10 if break_count == 0 and seal_amount >= 50_000_000 else 6 if break_count <= 1 else 3
        data_confidence_score = _data_confidence_score(has_pool_data_gap, has_history)
        data_quality_score = data_confidence_score
        theme_position_score = _theme_position_score(theme_context, row, symbol)
        risk_penalty_score = _risk_penalty_score(red_flags, hard_flags, break_count)
        raw_score = int(
            min(100, market_component + data_confidence_score + board_quality + theme_position_score)
        )
        review_score = _apply_hard_caps(raw_score, hard_flags)
        review_label = _review_label(review_score, red_flags, hard_flags)
        score_explain = _score_explain(
            data_confidence_score,
            board_quality,
            theme_position_score,
            risk_penalty_score,
            hard_flags,
        )
        rows.append(
            {
                "symbol": symbol,
                "name": row.get("name", ""),
                "trade_date": row.get("trade_date", ""),
                "review_score": review_score,
                "review_label": review_label,
                "red_flags": ",".join(red_flags),
                "hard_flags": ",".join(dict.fromkeys(hard_flags)),
                "market_context": market_state,
                "data_confidence_score": data_confidence_score,
                "board_quality_score": board_quality,
                "theme_position_score": theme_position_score,
                "risk_penalty_score": risk_penalty_score,
                "limit_up_strength": limit_up_strength,
                "streak_score": streak_score,
                "board_quality": board_quality,
                "liquidity_score": liquidity_score,
                "overnight_risk": overnight_risk,
                "data_quality_score": data_quality_score,
                "score_explain": score_explain,
                "reason": _reason(change_pct, streak_count, break_count, amount, red_flags),
            }
        )

    return pd.DataFrame(rows, columns=LIMIT_UP_REVIEW_COLUMNS).sort_values(
        ["review_score", "trade_date"], ascending=[False, False]
    ).reset_index(drop=True)


def _market_context_score(market_evidence: pd.DataFrame | None) -> tuple[int, str]:
    if market_evidence is None or market_evidence.empty or "status" not in market_evidence.columns:
        return 8, "UNKNOWN"
    statuses = set(market_evidence["status"].astype(str))
    if "NEGATIVE" in statuses:
        return 6, "RISK_OFF"
    if "POSITIVE" in statuses:
        return 15, "SUPPORTIVE"
    return 10, "NEUTRAL"


def _market_component(market_state: str) -> int:
    if market_state == "SUPPORTIVE":
        return 10
    if market_state == "NEUTRAL":
        return 6
    if market_state == "RISK_OFF":
        return 2
    return 5


def _review_label(score: int, red_flags: list[str], hard_flags: list[str]) -> str:
    if "DATA_GAP" in red_flags:
        return "DATA_GAP"
    if "HISTORY_GAP" in red_flags:
        return "DATA_REVIEW"
    if score >= 80 and not red_flags:
        return "CORE_REVIEW"
    if score >= 65:
        return "WATCH_REVIEW"
    return "RISK_REVIEW"


def _reason(change_pct: float, streak_count: int, break_count: int, amount: float, red_flags: list[str]) -> str:
    flags = "；风险标签 " + ",".join(red_flags) if red_flags else "；未触发硬风险标签"
    return (
        f"近期涨停复核：涨幅 {change_pct:.2f}%，连板 {streak_count}，"
        f"炸板 {break_count}，成交额 {amount / 100000000:.2f} 亿{flags}"
    )


def _number(value: object) -> float:
    number = pd.to_numeric(pd.Series([value]), errors="coerce").iloc[0]
    if pd.isna(number):
        return 0.0
    return float(number)


def _data_confidence_score(has_pool_data_gap: bool, has_history: bool) -> int:
    if has_pool_data_gap:
        return 4
    if not has_history:
        return 10
    return 20


def _board_quality_score(
    row: dict,
    change_pct: float,
    amount: float,
    break_count: int,
    seal_amount: float,
) -> int:
    if break_count == 0:
        break_score = 14
    elif break_count <= 1:
        break_score = 10
    elif break_count <= 3:
        break_score = 6
    else:
        break_score = 0

    if seal_amount >= 100_000_000:
        seal_score = 8
    elif seal_amount >= 50_000_000:
        seal_score = 6
    elif seal_amount >= 20_000_000:
        seal_score = 3
    else:
        seal_score = 0

    first_time = str(row.get("first_limit_time", "") or "")
    last_time = str(row.get("last_limit_time", "") or "")
    has_time = bool(first_time and last_time)
    if break_count == 0 and has_time and first_time == last_time:
        time_score = 5
    elif break_count <= 1 and has_time:
        time_score = 3
    elif break_count <= 3 and has_time:
        time_score = 1
    else:
        time_score = 0

    strength_score = 5 if change_pct >= 9.8 else 3 if change_pct >= 9 else 0
    liquidity_component = 3 if amount >= 100_000_000 else 1 if amount >= 50_000_000 else 0
    return int(min(35, break_score + seal_score + time_score + strength_score + liquidity_component))


def _theme_context(limit_up_pool: pd.DataFrame) -> dict[tuple[str, str], dict]:
    if limit_up_pool.empty:
        return {}
    frame = limit_up_pool.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    frame["trade_date"] = frame["trade_date"].astype(str)
    frame["industry"] = frame["industry"].fillna("未分类").astype(str)
    frame["streak_count"] = pd.to_numeric(frame["streak_count"], errors="coerce").fillna(1).astype(int)
    frame["break_count"] = pd.to_numeric(frame["break_count"], errors="coerce").fillna(0).astype(int)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0)

    context: dict[tuple[str, str], dict] = {}
    for (trade_date, industry), group in frame.groupby(["trade_date", "industry"]):
        leaders = group.sort_values(["streak_count", "amount"], ascending=[False, False]).head(5)
        context[(str(trade_date), str(industry))] = {
            "limit_up_count": int(len(group)),
            "max_streak_count": int(group["streak_count"].max()),
            "broken_count": int((group["break_count"] > 0).sum()),
            "leader_symbols": set(leaders["symbol"].astype(str).tolist()),
        }
    return context


def _theme_position_score(theme_context: dict[tuple[str, str], dict], row: dict, symbol: str) -> int:
    key = (str(row.get("trade_date", "")), str(row.get("industry", "未分类") or "未分类"))
    context = theme_context.get(key)
    if not context:
        return 0
    limit_up_count = int(context["limit_up_count"])
    max_streak = int(context["max_streak_count"])
    broken_count = int(context["broken_count"])
    leader_symbols = context["leader_symbols"]

    breadth_score = min(8, limit_up_count * 2)
    height_score = 6 if max_streak >= 3 else 4 if max_streak == 2 else 1
    leader_score = 5 if symbol in leader_symbols else 0
    continuity_score = 4 if int(_number(row.get("streak_count"))) >= 2 else 1
    broken_penalty = round((broken_count / limit_up_count) * 8) if limit_up_count else 0
    return int(max(0, min(25, breadth_score + height_score + leader_score + continuity_score - broken_penalty)))


def _risk_penalty_score(red_flags: list[str], hard_flags: list[str], break_count: int) -> int:
    penalty = 0
    if "DATA_GAP" in red_flags:
        penalty += 35
    if "HISTORY_GAP" in red_flags:
        penalty += 15
    if "ST_NAME" in red_flags:
        penalty += 35
    if "LOW_LIQUIDITY" in red_flags:
        penalty += 12
    if "WEAK_LIMIT_MOVE" in red_flags:
        penalty += 15
    if break_count >= 8:
        penalty += 25
    elif break_count >= 4:
        penalty += 18
    elif break_count > 0:
        penalty += 10
    return int(min(60, penalty + max(0, len(set(hard_flags)) - 1) * 2))


def _apply_hard_caps(raw_score: int, hard_flags: list[str]) -> int:
    score = raw_score
    if "DATA_GAP" in hard_flags:
        score = min(score, 45)
    if "HISTORY_GAP" in hard_flags:
        score = min(score, 75)
    if "BROKEN_BOARD_RISK" in hard_flags:
        score = min(score, 65)
    if "ST_NAME" in hard_flags:
        score = min(score, 45)
    return int(max(0, score))


def _score_explain(
    data_confidence_score: int,
    board_quality_score: int,
    theme_position_score: int,
    risk_penalty_score: int,
    hard_flags: list[str],
) -> str:
    flags = ",".join(dict.fromkeys(hard_flags)) if hard_flags else "未触发"
    return (
        f"数据可信度 {data_confidence_score}/20；"
        f"板面质量 {board_quality_score}/35；"
        f"题材地位 {theme_position_score}/25；"
        f"风险惩罚 {risk_penalty_score}/60；"
        f"硬风险 {flags}"
    )


def _is_st_name(name: str) -> bool:
    normalized = name.strip().upper()
    return normalized.startswith("ST") or normalized.startswith("*ST")


def _has_limit_up_pool_data_gap(row: dict) -> bool:
    for field in LIMIT_UP_REQUIRED_FIELDS:
        value = pd.to_numeric(pd.Series([row.get(field)]), errors="coerce").iloc[0]
        if pd.isna(value):
            return True
    return False
