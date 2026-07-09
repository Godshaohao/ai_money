from datetime import date, timedelta

import pandas as pd

try:
    import akshare as ak
except ImportError:  # pragma: no cover - dependency smoke check covers runtime install
    ak = None


LIMIT_UP_POOL_COLUMNS = [
    "symbol",
    "name",
    "trade_date",
    "close",
    "change_pct",
    "amount",
    "turnover_rate",
    "seal_amount",
    "first_limit_time",
    "last_limit_time",
    "break_count",
    "limit_up_stats",
    "streak_count",
    "industry",
    "source",
]


def empty_limit_up_pool_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=LIMIT_UP_POOL_COLUMNS)


def normalize_limit_up_pool_frame(frame: pd.DataFrame, trade_date: str) -> pd.DataFrame:
    if frame.empty:
        return empty_limit_up_pool_frame()

    renamed = frame.rename(
        columns={
            "代码": "symbol",
            "名称": "name",
            "最新价": "close",
            "涨跌幅": "change_pct",
            "成交额": "amount",
            "换手率": "turnover_rate",
            "封板资金": "seal_amount",
            "首次封板时间": "first_limit_time",
            "最后封板时间": "last_limit_time",
            "炸板次数": "break_count",
            "涨停统计": "limit_up_stats",
            "连板数": "streak_count",
            "所属行业": "industry",
        }
    )
    required = ["symbol", "name"]
    missing = [column for column in required if column not in renamed.columns]
    if missing:
        raise ValueError(f"limit-up pool data missing columns: {', '.join(missing)}")

    normalized = pd.DataFrame()
    normalized["symbol"] = renamed["symbol"].astype("string").str.strip().str.zfill(6)
    normalized["name"] = renamed["name"].astype("string").fillna("").str.strip()
    normalized["trade_date"] = pd.to_datetime(trade_date, format="%Y%m%d", errors="coerce").strftime("%Y-%m-%d")
    for source, target in [
        ("close", "close"),
        ("change_pct", "change_pct"),
        ("amount", "amount"),
        ("turnover_rate", "turnover_rate"),
        ("seal_amount", "seal_amount"),
        ("break_count", "break_count"),
        ("streak_count", "streak_count"),
    ]:
        normalized[target] = pd.to_numeric(renamed[source], errors="coerce") if source in renamed.columns else pd.NA
    for source, target in [
        ("first_limit_time", "first_limit_time"),
        ("last_limit_time", "last_limit_time"),
        ("limit_up_stats", "limit_up_stats"),
        ("industry", "industry"),
    ]:
        normalized[target] = renamed[source].astype("string").fillna("").str.strip() if source in renamed.columns else ""
    normalized["source"] = "akshare_eastmoney_zt_pool"
    normalized = normalized.dropna(subset=["trade_date"]).drop_duplicates(subset=["symbol", "trade_date"])
    return normalized[LIMIT_UP_POOL_COLUMNS].reset_index(drop=True)


def fetch_limit_up_pool_for_date(trade_date: str) -> pd.DataFrame:
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    raw = ak.stock_zt_pool_em(date=trade_date)
    return normalize_limit_up_pool_frame(raw, trade_date)


def fetch_recent_limit_up_pool(days: int = 10, today: date | None = None) -> pd.DataFrame:
    end_date = today or date.today()
    frames: list[pd.DataFrame] = []
    failures: list[str] = []
    for offset in range(days - 1, -1, -1):
        trade_date = (end_date - timedelta(days=offset)).strftime("%Y%m%d")
        try:
            frame = fetch_limit_up_pool_for_date(trade_date)
        except Exception as exc:
            failures.append(f"{trade_date}: {exc}")
            continue
        if not frame.empty:
            frames.append(frame)

    if not frames:
        if failures and len(failures) == days:
            raise RuntimeError("limit-up pool fetch failed for all dates: " + "; ".join(failures[:3]))
        return empty_limit_up_pool_frame()
    return pd.concat(frames, ignore_index=True).drop_duplicates(subset=["symbol", "trade_date"]).reset_index(drop=True)


def merge_limit_up_universe(universe: pd.DataFrame, limit_up: pd.DataFrame, max_size: int) -> pd.DataFrame:
    merged = universe.copy()
    if limit_up.empty or len(merged) >= max_size:
        return merged.reset_index(drop=True)

    existing = set(merged["symbol"].astype(str).str.zfill(6))
    additions: list[dict] = []
    candidates = limit_up.sort_values("trade_date", ascending=False) if "trade_date" in limit_up.columns else limit_up
    for row in candidates.to_dict("records"):
        symbol = str(row["symbol"]).zfill(6)
        if symbol in existing:
            continue
        additions.append({"symbol": symbol, "name": row["name"], "industry": "近期涨停"})
        existing.add(symbol)
        if len(merged) + len(additions) >= max_size:
            break

    if additions:
        merged = pd.concat([merged, pd.DataFrame(additions)], ignore_index=True)
    return merged.reset_index(drop=True)
