import sqlite3
from contextlib import closing

from app.config import get_settings

from .project import ROOT


def database_path():
    path = (ROOT / get_settings().database).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError("Development MCP only inspects workspace-local databases.")
    if not path.is_file():
        raise ValueError("Database does not exist; run task db:init if appropriate.")
    return path


def database_status() -> dict:
    """Inspect the configured workspace SQLite database without creating or writing it."""
    path = database_path()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as connection:
        journal = connection.execute("PRAGMA journal_mode").fetchone()[0]
        version = connection.execute("PRAGMA user_version").fetchone()[0]
    return {"path": path.relative_to(ROOT).as_posix(), "journal_mode": journal,
            "user_version": version, "size_bytes": path.stat().st_size}


def database_schema() -> dict:
    """List application tables, columns and indexes; never return record contents."""
    path = database_path()
    with closing(sqlite3.connect(path.as_uri() + "?mode=ro", uri=True, timeout=2)) as connection:
        connection.row_factory = sqlite3.Row
        tables = [row["name"] for row in connection.execute(
            "SELECT name FROM sqlite_schema WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name"
        )]
        return {"tables": [{
            "name": name,
            "columns": [dict(row) for row in connection.execute("SELECT * FROM pragma_table_xinfo(?)", (name,))],
            "indexes": [dict(row) for row in connection.execute("SELECT * FROM pragma_index_list(?)", (name,))],
        } for name in tables]}


def database_indexes() -> list[dict]:
    """List table indexes using the same read-only schema inspection."""
    return [{"table": table["name"], "indexes": table["indexes"]}
            for table in database_schema()["tables"]]
