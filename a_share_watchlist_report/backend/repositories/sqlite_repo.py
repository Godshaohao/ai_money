import sqlite3
from pathlib import Path


class ReportRunRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def create_run(self, status: str, started_at: str) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO report_runs (status, started_at, finished_at, message)
                VALUES (?, ?, NULL, NULL)
                """,
                (status, started_at),
            )
            return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, finished_at: str, message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE report_runs
                SET status = ?, finished_at = ?, message = ?
                WHERE id = ?
                """,
                (status, finished_at, message, run_id),
            )

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, status, started_at, finished_at, message
                FROM report_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [dict(row) for row in rows]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
