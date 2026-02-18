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
    conn = sqlite3.connect(db_path)
    conn.execute(CREATE_TABLE_SQL)
    conn.commit()
    conn.close()


def upsert_activity(conn: sqlite3.Connection, activity: dict) -> None:
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


def get_activity_ids(conn: sqlite3.Connection) -> set:
    cursor = conn.execute("SELECT id FROM activities")
    return {row[0] for row in cursor.fetchall()}


def get_activity(conn: sqlite3.Connection, activity_id: int) -> dict | None:
    conn.row_factory = sqlite3.Row
    cursor = conn.execute("SELECT * FROM activities WHERE id = ?", (activity_id,))
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)
