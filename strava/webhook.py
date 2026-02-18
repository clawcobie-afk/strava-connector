import sqlite3
from typing import TypedDict

from strava.client import get_activity
from strava.db import upsert_activity


class StravaEvent(TypedDict, total=False):
    """Payload sent by Strava to the webhook callback URL on each push event."""

    object_type: str   # "activity" or "athlete"
    aspect_type: str   # "create", "update", or "delete"
    object_id: int     # ID of the affected object
    owner_id: int      # Athlete ID that owns the object
    subscription_id: int
    event_time: int    # Unix timestamp of the event


def handle_verify(args: dict[str, str], verify_token: str) -> dict[str, str] | None:
    """Validate a Strava webhook subscription verification request.

    Args:
        args: Query-string parameters from the GET /webhook request.
        verify_token: The expected verification token configured for this subscription.

    Returns:
        A dict with the hub.challenge echo if verification succeeds, or None on failure.
    """
    if args.get("hub.verify_token") != verify_token:
        return None
    challenge = args.get("hub.challenge")
    if not challenge:
        return None
    return {"hub.challenge": challenge}


def handle_event(
    event: StravaEvent, access_token: str, conn: sqlite3.Connection
) -> str | None:
    """Process an incoming Strava webhook event and persist new activities.

    Only ``object_type=activity`` / ``aspect_type=create`` events are acted on;
    all other events return ``"ignored"``.

    Args:
        event: Parsed webhook event payload from Strava.
        access_token: Valid Strava OAuth access token used to fetch activity details.
        conn: Open SQLite connection used to store the fetched activity.

    Returns:
        ``"saved"`` when the activity was fetched and stored, ``"ignored"`` when the
        event type is not handled, or ``None`` if the object ID is missing/invalid.
    """
    if event.get("object_type") != "activity":
        return "ignored"
    if event.get("aspect_type") != "create":
        return "ignored"
    try:
        activity_id = int(event["object_id"])
    except (KeyError, ValueError, TypeError):
        return None
    activity = get_activity(access_token, activity_id)
    upsert_activity(conn, activity)
    return "saved"
