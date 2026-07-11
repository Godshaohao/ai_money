PRICE_COLUMNS = ["date", "symbol", "close", "amount"]
INDEX_PRICE_COLUMNS = ["date", "index_name", "index_code", "close"]
UNIVERSE_COLUMNS = ["symbol", "name", "industry"]
HOLDING_COLUMNS = ["symbol", "shares", "cost_basis"]
ALLOWED_RISK_ACTIONS = {"WATCH", "HOLD_REVIEW", "REDUCE_REVIEW", "DATA_ISSUE"}
DAILY_BAR_COLUMNS = [
    "date",
    "symbol",
    "name",
    "industry",
    "open",
    "high",
    "low",
    "close",
    "amount",
    "volume",
    "source",
    "adjust",
    "updated_at",
]
DATA_COVERAGE_KEYS = [
    "total_symbols",
    "cached_symbols",
    "latest_date",
    "missing_symbols",
    "stale_symbols",
    "failed_symbols",
]
