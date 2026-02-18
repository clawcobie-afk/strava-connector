#!/usr/bin/env python3
import os

import click

from strava.client import refresh_access_token


@click.command()
def main() -> None:
    """Check that all required Strava environment variables are set and the API is reachable."""
    failures = 0

    def check(label: str, ok: bool, message: str = "") -> bool:
        nonlocal failures
        if ok:
            click.echo(f"OK    {label}")
        else:
            suffix = f" — {message}" if message else ""
            click.echo(f"FAIL  {label}{suffix}")
            failures += 1
        return ok

    client_id = os.environ.get("STRAVA_CLIENT_ID", "")
    client_secret = os.environ.get("STRAVA_CLIENT_SECRET", "")
    access_token = os.environ.get("STRAVA_ACCESS_TOKEN", "")
    refresh_token = os.environ.get("STRAVA_REFRESH_TOKEN", "")

    ok_client_id = check("STRAVA_CLIENT_ID is set", bool(client_id))
    ok_client_secret = check("STRAVA_CLIENT_SECRET is set", bool(client_secret))
    ok_access_token = check("STRAVA_ACCESS_TOKEN is set", bool(access_token))
    ok_refresh_token = check("STRAVA_REFRESH_TOKEN is set", bool(refresh_token))

    if ok_client_id and ok_client_secret and ok_access_token and ok_refresh_token:
        try:
            refresh_access_token(client_id, client_secret, refresh_token)
            check("Strava API is reachable", True)
        except Exception as e:
            check("Strava API is reachable", False, str(e))

    if failures == 0:
        click.echo("All checks passed.")
    else:
        click.echo(f"{failures} check(s) failed.")


if __name__ == "__main__":
    main()
