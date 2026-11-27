import asyncio
import json
import sqlite3
import sys
import time
from importlib.metadata import version
from pathlib import Path

import pytest
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from scripts import verify_tests
from tools.dev_mcp import database, environment, verification
from tools.dev_mcp.project import inspect_endpoint, list_components, list_endpoints, list_pages, project_context
from tools.dev_mcp.server import create_server


def test_fastmcp_version():
    assert version("fastmcp") == "4.2.6"


def test_mcp_registration_and_calls():
    async def check():
        async with Client(create_server(), mode="auto") as client:
            tools = {tool.name for tool in await client.list_tools()}
            assert {"project_context", "doctor", "list_pages", "list_endpoints",
                    "inspect_endpoint", "database_schema", "run_checks",
                    "run_tests", "test_results"} <= tools
            assert len(tools) == 15
            assert client.protocol_version == "2026-07-28"
            result = await client.call_tool("project_context")
            assert not result.is_error
            assert result.structured_content["name"] == project_context()["name"]
            result = await client.call_tool("inspect_endpoint", {"method": "GET", "path": "/api/notes"})
            assert not result.is_error
            assert "Note" in result.structured_content["schemas"]

    asyncio.run(check())


def test_stdio_protocol():
    async def check():
        transport = StdioTransport(
            command=sys.executable, args=["-m", "tools.dev_mcp"],
            cwd=str(Path(__file__).resolve().parents[1]), keep_alive=False,
        )
        async with Client(transport, mode="auto", timeout=20) as client:
            assert client.server_info.name.endswith("-dev")
            assert client.protocol_version == "2026-07-28"
            tools = await client.list_tools()
            assert "project_context" in {tool.name for tool in tools}
            result = await client.call_tool("project_context")
            assert not result.is_error
            assert result.structured_content["name"] == project_context()["name"]

    asyncio.run(asyncio.wait_for(check(), timeout=45))


def test_contract_inspection():
    endpoint = inspect_endpoint("POST", "/api/notes")
    assert "NoteInput" in endpoint["schemas"]
    assert "Note" in endpoint["schemas"]
    assert endpoint["implementation"]["source"] == "app/api.py"
    assert endpoint["implementation"]["line"] > 0
    assert endpoint["frontend_references"]
    assert endpoint["test_references"]
    assert any(item["path"] == "/api/notes" and item.get("handler") for item in list_endpoints())
    with pytest.raises(ValueError, match="Unknown endpoint"):
        inspect_endpoint("GET", "/nonexistent")


def test_read_only_database(tmp_path, monkeypatch):
    path = tmp_path / "dev.sqlite"
    with sqlite3.connect(path) as connection:
        connection.execute("CREATE TABLE notes(id INTEGER PRIMARY KEY, text TEXT)")
        connection.execute("INSERT INTO notes VALUES(1, 'do not expose')")
        connection.execute("CREATE TABLE tags(id INTEGER PRIMARY KEY, note_id INTEGER REFERENCES notes(id))")
        connection.execute("CREATE INDEX tags_note ON tags(note_id)")
        connection.execute("CREATE VIEW note_ids AS SELECT id FROM notes")
        connection.execute("CREATE TRIGGER notes_cleanup AFTER DELETE ON notes BEGIN DELETE FROM tags WHERE note_id=OLD.id; END")
    monkeypatch.setattr(database, "ROOT", tmp_path)
    monkeypatch.setattr(database, "get_settings", lambda: type("Settings", (), {"database": path})())
    before = path.read_bytes()
    status = database.database_status(count_rows=True, integrity="quick")
    assert status["path"] == "dev.sqlite"
    assert status["row_counts"]["notes"] == 1
    assert status["page_size"] > 0
    assert status["integrity"] == ["ok"]
    result = database.database_schema()
    assert result["tables"][0]["name"] == "notes"
    tags = database.database_schema(table="tags")["tables"][0]
    assert tags["foreign_keys"][0]["table"] == "notes"
    assert any(column["name"] == "note_id" for column in tags["indexes"][0]["columns"])
    assert result["views"][0]["name"] == "note_ids"
    assert result["triggers"][0]["name"] == "notes_cleanup"
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



def test_project_and_component_discovery():
    context = project_context()
    assert context["version"]
    assert context["features"]
    assert "check" in {task["name"] for task in context["commands"]}
    pages = {page["id"]: page for page in list_pages()}
    assert pages["workspace"]["label"] == "Overview"
    assert pages["workspace"]["source"] == "frontend/src/pages/Overview.svelte"
    assert pages["workspace"]["route"] is None
    components = list_components(search="NoteForm", category="application")
    form = next(row for row in components["components"] if row["name"] == "NoteForm")
    assert form["props"]
    assert any("Overview.svelte" in path for path in form["imported_by"])


def test_contract_comparison_does_not_modify_generated_types():
    root = Path(__file__).resolve().parents[1]
    types = root / "frontend/src/lib/generated/api.d.ts"
    if not types.is_file():
        pytest.skip("Generated types require task install")
    before = types.read_bytes()
    report = verification.check_api_contract()
    assert report["ok"], report
    assert types.read_bytes() == before


def test_targeted_test_selection(tmp_path, monkeypatch):
    monkeypatch.setattr(verify_tests, "ROOT", tmp_path)
    tests = tmp_path / "tests"
    tests.mkdir()
    file = tests / "test_example.py"
    file.touch()
    args, cwd = verify_tests.test_command("backend", ["tests/test_example.py"], "example", True)
    assert cwd == tmp_path
    assert "-k" in args and "--lf" in args
    assert file.as_posix() in args
    with pytest.raises(ValueError, match="Test file"):
        verify_tests.test_command("backend", ["pyproject.toml"])


def test_report_freshness(tmp_path, monkeypatch):
    monkeypatch.setattr(verification, "ROOT", tmp_path)
    report = tmp_path / "backend.xml"
    report.write_text('<testsuite><testcase name="test" file="tests/test_a.py" line="3" time="1.5"><failure message="oops">trace</failure></testcase></testsuite>')
    tests = tmp_path / "tests"
    tests.mkdir()
    source = tests / "test_a.py"
    source.touch()
    import os

    os.utime(source, (time.time() + 5, time.time() + 5))
    result = verification.test_results("backend")["reports"][0]
    assert result["stale"]
    assert result["duration_seconds"] == 1.5
    assert result["failed_tests"][0]["file"] == "tests/test_a.py"
    assert result["failed_tests"][0]["traceback"] == "trace"


def test_structured_git_status(tmp_path, monkeypatch):
    import shutil
    import subprocess

    if not shutil.which("git"):
        pytest.skip("Git not installed")
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=tmp_path, check=True)
    (tmp_path / "staged.txt").write_text("staged")
    subprocess.run(["git", "add", "staged.txt"], cwd=tmp_path, check=True)
    (tmp_path / "untracked.txt").write_text("untracked")
    monkeypatch.setattr(environment, "ROOT", tmp_path)
    result = environment.git_status()
    assert result["staged"] == 1
    assert result["untracked"] == 1
    assert {row["path"] for row in result["files"]} == {"staged.txt", "untracked.txt"}
