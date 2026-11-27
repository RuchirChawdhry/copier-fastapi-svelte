import importlib.metadata
import json
import shutil
import socket
import subprocess
import time
import tomllib
from pathlib import Path

import httpx
import psutil
import yaml
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from scripts.dev_config import configuration
from scripts.doctor import inspect_environment

from .project import FRONTEND, ROOT
from .verification import run_task


def doctor() -> dict:
    """Run existing environment checks against discovered configuration."""
    checks = inspect_environment()
    return {"ok": not any(check["status"] == "error" for check in checks), "checks": checks}


def dependency_status() -> dict:
    """Compare direct declared, installed and locked dependencies, with native lock validation."""
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text())
    lockfile = ROOT / "uv.lock"
    packages = tomllib.loads(lockfile.read_text()).get("package", []) if lockfile.is_file() else []
    root_package = next((pkg for pkg in packages if canonicalize_name(pkg["name"]) == canonicalize_name(manifest["project"]["name"])), {})
    metadata = root_package.get("metadata", {})
    locked = {}
    for package in packages:
        locked.setdefault(canonicalize_name(package["name"]), set()).add(package["version"])
    python = []
    for group, values in (("runtime", manifest["project"]["dependencies"]),
                          ("dev", manifest.get("dependency-groups", {}).get("dev", []))):
        for raw in values:
            if not isinstance(raw, str):
                continue
            req = Requirement(raw)
            applicable = req.marker is None or req.marker.evaluate()
            try:
                installed = importlib.metadata.version(req.name)
            except importlib.metadata.PackageNotFoundError:
                installed = None
            versions = sorted(locked.get(canonicalize_name(req.name), ()))
            declarations = metadata.get("requires-dist", []) if group == "runtime" else metadata.get("requires-dev", {}).get("dev", [])
            locked_declarations = [item for item in declarations if canonicalize_name(item["name"]) == canonicalize_name(req.name)]
            python.append({"group": group, "name": req.name, "declared": str(req.specifier),
                           "installed": installed, "locked": versions, "locked_declarations": locked_declarations, "applicable": applicable,
                           "issues": (["missing_install"] if applicable and not installed else []) +
                           (["installed_outside_requirement"] if applicable and installed and installed not in req.specifier else []) +
                           (["missing_lock"] if applicable and not versions else []) +
                           (["installed_not_in_lock"] if applicable and installed and versions and installed not in versions else [])})
    package = json.loads((FRONTEND / "package.json").read_text())
    pnpm_lock = FRONTEND / "pnpm-lock.yaml"
    lock = yaml.safe_load(pnpm_lock.read_text()) if pnpm_lock.is_file() else {}
    importer = (lock or {}).get("importers", {}).get(".", {})
    frontend = []
    for group in ("dependencies", "devDependencies", "optionalDependencies"):
        for name, declared in package.get(group, {}).items():
            entry = importer.get(group, {}).get(name, {})
            installed_file = FRONTEND / "node_modules" / name / "package.json"
            installed = json.loads(installed_file.read_text()).get("version") if installed_file.is_file() else None
            locked_version = str(entry.get("version", "")).split("(", 1)[0] or None
            frontend.append({"group": group, "name": name, "declared": declared,
                             "installed": installed, "locked": locked_version,
                             "issues": (["missing_install"] if not installed and group != "optionalDependencies" else []) +
                             (["missing_lock"] if not entry else []) +
                             (["lock_specifier_mismatch"] if entry and entry.get("specifier") != declared else []) +
                             (["installed_not_in_lock"] if installed and locked_version and installed != locked_version else [])})
    checks = {"python": run_task("api:lock:check"), "frontend": run_task("ui:lock:check")}
    return {"ok": all(check["ok"] for check in checks.values()) and
            not any(row["issues"] for row in python + frontend),
            "python": python, "frontend": frontend, "lock_checks": checks}


def service_status() -> dict:
    """Inspect configured services, listener ownership, RAM, uptime and API readiness."""
    config = configuration()
    try:
        listeners = [connection for connection in psutil.net_connections(kind="inet")
                     if connection.status == psutil.CONN_LISTEN]
        ownership_available = True
    except (psutil.AccessDenied, OSError):
        listeners, ownership_available = [], False
    services = {}
    with httpx.Client(timeout=2, follow_redirects=False, trust_env=False) as client:
        for name, service in config["services"].items():
            row = {**service, "listeners": []}
            if service["host"] in ("127.0.0.1", "localhost", "::1"):
                for listener in listeners:
                    if listener.laddr.port != service["port"] or listener.laddr.ip not in (
                        "127.0.0.1", "::1", "0.0.0.0", "::"
                    ):
                        continue
                    item = {"address": listener.laddr.ip, "pid": listener.pid}
                    if listener.pid:
                        try:
                            process = psutil.Process(listener.pid)
                            item.update(name=process.name(), rss_bytes=process.memory_info().rss,
                                        uptime_seconds=round(time.time() - process.create_time(), 1),
                                        workspace_owned=Path(process.cwd()).resolve().is_relative_to(ROOT.resolve()))
                        except (psutil.Error, OSError):
                            pass
                    row["listeners"].append(item)
            if service.get("url"):
                try:
                    response = client.get(service["url"])
                    row.update(http_status=response.status_code, reachable=True, healthy=response.is_success)
                    if name == "api":
                        payload = response.json()
                        row["dependencies"] = payload.get("dependencies", {})
                except (httpx.RequestError, ValueError):
                    row.update(reachable=False, healthy=False)
            else:
                try:
                    with socket.create_connection((service["host"], service["port"]), timeout=1):
                        row["reachable"] = True
                except OSError:
                    row["reachable"] = False
                row["healthy"] = None
            row["state"] = "running" if row["reachable"] else "not_running" if row["expected"] else "optional_not_running"
            services[name] = row
    return {"services": services, "listener_inspection_available": ownership_available,
            "configuration_source": config["settings_source"]}


def git_status() -> dict:
    """Parse Git porcelain v1 NUL records into branch and staged/unstaged/untracked paths."""
    if not shutil.which("git"):
        return {"ok": False, "detail": "Git is unavailable"}
    result = subprocess.run(
        ["git", "status", "--porcelain=v1", "-z", "--branch"], cwd=ROOT,
        capture_output=True, text=True, timeout=10, check=False,
    )
    if result.returncode:
        return {"ok": False, "detail": result.stderr.strip()}
    entries = iter(result.stdout.split("\0"))
    branch = next(entries).removeprefix("## ")
    branch_name = branch.split("...")[0].removeprefix("No commits yet on ").removeprefix("Initial commit on ")
    files = []
    for entry in entries:
        if not entry:
            continue
        staged, unstaged = entry[:2]
        file = {"path": entry[3:], "staged": staged.strip() or None,
                "unstaged": unstaged.strip() or None, "untracked": entry.startswith("??")}
        if staged in {"R", "C"} or unstaged in {"R", "C"}:
            file["original_path"] = next(entries)
        files.append(file)
    return {"ok": True, "branch": branch_name, "tracking": branch,
            "files": files[:500], "total": len(files),
            "staged": sum(bool(f["staged"]) and not f["untracked"] for f in files),
            "unstaged": sum(bool(f["unstaged"]) and not f["untracked"] for f in files),
            "untracked": sum(f["untracked"] for f in files)}
