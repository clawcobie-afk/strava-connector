# strava-connector

Synchronizuje Strava aktivity do SQLite. Podporuje historický bulk sync a real-time webhook notifikace.

## Instalace

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Historický sync

```bash
export STRAVA_CLIENT_ID=12345
export STRAVA_CLIENT_SECRET=abc...
export STRAVA_ACCESS_TOKEN=...
export STRAVA_REFRESH_TOKEN=...

python sync.py --db strava.db
python sync.py --db strava.db --after 2024-01-01
```

### Flagy

| Flag | Výchozí | Popis |
|------|---------|-------|
| `--db` | `strava.db` | Cesta k SQLite databázi |
| `--after` | — | Synchronizovat jen aktivity od tohoto data (YYYY-MM-DD) |

Výstup:
```
Stahuju aktivity...
[1] Morning Run — 10.2 km — 2024-03-15
[2] Evening Ride — 42.0 km — 2024-03-16
Hotovo: 247 aktivit uloženo, 12 přeskočeno (již existují).
```

## Webhook server

```bash
export STRAVA_ACCESS_TOKEN=...
export STRAVA_WEBHOOK_VERIFY_TOKEN=mytoken

python webhook_server.py --db strava.db --port 8080
```

### Flagy

| Flag | Výchozí | Popis |
|------|---------|-------|
| `--db` | `strava.db` | Cesta k SQLite databázi |
| `--port` | `8080` | Port serveru |

### Endpointy

- `GET /webhook` — verifikace Strava subscripce
- `POST /webhook` — příjem aktivity event → uložení do DB

### Registrace webhooků (jednorázově)

```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F "client_id=$STRAVA_CLIENT_ID" \
  -F "client_secret=$STRAVA_CLIENT_SECRET" \
  -F "callback_url=https://yourdomain.com/webhook" \
  -F "verify_token=$STRAVA_WEBHOOK_VERIFY_TOKEN"
```

## Env proměnné

| Proměnná | Kde se používá | Popis |
|----------|---------------|-------|
| `STRAVA_CLIENT_ID` | sync | OAuth client ID |
| `STRAVA_CLIENT_SECRET` | sync | OAuth client secret |
| `STRAVA_ACCESS_TOKEN` | sync, webhook | Aktuální access token |
| `STRAVA_REFRESH_TOKEN` | sync | Refresh token (auto-rotate) |
| `STRAVA_WEBHOOK_VERIFY_TOKEN` | webhook | Vlastní verify token pro handshake |

## SQLite schéma

```sql
CREATE TABLE activities (
    id                   INTEGER PRIMARY KEY,  -- Strava activity ID
    name                 TEXT,
    type                 TEXT,                 -- Run, Ride, Swim...
    sport_type           TEXT,
    distance             REAL,                 -- metry
    moving_time          INTEGER,              -- sekundy
    elapsed_time         INTEGER,
    total_elevation_gain REAL,
    start_date           TEXT,                 -- ISO 8601 UTC
    start_date_local     TEXT,
    timezone             TEXT,
    raw_json             TEXT,                 -- kompletní JSON z API
    synced_at            TEXT DEFAULT (datetime('now'))
);
```

## Testy

```bash
pytest tests/ -v
```
