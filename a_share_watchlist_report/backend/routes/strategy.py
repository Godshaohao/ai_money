from fastapi import APIRouter, Request

from backend.services.strategy import inspect_strategy_symbol, list_strategy_candidates, list_strategy_runs


router = APIRouter(prefix="/api/strategy")


@router.get("/runs")
async def strategy_runs(request: Request, limit: int = 20) -> dict:
    request.app.state.ensure_database()
    return list_strategy_runs(request.app.state.db_path, limit=min(max(limit, 1), 100))


@router.get("/candidates")
async def strategy_candidates(
    request: Request,
    run_id: int | None = None,
    module: str = "",
    search: str = "",
    sort_by: str = "score",
    sort_dir: str = "desc",
    limit: int = 200,
    offset: int = 0,
) -> dict:
    request.app.state.ensure_database()
    return list_strategy_candidates(
        request.app.state.db_path,
        run_id=run_id,
        module=module,
        search=search,
        sort_by=sort_by,
        sort_dir=sort_dir,
        limit=min(max(limit, 1), 500),
        offset=max(offset, 0),
    )


@router.get("/securities/{symbol}")
async def strategy_symbol(symbol: str, request: Request, run_id: int | None = None) -> dict:
    request.app.state.ensure_database()
    return inspect_strategy_symbol(request.app.state.db_path, symbol=symbol, run_id=run_id)
