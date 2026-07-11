from fastapi import APIRouter, HTTPException, Request

from backend.services.tables import read_report_table


router = APIRouter(prefix="/api/report/tables")


@router.get("/{table_name}")
async def report_table(
    table_name: str,
    request: Request,
    limit: int = 200,
    offset: int = 0,
    search: str = "",
    sort_by: str = "",
    sort_dir: str = "asc",
) -> dict:
    try:
        bounded_limit = min(max(limit, 1), 500)
        bounded_offset = max(offset, 0)
        return read_report_table(
            request.app.state.output_dir,
            table_name,
            limit=bounded_limit,
            offset=bounded_offset,
            search=search,
            sort_by=sort_by,
            sort_dir=sort_dir,
            db_path=request.app.state.db_path,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail="unknown report table") from exc
