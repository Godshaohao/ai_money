from pathlib import Path

import pandas as pd
from pandas.errors import EmptyDataError, ParserError

from backend.repositories.sqlite_repo import ReportTableRepository


def write_report_tables_to_sqlite(
    output_dir: Path,
    db_path: Path,
    table_files: dict[str, str],
    updated_at: str,
) -> list[str]:
    repo = ReportTableRepository(db_path)
    written: list[str] = []
    for table_name, filename in table_files.items():
        path = Path(output_dir) / filename
        if not path.exists():
            continue
        try:
            frame = pd.read_csv(path, dtype="string")
        except (EmptyDataError, ParserError, UnicodeDecodeError, OSError):
            continue
        normalized = frame.where(pd.notna(frame), None)
        repo.replace_table(
            table_name,
            columns=list(frame.columns),
            rows=normalized.to_dict(orient="records"),
            updated_at=updated_at,
        )
        written.append(table_name)
    return written
