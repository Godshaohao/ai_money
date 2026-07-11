import sqlite3
from pathlib import Path


def initialize_database(db_path: Path) -> None:
    """Create the SQLite database and required tables if they do not exist."""
    path = Path(db_path)
    path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(path) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS report_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                message TEXT
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS report_table_metadata (
                table_name TEXT PRIMARY KEY,
                columns_json TEXT NOT NULL,
                row_count INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS report_table_rows (
                table_name TEXT NOT NULL,
                row_index INTEGER NOT NULL,
                payload_json TEXT NOT NULL,
                PRIMARY KEY (table_name, row_index),
                FOREIGN KEY (table_name) REFERENCES report_table_metadata(table_name)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT,
                message TEXT,
                params_json TEXT NOT NULL
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                module TEXT NOT NULL,
                symbol TEXT NOT NULL,
                name TEXT NOT NULL,
                score REAL NOT NULL,
                label TEXT NOT NULL,
                risk_flags TEXT NOT NULL,
                reason TEXT NOT NULL,
                source_table TEXT NOT NULL,
                source_row_json TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES strategy_runs(id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                symbol TEXT NOT NULL,
                module TEXT NOT NULL,
                evidence_type TEXT NOT NULL,
                title TEXT NOT NULL,
                detail TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES strategy_runs(id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS strategy_run_metrics (
                run_id INTEGER PRIMARY KEY,
                metrics_json TEXT NOT NULL,
                FOREIGN KEY (run_id) REFERENCES strategy_runs(id)
                    ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_strategy_candidates_symbol
            ON strategy_candidates(symbol)
            """
        )
        connection.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_strategy_evidence_symbol
            ON strategy_evidence(symbol)
            """
        )
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS cli_tool_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tool_name TEXT NOT NULL,
                status TEXT NOT NULL,
                started_at TEXT NOT NULL,
                finished_at TEXT NOT NULL,
                args_json TEXT NOT NULL,
                result_json TEXT NOT NULL
            )
            """
        )
