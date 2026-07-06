import pandas as pd

from src.data_quality import run_data_quality_checks


def _universe() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "000001", "name": "平安银行", "industry": "银行"},
            {"symbol": "300750", "name": "宁德时代", "industry": "电力设备"},
            {"symbol": "000002", "name": "万科A", "industry": "房地产"},
        ]
    )


def _config() -> dict:
    return {
        "min_listing_days": 3,
        "min_avg_amount_20d": 100.0,
        "max_missing_days": 1,
    }


def test_data_quality_excludes_no_price_data() -> None:
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "600519", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "600519", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "600519", "close": 12.0, "amount": 200.0},
        ]
    )

    result = run_data_quality_checks(prices, _universe().iloc[:2], _config())

    excluded = result.excluded.set_index("symbol")
    assert "000001" in excluded.index
    assert "no price data" in excluded.loc["000001", "exclude_reason"]


def test_data_quality_excludes_low_amount_short_history_and_bad_close() -> None:
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "600519", "close": 10.0, "amount": 1.0},
            {"date": "2024-01-02", "symbol": "600519", "close": 11.0, "amount": 1.0},
            {"date": "2024-01-03", "symbol": "600519", "close": 12.0, "amount": 1.0},
            {"date": "2024-01-03", "symbol": "000001", "close": 9.0, "amount": 200.0},
            {"date": "2024-01-01", "symbol": "300750", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "300750", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "300750", "close": 0.0, "amount": 200.0},
        ]
    )

    result = run_data_quality_checks(prices, _universe().iloc[:3], _config())

    excluded = result.excluded.set_index("symbol")
    assert "low 20-day average amount" in excluded.loc["600519", "exclude_reason"]
    assert "short history" in excluded.loc["000001", "exclude_reason"]
    assert "latest close <= 0" in excluded.loc["300750", "exclude_reason"]


def test_data_quality_does_not_count_pre_listing_dates_as_missing() -> None:
    universe = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "300750", "name": "宁德时代", "industry": "电力设备"},
        ]
    )
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "600519", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "600519", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "600519", "close": 12.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "300750", "close": 20.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "300750", "close": 21.0, "amount": 200.0},
            {"date": "2024-01-04", "symbol": "300750", "close": 22.0, "amount": 200.0},
        ]
    )

    config = _config()
    config["max_missing_days"] = 0
    result = run_data_quality_checks(prices, universe, config)

    assert "300750" not in set(result.excluded["symbol"])


def test_data_quality_excludes_st_name_from_universe() -> None:
    universe = pd.DataFrame(
        [
            {"symbol": "600519", "name": "ST茅台", "industry": "食品饮料"},
        ]
    )
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "600519", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "600519", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "600519", "close": 12.0, "amount": 200.0},
        ]
    )

    result = run_data_quality_checks(prices, universe, _config())

    excluded = result.excluded.set_index("symbol")
    assert "600519" in excluded.index
    assert "ST name" in excluded.loc["600519", "exclude_reason"]


def test_data_quality_does_not_duplicate_stale_date_reasons() -> None:
    universe = pd.DataFrame(
        [
            {"symbol": "600519", "name": "贵州茅台", "industry": "食品饮料"},
            {"symbol": "000001", "name": "平安银行", "industry": "银行"},
        ]
    )
    prices = pd.DataFrame(
        [
            {"date": "2024-01-01", "symbol": "600519", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "600519", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-01", "symbol": "000001", "close": 10.0, "amount": 200.0},
            {"date": "2024-01-02", "symbol": "000001", "close": 11.0, "amount": 200.0},
            {"date": "2024-01-03", "symbol": "000001", "close": 12.0, "amount": 200.0},
        ]
    )

    result = run_data_quality_checks(prices, universe, _config())

    reason = result.excluded.set_index("symbol").loc["600519", "exclude_reason"]
    assert "suspected suspension" in reason
    assert "latest date too old" not in reason
