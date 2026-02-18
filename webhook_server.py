#!/usr/bin/env python3
import os
import sqlite3
import threading
import time

import click
from flask import Flask, request, jsonify, abort

from strava.client import refresh_access_token
from strava.db import init_db
from strava.webhook import handle_verify, handle_event

app = Flask(__name__)

_db_path: str = ""
_access_token: str = ""
_token_lock = threading.Lock()

_REFRESH_INTERVAL = 5 * 3600  # 5 hours; Strava tokens expire after 6


def _token_refresh_loop(client_id: str, client_secret: str, refresh_token: str) -> None:
    """Background daemon: refresh the Strava access token every 5 hours."""
    while True:
        time.sleep(_REFRESH_INTERVAL)
        try:
            tokens = refresh_access_token(client_id, client_secret, refresh_token)
            with _token_lock:
                global _access_token
                _access_token = tokens["access_token"]
        except Exception as e:
            print(f"[token-refresh] failed: {e}", flush=True)


def get_conn() -> sqlite3.Connection:
    """Open and return a new SQLite connection to the configured database.

    Returns:
        SQLite connection with row_factory set to sqlite3.Row.
    """
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    """Handle the Strava webhook subscription verification handshake (GET /webhook).

    Reads the hub.verify_token and hub.challenge from query parameters and
    returns the challenge echo on success, or aborts with 403 on failure.
    """
    verify_token = os.environ.get("STRAVA_WEBHOOK_VERIFY_TOKEN", "")
    result = handle_verify(request.args.to_dict(), verify_token)
    if result is None:
        abort(403)
    return jsonify(result)


@app.route("/webhook", methods=["POST"])
def webhook_event():
    """Handle an incoming Strava webhook event (POST /webhook).

    Parses the JSON body, delegates to handle_event, and returns a JSON status
    response indicating whether the event was saved or ignored.
    """
    event = request.get_json(force=True)
    with _token_lock:
        access_token = _access_token
    conn = get_conn()
    try:
        status = handle_event(event, access_token, conn)
    finally:
        conn.close()
    return jsonify({"status": status})


@click.command()
@click.option("--db", default="strava.db", show_default=True, help="Path to SQLite database")
@click.option("--port", default=8080, show_default=True, help="Port to listen on")
def main(db: str, port: int) -> None:
    """Initialise the database, start the token refresh thread, and run the Flask server."""
    global _db_path, _access_token
    _db_path = db
    _access_token = os.environ["STRAVA_ACCESS_TOKEN"]
    client_id = os.environ["STRAVA_CLIENT_ID"]
    client_secret = os.environ["STRAVA_CLIENT_SECRET"]
    refresh_token = os.environ["STRAVA_REFRESH_TOKEN"]

    t = threading.Thread(
        target=_token_refresh_loop,
        args=(client_id, client_secret, refresh_token),
        daemon=True,
    )
    t.start()

    init_db(db)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
