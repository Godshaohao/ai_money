from collections.abc import Callable
from pathlib import Path
from threading import Lock

from fastapi import FastAPI

from backend.db.schema import initialize_database
from backend.routes.analysis import router as analysis_router
from backend.routes.health import router as health_router
from backend.routes.report import router as report_router
from backend.routes.securities import router as securities_router
from backend.routes.strategy import router as strategy_router
from backend.routes.tables import router as tables_router
from backend.services.report_runner import resolve_runner
from backend.services.analysis import AnalysisCache


ROOT = Path(__file__).resolve().parents[1]


def create_app(
    root: Path = ROOT,
    db_path: Path | None = None,
    runner: Callable[[], int] | None = None,
    initialize_on_create: bool = True,
) -> FastAPI:
    app_root = Path(root)
    database_path = Path(db_path) if db_path is not None else app_root / "data" / "workbench.sqlite"
    if initialize_on_create:
        initialize_database(database_path)

    app = FastAPI(title="A-share Research Workbench")
    app.state.root = app_root
    app.state.output_dir = app_root / "output"
    app.state.db_path = database_path
    app.state.runner = resolve_runner(app_root, runner)
    app.state.run_lock = Lock()
    app.state.analysis_cache = AnalysisCache()
    app.state.initialize_on_create = initialize_on_create
    app.state.ensure_database = lambda: initialize_database(database_path)
    app.include_router(analysis_router)
    app.include_router(health_router)
    app.include_router(report_router)
    app.include_router(securities_router)
    app.include_router(strategy_router)
    app.include_router(tables_router)
    return app


app = create_app(initialize_on_create=False)
