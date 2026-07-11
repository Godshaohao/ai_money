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
