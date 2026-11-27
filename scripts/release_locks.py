"""Generate and verify dependency lock templates for immutable Copier releases."""

import argparse
import json
import subprocess
import tempfile
from itertools import product
from pathlib import Path

from copier import run_copy

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / "template"
PLACEHOLDER = "copier-lock-profile-placeholder"
BACKEND_FLAGS = ("enable_jobs", "enable_events", "enable_mcp", "enable_rss", "enable_ntfy")
FRONTEND_FLAGS = ("enable_schema_forms",)


def profiles(flags):
    return [dict(zip(flags, values, strict=True)) for values in product((False, True), repeat=len(flags))]


def conditional_name(flags, filename):
    condition = " and ".join(key if value else f"not {key}" for key, value in flags.items())
    return "{% if " + condition + " %}" + filename + "{% endif %}.jinja"


def run(*args, cwd):
    subprocess.run(args, cwd=cwd, check=True)


def render(destination, flags, slug):
    run_copy(
        str(ROOT), str(destination), defaults=True, vcs_ref="HEAD",
        data={"project_name": slug, "project_slug": slug, **flags},
    )


def generate():
    # Release snapshots are built in a clean workflow checkout, not on main.
    for directory, filename in ((TEMPLATE, "uv.lock"), (TEMPLATE / "frontend", "pnpm-lock.yaml")):
        for old in directory.glob("{% if *%}" + filename + "{% endif %}.jinja"):
            old.unlink()
    for flags in profiles(BACKEND_FLAGS):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            render(dest, flags, PLACEHOLDER)
            run("uv", "lock", cwd=dest)
            content = (dest / "uv.lock").read_text(encoding="utf-8")
            original = f'name = "{PLACEHOLDER}"'
            assert content.count(original) == 1, "Unexpected uv root package metadata"
            content = content.replace(original, 'name = "{{ project_slug }}"')
            (TEMPLATE / conditional_name(flags, "uv.lock")).write_text(content, encoding="utf-8")
    for flags in profiles(FRONTEND_FLAGS):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            render(dest, flags, PLACEHOLDER)
            run("pnpm", "install", "--lockfile-only", "--no-frozen-lockfile", cwd=dest / "frontend")
            content = (dest / "frontend/pnpm-lock.yaml").read_text(encoding="utf-8")
            assert PLACEHOLDER not in content, "Unexpected frontend root package metadata"
            (TEMPLATE / "frontend" / conditional_name(flags, "pnpm-lock.yaml")).write_text(
                content, encoding="utf-8"
            )
    (ROOT / "release-locks.json").write_text(
        json.dumps({"backend_profiles": len(profiles(BACKEND_FLAGS)), "frontend_profiles": len(profiles(FRONTEND_FLAGS))}, indent=2) + "\n",
        encoding="utf-8",
    )


def verify():
    for flags in profiles(BACKEND_FLAGS):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            render(dest, flags, "release-verification-app")
            lock = dest / "uv.lock"
            before = lock.read_bytes()
            run("uv", "lock", "--check", cwd=dest)
            assert lock.read_bytes() == before, "Backend lock was modified"
    for flags in profiles(FRONTEND_FLAGS):
        with tempfile.TemporaryDirectory() as directory:
            dest = Path(directory)
            render(dest, flags, "release-verification-app")
            lock = dest / "frontend/pnpm-lock.yaml"
            before = lock.read_bytes()
            run("pnpm", "install", "--lockfile-only", "--frozen-lockfile", cwd=dest / "frontend")
            assert lock.read_bytes() == before, "Frontend lock was modified"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("generate", "verify"))
    args = parser.parse_args()
    {"generate": generate, "verify": verify}[args.action]()
