import json
import subprocess
import tomllib
from itertools import combinations, product
from pathlib import Path

import pytest
from packaging.requirements import Requirement
from copier import run_copy

ROOT = Path(__file__).resolve().parents[1]


FLAGS = ("jobs", "terminal", "events", "mcp", "schema_forms", "rss", "ntfy")
MATRIX = json.loads((ROOT / "tests/feature-matrix.json").read_text())["include"]


def test_pairwise_coverage():
    from yaml import safe_load

    config = safe_load((ROOT / "copier.yml").read_text())
    assert {f"enable_{flag}" for flag in FLAGS} == {
        name for name, value in config.items()
        if isinstance(value, dict) and value.get("type") == "bool"
    }
    assert any(all(not row[flag] for flag in FLAGS) for row in MATRIX)
    assert any(all(row[flag] for flag in FLAGS) for row in MATRIX)
    for left, right in combinations(FLAGS, 2):
        assert {(row[left], row[right]) for row in MATRIX} == set(product((False, True), repeat=2))


@pytest.mark.parametrize(",".join(FLAGS), [
    pytest.param(*(row[flag] for flag in FLAGS), id=row["name"]) for row in MATRIX
])
def test_options(tmp_path, jobs, terminal, events, mcp, schema_forms, rss, ntfy):
    run_copy(str(ROOT), str(tmp_path), defaults=True, vcs_ref="HEAD", data={
        "project_name": "Example App", "enable_jobs": jobs, "enable_terminal": terminal, "enable_events": events, "enable_mcp": mcp, "enable_schema_forms": schema_forms, "enable_rss": rss, "enable_ntfy": ntfy,
    })
    assert (tmp_path / ".copier-answers.yml").is_file()
    assert (tmp_path / "app/jobs.py").exists() == jobs
    assert (tmp_path / "compose.yml").exists() == jobs
    assert (tmp_path / "frontend/src/lib/features/terminal/Terminal.svelte").exists() == terminal
    dependencies = (tmp_path / "pyproject.toml").read_text()
    manifest = tomllib.loads(dependencies)
    runtime = {req.name: req for value in manifest["project"]["dependencies"]
               if (req := Requirement(value))}
    dev = {req.name: req for value in manifest["dependency-groups"]["dev"]
           if (req := Requirement(value))}
    for name in ("taskiq", "taskiq-redis", "taskiq-fastapi"):
        assert (name in runtime) == jobs
    assert (tmp_path / "app/events.py").exists() == events
    assert ("sse-starlette" in runtime) == events
    assert ("fastmcp" in runtime) == mcp
    assert "fastmcp" in dev
    assert len(list(dev["fastmcp"].specifier)) == 1
    assert next(iter(dev["fastmcp"].specifier)).operator == "=="
    if mcp:
        assert runtime["fastmcp"] == dev["fastmcp"]
    assert manifest["tool"]["hatch"]["build"]["targets"]["wheel"]["packages"] == ["app"]
    assert "/tools" in manifest["tool"]["hatch"]["build"]["targets"]["sdist"]["exclude"]
    assert (tmp_path / "tools/dev_mcp/server.py").is_file()
    assert (tmp_path / "tests/test_dev_mcp.py").is_file()
    assert (tmp_path / "frontend/scripts/dev-browser.mjs").is_file()
    assert (tmp_path / "app/mcp.py").exists() == mcp
    assert (tmp_path / "tests/test_mcp.py").exists() == mcp
    assert ("/mcp" in (tmp_path / "Caddyfile").read_text()) == mcp
    assert ("/mcp" in (tmp_path / "frontend/vite.config.ts").read_text()) == mcp
    assert ("ttyd" in (tmp_path / "Taskfile.yml").read_text()) == terminal
    assert ("basic_auth" in (tmp_path / "Caddyfile").read_text()) == terminal
    source = tmp_path / "frontend/src"
    for name in (
        "App.svelte", "pages/Overview.svelte", "pages/Settings.svelte", "pages/Diagnostics.svelte",
        "lib/shell/WorkspaceHeader.svelte", "lib/shell/WorkspaceSidebar.svelte",
        "lib/shell/CommandPalette.svelte", "lib/shell/PageNavigation.svelte",
        "lib/shell/ResourceNavigation.svelte", "lib/settings/AppearanceSettings.svelte",
        "lib/settings/NotificationSettings.svelte", "lib/settings/AccessibilitySettings.svelte",
        "lib/features/notes/NoteForm.svelte", "lib/features/notes/NotesTable.svelte",
        "lib/features/notes/NoteDetails.svelte", "lib/features/notes/workspace.svelte.ts",
    ):
        assert (source / name).is_file(), name
    for name in ("WorkspaceHeader", "WorkspaceSidebar", "NoteForm", "NotesTable", "Diagnostics"):
        assert not (source / f"lib/{name}.svelte").exists()
    frontend = (tmp_path / "frontend/package.json").read_text()
    assert ("@sjsf/form" in frontend) == schema_forms
    assert (tmp_path / "frontend/src/lib/features/notes/SchemaNoteForm.svelte").exists() == schema_forms
    assert "@tanstack/svelte-form" in frontend
    assert "@sveltejs/kit" not in frontend
    assert "formsnap" not in frontend
    assert (tmp_path / "frontend/index.html").exists()


    assert ("feedgenerator" in dependencies) == rss
    assert (tmp_path / "app/rss.py").exists() == rss
    assert (tmp_path / "tests/test_rss.py").exists() == rss
    assert ("/feed.rss" in (tmp_path / "frontend/index.html").read_text()) == rss
    assert ("/feed.rss" in (tmp_path / "Caddyfile").read_text()) == rss
    assert ("/feed.rss" in (tmp_path / "frontend/vite.config.ts").read_text()) == rss

    taskfile = (tmp_path / "Taskfile.yml").read_text()
    assert ("rss:publish:" in taskfile) == rss
    assert "{{.CLI_ARGS}}" in taskfile
    assert "task: browser:install" in taskfile
    assert "test:e2e:ci:" in taskfile

    assert (tmp_path / "app/ntfy.py").exists() == ntfy
    assert (tmp_path / "tests/test_ntfy.py").exists() == ntfy
    assert ("ntfy:send:" in taskfile) == ntfy
    assert "doctor:json:" in taskfile
    assert "mcp:dev:" in taskfile
    assert "mcp:dev:check:" in taskfile
    assert (tmp_path / "scripts/doctor.py").is_file()
    assert ("httpx" in runtime) == ntfy
    json.loads(frontend)
    assert "standard" in runtime["uvicorn"].extras
    assert "uv sync --locked" in taskfile
    assert "pnpm install --frozen-lockfile" in taskfile
    assert "deps:check:" in taskfile
    if (ROOT / "release-locks.json").is_file():
        assert (tmp_path / "uv.lock").is_file()
        assert (tmp_path / "frontend/pnpm-lock.yaml").is_file()
        assert any(package["name"] == "example-app" for package in tomllib.loads(
            (tmp_path / "uv.lock").read_text()
        )["package"])
    subprocess.run(["task", "--list-all"], cwd=tmp_path, check=True)
    subprocess.run(["ruff", "check", "app", "tests", "scripts", "tools"], cwd=tmp_path, check=True)
