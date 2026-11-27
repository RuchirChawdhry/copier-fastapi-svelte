import json

import uvicorn
from cyclopts import App

from .config import get_settings
from .db import Database

cli = App(help="Manage the application.")


@cli.command
def serve(port: int = 8000, *, reload: bool = False) -> None:
    """Run the API on loopback."""
    uvicorn.run("app.api:app", host="127.0.0.1", port=port, reload=reload)


@cli.command
def init_db() -> None:
    Database(get_settings().database).initialize()


@cli.command
def notes() -> None:
    print(json.dumps(Database(get_settings().database).notes()))


if __name__ == "__main__":
    cli()

