import sqlite3

from app.config import get_settings


def test_health_and_notes(client):
    assert client.get("/api/health/live").json() == {"status": "ok"}
    assert client.get("/api/health").status_code == 200
    response = client.post("/api/notes", json={"text": "Example"})
    assert response.status_code == 201
    note = response.json()
    assert note['created_at'].endswith('Z')
    assert note in client.get("/api/notes").json()
    assert client.delete(f"/api/notes/{note['id']}").status_code == 204
    assert client.delete(f"/api/notes/{note['id']}").status_code == 404
    assert client.post("/api/notes", json={"text": ""}).status_code == 422
    with sqlite3.connect(get_settings().database) as connection:
        assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_diagnostics(client):
    response = client.get("/api/diagnostics")
    assert response.status_code == 200
    data = response.json()
    assert 0 <= data["cpu_percent"] <= 100
    assert 0 < data["memory_used_bytes"] <= data["memory_total_bytes"]
    assert 0 < data["process_rss_bytes"]


def test_legacy_note_migration(tmp_path):
    from app.db import Database

    path = tmp_path / "legacy.sqlite3"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE notes (id INTEGER PRIMARY KEY, text TEXT NOT NULL)")
        connection.execute("INSERT INTO notes (text) VALUES ('Legacy note')")
    database = Database(path)
    database.initialize()
    database.initialize()
    assert database.notes() == [{"id": 1, "text": "Legacy note", "created_at": None}]
    assert database.add_note("New note")["created_at"].endswith("Z")
