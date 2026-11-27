import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path


class Database:
    def __init__(self, path: Path):
        self.path = path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        try:
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=NORMAL")
            with connection:
                yield connection
        finally:
            connection.close()

    def initialize(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as connection:
            connection.execute("PRAGMA journal_mode=WAL")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)"
            )

    def ready(self) -> bool:
        with self.connect() as connection:
            connection.execute("SELECT id FROM notes LIMIT 1").fetchall()
            return connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"

    def notes(self) -> list[dict]:
        with self.connect() as connection:
            return [dict(row) for row in connection.execute("SELECT id, text FROM notes ORDER BY id")]

    def add_note(self, text: str) -> dict:
        with self.connect() as connection:
            cursor = connection.execute("INSERT INTO notes (text) VALUES (?)", (text,))
            return {"id": cursor.lastrowid, "text": text}

    def delete_note(self, note_id: int) -> bool:
        with self.connect() as connection:
            return connection.execute("DELETE FROM notes WHERE id = ?", (note_id,)).rowcount > 0

