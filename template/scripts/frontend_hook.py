"""Run frontend tools against only staged source files."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = ROOT / "frontend"


def main() -> int:
    tool, *files = sys.argv[1:]
    paths = [str((ROOT / file).relative_to(FRONTEND)) for file in files]
    command = ["pnpm.cmd" if sys.platform == "win32" else "pnpm", "exec", tool]
    return subprocess.call(
        [*command, "--fix" if tool == "eslint" else "--write", *paths], cwd=FRONTEND
    )


if __name__ == "__main__":
    raise SystemExit(main())
