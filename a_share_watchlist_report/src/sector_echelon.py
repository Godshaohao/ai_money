import pandas as pd


SECTOR_ECHELON_COLUMNS = [
    "trade_date",
    "industry",
    "limit_up_count",
    "first_board_count",
    "second_board_count",
    "high_board_count",
    "max_streak_count",
    "broken_count",
    "total_amount",
    "leader_symbols",
    "leader_names",
    "echelon_summary",
]


def build_sector_echelons(limit_up_pool: pd.DataFrame) -> pd.DataFrame:
    if limit_up_pool.empty:
        return pd.DataFrame(columns=SECTOR_ECHELON_COLUMNS)

    frame = limit_up_pool.copy()
    frame["symbol"] = frame["symbol"].astype(str).str.zfill(6)
    frame["industry"] = frame["industry"].fillna("未分类").astype(str)
    frame["trade_date"] = frame["trade_date"].astype(str)
    frame["streak_count"] = pd.to_numeric(frame["streak_count"], errors="coerce").fillna(1).astype(int)
    frame["break_count"] = pd.to_numeric(frame["break_count"], errors="coerce").fillna(0).astype(int)
    frame["amount"] = pd.to_numeric(frame["amount"], errors="coerce").fillna(0.0)

    rows: list[dict] = []
    for (trade_date, industry), group in frame.groupby(["trade_date", "industry"], sort=True):
        leaders = group.sort_values(["streak_count", "amount"], ascending=[False, False]).head(5)
        first_count = int((group["streak_count"] == 1).sum())
        second_count = int((group["streak_count"] == 2).sum())
        high_count = int((group["streak_count"] >= 3).sum())
        broken_count = int((group["break_count"] > 0).sum())
        max_streak = int(group["streak_count"].max())
        rows.append(
            {
                "trade_date": trade_date,
                "industry": industry,
                "limit_up_count": int(len(group)),
                "first_board_count": first_count,
                "second_board_count": second_count,
                "high_board_count": high_count,
                "max_streak_count": max_streak,
                "broken_count": broken_count,
                "total_amount": float(group["amount"].sum()),
                "leader_symbols": ",".join(leaders["symbol"].astype(str).tolist()),
                "leader_names": ",".join(leaders["name"].astype(str).tolist()),
                "echelon_summary": (
                    f"涨停 {len(group)}；首板 {first_count}；二板 {second_count}；"
                    f"高标 {high_count}；最高 {max_streak} 连板；炸板 {broken_count}"
                ),
            }
        )

    return pd.DataFrame(rows, columns=SECTOR_ECHELON_COLUMNS).sort_values(
        ["trade_date", "limit_up_count", "max_streak_count", "total_amount"],
        ascending=[False, False, False, False],
    ).reset_index(drop=True)
