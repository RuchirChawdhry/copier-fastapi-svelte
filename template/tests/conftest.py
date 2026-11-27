import os
import tempfile

import pytest

_database_dir = tempfile.TemporaryDirectory()
os.environ["APP_DATABASE"] = _database_dir.name + "/test.sqlite3"


@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield
    _database_dir.cleanup()


@pytest.fixture(scope="session")
def client():
    from fastapi.testclient import TestClient

    from app.api import create_app

    with TestClient(create_app()) as test_client:
        yield test_client
