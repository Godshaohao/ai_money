from datetime import datetime

import pandas as pd

try:
    import akshare as ak
except ImportError:  # pragma: no cover - dependency smoke check covers runtime install
    ak = None

DRAGON_TIGER_COLUMNS = [
    "symbol",
    "name",
    "trade_date",
    "close",
    "change_pct",
    "net_buy_amount",
    "buy_amount",
    "sell_amount",
    "deal_amount",
    "turnover_rate",
    "reason",
    "source",
]


def empty_dragon_tiger_frame() -> pd.DataFrame:
    return pd.DataFrame(columns=DRAGON_TIGER_COLUMNS)


def normalize_dragon_tiger_frame(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return empty_dragon_tiger_frame()

    renamed = frame.rename(
        columns={
            "代码": "symbol",
            "名称": "name",
            "上榜日": "trade_date",
            "收盘价": "close",
            "涨跌幅": "change_pct",
            "龙虎榜净买额": "net_buy_amount",
            "龙虎榜买入额": "buy_amount",
            "龙虎榜卖出额": "sell_amount",
            "龙虎榜成交额": "deal_amount",
            "换手率": "turnover_rate",
            "上榜原因": "reason",
        }
    )
    required = ["symbol", "name", "trade_date", "reason"]
    missing = [column for column in required if column not in renamed.columns]
    if missing:
        raise ValueError(f"dragon tiger data missing columns: {', '.join(missing)}")

    normalized = pd.DataFrame()
    normalized["symbol"] = renamed["symbol"].astype("string").str.strip().str.zfill(6)
    normalized["name"] = renamed["name"].astype("string").fillna("").str.strip()
    normalized["trade_date"] = pd.to_datetime(renamed["trade_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    for source, target in [
        ("close", "close"),
        ("change_pct", "change_pct"),
        ("net_buy_amount", "net_buy_amount"),
        ("buy_amount", "buy_amount"),
        ("sell_amount", "sell_amount"),
        ("deal_amount", "deal_amount"),
        ("turnover_rate", "turnover_rate"),
    ]:
        normalized[target] = pd.to_numeric(renamed[source], errors="coerce") if source in renamed.columns else pd.NA
    normalized["reason"] = renamed["reason"].astype("string").fillna("").str.strip()
    normalized["source"] = "akshare_eastmoney_lhb"
    normalized = normalized.dropna(subset=["trade_date"]).drop_duplicates(subset=["symbol", "trade_date", "reason"])
    return normalized[DRAGON_TIGER_COLUMNS].reset_index(drop=True)


def fetch_today_dragon_tiger(today: str | None = None) -> pd.DataFrame:
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before running the report.")
    trade_date = today or datetime.today().strftime("%Y%m%d")
    parsed_trade_date = datetime.strptime(trade_date, "%Y%m%d")
    if parsed_trade_date.weekday() >= 5:
        return empty_dragon_tiger_frame()
    raw = ak.stock_lhb_detail_em(start_date=trade_date, end_date=trade_date)
    return normalize_dragon_tiger_frame(raw)


def merge_dragon_tiger_universe(universe: pd.DataFrame, dragon_tiger: pd.DataFrame, max_size: int) -> pd.DataFrame:
    merged = universe.copy()
    if dragon_tiger.empty or len(merged) >= max_size:
        return merged.reset_index(drop=True)

    existing = set(merged["symbol"].astype(str).str.zfill(6))
    additions: list[dict] = []
    for row in dragon_tiger.to_dict("records"):
        symbol = str(row["symbol"]).zfill(6)
        if symbol in existing:
            continue
        additions.append({"symbol": symbol, "name": row["name"], "industry": "龙虎榜"})
        existing.add(symbol)
        if len(merged) + len(additions) >= max_size:
            break

    if additions:
        merged = pd.concat([merged, pd.DataFrame(additions)], ignore_index=True)
    return merged.reset_index(drop=True)
