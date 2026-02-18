#!/usr/bin/env python3
import os
import sqlite3
from datetime import datetime, timezone

import click

from strava.client import get_activities, refresh_access_token
from strava.db import init_db, upsert_activity, get_activity_ids


@click.command()
@click.option("--db", default="strava.db", show_default=True, help="Path to SQLite database")
@click.option("--after", default=None, help="Only sync activities after this date (YYYY-MM-DD)")
def main(db, after):
    client_id = os.environ["STRAVA_CLIENT_ID"]
    client_secret = os.environ["STRAVA_CLIENT_SECRET"]
    access_token = os.environ["STRAVA_ACCESS_TOKEN"]
    refresh_token = os.environ["STRAVA_REFRESH_TOKEN"]

    # Refresh token upfront to ensure it's valid
    tokens = refresh_access_token(client_id, client_secret, refresh_token)
    access_token = tokens["access_token"]

    after_ts = None
    if after:
        dt = datetime.strptime(after, "%Y-%m-%d").replace(tzinfo=timezone.utc)
        after_ts = int(dt.timestamp())

    init_db(db)
    conn = sqlite3.connect(db)
    conn.row_factory = sqlite3.Row
    existing_ids = get_activity_ids(conn)

    click.echo("Stahuju aktivity...")

    saved = 0
    skipped = 0
    page = 1
    per_page = 200

    while True:
        activities = get_activities(access_token, page=page, per_page=per_page, after=after_ts)
        if not activities:
            break

        for activity in activities:
            activity_id = activity["id"]
            if activity_id in existing_ids:
                skipped += 1
                continue

            upsert_activity(conn, activity)
            saved += 1
            distance_km = activity.get("distance", 0) / 1000
            name = activity.get("name", "")
            date = activity.get("start_date_local", activity.get("start_date", ""))[:10]
            click.echo(f"[{saved}] {name} — {distance_km:.1f} km — {date}")

        if len(activities) < per_page:
            break
        page += 1

    conn.close()
    click.echo(f"Hotovo: {saved} aktivit uloženo, {skipped} přeskočeno (již existují).")


if __name__ == "__main__":
    main()
