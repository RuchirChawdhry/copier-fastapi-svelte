"""Fresh API snapshot, isolated from the long-lived MCP process."""

import inspect
import json

from fastapi.routing import APIRoute

from app.api import app

from .project import ROOT


def snapshot():
    handlers = {}
    for route in app.routes:
        if not isinstance(route, APIRoute):
            continue
        endpoint = inspect.unwrap(route.endpoint)
        source = inspect.getsourcefile(endpoint)
        if source:
            from pathlib import Path

            path = Path(source).resolve()
            location = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
            try:
                line = inspect.getsourcelines(endpoint)[1]
            except OSError:
                line = None
        else:
            location, line = None, None
        for method in route.methods:
            handlers[f"{method} {route.path}"] = {
                "handler": endpoint.__qualname__, "source": location, "line": line,
            }
    return {"schema": app.openapi(), "handlers": handlers}


if __name__ == "__main__":
    print(json.dumps(snapshot()))
