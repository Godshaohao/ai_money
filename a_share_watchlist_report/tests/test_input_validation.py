from pathlib import Path

import pandas as pd
import pytest

from src.input_validation import load_holdings, load_universe


def test_universe_over_max_size_fails(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    rows = [{"symbol": f"{i:06d}", "name": f"name{i}", "industry": "行业"} for i in range(101)]
    pd.DataFrame(rows).to_csv(path, index=False)

    with pytest.raises(ValueError, match="max_universe_size"):
        load_universe(path, max_size=100)


def test_universe_missing_required_columns_fails(tmp_path: Path) -> None:
    path = tmp_path / "universe.csv"
    pd.DataFrame([{"symbol": "600519", "name": "贵州茅台"}]).to_csv(path, index=False)

    with pytest.raises(ValueError, match="industry"):
        load_universe(path, max_size=100)


def test_empty_holdings_header_passes(tmp_path: Path) -> None:
    path = tmp_path / "holdings.csv"
    path.write_text("symbol,shares,cost_basis\n", encoding="utf-8")

    holdings = load_holdings(path)

    assert list(holdings.columns) == ["symbol", "shares", "cost_basis"]
    assert holdings.empty
