import sqlite3

from fastapi.testclient import TestClient

from app.api import app
from app.config import get_settings


def test_health_and_notes():
    with TestClient(app) as client:
        assert client.get("/api/health/live").json() == {"status": "ok"}
        assert client.get("/api/health").status_code == 200
        response = client.post("/api/notes", json={"text": "Example"})
        assert response.status_code == 201
        note = response.json()
        assert note in client.get("/api/notes").json()
        assert client.delete(f"/api/notes/{note['id']}").status_code == 204
        assert client.delete(f"/api/notes/{note['id']}").status_code == 404
        assert client.post("/api/notes", json={"text": ""}).status_code == 422
        with sqlite3.connect(get_settings().database) as connection:
            assert connection.execute("PRAGMA journal_mode").fetchone()[0] == "wal"


def test_mcp_initialization():
    with TestClient(app) as client:
        response = client.post(
            "/mcp/",
            headers={"Accept": "application/json, text/event-stream"},
            json={
                "jsonrpc": "2.0", "id": 1, "method": "initialize",
                "params": {
                    "protocolVersion": "2025-03-26",
                    "capabilities": {},
                    "clientInfo": {"name": "template-test", "version": "1.0"},
                },
            },
        )
        assert response.status_code == 200
        assert "protocolVersion" in response.text
        assert "serverInfo" in response.text
