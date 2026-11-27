import shutil
import subprocess

import httpx

from scripts.doctor import inspect_environment

from .project import ROOT


def doctor() -> dict:
    """Run the existing environment doctor and return actionable check results."""
    checks = inspect_environment()
    return {"ok": not any(check["status"] == "error" for check in checks), "checks": checks}


def dependency_status() -> dict:
    """Check lockfile consistency with existing Task commands."""
    from .verification import run_task

    return run_task("deps:check")


def service_status() -> dict:
    """Probe fixed loopback development services without starting them."""
    result = {}
    with httpx.Client(timeout=2, follow_redirects=False, trust_env=False) as client:
        for name, url in {
            "api": "http://127.0.0.1:8000/api/health",
            "frontend": "http://127.0.0.1:5173/",
            "proxy": "http://127.0.0.1:8080/",
        }.items():
            try:
                response = client.get(url)
                result[name] = {"url": url, "status": response.status_code, "ok": response.is_success}
            except httpx.RequestError:
                result[name] = {"url": url, "ok": False, "detail": "Not reachable"}
    return result


def git_status() -> dict:
    """Return Git worktree status without reading file contents."""
    executable = shutil.which("git")
    if not executable:
        return {"ok": False, "detail": "Git is unavailable"}
    result = subprocess.run(
        [executable, "status", "--short", "--branch"], cwd=ROOT, capture_output=True,
        text=True, timeout=10, check=False,
    )
    return {"ok": result.returncode == 0, "status": result.stdout[:8000]}
