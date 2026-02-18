import requests

STRAVA_API = "https://www.strava.com/api/v3"
TOKEN_URL = "https://www.strava.com/oauth/token"


def _auth_headers(access_token: str) -> dict:
    return {"Authorization": f"Bearer {access_token}"}


def get_activities(
    access_token: str,
    page: int = 1,
    per_page: int = 200,
    after: int | None = None,
) -> list[dict]:
    params = {"page": page, "per_page": per_page}
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
    resp = requests.get(
        f"{STRAVA_API}/activities/{activity_id}",
        headers=_auth_headers(access_token),
    )
    resp.raise_for_status()
    return resp.json()


def refresh_access_token(
    client_id: str, client_secret: str, refresh_token: str
) -> dict:
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
