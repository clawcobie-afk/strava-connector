import os

import pytest
from click.testing import CliRunner
from unittest.mock import patch

from auth import main, CENTRAL_CONFIG_PATH, CENTRAL_CONFIG_DIR, _merge_env_file


TOKEN_RESPONSE = {
    "access_token": "fresh_access_token",
    "refresh_token": "old_refresh_token",
    "expires_at": 9999999999,
    "expires_in": 21600,
    "token_type": "Bearer",
}

BASE_ARGS = [
    "--client-id", "my_client_id",
    "--client-secret", "my_client_secret",
    "--access-token", "user_access_token",
    "--refresh-token", "my_refresh_token",
]


def _invoke(runner, extra_args=None, **invoke_kwargs):
    args = list(BASE_ARGS)
    if extra_args:
        args.extend(extra_args)
    return runner.invoke(main, args, catch_exceptions=False, **invoke_kwargs)


# ---------------------------------------------------------------------------
# Local .env tests (existing behaviour)
# ---------------------------------------------------------------------------

def test_successful_auth_saves_env_file(tmp_path, mocker):
    """Successful auth should create a .env file in the current directory."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(tmp_path / "central"))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(tmp_path / "central" / ".env"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = _invoke(runner)

    assert result.exit_code == 0
    assert ".env" in result.output


def test_successful_auth_env_file_content(tmp_path, mocker):
    """The saved .env file must contain all four variables with correct values."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(tmp_path / "central"))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(tmp_path / "central" / ".env"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        _invoke(runner)
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
        result = runner.invoke(main, BASE_ARGS)

    assert result.exit_code == 1


def test_failed_refresh_prints_error_message(tmp_path, mocker):
    """When refresh fails, a clear error message must be printed."""
    mocker.patch("auth.refresh_access_token", side_effect=Exception("HTTP 401 Unauthorized"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = runner.invoke(main, BASE_ARGS)

    assert "Error" in result.output or "Error" in (result.stderr or "")


def test_saved_access_token_comes_from_refresh_response(tmp_path, mocker):
    """The .env access token must be the one returned by the refresh, not user input."""
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(tmp_path / "central"))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(tmp_path / "central" / ".env"))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        _invoke(runner)
        env_path = os.path.join(td, ".env")
        with open(env_path) as f:
            content = f.read()

    assert "STRAVA_ACCESS_TOKEN=fresh_access_token\n" in content
    assert "STRAVA_ACCESS_TOKEN=user_access_token" not in content


# ---------------------------------------------------------------------------
# Central config tests
# ---------------------------------------------------------------------------

def test_central_config_dir_created(tmp_path, mocker):
    """The central config directory must be created if it does not exist."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = _invoke(runner)

    assert result.exit_code == 0
    assert central_dir.exists()


def test_central_config_written(tmp_path, mocker):
    """Central config must contain all four STRAVA_* keys after a successful run."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = _invoke(runner)

    assert result.exit_code == 0
    content = central_env.read_text()
    assert "STRAVA_CLIENT_ID=my_client_id\n" in content
    assert "STRAVA_CLIENT_SECRET=my_client_secret\n" in content
    assert "STRAVA_ACCESS_TOKEN=fresh_access_token\n" in content
    assert "STRAVA_REFRESH_TOKEN=my_refresh_token\n" in content


def test_central_config_merges_existing_keys(tmp_path):
    """_merge_env_file must preserve non-STRAVA keys and update STRAVA keys."""
    env_file = tmp_path / ".env"
    env_file.write_text(
        "OTHER_KEY=keep_me\n"
        "STRAVA_CLIENT_ID=old_id\n"
        "ANOTHER_KEY=also_keep\n"
    )
    _merge_env_file(str(env_file), {"STRAVA_CLIENT_ID": "new_id", "STRAVA_ACCESS_TOKEN": "tok"})
    content = env_file.read_text()
    assert "OTHER_KEY=keep_me\n" in content
    assert "ANOTHER_KEY=also_keep\n" in content
    assert "STRAVA_CLIENT_ID=new_id\n" in content
    assert "STRAVA_CLIENT_ID=old_id" not in content
    assert "STRAVA_ACCESS_TOKEN=tok\n" in content


def test_central_config_created_from_scratch(tmp_path):
    """_merge_env_file must work when the file does not exist yet."""
    env_file = tmp_path / "new.env"
    _merge_env_file(str(env_file), {"STRAVA_CLIENT_ID": "cid"})
    assert "STRAVA_CLIENT_ID=cid\n" in env_file.read_text()


def test_success_message_mentions_both_files(tmp_path, mocker):
    """The final echo must mention both .env and the central config path."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        result = _invoke(runner)

    assert ".env" in result.output
    assert str(central_env) in result.output


# ---------------------------------------------------------------------------
# Webhook verify token tests
# ---------------------------------------------------------------------------

def test_verify_token_written_to_local_env(tmp_path, mocker):
    """When --verify-token is supplied it must appear in the local .env."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        _invoke(runner, extra_args=["--verify-token", "mysecret"])
        content = open(os.path.join(td, ".env")).read()

    assert "STRAVA_WEBHOOK_VERIFY_TOKEN=mysecret\n" in content


def test_verify_token_written_to_central_config(tmp_path, mocker):
    """When --verify-token is supplied it must appear in the central config."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path):
        _invoke(runner, extra_args=["--verify-token", "mysecret"])

    assert "STRAVA_WEBHOOK_VERIFY_TOKEN=mysecret\n" in central_env.read_text()


def test_verify_token_absent_when_empty(tmp_path, mocker):
    """When --verify-token is not provided the key must not appear in either file."""
    central_dir = tmp_path / "central"
    central_env = central_dir / ".env"
    mocker.patch("auth.refresh_access_token", return_value=TOKEN_RESPONSE)
    mocker.patch("auth.CENTRAL_CONFIG_DIR", str(central_dir))
    mocker.patch("auth.CENTRAL_CONFIG_PATH", str(central_env))
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        _invoke(runner)
        local_content = open(os.path.join(td, ".env")).read()

    assert "STRAVA_WEBHOOK_VERIFY_TOKEN" not in local_content
    assert "STRAVA_WEBHOOK_VERIFY_TOKEN" not in central_env.read_text()
