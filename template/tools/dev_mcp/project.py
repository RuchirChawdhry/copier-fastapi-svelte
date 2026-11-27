import json
import subprocess
import sys
import tomllib
from pathlib import Path
from typing import Literal

import yaml

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def node_inspect(*args, data=None):
    result = subprocess.run(
        ["node", "scripts/dev-inspect.mjs", *args], cwd=FRONTEND,
        input=json.dumps(data) if data is not None else None, capture_output=True,
        text=True, timeout=60, check=True,
    )
    return json.loads(result.stdout)


def project_context() -> dict:
    """Discover project manifests, versions, features, architecture and Task commands."""
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    frontend = json.loads((FRONTEND / "package.json").read_text(encoding="utf-8"))
    answers_file = ROOT / ".copier-answers.yml"
    answers = (yaml.safe_load(answers_file.read_text(encoding="utf-8")) or {}) if answers_file.is_file() else {}
    try:
        result = subprocess.run(["task", "--list-all", "--json"], cwd=ROOT, capture_output=True,
                                text=True, timeout=10, check=True)
        tasks = [{"name": task.get("name"), "description": task.get("desc")}
                 for task in json.loads(result.stdout)["tasks"]]
    except (OSError, subprocess.SubprocessError, ValueError, KeyError):
        taskfile = yaml.safe_load((ROOT / "Taskfile.yml").read_text(encoding="utf-8"))
        tasks = [{"name": name, "description": (task or {}).get("desc")}
                 for name, task in taskfile["tasks"].items()]
    return {
        "name": manifest["project"]["name"], "version": manifest["project"].get("version"),
        "python_requires": manifest["project"].get("requires-python"),
        "frontend_version": frontend.get("version"), "node_requires": frontend.get("engines", {}).get("node"),
        "package_manager": frontend.get("packageManager"), "template_version": answers.get("_commit"),
        "features": {key: value for key, value in answers.items()
                     if key.startswith("enable_") and isinstance(value, bool)},
        "paths": [path.relative_to(ROOT).as_posix() for path in sorted(ROOT.iterdir())
                  if not path.name.startswith(".") and path.name not in {"data", "dist"}],
        "frontend_paths": [path.relative_to(ROOT).as_posix() for path in sorted((FRONTEND / "src").rglob("*"))
                           if path.is_dir() and "components" not in path.parts][:100],
        "commands": tasks, "application_mcp": (ROOT / "app/mcp.py").is_file(),
    }


def list_pages() -> list[dict]:
    """Read registered page IDs, labels and paths; unregistered page files are also listed."""
    pages = node_inspect("pages")
    registered = {page["source"] for page in pages}
    return pages + [{"id": None, "label": path.stem, "route": None,
                     "source": path.relative_to(ROOT).as_posix()}
                    for path in sorted((FRONTEND / "src/pages").rglob("*.svelte"))
                    if path.relative_to(ROOT).as_posix() not in registered]


def list_components(search: str = "", category: Literal["all", "ui", "page", "application"] = "all",
                    limit: int = 100) -> dict:
    """Search Svelte components, prop bindings/types and static import references."""
    return node_inspect("components", search, category, str(max(1, min(limit, 300))))


def api_snapshot() -> dict:
    result = subprocess.run(
        [sys.executable, "-m", "tools.dev_mcp.contract"], cwd=ROOT,
        capture_output=True, text=True, timeout=30, check=True,
    )
    return json.loads(result.stdout)


def list_endpoints() -> list[dict]:
    """Discover current OpenAPI operations and handler source locations in a fresh process."""
    snapshot = api_snapshot()
    return [{"method": method.upper(), "path": path, "operation_id": operation.get("operationId"),
             "summary": operation.get("summary"), **snapshot["handlers"].get(f"{method.upper()} {path}", {})}
            for path, item in snapshot["schema"]["paths"].items()
            for method, operation in item.items()
            if method in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}]


def references(path: str, directory: Path, extensions: set[str]) -> list[dict]:
    # Literal references are candidates, not proof of a call graph.
    prefix = path.split("{", 1)[0].rstrip("/") or path
    found = []
    for file in sorted(directory.rglob("*")):
        if file.suffix not in extensions or not file.is_file() or "generated" in file.parts or "ui" in file.parts:
            continue
        for line, text in enumerate(file.read_text(encoding="utf-8").splitlines(), 1):
            if prefix in text:
                found.append({"source": file.relative_to(ROOT).as_posix(), "line": line})
                if len(found) >= 50:
                    return found
    return found


def inspect_endpoint(method: str, path: str) -> dict:
    """Return fresh OpenAPI operation, referenced schemas, implementation and candidate consumers/tests."""
    snapshot = api_snapshot()
    contract = snapshot["schema"]
    operation = contract["paths"].get(path, {}).get(method.lower())
    if operation is None:
        raise ValueError("Unknown endpoint; call list_endpoints first.")
    schemas = contract.get("components", {}).get("schemas", {})
    referenced = {}

    def collect(value):
        match value:
            case dict():
                ref = value.get("$ref", "")
                if ref.startswith("#/components/schemas/"):
                    name = ref.rsplit("/", 1)[-1]
                    if name in schemas and name not in referenced:
                        referenced[name] = schemas[name]
                        collect(schemas[name])
                for item in value.values():
                    collect(item)
            case list():
                for item in value:
                    collect(item)

    collect(operation)
    return {"method": method.upper(), "path": path, "operation": operation, "schemas": referenced,
            "implementation": snapshot["handlers"].get(f"{method.upper()} {path}"),
            "frontend_references": references(path, FRONTEND / "src", {".ts", ".svelte"}),
            "test_references": references(path, ROOT / "tests", {".py"}) +
                               references(path, FRONTEND / "tests", {".ts"}),
            "reference_kind": "literal path matches; inspect candidate sources for exact call sites"}
