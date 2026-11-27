"""Read-only environment diagnostics; runnable before project dependencies are installed."""

import argparse
import json
import os
import shutil
import socket
import sqlite3
import subprocess
import sys
from contextlib import closing
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def inspect_environment() -> list[dict[str, str]]:
    from scripts.dev_config import configuration

    config = configuration()
    checks = []

    def add(code, status, detail, remediation=""):
        checks.append(dict(code=code, status=status, detail=detail, remediation=remediation))

    def command(args, cwd=ROOT):
        try:
            executable = shutil.which(args[0])
            if not executable:
                return None
            result = subprocess.run(
                [executable, *args[1:]], cwd=cwd, capture_output=True, text=True, timeout=10
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except (OSError, subprocess.TimeoutExpired):
            return None

    for name, help_text in {
        "uv": "Install uv: https://docs.astral.sh/uv/getting-started/installation/",
        "node": "Install Node.js 24 or newer.",
        "pnpm": "Enable pnpm with Corepack.",
        "task": "Install Go Task.",
    }.items():
        version = command([name, "--version"])
        supported = bool(version) and (
            name != "node" or int(version.lstrip("v").split(".")[0]) >= 24
        )
        add(name, "ok" if supported else "error", version or "Unavailable", help_text if not supported else "")

    python_file = ROOT / ".python-version"
    required = python_file.read_text().strip() if python_file.is_file() else "3.14"
    python = command(["uv", "python", "find", required, "--no-python-downloads"])
    actual = command([python, "--version"]) if python else None
    add("python", "ok" if actual else "error", actual or f"Python {required} not found", f"uv python install {required}" if not actual else "")
    interpreter = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    backend = interpreter.is_file() and command([str(interpreter), "-c", "import fastapi, uvicorn, cyclopts; print('ok')"]) == "ok"
    add("backend_dependencies", "ok" if backend else "error", "Importable" if backend else "Not installed", "task api:install" if not backend else "")
    frontend = ROOT / "frontend"
    modules = frontend / "node_modules"
    installed = (modules / "svelte").exists() and (modules / "vite").exists()
    add("frontend_dependencies", "ok" if installed else "error", "Installed" if installed else "Not installed", "task ui:install" if not installed else "")
    browser = command(["node", "-e", "console.log(require('node:fs').existsSync(require('@playwright/test').chromium.executablePath()))"], frontend) == "true" if installed else False
    add("chromium", "ok" if browser else "warning", "Installed" if browser else "Not installed", "task browser:install" if not browser else "")
    types = (frontend / "src/lib/generated/api.d.ts").is_file()
    add("api_types", "ok" if types else "error", "Present (freshness not checked)" if types else "Missing", "task api:generate" if not types else "")
    for port in sorted({service["port"] for service in config["services"].values()
                        if service.get("host") == "127.0.0.1" and service.get("port")}):
        with socket.socket() as connection:
            connection.settimeout(0.2)
            occupied = connection.connect_ex(("127.0.0.1", port)) == 0
        add(f"port_{port}", "warning" if occupied else "ok", "Listening; may be an existing development service" if occupied else "Available", "Inspect the listener before starting another service." if occupied else "")
    database = (ROOT / config["database"]).resolve()
    if database.is_file():
        try:
            with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True, timeout=1)) as connection:
                mode = connection.execute("PRAGMA journal_mode").fetchone()[0]
                connection.execute("SELECT name FROM sqlite_schema LIMIT 1")
            add("sqlite", "ok" if mode == "wal" else "warning", f"Readable; journal mode {mode}", "task db:init" if mode != "wal" else "")
        except sqlite3.Error:
            add("sqlite", "error", "Database unreadable or schema missing", "Inspect the database and run task db:init if appropriate.")
    else:
        add("sqlite", "warning", f"Configured database not initialized ({config['settings_source']})", "task db:init")
    for file, code in [(ROOT / "uv.lock", "uv_lock"), (frontend / "pnpm-lock.yaml", "pnpm_lock")]:
        add(code, "ok" if file.is_file() else "warning", "Present" if file.is_file() else "Missing", "task install; commit the lockfiles" if not file.is_file() else "")
    if (ROOT / "app/jobs.py").exists():
        docker = command(["docker", "compose", "version"])
        add("docker_compose", "ok" if docker else "warning", docker or "Unavailable", "Install Docker Compose or configure an existing Redis server." if not docker else "")
    for enabled, tool in [(True, "caddy"), ((ROOT / "frontend/src/lib/features/terminal/Terminal.svelte").exists(), "ttyd")]:
        if enabled:
            available = shutil.which(tool)
            add(tool, "ok" if available else "warning", "Available" if available else "Unavailable", f"Install {tool} if using the corresponding service." if not available else "")
    if backend:
        versions = command([str(interpreter), "-c", "from importlib.metadata import version; print(', '.join(n+' '+version(n) for n in ('fastapi','uvicorn','cyclopts')))"])
        add("backend_versions", "ok" if versions else "warning", versions or "Unavailable")
    if installed:
        versions = command(["node", "-e", "console.log(['svelte','vite','typescript'].map(n=>n+' '+require(n+'/package.json').version).join(', '))"], frontend)
        add("frontend_versions", "ok" if versions else "warning", versions or "Unavailable")
    return checks


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    checks = inspect_environment()
    healthy = not any(check["status"] == "error" for check in checks)
    if args.json:
        print(json.dumps({"ok": healthy, "checks": checks}, indent=2))
    else:
        for check in checks:
            print(f'{check["status"].upper():7} {check["code"]}: {check["detail"]}')
            if check["remediation"]:
                print(f'        {check["remediation"]}')
    return 0 if healthy else 1


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT))
    raise SystemExit(main())
