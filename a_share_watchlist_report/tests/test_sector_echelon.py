import pandas as pd

from src.sector_echelon import build_sector_echelons


def test_build_sector_echelons_summarizes_board_layers_and_leaders() -> None:
    pool = pd.DataFrame(
        [
            {
                "symbol": "603538",
                "name": "美诺华",
                "trade_date": "2026-07-10",
                "industry": "化学制药",
                "streak_count": 1,
                "break_count": 9,
                "amount": 2_134_658_736,
            },
            {
                "symbol": "600276",
                "name": "恒瑞医药",
                "trade_date": "2026-07-10",
                "industry": "化学制药",
                "streak_count": 2,
                "break_count": 0,
                "amount": 800_000_000,
            },
            {
                "symbol": "000001",
                "name": "平安银行",
                "trade_date": "2026-07-10",
                "industry": "银行",
                "streak_count": 3,
                "break_count": 0,
                "amount": 300_000_000,
            },
        ]
    )

    result = build_sector_echelons(pool)
    pharma = result.loc[result["industry"] == "化学制药"].iloc[0].to_dict()

    assert pharma["trade_date"] == "2026-07-10"
    assert pharma["limit_up_count"] == 2
    assert pharma["first_board_count"] == 1
    assert pharma["second_board_count"] == 1
    assert pharma["high_board_count"] == 0
    assert pharma["max_streak_count"] == 2
    assert pharma["broken_count"] == 1
    assert pharma["total_amount"] == 2_934_658_736.0
    assert pharma["leader_symbols"] == "600276,603538"
    assert pharma["leader_names"] == "恒瑞医药,美诺华"
    assert "首板 1" in pharma["echelon_summary"]
    assert "二板 1" in pharma["echelon_summary"]
