from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request

from backend.repositories.sqlite_repo import ReportRunRepository
from backend.services.artifacts import build_report_summary


router = APIRouter(prefix="/api/report")


@router.get("/summary")
async def report_summary(request: Request) -> dict:
    return build_report_summary(request.app.state.output_dir)


@router.get("/runs")
async def report_runs(request: Request) -> dict[str, list[dict]]:
    request.app.state.ensure_database()
    repo = ReportRunRepository(request.app.state.db_path)
    return {"runs": repo.list_runs()}


@router.post("/run")
async def run_report_job(request: Request) -> dict:
    if not request.app.state.run_lock.acquire(blocking=False):
        raise HTTPException(status_code=409, detail="report run already in progress")

    try:
        request.app.state.ensure_database()
        repo = ReportRunRepository(request.app.state.db_path)
        started_at = _now()
        run_id = repo.create_run(status="RUNNING", started_at=started_at)

        try:
            exit_code = int(request.app.state.runner())
        except Exception as exc:
            status = "FAILED"
            message = str(exc)
        else:
            status = "SUCCESS" if exit_code == 0 else "FAILED"
            message = f"exit_code={exit_code}"

        finished_at = _now()
        repo.finish_run(run_id, status=status, finished_at=finished_at, message=message)
        return {
            "id": run_id,
            "status": status,
            "started_at": started_at,
            "finished_at": finished_at,
            "message": message,
            "summary": build_report_summary(request.app.state.output_dir),
        }
    finally:
        request.app.state.run_lock.release()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()
