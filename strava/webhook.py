import sqlite3
from strava.client import get_activity
from strava.db import upsert_activity


def handle_verify(args: dict, verify_token: str) -> dict | None:
    if args.get("hub.verify_token") != verify_token:
        return None
    challenge = args.get("hub.challenge")
    if challenge is None:
        return None
    return {"hub.challenge": challenge}


def handle_event(event: dict, access_token: str, conn: sqlite3.Connection) -> str:
    if event.get("object_type") != "activity":
        return "ignored"
    if event.get("aspect_type") != "create":
        return "ignored"
    activity_id = event["object_id"]
    activity = get_activity(access_token, activity_id)
    upsert_activity(conn, activity)
    return "saved"
