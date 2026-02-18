import sqlite3
import json


CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS activities (
    id                   INTEGER PRIMARY KEY,
    name                 TEXT,
    type                 TEXT,
    sport_type           TEXT,
    distance             REAL,
    moving_time          INTEGER,
    elapsed_time         INTEGER,
    total_elevation_gain REAL,
    start_date           TEXT,
    start_date_local     TEXT,
    timezone             TEXT,
    raw_json             TEXT,
    synced_at            TEXT DEFAULT (datetime('now'))
);
"""


def init_db(db_path: str) -> None:
    """Create the SQLite database file and the activities table if they don't exist.

    Args:
        db_path: Filesystem path to the SQLite database file.
    """
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def upsert_activity(conn: sqlite3.Connection, activity: dict) -> None:
    """Insert or replace an activity record in the database.

    The full activity dict is also serialised and stored in the raw_json column.

    Args:
        conn: Open SQLite connection to the activities database.
        activity: Activity dict containing at least the columns defined in CREATE_TABLE_SQL.
    """
    conn.execute(
        """
        INSERT OR REPLACE INTO activities
            (id, name, type, sport_type, distance, moving_time, elapsed_time,
             total_elevation_gain, start_date, start_date_local, timezone, raw_json)
        VALUES
            (:id, :name, :type, :sport_type, :distance, :moving_time, :elapsed_time,
             :total_elevation_gain, :start_date, :start_date_local, :timezone, :raw_json)
        """,
        {**activity, "raw_json": json.dumps(activity)},
    )
    conn.commit()


def get_activity_ids(conn: sqlite3.Connection) -> set[int]:
    """Return the set of all activity IDs currently stored in the database.

    Args:
        conn: Open SQLite connection to the activities database.

    Returns:
        Set of integer activity IDs.
    """
    cursor = conn.execute("SELECT id FROM activities")
    return {row[0] for row in cursor.fetchall()}


def get_activity(conn: sqlite3.Connection, activity_id: int) -> dict | None:
    """Retrieve a single activity record by its ID.

    Args:
        conn: Open SQLite connection to the activities database.
        activity_id: Numeric Strava activity ID to look up.

    Returns:
        Activity record as a plain dict, or None if no matching row exists.
    """
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)
