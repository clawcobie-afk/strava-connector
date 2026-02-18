import pytest
from unittest.mock import patch, MagicMock
from strava.client import get_activities, get_activity, refresh_access_token

STRAVA_API = "https://www.strava.com/api/v3"


def make_response(data, status_code=200):
    mock = MagicMock()
    mock.status_code = status_code
    mock.json.return_value = data
    mock.raise_for_status.return_value = None
    return mock


def test_get_activities_calls_correct_endpoint(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response([]))
    get_activities("token123")
    mock_get.assert_called_once()
    url = mock_get.call_args[0][0]
    assert url == f"{STRAVA_API}/athlete/activities"


def test_get_activities_sends_access_token(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response([]))
    get_activities("token123")
    headers = mock_get.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer token123"


def test_get_activities_passes_page_and_per_page(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response([]))
    get_activities("token123", page=2, per_page=50)
    params = mock_get.call_args[1]["params"]
    assert params["page"] == 2
    assert params["per_page"] == 50


def test_get_activities_passes_after_param(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response([]))
    get_activities("token123", after=1700000000)
    params = mock_get.call_args[1]["params"]
    assert params["after"] == 1700000000


def test_get_activities_no_after_by_default(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response([]))
    get_activities("token123")
    params = mock_get.call_args[1]["params"]
    assert "after" not in params


def test_get_activities_returns_list(mocker):
    data = [{"id": 1, "name": "Run"}]
    mocker.patch("requests.get", return_value=make_response(data))
    result = get_activities("token123")
    assert result == data


def test_get_activity_calls_correct_endpoint(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response({"id": 42}))
    get_activity("token123", 42)
    url = mock_get.call_args[0][0]
    assert url == f"{STRAVA_API}/activities/42"


def test_get_activity_sends_access_token(mocker):
    mock_get = mocker.patch("requests.get", return_value=make_response({"id": 42}))
    get_activity("token123", 42)
    headers = mock_get.call_args[1]["headers"]
    assert headers["Authorization"] == "Bearer token123"


def test_get_activity_returns_dict(mocker):
    data = {"id": 42, "name": "Morning Run"}
    mocker.patch("requests.get", return_value=make_response(data))
    result = get_activity("token123", 42)
    assert result == data


def test_refresh_access_token_calls_token_endpoint(mocker):
    mock_post = mocker.patch(
        "requests.post",
        return_value=make_response({"access_token": "new", "refresh_token": "r2"}),
    )
    refresh_access_token("cid", "csecret", "old_refresh")
    url = mock_post.call_args[0][0]
    assert url == "https://www.strava.com/oauth/token"


def test_refresh_access_token_sends_correct_params(mocker):
    mock_post = mocker.patch(
        "requests.post",
        return_value=make_response({"access_token": "new", "refresh_token": "r2"}),
    )
    refresh_access_token("cid", "csecret", "old_refresh")
    data = mock_post.call_args[1]["data"]
    assert data["client_id"] == "cid"
    assert data["client_secret"] == "csecret"
    assert data["refresh_token"] == "old_refresh"
    assert data["grant_type"] == "refresh_token"


def test_refresh_access_token_returns_dict(mocker):
    response_data = {"access_token": "new_token", "refresh_token": "new_refresh"}
    mocker.patch("requests.post", return_value=make_response(response_data))
    result = refresh_access_token("cid", "csecret", "old")
    assert result == response_data
