from fastapi import APIRouter, Request

from backend.services.security_detail import read_security_detail


router = APIRouter(prefix="/api/report/securities")


@router.get("/{symbol}")
async def security_detail(symbol: str, request: Request) -> dict:
    return read_security_detail(request.app.state.db_path, symbol)
