#!/usr/bin/env python3
import os
import sqlite3

import click
from flask import Flask, request, jsonify, abort

from strava.db import init_db
from strava.webhook import handle_verify, handle_event

app = Flask(__name__)

_db_path: str = ""


def get_conn() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/webhook", methods=["GET"])
def webhook_verify():
    verify_token = os.environ.get("STRAVA_WEBHOOK_VERIFY_TOKEN", "")
    result = handle_verify(request.args.to_dict(), verify_token)
    if result is None:
        abort(403)
    return jsonify(result)


@app.route("/webhook", methods=["POST"])
def webhook_event():
    event = request.get_json(force=True)
    access_token = os.environ.get("STRAVA_ACCESS_TOKEN", "")
    conn = get_conn()
    try:
        status = handle_event(event, access_token, conn)
    finally:
        conn.close()
    return jsonify({"status": status})


@click.command()
@click.option("--db", default="strava.db", show_default=True, help="Path to SQLite database")
@click.option("--port", default=8080, show_default=True, help="Port to listen on")
def main(db, port):
    global _db_path
    _db_path = db
    init_db(db)
    app.run(host="0.0.0.0", port=port)


if __name__ == "__main__":
    main()
