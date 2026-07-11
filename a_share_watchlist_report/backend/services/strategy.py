from pathlib import Path

from backend.repositories.sqlite_repo import StrategyRepository


def list_strategy_runs(db_path: Path, limit: int = 20) -> dict:
    return {"runs": StrategyRepository(db_path).list_runs(limit=limit)}


def list_strategy_candidates(
    db_path: Path,
    run_id: int | None = None,
    module: str = "",
    search: str = "",
    sort_by: str = "score",
    sort_dir: str = "desc",
    limit: int = 200,
    offset: int = 0,
) -> dict:
    return StrategyRepository(db_path).list_candidates(
        run_id=run_id,
        module=module,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=limit,
        offset=offset,
    )


def inspect_strategy_symbol(db_path: Path, symbol: str, run_id: int | None = None) -> dict:
    return StrategyRepository(db_path).inspect_symbol(symbol=symbol, run_id=run_id)
