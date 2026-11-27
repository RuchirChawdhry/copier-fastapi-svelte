import tomllib
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
FRONTEND = ROOT / "frontend"


def project_context() -> dict:
    """Return safe project metadata, feature switches and development paths."""
    manifest = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    answers = yaml.safe_load((ROOT / ".copier-answers.yml").read_text(encoding="utf-8")) or {}
    return {
        "name": manifest["project"]["name"],
        "template_version": answers.get("_commit"),
        "features": {key: value for key, value in answers.items()
                     if key.startswith("enable_") and isinstance(value, bool)},
        "paths": {
            "backend": "app/", "frontend": "frontend/src/", "pages": "frontend/src/pages/",
            "ui_components": "frontend/src/lib/components/ui/",
            "api_types": "frontend/src/lib/generated/api.d.ts",
            "backend_tests": "tests/", "browser_tests": "frontend/tests/",
        },
        "commands": ["task doctor", "task dev", "task check", "task test", "task screenshots"],
        "application_mcp": (ROOT / "app/mcp.py").is_file(),
    }


def list_features() -> dict:
    """Return enabled and disabled Copier features."""
    return project_context()["features"]


def list_pages() -> list[dict]:
    """List page components and the shared navigation registry."""
    return [{"name": path.stem, "source": path.relative_to(ROOT).as_posix()}
            for path in sorted((FRONTEND / "src/pages").glob("*.svelte"))]


def list_components() -> dict:
    """List vendored UI primitives and reusable application components."""
    lib = FRONTEND / "src/lib"
    return {
        "ui": sorted(path.name for path in (lib / "components/ui").iterdir() if path.is_dir()),
        "application": [path.relative_to(ROOT).as_posix() for path in sorted(lib.rglob("*.svelte"))
                        if "ui" not in path.relative_to(lib).parts],
    }


def list_endpoints() -> list[dict]:
    """List HTTP operations from the current FastAPI source without starting the server."""
    from app.api import app

    return [{"method": method.upper(), "path": path, "operation_id": operation.get("operationId"),
             "summary": operation.get("summary")}
            for path, item in app.openapi()["paths"].items()
            for method, operation in item.items()
            if method in {"get", "post", "put", "patch", "delete", "head", "options", "trace"}]


def inspect_endpoint(method: str, path: str) -> dict:
    """Return the current OpenAPI operation and its referenced component schemas."""
    from app.api import app

    contract = app.openapi()
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
    return {"method": method.upper(), "path": path, "operation": operation, "schemas": referenced}
