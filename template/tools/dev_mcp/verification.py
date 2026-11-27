import re
import shutil
import subprocess
from typing import Literal
from xml.etree import ElementTree

from .project import ROOT

COMMANDS = {
    "deps:check", "api:check", "api:check-code", "ui:check", "check", "test:ci", "test:e2e:ci",
}


def redact(text: str) -> str:
    # Best-effort redaction; arbitrary application output can still contain sensitive text.
    text = re.sub(r"(?i)(bearer\s+)[^\s,;]+", r"\1[redacted]", text)
    return re.sub(r"(?i)((?:token|password|secret|api[_-]?key)\s*[:=]\s*)[^\s,;]+",
                  r"\1[redacted]", text)


def run_task(task: str) -> dict:
    if task not in COMMANDS:
        raise ValueError("Unsupported verification command")
    executable = shutil.which("task")
    if not executable:
        return {"ok": False, "command": f"task {task}", "detail": "Go Task is not installed"}
    try:
        result = subprocess.run([executable, task], cwd=ROOT, capture_output=True,
                                text=True, errors="replace", timeout=180, check=False)
    except subprocess.TimeoutExpired:
        return {"ok": False, "command": f"task {task}", "detail": "Verification timed out"}
    return {"ok": result.returncode == 0, "command": f"task {task}",
            "exit_code": result.returncode, "stdout": redact(result.stdout[-12000:]),
            "stderr": redact(result.stderr[-12000:])}


def check_api_contract() -> dict:
    """Run the existing API contract check; it regenerates the disposable OpenAPI JSON."""
    return run_task("api:check")


def run_checks(scope: Literal["all", "api", "ui"] = "all") -> dict:
    """Run predefined lint/type/contract checks. No arbitrary commands."""
    return run_task({"all": "check", "api": "api:check-code", "ui": "ui:check"}[scope])


def run_tests(scope: Literal["backend", "browser"] = "backend") -> dict:
    """Run backend tests or browser tests (browser requires a build and free dev ports)."""
    return run_task({"backend": "test:ci", "browser": "test:e2e:ci"}[scope])


def test_results() -> dict:
    """Read existing JUnit reports from task test:ci and task test:e2e:ci."""
    reports = []
    for relative in ("backend.xml", "frontend/browser.xml"):
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
                                 "message": redact(problem.get("message", "")[:2000])})
        reports.append({"path": relative, "modified_at": path.stat().st_mtime,
                        "tests": len(cases), "failures": len(failures),
                        "skipped": sum(case.find("skipped") is not None for case in cases),
                        "failed_tests": failures[:50]})
    return {"reports": reports, "detail": "Run a verification task if reports are missing."}
