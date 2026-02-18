import sqlite3
import pytest
from unittest.mock import MagicMock, patch
from strava.webhook import handle_verify, handle_event

VERIFY_TOKEN = "mysecrettoken"


# --- handle_verify ---

def test_handle_verify_returns_challenge_on_correct_token():
    args = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "abc123",
    }
    result = handle_verify(args, VERIFY_TOKEN)
    assert result == {"hub.challenge": "abc123"}


def test_handle_verify_returns_none_on_wrong_token():
    args = {
        "hub.mode": "subscribe",
        "hub.verify_token": "wrong",
        "hub.challenge": "abc123",
    }
    result = handle_verify(args, VERIFY_TOKEN)
    assert result is None


def test_handle_verify_returns_none_when_token_missing():
    args = {"hub.challenge": "abc123"}
    result = handle_verify(args, VERIFY_TOKEN)
    assert result is None


# --- handle_event ---

@pytest.fixture
def conn(tmp_path):
    from strava.db import init_db
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    c = sqlite3.connect(db_path)
    c.row_factory = sqlite3.Row
    yield c
    c.close()


CREATE_EVENT = {
    "object_type": "activity",
    "aspect_type": "create",
    "object_id": 42,
    "owner_id": 1,
}

ACTIVITY_DATA = {
    "id": 42,
    "name": "Morning Run",
    "type": "Run",
    "sport_type": "Run",
    "distance": 5000.0,
    "moving_time": 1800,
    "elapsed_time": 1850,
    "total_elevation_gain": 20.0,
    "start_date": "2024-03-15T06:00:00Z",
    "start_date_local": "2024-03-15T07:00:00",
    "timezone": "Europe/Prague",
}


def test_handle_event_create_calls_get_activity(mocker, conn):
    mock_get = mocker.patch("strava.webhook.get_activity", return_value=ACTIVITY_DATA)
    result = handle_event(CREATE_EVENT, "token123", conn)
    mock_get.assert_called_once_with("token123", 42)
    assert result == "saved"


def test_handle_event_create_saves_to_db(mocker, conn):
    mocker.patch("strava.webhook.get_activity", return_value=ACTIVITY_DATA)
    handle_event(CREATE_EVENT, "token123", conn)
    from strava.db import get_activity
    saved = get_activity(conn, 42)
    assert saved is not None
    assert saved["name"] == "Morning Run"


def test_handle_event_ignores_update(mocker, conn):
    mock_get = mocker.patch("strava.webhook.get_activity", return_value=ACTIVITY_DATA)
    event = {**CREATE_EVENT, "aspect_type": "update"}
    result = handle_event(event, "token123", conn)
    mock_get.assert_not_called()
    assert result == "ignored"


def test_handle_event_ignores_delete(mocker, conn):
    mock_get = mocker.patch("strava.webhook.get_activity", return_value=ACTIVITY_DATA)
    event = {**CREATE_EVENT, "aspect_type": "delete"}
    result = handle_event(event, "token123", conn)
    mock_get.assert_not_called()
    assert result == "ignored"


def test_handle_event_ignores_athlete_object_type(mocker, conn):
    mock_get = mocker.patch("strava.webhook.get_activity", return_value=ACTIVITY_DATA)
    event = {**CREATE_EVENT, "object_type": "athlete"}
    result = handle_event(event, "token123", conn)
    mock_get.assert_not_called()
    assert result == "ignored"
