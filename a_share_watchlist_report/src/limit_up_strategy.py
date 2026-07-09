import pandas as pd


LIMIT_UP_REVIEW_COLUMNS = [
    "symbol",
    "name",
    "trade_date",
    "review_score",
    "review_label",
    "red_flags",
    "market_context",
    "limit_up_strength",
    "streak_score",
    "board_quality",
    "liquidity_score",
    "overnight_risk",
    "data_quality_score",
    "reason",
]


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
    market_score, market_state = _market_context_score(market_evidence)
    rows: list[dict] = []
    for row in limit_up_pool.to_dict("records"):
        symbol = str(row.get("symbol", "")).zfill(6)
        red_flags: list[str] = []
        if _is_st_name(str(row.get("name", ""))):
            red_flags.append("ST_NAME")
        if symbol not in price_symbols:
            red_flags.append("DATA_GAP")

        change_pct = _number(row.get("change_pct"))
        amount = _number(row.get("amount"))
        break_count = int(_number(row.get("break_count")))
        streak_count = int(_number(row.get("streak_count")))
        seal_amount = _number(row.get("seal_amount"))

        if amount < 50_000_000:
            red_flags.append("LOW_LIQUIDITY")
        if break_count > 0:
            red_flags.append("BROKEN_BOARD_RISK")
        if change_pct < 9:
            red_flags.append("WEAK_LIMIT_MOVE")

        limit_up_strength = 20 if change_pct >= 9.8 else 16 if change_pct >= 9 else 10
        streak_score = min(max(streak_count, 1) * 5, 15)
        board_quality = max(4, 15 - break_count * 4 + (2 if seal_amount >= 50_000_000 else 0))
        liquidity_score = 10 if amount >= 100_000_000 else 7 if amount >= 50_000_000 else 3
        overnight_risk = 10 if break_count == 0 and seal_amount >= 50_000_000 else 6 if break_count <= 1 else 3
        data_quality_score = 10 if symbol in price_symbols else 3
        review_score = int(
            min(
                100,
                market_score
                + limit_up_strength
                + streak_score
                + board_quality
                + liquidity_score
                + overnight_risk
                + data_quality_score
                + 5,
            )
        )
        if "DATA_GAP" in red_flags:
            review_score = min(review_score, 60)
        if "ST_NAME" in red_flags:
            review_score = min(review_score, 50)
        review_label = _review_label(review_score, red_flags)
        rows.append(
            {
                "symbol": symbol,
                "name": row.get("name", ""),
                "trade_date": row.get("trade_date", ""),
                "review_score": review_score,
                "review_label": review_label,
                "red_flags": ",".join(red_flags),
                "market_context": market_state,
                "limit_up_strength": limit_up_strength,
                "streak_score": streak_score,
                "board_quality": board_quality,
                "liquidity_score": liquidity_score,
                "overnight_risk": overnight_risk,
                "data_quality_score": data_quality_score,
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


def _review_label(score: int, red_flags: list[str]) -> str:
    if "DATA_GAP" in red_flags:
        return "DATA_GAP"
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


def _is_st_name(name: str) -> bool:
    normalized = name.strip().upper()
    return normalized.startswith("ST") or normalized.startswith("*ST")
