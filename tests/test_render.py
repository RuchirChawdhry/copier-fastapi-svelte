from itertools import product
from pathlib import Path

import pytest
from copier import run_copy

ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.parametrize("jobs,terminal", list(product([False, True], repeat=2)))
def test_options(tmp_path, jobs, terminal):
    run_copy(str(ROOT), str(tmp_path), defaults=True, vcs_ref="HEAD", data={
        "project_name": "Example App", "enable_jobs": jobs, "enable_terminal": terminal,
    })
    assert (tmp_path / ".copier-answers.yml").is_file()
    assert (tmp_path / "app/jobs.py").exists() == jobs
    assert (tmp_path / "compose.yml").exists() == jobs
    assert (tmp_path / "frontend/src/lib/Terminal.svelte").exists() == terminal
    assert ("taskiq" in (tmp_path / "pyproject.toml").read_text()) == jobs
    assert ("ttyd" in (tmp_path / "Taskfile.yml").read_text()) == terminal
    assert ("basic_auth" in (tmp_path / "Caddyfile").read_text()) == terminal
    assert (tmp_path / "frontend/src/App.svelte").exists()

