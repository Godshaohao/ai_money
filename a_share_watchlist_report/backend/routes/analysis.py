from fastapi import APIRouter, Request

from backend.services.analysis import build_sector_workbench, build_stock_review


router = APIRouter(prefix="/api/analysis")


@router.get("/sectors")
async def sector_workbench(request: Request) -> dict:
    return build_sector_workbench(request.app.state.output_dir, cache=request.app.state.analysis_cache)


@router.get("/stocks/{symbol}")
async def stock_review(symbol: str, request: Request) -> dict:
    request.app.state.ensure_database()
    return build_stock_review(
        request.app.state.output_dir,
        request.app.state.db_path,
        symbol,
        cache=request.app.state.analysis_cache,
    )
