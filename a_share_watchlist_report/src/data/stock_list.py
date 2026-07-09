import pandas as pd

try:
    import akshare as ak
except ImportError:  # pragma: no cover - exercised in environments without runtime deps
    ak = None

from src.schemas import UNIVERSE_COLUMNS


def normalize_stock_list_frame(frame: pd.DataFrame) -> pd.DataFrame:
    renamed = frame.rename(columns={"代码": "symbol", "名称": "name", "行业": "industry"})
    missing = [column for column in ["symbol", "name"] if column not in renamed.columns]
    if missing:
        raise ValueError(f"AKShare stock list missing columns: {', '.join(missing)}")

    normalized = renamed.copy()
    if "industry" not in normalized.columns:
        normalized["industry"] = ""

    normalized = normalized[UNIVERSE_COLUMNS].copy()
    normalized["symbol"] = normalized["symbol"].astype("string").str.strip()
    normalized["name"] = normalized["name"].astype("string").fillna("").str.strip()
    normalized["industry"] = normalized["industry"].astype("string").fillna("").str.strip()

    invalid = normalized.loc[~normalized["symbol"].str.fullmatch(r"\d{6}", na=False), "symbol"].astype(str).tolist()
    if invalid:
        raise ValueError(f"AKShare stock list contains invalid symbols: {', '.join(invalid)}")

    normalized = normalized.drop_duplicates().reset_index(drop=True)
    conflicts = normalized.loc[normalized["symbol"].duplicated(keep=False)].sort_values("symbol")
    if not conflicts.empty:
        symbols = sorted(conflicts["symbol"].astype(str).unique().tolist())
        raise ValueError(f"AKShare stock list duplicate symbols with conflicting metadata: {', '.join(symbols)}")

    return normalized


def fetch_a_stock_list() -> pd.DataFrame:
    if ak is None:
        raise RuntimeError("AKShare is not installed. Install requirements.txt before fetching the stock list.")
    return normalize_stock_list_frame(ak.stock_info_a_code_name())
