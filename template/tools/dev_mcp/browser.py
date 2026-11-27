import base64
import json
import shutil
import subprocess
from typing import Literal

from fastmcp.utilities.types import Image

from .project import FRONTEND

Page = Literal["Overview", "Settings", "Diagnostics"]


def probe(page: Page, mode: str, theme: str = "dark") -> dict:
    node = shutil.which("node")
    if not node:
        raise ValueError("Node is unavailable; run task doctor.")
    result = subprocess.run(
        [node, "scripts/dev-browser.mjs", page, mode, theme], cwd=FRONTEND,
        capture_output=True, text=True, errors="replace", timeout=45, check=False,
    )
    if result.returncode != 0:
        raise ValueError("Browser inspection failed. Start task dev and run task browser:install.")
    return json.loads(result.stdout)


def browser_diagnostics(page: Page = "Overview") -> dict:
    """Inspect a fresh loopback browser session: console errors, network failures and DOM."""
    return probe(page, "diagnostics")


def inspect_page(page: Page = "Overview") -> dict:
    """Inspect the accessible structure of a live development page."""
    return probe(page, "diagnostics")


def browser_errors(page: Page = "Overview") -> dict:
    """Return errors observed during a new browser visit, not historical application logs."""
    data = probe(page, "diagnostics")
    return {"page": page, "errors": data["errors"], "failed_requests": data["failed_requests"]}


def inspect_network(page: Page = "Overview") -> dict:
    """Inspect request methods, paths and statuses; omit headers, bodies and query strings."""
    data = probe(page, "diagnostics")
    return {"page": page, "requests": data["requests"], "failed_requests": data["failed_requests"]}


def capture_screenshot(page: Page = "Overview",
                       theme: Literal["dark", "light", "oled", "solarized-light", "solarized-dark"] = "dark") -> Image:
    """Return a live Chromium screenshot as MCP image content, not a repository showcase."""
    data = probe(page, "screenshot", theme)
    return Image(data=base64.b64decode(data["image"]), format="png")


def accessibility_audit(page: Page = "Overview") -> dict:
    """Run axe-core against a live development page and return detected violations."""
    return probe(page, "accessibility")
