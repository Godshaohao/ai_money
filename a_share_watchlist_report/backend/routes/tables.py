from fastapi import APIRouter, HTTPException, Request

from backend.services.tables import read_report_table


router = APIRouter(prefix="/api/report/tables")


@router.get("/{table_name}")
async def report_table(table_name: str, request: Request) -> dict:
    try:
        return read_report_table(request.app.state.output_dir, table_name)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="unknown report table") from exc
