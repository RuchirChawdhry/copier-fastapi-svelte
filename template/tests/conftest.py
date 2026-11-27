import os
import tempfile

import pytest

_database_dir = tempfile.TemporaryDirectory()
os.environ["APP_DATABASE"] = _database_dir.name + "/test.sqlite3"


@pytest.fixture(scope="session", autouse=True)
def cleanup_database():
    yield
    _database_dir.cleanup()

