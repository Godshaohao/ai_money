from datetime import date, timedelta

import pandas as pd

from src.data.eastmoney_http import em_get_json

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
ZTB_UT = "7eea3edcaed734bea9cbfc24409ed989"


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


def _fmt_zt_time(value: object) -> str:
    if value in (None, "") or pd.isna(value):
        return ""
    text = str(int(value)).zfill(6)
    return f"{text[0:2]}:{text[2:4]}:{text[4:6]}"


def parse_eastmoney_limit_up_payload(payload: dict, trade_date: str) -> pd.DataFrame:
    data = payload.get("data") if isinstance(payload, dict) else None
    pool = data.get("pool") if isinstance(data, dict) else None
    if not pool:
        return empty_limit_up_pool_frame()

    rows: list[dict] = []
    parsed_trade_date = pd.to_datetime(trade_date, format="%Y%m%d", errors="coerce").strftime("%Y-%m-%d")
    for item in pool:
        zt_stats = item.get("zttj") or {}
        rows.append(
            {
                "symbol": str(item.get("c", "")).strip().zfill(6),
                "name": str(item.get("n", "")).strip(),
                "trade_date": parsed_trade_date,
                "close": pd.to_numeric(pd.Series([item.get("p")]), errors="coerce").iloc[0] / 1000,
                "change_pct": pd.to_numeric(pd.Series([item.get("zdp")]), errors="coerce").iloc[0],
                "amount": pd.to_numeric(pd.Series([item.get("amount")]), errors="coerce").iloc[0],
                "turnover_rate": pd.to_numeric(pd.Series([item.get("hs")]), errors="coerce").iloc[0],
                "seal_amount": pd.to_numeric(pd.Series([item.get("fund")]), errors="coerce").iloc[0],
                "first_limit_time": _fmt_zt_time(item.get("fbt")),
                "last_limit_time": _fmt_zt_time(item.get("lbt")),
                "break_count": pd.to_numeric(pd.Series([item.get("zbc")]), errors="coerce").iloc[0],
                "limit_up_stats": f"{zt_stats.get('days', '?')}天{zt_stats.get('ct', '?')}板",
                "streak_count": pd.to_numeric(pd.Series([item.get("lbc")]), errors="coerce").iloc[0],
                "industry": str(item.get("hybk", "") or "").strip(),
                "source": "eastmoney_push2ex_zt_pool",
            }
        )
    return pd.DataFrame(rows, columns=LIMIT_UP_POOL_COLUMNS).drop_duplicates(
        subset=["symbol", "trade_date"]
    ).reset_index(drop=True)


def fetch_limit_up_pool_eastmoney_direct(trade_date: str) -> pd.DataFrame:
    payload = em_get_json(
        "https://push2ex.eastmoney.com/getTopicZTPool",
        params={
            "ut": ZTB_UT,
            "dpt": "wz.ztzt",
            "Pageindex": 0,
            "pagesize": 10000,
            "sort": "fbt:asc",
            "date": trade_date,
        },
        headers={"Referer": "https://quote.eastmoney.com/"},
        timeout=10,
        impersonate="chrome",
    )
    return parse_eastmoney_limit_up_payload(payload, trade_date)


def fetch_limit_up_pool_for_date(trade_date: str) -> pd.DataFrame:
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    try:
        raw = ak.stock_zt_pool_em(date=trade_date)
        return normalize_limit_up_pool_frame(raw, trade_date)
    except Exception as ak_exc:
        try:
            return fetch_limit_up_pool_eastmoney_direct(trade_date)
        except Exception as direct_exc:
            raise RuntimeError(
                f"limit-up pool fetch failed for {trade_date}: akshare={ak_exc}; eastmoney_direct={direct_exc}"
            ) from direct_exc


def _recent_weekday_strings(days: int, end_date: date) -> list[str]:
    trade_dates: list[str] = []
    cursor = end_date
    while len(trade_dates) < days:
        if cursor.weekday() < 5:
            trade_dates.append(cursor.strftime("%Y%m%d"))
        cursor -= timedelta(days=1)
    return list(reversed(trade_dates))


def fetch_recent_limit_up_pool(days: int = 10, today: date | None = None) -> pd.DataFrame:
    end_date = today or date.today()
    frames: list[pd.DataFrame] = []
    failures: list[str] = []
    trade_dates = _recent_weekday_strings(days, end_date)
    for trade_date in trade_dates:
        try:
            frame = fetch_limit_up_pool_for_date(trade_date)
        except Exception as exc:
            failures.append(f"{trade_date}: {exc}")
            continue
        if not frame.empty:
            frames.append(frame)

    if not frames:
        if failures and len(failures) == len(trade_dates):
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
