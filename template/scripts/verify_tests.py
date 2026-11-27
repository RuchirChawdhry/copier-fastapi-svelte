"""Shared Task/MCP test runner; selection is passed as JSON, never shell fragments."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_command(scope, files=(), match="", failed_only=False):
    base = ROOT / ("tests" if scope == "backend" else "frontend/tests")
    selected = []
    for file in files:
        path = (ROOT / file).resolve()
        if not path.is_relative_to(base) or not path.is_file():
            raise ValueError(f"Test file must exist under {base.relative_to(ROOT)}: {file}")
        selected.append(path.as_posix())
    if scope == "backend":
        args = [sys.executable, "-m", "pytest", "-q", "--benchmark-disable",
                "--junitxml=backend.xml", "-o", "junit_family=xunit1"]
        if match:
            args.extend(["-k", match])
        if failed_only:
            args.extend(["--lf", "--last-failed-no-failures=none"])
        return args + selected, ROOT
    if scope != "browser":
        raise ValueError("Unsupported test scope")
    args = [shutil.which("pnpm") or "pnpm", "exec", "playwright", "test", "--reporter=list,junit"]
    if match:
        args.extend(["--grep", match])
    if failed_only:
        args.append("--last-failed")
    # Playwright treats positional paths as regexes.
    import re

    args.extend(re.escape(Path(file).relative_to(ROOT / "frontend").as_posix()) + "$" for file in selected)
    return args, ROOT / "frontend"


def main():
    scope = sys.argv[1]
    options = json.loads(os.environ.get("DEV_TEST_SELECTION", "{}"))
    command, cwd = test_command(scope, **options)
    env = {**os.environ, "PLAYWRIGHT_JUNIT_OUTPUT_FILE": "browser.xml"}
    report = ROOT / ("backend.xml" if scope == "backend" else "frontend/browser.xml")
    report.unlink(missing_ok=True)
    return subprocess.run(command, cwd=cwd, env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
