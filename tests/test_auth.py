import pytest
from click.testing import CliRunner
from unittest.mock import patch

from auth import main


TOKEN_RESPONSE = {
    "access_token": "fresh_access_token",
    "refresh_token": "old_refresh_token",
    "expires_at": 9999999999,
    "expires_in": 21600,
    "token_type": "Bearer",
}


def invoke_main(tmp_path, extra_args=None):
    """Invoke the main CLI command inside tmp_path with default valid credentials."""
    runner = CliRunner()
    args = [
        "--client-id", "my_client_id",
        "--client-secret", "my_client_secret",
        "--access-token", "user_access_token",
        "--refresh-token", "my_refresh_token",
    ]
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(main, args, catch_exceptions=False)


def test_successful_auth_saves_env_file(tmp_path, mocker):
    """Successful auth should create a .env file in the current directory."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [
            "--client-id", "my_client_id",
            "--client-secret", "my_client_secret",
            "--access-token", "user_access_token",
            "--refresh-token", "my_refresh_token",
        ], catch_exceptions=False)

    assert result.exit_code == 0
    assert "Credentials saved to .env" in result.output


def test_successful_auth_env_file_content(tmp_path, mocker):
    """The saved .env file must contain all four variables with correct values."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(main, [
            "--client-id", "my_client_id",
            "--client-secret", "my_client_secret",
            "--access-token", "user_access_token",
            "--refresh-token", "my_refresh_token",
        ], catch_exceptions=False)

        import os
        env_path = os.path.join(td, ".env")
        with open(env_path) as f:
            content = f.read()

    assert "STRAVA_CLIENT_ID=my_client_id\n" in content
    assert "STRAVA_CLIENT_SECRET=my_client_secret\n" in content
    assert "STRAVA_ACCESS_TOKEN=fresh_access_token\n" in content
    assert "STRAVA_REFRESH_TOKEN=my_refresh_token\n" in content


def test_failed_refresh_exits_with_code_1(tmp_path, mocker):
    """When refresh_access_token raises, the command must exit with code 1."""
    mocker.patch("auth.refresh_access_token", side_effect=Exception("HTTP 401 Unauthorized"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [
            "--client-id", "bad_id",
            "--client-secret", "bad_secret",
            "--access-token", "bad_token",
            "--refresh-token", "bad_refresh",
        ])

    assert result.exit_code == 1


def test_failed_refresh_prints_error_message(tmp_path, mocker):
    """When refresh fails, a clear error message must be printed."""
    mocker.patch("auth.refresh_access_token", side_effect=Exception("HTTP 401 Unauthorized"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, [
            "--client-id", "bad_id",
            "--client-secret", "bad_secret",
            "--access-token", "bad_token",
            "--refresh-token", "bad_refresh",
        ])

    assert "Error" in result.output or "Error" in (result.stderr or "")


def test_saved_access_token_comes_from_refresh_response(tmp_path, mocker):
    """The .env access token must be the one returned by the refresh, not user input."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        runner.invoke(main, [
            "--client-id", "my_client_id",
            "--client-secret", "my_client_secret",
            "--access-token", "user_access_token",   # this value must NOT appear in .env
            "--refresh-token", "my_refresh_token",
        ], catch_exceptions=False)

        import os
        env_path = os.path.join(td, ".env")
        with open(env_path) as f:
            content = f.read()

    # The fresh token from the API response must be present
    assert "STRAVA_ACCESS_TOKEN=fresh_access_token\n" in content
    # The token the user typed must NOT be stored as the access token
    assert "STRAVA_ACCESS_TOKEN=user_access_token" not in content
