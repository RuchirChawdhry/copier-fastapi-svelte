import asyncio
import json
import sqlite3
import sys
from importlib.metadata import version
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from tools.dev_mcp import browser, database, verification
from tools.dev_mcp.project import inspect_endpoint, project_context
from tools.dev_mcp.server import create_server


def test_fastmcp_version():
    assert version("fastmcp") == "4.2.6"


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_mcp_registration_and_calls(mode):
    async def check():
        async with Client(create_server(), mode=mode) as client:
            tools = {tool.name for tool in await client.list_tools()}
            assert {"project_context", "doctor", "list_pages", "list_endpoints",
                    "inspect_endpoint", "database_schema", "browser_diagnostics",
                    "capture_screenshot", "accessibility_audit", "run_checks",
                    "run_tests", "test_results"} <= tools
            result = await client.call_tool("project_context")
            assert not result.is_error
            assert result.structured_content["name"] == project_context()["name"]
            result = await client.call_tool("inspect_endpoint", {"method": "GET", "path": "/api/notes"})
            assert not result.is_error
            assert "Note" in result.structured_content["schemas"]

    asyncio.run(check())


@pytest.mark.parametrize("mode", ["auto", "legacy"])
def test_stdio_protocol(mode):
    async def check():
        transport = StdioTransport(
            command=sys.executable, args=["-m", "tools.dev_mcp"],
            cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False,
        )
        async with Client(transport, mode=mode, timeout=20) as client:
            assert client.server_info.name.endswith("-dev")
            assert client.protocol_version
            if mode == "legacy":
                assert client.initialize_result is not None
                assert client.initialize_result.server_info.name.endswith("-dev")
            else:
                assert client.protocol_version == "2026-07-28"
            tools = await client.list_tools()
            assert "project_context" in {tool.name for tool in tools}
            result = await client.call_tool("project_context")
            assert not result.is_error
            assert result.structured_content["name"] == project_context()["name"]

    asyncio.run(asyncio.wait_for(check(), timeout=45))


def test_screenshot_image_content(monkeypatch):
    import base64

    # Test the MCP image serialization separately from the live Chromium integration test.
    png = base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jR1sAAAAASUVORK5CYII="
    )
    monkeypatch.setattr(browser, "probe", lambda *args: {"image": base64.b64encode(png).decode()})

    async def check():
        async with Client(create_server()) as client:
            result = await client.call_tool("capture_screenshot")
            assert not result.is_error
            image = result.content[0]
            assert image.type == "image"
            assert image.mime_type == "image/png"
            assert base64.b64decode(image.data) == png

    asyncio.run(check())


def test_contract_inspection():
    endpoint = inspect_endpoint("POST", "/api/notes")
    assert "NoteInput" in endpoint["schemas"]
    assert "Note" in endpoint["schemas"]
    with pytest.raises(ValueError, match="Unknown endpoint"):
        inspect_endpoint("GET", "/nonexistent")


def test_read_only_database(tmp_path, monkeypatch):
    path = tmp_path / "dev.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE notes(id INTEGER PRIMARY KEY, text TEXT)")
        connection.execute("INSERT INTO notes VALUES(1, 'do not expose')")
    monkeypatch.setattr(database, "ROOT", tmp_path)
    monkeypatch.setattr(database, "get_settings", lambda: type("Settings", (), {"database": path})())
    before = path.read_bytes()
    assert database.database_status()["path"] == "dev.sqlite"
    result = database.database_schema()
    assert result["tables"][0]["name"] == "notes"
    assert "do not expose" not in json.dumps(result)
    assert path.read_bytes() == before
    monkeypatch.setattr(database, "get_settings", lambda: type("Settings", (), {"database": Path("/outside.sqlite")})())
    with pytest.raises(ValueError, match="workspace-local"):
        database.database_schema()


def test_verification_allowlist_and_reports(tmp_path, monkeypatch):
    with pytest.raises(ValueError, match="Unsupported"):
        verification.run_task("arbitrary command")
    monkeypatch.setattr(verification, "ROOT", tmp_path)
    (tmp_path / "backend.xml").write_text(
        '<testsuite><testcase name="example"><failure message="password=hidden"/></testcase>'
        '<testcase name="passing"/></testsuite>', encoding="utf-8"
    )
    report = verification.test_results()["reports"][0]
    assert report["tests"] == 2
    assert report["failures"] == 1
    assert "hidden" not in json.dumps(report)
