import requests
from typing import TypedDict

STRAVA_API = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"


class TokenResponse(TypedDict):
    """Response payload returned by the Strava OAuth token endpoint."""

    access_token: str
    refresh_token: str
    expires_at: int
    expires_in: int
    token_type: str


def _auth_headers(access_token: str) -> dict[str, str]:
    """Return HTTP headers with a Bearer token for Strava API requests."""
    return {"Authorization": f"Bearer {access_token}"}


def get_activities(
    access_token: str,
    page: int = 1,
    per_page: int = 200,
    after: int | None = None,
) -> list[dict]:
    """Fetch a paginated list of the authenticated athlete's activities.

    Args:
        access_token: Valid Strava OAuth access token.
        page: Page number to fetch (1-based).
        per_page: Number of activities per page (max 200).
        after: Optional Unix timestamp; only activities after this time are returned.

    Returns:
        List of activity dicts as returned by the Strava API.
    """
    params: dict[str, int] = {"page": page, "per_page": per_page}
    if after is not None:
        params["after"] = after
    resp = requests.get(
        f"{STRAVA_API}/athlete/activities",
        headers=_auth_headers(access_token),
        params=params,
    )
    resp.raise_for_status()
    return resp.json()


def get_activity(access_token: str, activity_id: int) -> dict:
    """Fetch a single activity by ID from the Strava API.

    Args:
        access_token: Valid Strava OAuth access token.
        activity_id: Numeric Strava activity ID.

    Returns:
        Activity detail dict as returned by the Strava API.
    """
    resp = requests.get(
        f"{STRAVA_API}/activities/{activity_id}",
        headers=_auth_headers(access_token),
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    client_id: str, client_secret: str, refresh_token: str
) -> TokenResponse:
    """Exchange a refresh token for a new access token via the Strava OAuth endpoint.

    Args:
        client_id: Strava application client ID.
        client_secret: Strava application client secret.
        refresh_token: Current refresh token to exchange.

    Returns:
        TokenResponse dict containing the new access_token, refresh_token and expiry info.
    """
    resp = requests.post(
        TOKEN_URL,
        data={
            "client_id": client_id,
            "client_secret": client_secret,
            "refresh_token": refresh_token,
            "grant_type": "refresh_token",
        },
    )
    resp.raise_for_status()
    return resp.json()
