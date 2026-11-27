"""Discover actual local configuration without printing credentials."""

import json
import os
import re
import subprocess
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]


def configuration():
    # Vite and Caddy are the existing authorities for the local service URLs.
    vite = (ROOT / "frontend/vite.config.ts").read_text(encoding="utf-8")
    caddy = (ROOT / "Caddyfile").read_text(encoding="utf-8")
    proxy = re.search(r"['\"]\/api['\"]\s*:\s*['\"](http://127\.0\.0\.1:\d+)['\"]", vite)
    frontend = re.search(r"\bport\s*:\s*(\d+)", vite)
    gateway = re.search(r"(?m)^http://:(\d+)\s*\{", caddy)
    services = {}
    if proxy:
        services["api"] = {"url": proxy.group(1) + "/api/health", "expected": True}
    if frontend:
        services["frontend"] = {"url": f"http://127.0.0.1:{frontend.group(1)}/", "expected": True}
    if gateway:
        services["proxy"] = {"url": f"http://127.0.0.1:{gateway.group(1)}/", "expected": False}
    interpreter = ROOT / ".venv" / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
    settings = {}
    if interpreter.is_file():
        try:
            result = subprocess.run(
                [str(interpreter), "-c",
                 "import json; from app.config import Settings; s=Settings(); "
                 "print(json.dumps({'database':str(s.database),'redis_url':getattr(s,'redis_url',None)}))"],
                cwd=ROOT, capture_output=True, text=True, timeout=10, check=True,
            )
            settings = json.loads(result.stdout)
        except (OSError, subprocess.SubprocessError, ValueError):
            pass
    database = settings.get("database", os.environ.get("APP_DATABASE", "data/app.sqlite3"))
    redis = settings.get("redis_url")
    if redis:
        parsed = urlsplit(redis)
        services["redis"] = {"host": parsed.hostname, "port": parsed.port or 6379, "expected": False}
    for service in services.values():
        if "url" in service:
            parsed = urlsplit(service["url"])
            service.update(host=parsed.hostname, port=parsed.port)
    return {"database": database, "settings_source": "pydantic" if settings else "environment/default",
            "services": services}
