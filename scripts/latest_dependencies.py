"""Create a latest-stable candidate in an isolated CI checkout."""

import json
import os
import re
import subprocess
import sys
import tempfile
import tomllib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.request import urlopen

from copier import run_copy
from packaging.requirements import Requirement
from packaging.version import InvalidVersion, Version
from yaml import safe_load

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
REPORT = ROOT / "latest-deps-report.json"


def command(*args):
    return subprocess.check_output(args, text=True, cwd=ROOT).strip()


def pypi(name):
    with urlopen(f"https://pypi.org/pypi/{name}/json", timeout=30) as response:
        releases = json.load(response)["releases"]
    versions = []
    for raw, files in releases.items():
        try:
            version = Version(raw)
        except InvalidVersion:
            continue
        if not version.is_prerelease and not version.is_devrelease and any(
            not file["yanked"] for file in files
        ):
            versions.append(version)
    return str(max(versions))


def npm(name):
    versions = json.loads(command("npm", "view", name, "versions", "--json"))
    if isinstance(versions, str):
        versions = [versions]
    return max(
        (v for v in versions if re.fullmatch(r"\d+\.\d+\.\d+", v)),
        key=Version,
    )


def replace(path, old, new):
    source = path.read_text()
    if old not in source:
        raise ValueError(f"Missing expected value {old!r} in {path}")
    path.write_text(source.replace(old, new))


def resolve(names, resolver):
    with ThreadPoolExecutor(max_workers=8) as pool:
        return dict(zip(sorted(names), pool.map(resolver, sorted(names)), strict=True))


def main():
    python = ".".join(map(str, sys.version_info[:3]))
    node = command("node", "--version").removeprefix("v")
    config_path = ROOT / "copier.yml"
    config = safe_load(config_path.read_text())
    flags = {key: True for key, value in config.items()
             if isinstance(value, dict) and value.get("type") == "bool"}
    with tempfile.TemporaryDirectory() as directory:
        run_copy(str(ROOT), directory, defaults=True, vcs_ref="HEAD", data=flags)
        rendered = Path(directory)
        backend = tomllib.loads((rendered / "pyproject.toml").read_text())
        frontend = json.loads((rendered / "frontend/package.json").read_text())

    requirements = set(
        backend["project"]["dependencies"]
        + backend["dependency-groups"]["dev"]
        + backend["build-system"]["requires"]
    )
    parsed = {raw: Requirement(raw) for raw in requirements}
    python_versions = resolve({req.name for req in parsed.values()} | {"copier"}, pypi)
    npm_dependencies = frontend["dependencies"] | frontend["devDependencies"]
    npm_versions = resolve(set(npm_dependencies) | {"pnpm", "corepack"}, npm)
    report = {
        "source_commit": command("git", "rev-parse", "HEAD"),
        "python": python,
        "node": node,
        "uv": command("uv", "--version"),
        "task": command("task", "--version"),
        "pypi": python_versions,
        "npm": npm_versions,
        "redis": None,
    }
    REPORT.write_text(json.dumps(report, indent=2) + "\n")

    pyproject = TEMPLATE / "pyproject.toml.jinja"
    for raw, req in sorted(parsed.items()):
        extras = "[" + ",".join(sorted(req.extras)) + "]" if req.extras else ""
        if req.url or req.marker:
            raise ValueError(f"Unsupported requirement for upgrade probe: {raw}")
        replace(pyproject, f'"{raw}"', f'"{req.name}{extras}=={python_versions[req.name]}"')
    minor = ".".join(python.split(".")[:2])
    replace(pyproject, f'requires-python = "{backend["project"]["requires-python"]}"',
            f'requires-python = ">={minor}"')
    (TEMPLATE / ".python-version").write_text(python + "\n")

    package = TEMPLATE / "frontend/package.json.jinja"
    for name, old in npm_dependencies.items():
        replace(package, f'"{name}": "{old}"', f'"{name}": "{npm_versions[name]}"')
    replace(package, f'"packageManager": "{frontend["packageManager"]}"',
            f'"packageManager": "pnpm@{npm_versions["pnpm"]}"')
    replace(package, f'"node": "{frontend["engines"]["node"]}"',
            f'"node": ">={node.split(".")[0]}"')
    (TEMPLATE / "frontend/.node-version").write_text(node + "\n")

    taskfile = ROOT / "Taskfile.yml"
    old_copier = config["_min_copier_version"]
    replace(config_path, f'"{old_copier}"', f'"{python_versions["copier"]}"')
    replace(taskfile, f"copier=={old_copier}", f'copier=={python_versions["copier"]}')
    replace(taskfile, "--with pytest --with ruff",
            f'--with pytest=={python_versions["pytest"]} --with ruff=={python_versions["ruff"]}')
    replace(taskfile, "npm install -g corepack", f'npm install -g corepack@{npm_versions["corepack"]}')

    subprocess.run(["docker", "pull", "redis:latest"], check=True)
    digest = command("docker", "image", "inspect", "--format", "{{index .RepoDigests 0}}", "redis:latest")
    redis_version = command("docker", "run", "--rm", digest, "redis-server", "--version")
    compose = next(TEMPLATE.glob("*compose.yml*.jinja"))
    replace(compose, "image: redis:7-alpine", f"image: {digest}")
    report["redis"] = {"image": digest, "version": redis_version}
    REPORT.write_text(json.dumps(report, indent=2) + "\n")
    with open(os.environ["GITHUB_OUTPUT"], "a") as output:
        print(f"node={node}", file=output)
        print(f"python={python}", file=output)
        print(f"uv={report['uv'].split()[1]}", file=output)
        print(f"task={re.search(r'\d+\.\d+\.\d+', report['task']).group()}", file=output)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
