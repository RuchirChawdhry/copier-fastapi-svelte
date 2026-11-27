import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Literal

from app.config import Settings

from .project import ROOT


def get_settings():
    return Settings()


def database_path():
    path = (ROOT / get_settings().database).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Development MCP only inspects workspace-local databases.")
    if not path.is_file():
        raise ValueError("Database does not exist; run task db:init if appropriate.")
    return path


def database_status(count_rows: bool = False, integrity: Literal["none", "quick", "full"] = "none") -> dict:
    """Inspect SQLite size and page statistics; row counts and integrity scans are opt-in."""
    path = database_path()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as connection:
        stats = {key: connection.execute(f"PRAGMA {key}").fetchone()[0]
                 for key in ("journal_mode", "user_version", "page_size", "page_count", "freelist_count")}
        if count_rows:
            tables = connection.execute("SELECT name FROM sqlite_schema WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall()
            stats["row_counts"] = {name: connection.execute('SELECT count(*) FROM "' + name.replace('"', '""') + '"').fetchone()[0]
                                   for (name,) in tables}
        if integrity != "none":
            pragma = "quick_check" if integrity == "quick" else "integrity_check"
            stats["integrity"] = [row[0] for row in connection.execute(f"PRAGMA {pragma}")]
    wal = Path(str(path) + "-wal")
    return {"path": path.relative_to(ROOT).as_posix(), "size_bytes": path.stat().st_size,
            "wal_bytes": wal.stat().st_size if wal.is_file() else 0, **stats}


def database_schema(table: str | None = None) -> dict:
    """Return table DDL, constraints, foreign keys, index columns, views and triggers; no records."""
    path = database_path()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as connection:
        connection.row_factory = sqlite3.Row
        objects = [dict(row) for row in connection.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_schema WHERE name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        tables = []
        for obj in objects:
            name = obj["name"]
            if obj["type"] != "table" or table is not None and name != table:
                continue
            indexes = [dict(row) for row in connection.execute("SELECT * FROM pragma_index_list(?)", (name,))]
            for index in indexes:
                index["columns"] = [dict(row) for row in connection.execute("SELECT * FROM pragma_index_xinfo(?)", (index["name"],))]
                index["sql"] = next((item["sql"] for item in objects if item["name"] == index["name"]), None)
            tables.append({"name": name, "sql": obj["sql"],
                           "columns": [dict(row) for row in connection.execute("SELECT * FROM pragma_table_xinfo(?)", (name,))],
                           "foreign_keys": [dict(row) for row in connection.execute("SELECT * FROM pragma_foreign_key_list(?)", (name,))],
                           "indexes": indexes})
    return {"tables": tables, "views": [obj for obj in objects if obj["type"] == "view"],
            "triggers": [obj for obj in objects if obj["type"] == "trigger" and (table is None or obj["tbl_name"] == table)]}
