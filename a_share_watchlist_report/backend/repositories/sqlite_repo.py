import json
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


class ReportTableRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def replace_table(self, table_name: str, columns: list[str], rows: list[dict], updated_at: str) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM report_table_rows WHERE table_name = ?", (table_name,))
            connection.execute(
                """
                INSERT INTO report_table_metadata (table_name, columns_json, row_count, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(table_name) DO UPDATE SET
                    columns_json = excluded.columns_json,
                    row_count = excluded.row_count,
                    updated_at = excluded.updated_at
                """,
                (table_name, json.dumps(columns, ensure_ascii=False), len(rows), updated_at),
            )
            connection.executemany(
                """
                INSERT INTO report_table_rows (table_name, row_index, payload_json)
                VALUES (?, ?, ?)
                """,
                [
                    (table_name, index, json.dumps(row, ensure_ascii=False))
                    for index, row in enumerate(rows)
                ],
            )

    def read_table(
        self,
        table_name: str,
        limit: int = 200,
        offset: int = 0,
        search: str = "",
        sort_by: str = "",
        sort_dir: str = "asc",
    ) -> dict:
        with self._connect() as connection:
            metadata = connection.execute(
                """
                SELECT table_name, columns_json, row_count, updated_at
                FROM report_table_metadata
                WHERE table_name = ?
                """,
                (table_name,),
            ).fetchone()
            if metadata is None:
                return {
                    "name": table_name,
                    "exists": False,
                    "columns": [],
                    "row_count": 0,
                    "filtered_count": 0,
                    "rows": [],
                    "errors": [],
                    "source": "sqlite",
                    "limit": limit,
                    "offset": offset,
                }
            row_records = connection.execute(
                """
                SELECT payload_json
                FROM report_table_rows
                WHERE table_name = ?
                ORDER BY row_index ASC
                """,
                (table_name,),
            ).fetchall()

        rows = [json.loads(str(row["payload_json"])) for row in row_records]
        filtered_rows = self._filter_rows(rows, search)
        sorted_rows = self._sort_rows(filtered_rows, sort_by, sort_dir)
        paged_rows = sorted_rows[max(offset, 0) : max(offset, 0) + max(limit, 0)]
        return {
            "name": table_name,
            "exists": True,
            "columns": json.loads(str(metadata["columns_json"])),
            "row_count": int(metadata["row_count"]),
            "filtered_count": len(filtered_rows),
            "rows": paged_rows,
            "errors": [],
            "source": "sqlite",
            "updated_at": metadata["updated_at"],
            "limit": limit,
            "offset": offset,
        }

    def _filter_rows(self, rows: list[dict], search: str) -> list[dict]:
        query = search.strip().lower()
        if not query:
            return rows
        return [row for row in rows if query in " ".join(str(value).lower() for value in row.values()).lower()]

    def _sort_rows(self, rows: list[dict], sort_by: str, sort_dir: str) -> list[dict]:
        if not sort_by:
            return rows
        reverse = sort_dir.lower() == "desc"

        def sort_key(row: dict) -> tuple[int, float | str]:
            value = row.get(sort_by)
            if value is None or value == "":
                return (1, "")
            try:
                return (0, float(str(value).replace("%", "")))
            except ValueError:
                return (0, str(value))

        return sorted(rows, key=sort_key, reverse=reverse)

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
