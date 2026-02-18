#!/usr/bin/env python3
import os
import sys

import click

from strava.client import refresh_access_token

CENTRAL_CONFIG_DIR = os.path.expanduser("~/.config/knowledge-vault")
CENTRAL_CONFIG_PATH = os.path.join(CENTRAL_CONFIG_DIR, ".env")


def _merge_env_file(path: str, updates: dict) -> None:
    """Read an existing key=value env file, update the given keys, and write it back.

    Lines that don't correspond to a key in *updates* are preserved unchanged.
    Keys in *updates* that are not already present are appended at the end.
    """
    existing_lines: list[str] = []
    if os.path.exists(path):
        with open(path) as f:
            existing_lines = f.readlines()

    # Rebuild line list, replacing values for keys we own.
    written_keys: set[str] = set()
    new_lines: list[str] = []
    for line in existing_lines:
        stripped = line.rstrip("\n")
        if "=" in stripped and not stripped.startswith("#"):
            key = stripped.split("=", 1)[0].strip()
            if key in updates:
                new_lines.append(f"{key}={updates[key]}\n")
                written_keys.add(key)
                continue
        new_lines.append(line if line.endswith("\n") else line + "\n")

    # Append any keys that were not already present.
    for key, value in updates.items():
        if key not in written_keys:
            new_lines.append(f"{key}={value}\n")

    with open(path, "w") as f:
        f.writelines(new_lines)


@click.command()
@click.option("--client-id", prompt=True, help="Strava application client ID.")
@click.option("--client-secret", prompt=True, help="Strava application client secret.")
@click.option("--access-token", prompt=True, help="Current Strava access token.")
@click.option("--refresh-token", prompt=True, help="Current Strava refresh token.")
@click.option(
    "--verify-token",
    default=None,
    prompt="Webhook verify token (leave empty to skip)",
    prompt_required=False,
    help="Optional webhook verify token.",
)
def main(
    client_id: str,
    client_secret: str,
    access_token: str,
    refresh_token: str,
    verify_token: str | None,
) -> None:
    """Validate Strava OAuth credentials and save them to .env files."""
    try:
        tokens = refresh_access_token(client_id, client_secret, refresh_token)
    except Exception as e:
        click.echo(f"Error: Failed to validate credentials — {e}", err=True)
        sys.exit(1)

    new_access_token = tokens["access_token"]

    strava_keys: dict[str, str] = {
        "STRAVA_CLIENT_ID": client_id,
        "STRAVA_CLIENT_SECRET": client_secret,
        "STRAVA_ACCESS_TOKEN": new_access_token,
        "STRAVA_REFRESH_TOKEN": refresh_token,
    }
    if verify_token:
        strava_keys["STRAVA_WEBHOOK_VERIFY_TOKEN"] = verify_token

    # Write local .env (overwrite entirely — existing behaviour).
    local_env_lines = "".join(f"{k}={v}\n" for k, v in strava_keys.items())
    env_path = ".env"
    with open(env_path, "w") as f:
        f.write(local_env_lines)

    # Write central config (merge — only update STRAVA_* keys).
    os.makedirs(CENTRAL_CONFIG_DIR, exist_ok=True)
    _merge_env_file(CENTRAL_CONFIG_PATH, strava_keys)

    click.echo(f"Config written to .env and {CENTRAL_CONFIG_PATH}")


if __name__ == "__main__":
    main()
