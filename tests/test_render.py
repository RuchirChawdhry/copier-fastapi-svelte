from itertools import product
from pathlib import Path

import pytest
from copier import run_copy

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("jobs,terminal,events,mcp,schema_forms,rss", list(product([False, True], repeat=6)))
def test_options(tmp_path, jobs, terminal, events, mcp, schema_forms, rss):
    run_copy(str(ROOT), str(tmp_path), defaults=True, vcs_ref="HEAD", data={
        "project_name": "Example App", "enable_jobs": jobs, "enable_terminal": terminal, "enable_events": events, "enable_mcp": mcp, "enable_schema_forms": schema_forms, "enable_rss": rss,
    })
    assert (tmp_path / ".copier-answers.yml").is_file()
    assert (tmp_path / "app/jobs.py").exists() == jobs
    assert (tmp_path / "compose.yml").exists() == jobs
    assert (tmp_path / "frontend/src/lib/Terminal.svelte").exists() == terminal
    dependencies = (tmp_path / "pyproject.toml").read_text()
    for name in ("taskiq", "taskiq-redis", "taskiq-fastapi"):
        assert (f'"{name}"' in dependencies) == jobs
    assert (tmp_path / "app/events.py").exists() == events
    assert ("sse-starlette" in dependencies) == events
    assert ("fastmcp" in dependencies) == mcp
    assert (tmp_path / "app/mcp.py").exists() == mcp
    assert (tmp_path / "tests/test_mcp.py").exists() == mcp
    assert ("/mcp" in (tmp_path / "Caddyfile").read_text()) == mcp
    assert ("/mcp" in (tmp_path / "frontend/vite.config.ts").read_text()) == mcp
    assert ("ttyd" in (tmp_path / "Taskfile.yml").read_text()) == terminal
    assert ("basic_auth" in (tmp_path / "Caddyfile").read_text()) == terminal
    assert (tmp_path / "frontend/src/App.svelte").exists()
    frontend = (tmp_path / "frontend/package.json").read_text()
    assert ("@sjsf/form" in frontend) == schema_forms
    assert (tmp_path / "frontend/src/lib/SchemaNoteForm.svelte").exists() == schema_forms
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
