import sqlite3
import tempfile
import os
import pytest
from strava.db import init_db, upsert_activity, get_activity_ids, get_activity


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def conn(db_path):
    init_db(db_path)
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


SAMPLE_ACTIVITY = {
    "id": 12345,
    "name": "Morning Run",
    "type": "Run",
    "sport_type": "Run",
    "distance": 10200.0,
    "moving_time": 3600,
    "elapsed_time": 3700,
    "total_elevation_gain": 50.0,
    "start_date": "2024-03-15T06:00:00Z",
    "start_date_local": "2024-03-15T07:00:00",
    "timezone": "Europe/Prague",
}


def test_init_db_creates_file(db_path):
    init_db(db_path)
    assert os.path.exists(db_path)


def test_init_db_creates_table(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='activities'")
    assert cursor.fetchone() is not None
    conn.close()


def test_upsert_activity_inserts(conn):
    upsert_activity(conn, SAMPLE_ACTIVITY)
    cursor = conn.execute("SELECT id, name FROM activities WHERE id = 12345")
    row = cursor.fetchone()
    assert row is not None
    assert row["name"] == "Morning Run"


def test_upsert_activity_replace_no_error(conn):
    upsert_activity(conn, SAMPLE_ACTIVITY)
    updated = dict(SAMPLE_ACTIVITY, name="Evening Run")
    upsert_activity(conn, updated)
    cursor = conn.execute("SELECT name FROM activities WHERE id = 12345")
    assert cursor.fetchone()["name"] == "Evening Run"


def test_upsert_activity_stores_raw_json(conn):
    import json
    upsert_activity(conn, SAMPLE_ACTIVITY)
    cursor = conn.execute("SELECT raw_json FROM activities WHERE id = 12345")
    raw = cursor.fetchone()["raw_json"]
    parsed = json.loads(raw)
    assert parsed["id"] == 12345


def test_get_activity_ids_empty(conn):
    assert get_activity_ids(conn) == set()


def test_get_activity_ids_returns_set(conn):
    upsert_activity(conn, SAMPLE_ACTIVITY)
    upsert_activity(conn, dict(SAMPLE_ACTIVITY, id=99999, name="Other"))
    ids = get_activity_ids(conn)
    assert ids == {12345, 99999}


def test_get_activity_returns_dict(conn):
    upsert_activity(conn, SAMPLE_ACTIVITY)
    result = get_activity(conn, 12345)
    assert result is not None
    assert result["name"] == "Morning Run"
    assert result["distance"] == 10200.0


def test_get_activity_returns_none_for_missing(conn):
    assert get_activity(conn, 99999) is None
