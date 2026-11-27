import json
import os
import re
import shutil
import subprocess
import time
from datetime import UTC, datetime
from typing import Literal
from xml.etree import ElementTree

from .project import ROOT, api_snapshot, node_inspect

COMMANDS = {
    "deps:check", "api:lock:check", "ui:lock:check", "api:check", "api:check-code",
    "api:lint", "api:typecheck", "ui:check", "ui:lint", "ui:format:check", "ui:typecheck",
    "check", "test:ci", "test:e2e:ci",
}


def redact(text: str) -> str:
    text = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[redacted]", text)
    return re.sub(r"(?i)((?:token|password|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+",
                  r"\1[redacted]", text)


def run_task(task: str, timeout: int = 180, selection: dict | None = None) -> dict:
    if task not in COMMANDS:
        raise ValueError("Unsupported verification command")
    executable = shutil.which("task")
    if not executable:
        return {"ok": False, "command": f"task {task}", "detail": "Go Task is not installed"}
    env = os.environ.copy()
    env.pop("DEV_TEST_SELECTION", None)
    if selection is not None:
        env["DEV_TEST_SELECTION"] = json.dumps(selection)
    started = time.monotonic()
    try:
        result = subprocess.run([executable, task], cwd=ROOT, capture_output=True,
                                text=True, errors="replace", timeout=timeout, env=env, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": f"task {task}", "detail": "Verification timed out",
                "duration_seconds": round(time.monotonic() - started, 2)}
    return {"ok": result.returncode == 0, "command": f"task {task}",
            "duration_seconds": round(time.monotonic() - started, 2),
            "exit_code": result.returncode, "stdout": redact(result.stdout[-12000:]),
            "stderr": redact(result.stderr[-12000:])}


def check_api_contract() -> dict:
    """Compare freshly generated TypeScript endpoint and schema signatures without modifying files."""
    return node_inspect("contract", data=api_snapshot()["schema"])


def run_checks(scope: Literal["all", "api", "ui", "ruff", "ty", "eslint", "prettier",
                              "svelte", "contract", "dependencies"] = "all") -> dict:
    """Run individual or combined existing project checks."""
    if scope == "contract":
        return check_api_contract()
    return run_task({"all": "check", "api": "api:check-code", "ui": "ui:check",
                     "ruff": "api:lint", "ty": "api:typecheck", "eslint": "ui:lint",
                     "prettier": "ui:format:check", "svelte": "ui:typecheck",
                     "dependencies": "deps:check"}[scope])


def run_tests(scope: Literal["backend", "browser"] = "backend", files: list[str] | None = None,
              match: str = "", failed_only: bool = False, timeout: int = 600) -> dict:
    """Run selected files, names or last failures with the existing pytest/Playwright runner."""
    from scripts.verify_tests import test_command

    selection = {"files": files or [], "match": match, "failed_only": failed_only}
    test_command(scope, **selection)
    result = run_task({"backend": "test:ci", "browser": "test:e2e:ci"}[scope],
                      timeout=max(10, min(timeout, 1800)), selection=selection)
    result["reports"] = test_results(scope)["reports"]
    return result


def test_results(scope: Literal["all", "backend", "browser"] = "all") -> dict:
    """Read bounded JUnit reports with failures, duration, artifacts and source freshness."""
    reports = []
    for kind, relative in (("backend", "backend.xml"), ("browser", "frontend/browser.xml")):
        if scope not in ("all", kind):
            continue
        path = ROOT / relative
        if not path.is_file() or not path.resolve().is_relative_to(ROOT.resolve()):
            continue
        if path.stat().st_size > 10_000_000:
            reports.append({"path": relative, "detail": "Report exceeds 10 MB"})
            continue
        try:
            tree = ElementTree.parse(path)
        except ElementTree.ParseError:
            reports.append({"path": relative, "detail": "Invalid JUnit XML"})
            continue
        cases = tree.findall(".//testcase")
        failures = []
        for case in cases:
            problem = case.find("failure")
            if problem is None:
                problem = case.find("error")
            if problem is not None:
                failures.append({"name": case.get("name"), "class": case.get("classname"),
                                 "file": case.get("file"), "line": case.get("line"),
                                 "duration_seconds": float(case.get("time", 0)),
                                 "message": redact(problem.get("message", "")[:2000]),
                                 "traceback": redact((problem.text or "")[-6000:])})
        timestamp = path.stat().st_mtime
        folders = ("app", "tests", "scripts", "tools") if kind == "backend" else ("frontend/src", "frontend/tests")
        newer = [file.relative_to(ROOT).as_posix() for folder in folders for file in (ROOT / folder).rglob("*")
                 if file.is_file() and file.suffix in {".py", ".ts", ".js", ".svelte", ".mjs", ".css"}
                 and file.stat().st_mtime > timestamp]
        artifact_root = ROOT / "frontend/test-results"
        artifacts = [file.relative_to(ROOT).as_posix() for file in sorted(artifact_root.rglob("*"))
                     if kind == "browser" and file.is_file() and file.suffix in {".zip", ".png", ".webm"}
                     and file.stat().st_mtime >= timestamp - 3600][:50]
        skipped = sum(case.find("skipped") is not None for case in cases)
        reports.append({"path": relative, "modified_at": datetime.fromtimestamp(timestamp, UTC).isoformat(),
                        "stale": bool(newer), "newer_sources": newer[:30], "tests": len(cases),
                        "passed": len(cases) - len(failures) - skipped, "failures": len(failures),
                        "skipped": skipped, "duration_seconds": sum(float(case.get("time", 0)) for case in cases),
                        "failed_tests": failures[:50], "artifacts": artifacts})
    return {"reports": reports, "detail": "Run a verification task if reports are missing."}
