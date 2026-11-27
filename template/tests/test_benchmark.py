from app.db import Database


def test_sqlite_read(benchmark, tmp_path):
    db = Database(tmp_path / "bench.sqlite3")
    db.initialize()
    db.add_note("sample")
    assert benchmark(db.notes)[0]["text"] == "sample"

