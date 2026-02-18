#!/usr/bin/env python3
import sys

import click

from strava.client import refresh_access_token


@click.command()
@click.option("--client-id", prompt=True, help="Strava application client ID.")
@click.option("--client-secret", prompt=True, help="Strava application client secret.")
@click.option("--access-token", prompt=True, help="Current Strava access token.")
@click.option("--refresh-token", prompt=True, help="Current Strava refresh token.")
def main(client_id: str, client_secret: str, access_token: str, refresh_token: str) -> None:
    """Validate Strava OAuth credentials and save them to a .env file."""
    try:
        tokens = refresh_access_token(client_id, client_secret, refresh_token)
    except Exception as e:
        click.echo(f"Error: Failed to validate credentials — {e}", err=True)
        sys.exit(1)

    new_access_token = tokens["access_token"]

    env_content = (
        f"STRAVA_CLIENT_ID={client_id}\n"
        f"STRAVA_CLIENT_SECRET={client_secret}\n"
        f"STRAVA_ACCESS_TOKEN={new_access_token}\n"
        f"STRAVA_REFRESH_TOKEN={refresh_token}\n"
    )

    env_path = ".env"
    with open(env_path, "w") as f:
        f.write(env_content)

    click.echo(f"Credentials saved to {env_path}")


if __name__ == "__main__":
    main()
