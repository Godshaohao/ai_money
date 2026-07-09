import pandas as pd
import pytest

from src.data.stock_list import normalize_stock_list_frame
from src.schemas import UNIVERSE_COLUMNS


def test_normalize_stock_list_frame_outputs_universe_columns() -> None:
    raw = pd.DataFrame({"代码": ["600519"], "名称": ["贵州茅台"]})

    normalized = normalize_stock_list_frame(raw)

    assert list(normalized.columns) == UNIVERSE_COLUMNS
    assert normalized.loc[0, "symbol"] == "600519"
    assert normalized.loc[0, "name"] == "贵州茅台"
    assert normalized.loc[0, "industry"] == ""


def test_normalize_stock_list_frame_drops_exact_duplicates() -> None:
    raw = pd.DataFrame({"代码": ["600519", "600519"], "名称": ["贵州茅台", "贵州茅台"]})

    normalized = normalize_stock_list_frame(raw)

    assert len(normalized) == 1


def test_normalize_stock_list_frame_fails_closed_on_invalid_symbol() -> None:
    raw = pd.DataFrame({"代码": ["6005190"], "名称": ["坏代码"]})

    with pytest.raises(ValueError, match="invalid symbols: 6005190"):
        normalize_stock_list_frame(raw)


def test_normalize_stock_list_frame_fails_closed_on_conflicting_duplicates() -> None:
    raw = pd.DataFrame({"代码": ["600519", "600519"], "名称": ["贵州茅台", "茅台"]})

    with pytest.raises(ValueError, match="conflicting metadata: 600519"):
        normalize_stock_list_frame(raw)

