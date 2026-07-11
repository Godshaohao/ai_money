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


class StrategyRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def create_run(self, strategy_name: str, status: str, started_at: str, params: dict) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO strategy_runs (strategy_name, status, started_at, finished_at, message, params_json)
                VALUES (?, ?, ?, NULL, NULL, ?)
                """,
                (strategy_name, status, started_at, json.dumps(params, ensure_ascii=False)),
            )
            return int(cursor.lastrowid)

    def finish_run(self, run_id: int, status: str, finished_at: str, message: str) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                UPDATE strategy_runs
                SET status = ?, finished_at = ?, message = ?
                WHERE id = ?
                """,
                (status, finished_at, message, run_id),
            )

    def replace_candidates(self, run_id: int, candidates: list[dict]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM strategy_candidates WHERE run_id = ?", (run_id,))
            connection.executemany(
                """
                INSERT INTO strategy_candidates (
                    run_id, module, symbol, name, score, label, risk_flags, reason, source_table, source_row_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        str(candidate.get("module", "")),
                        str(candidate.get("symbol", "")).zfill(6),
                        str(candidate.get("name", "")),
                        float(candidate.get("score", 0)),
                        str(candidate.get("label", "")),
                        str(candidate.get("risk_flags", "")),
                        str(candidate.get("reason", "")),
                        str(candidate.get("source_table", "")),
                        json.dumps(candidate.get("source_row", {}), ensure_ascii=False),
                    )
                    for candidate in candidates
                ],
            )

    def replace_evidence(self, run_id: int, evidence: list[dict]) -> None:
        with self._connect() as connection:
            connection.execute("DELETE FROM strategy_evidence WHERE run_id = ?", (run_id,))
            connection.executemany(
                """
                INSERT INTO strategy_evidence (
                    run_id, symbol, module, evidence_type, title, detail, payload_json
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        run_id,
                        str(item.get("symbol", "")).zfill(6),
                        str(item.get("module", "")),
                        str(item.get("evidence_type", "")),
                        str(item.get("title", "")),
                        str(item.get("detail", "")),
                        json.dumps(item.get("payload", {}), ensure_ascii=False),
                    )
                    for item in evidence
                ],
            )

    def replace_metrics(self, run_id: int, metrics: dict) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                INSERT INTO strategy_run_metrics (run_id, metrics_json)
                VALUES (?, ?)
                ON CONFLICT(run_id) DO UPDATE SET metrics_json = excluded.metrics_json
                """,
                (run_id, json.dumps(metrics, ensure_ascii=False)),
            )

    def list_runs(self, limit: int = 20) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT r.id, r.strategy_name, r.status, r.started_at, r.finished_at, r.message,
                       r.params_json, COALESCE(m.metrics_json, '{}') AS metrics_json
                FROM strategy_runs r
                LEFT JOIN strategy_run_metrics m ON m.run_id = r.id
                ORDER BY r.id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [self._run_from_row(row) for row in rows]

    def list_candidates(
        self,
        run_id: int | None = None,
        module: str = "",
        search: str = "",
        sort_by: str = "score",
        sort_dir: str = "desc",
        limit: int = 200,
        offset: int = 0,
    ) -> dict:
        latest_run_id = run_id if run_id is not None else self._latest_run_id()
        if latest_run_id is None:
            return {
                "run_id": None,
                "row_count": 0,
                "filtered_count": 0,
                "rows": [],
                "limit": limit,
                "offset": offset,
            }

        with self._connect() as connection:
            all_rows = connection.execute(
                """
                SELECT id, run_id, module, symbol, name, score, label, risk_flags, reason,
                       source_table, source_row_json
                FROM strategy_candidates
                WHERE run_id = ?
                ORDER BY id ASC
                """,
                (latest_run_id,),
            ).fetchall()

        rows = [self._candidate_from_row(row) for row in all_rows]
        filtered_rows = self._filter_candidates(rows, module, search)
        sorted_rows = self._sort_candidates(filtered_rows, sort_by, sort_dir)
        safe_offset = max(offset, 0)
        safe_limit = max(limit, 0)
        return {
            "run_id": latest_run_id,
            "row_count": len(rows),
            "filtered_count": len(filtered_rows),
            "rows": sorted_rows[safe_offset : safe_offset + safe_limit],
            "limit": limit,
            "offset": offset,
        }

    def inspect_symbol(self, symbol: str, run_id: int | None = None) -> dict:
        normalized_symbol = str(symbol).zfill(6)
        latest_run_id = run_id if run_id is not None else self._latest_run_id()
        if latest_run_id is None:
            return {"symbol": normalized_symbol, "exists": False, "candidates": [], "evidence": []}

        with self._connect() as connection:
            candidate_rows = connection.execute(
                """
                SELECT id, run_id, module, symbol, name, score, label, risk_flags, reason,
                       source_table, source_row_json
                FROM strategy_candidates
                WHERE run_id = ? AND symbol = ?
                ORDER BY score DESC, id ASC
                """,
                (latest_run_id, normalized_symbol),
            ).fetchall()
            evidence_rows = connection.execute(
                """
                SELECT id, run_id, symbol, module, evidence_type, title, detail, payload_json
                FROM strategy_evidence
                WHERE run_id = ? AND symbol = ?
                ORDER BY id ASC
                """,
                (latest_run_id, normalized_symbol),
            ).fetchall()

        candidates = [self._candidate_from_row(row) for row in candidate_rows]
        evidence = [self._evidence_from_row(row) for row in evidence_rows]
        return {
            "symbol": normalized_symbol,
            "exists": bool(candidates or evidence),
            "candidates": candidates,
            "evidence": evidence,
        }

    def _latest_run_id(self) -> int | None:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id FROM strategy_runs WHERE status = 'SUCCESS' ORDER BY id DESC LIMIT 1",
            ).fetchone()
        return int(row["id"]) if row is not None else None

    def _run_from_row(self, row: sqlite3.Row) -> dict:
        return {
            "id": int(row["id"]),
            "strategy_name": row["strategy_name"],
            "status": row["status"],
            "started_at": row["started_at"],
            "finished_at": row["finished_at"],
            "message": row["message"],
            "params": json.loads(str(row["params_json"])),
            "metrics": json.loads(str(row["metrics_json"])),
        }

    def _candidate_from_row(self, row: sqlite3.Row) -> dict:
        return {
            "id": int(row["id"]),
            "run_id": int(row["run_id"]),
            "module": row["module"],
            "symbol": row["symbol"],
            "name": row["name"],
            "score": float(row["score"]),
            "label": row["label"],
            "risk_flags": row["risk_flags"],
            "reason": row["reason"],
            "source_table": row["source_table"],
            "source_row": json.loads(str(row["source_row_json"])),
        }

    def _evidence_from_row(self, row: sqlite3.Row) -> dict:
        return {
            "id": int(row["id"]),
            "run_id": int(row["run_id"]),
            "symbol": row["symbol"],
            "module": row["module"],
            "evidence_type": row["evidence_type"],
            "title": row["title"],
            "detail": row["detail"],
            "payload": json.loads(str(row["payload_json"])),
        }

    def _filter_candidates(self, rows: list[dict], module: str, search: str) -> list[dict]:
        module_query = module.strip()
        query = search.strip().lower()
        filtered = [row for row in rows if not module_query or row["module"] == module_query]
        if not query:
            return filtered
        return [
            row
            for row in filtered
            if query in " ".join(str(value).lower() for value in row.values()).lower()
        ]

    def _sort_candidates(self, rows: list[dict], sort_by: str, sort_dir: str) -> list[dict]:
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


class CliAuditRepository:
    def __init__(self, db_path: Path) -> None:
        self.db_path = Path(db_path)

    def record_call(
        self,
        tool_name: str,
        status: str,
        started_at: str,
        finished_at: str,
        args: dict,
        result: dict,
    ) -> int:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO cli_tool_runs (
                    tool_name, status, started_at, finished_at, args_json, result_json
                )
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    tool_name,
                    status,
                    started_at,
                    finished_at,
                    json.dumps(args, ensure_ascii=False),
                    json.dumps(result, ensure_ascii=False),
                ),
            )
            return int(cursor.lastrowid)

    def list_calls(self, limit: int = 20) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, tool_name, status, started_at, finished_at, args_json, result_json
                FROM cli_tool_runs
                ORDER BY id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            {
                "id": int(row["id"]),
                "tool_name": row["tool_name"],
                "status": row["status"],
                "started_at": row["started_at"],
                "finished_at": row["finished_at"],
                "args": json.loads(str(row["args_json"])),
                "result": json.loads(str(row["result_json"])),
            }
            for row in rows
        ]

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection
