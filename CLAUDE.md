# CLAUDE.md — strava-connector

## Spuštění testů
```bash
source venv/bin/activate
pytest tests/ -v
```

## CLI
```bash
# Historický sync
STRAVA_CLIENT_ID=... STRAVA_CLIENT_SECRET=... \
STRAVA_ACCESS_TOKEN=... STRAVA_REFRESH_TOKEN=... \
python sync.py --db strava.db [--after 2024-01-01]

# Webhook server
STRAVA_ACCESS_TOKEN=... STRAVA_WEBHOOK_VERIFY_TOKEN=mytoken \
python webhook_server.py --db strava.db --port 8080
```

## Architektura
- `sync.py` — Click CLI, stránkuje API, skipuje existující ID
- `webhook_server.py` — Flask, GET /webhook (verify), POST /webhook (event)
- `strava/client.py` — `get_activities()`, `get_activity()`, `refresh_access_token()`
- `strava/db.py` — `init_db()`, `upsert_activity()`, `get_activity_ids()`, `get_activity()`
- `strava/webhook.py` — `handle_verify()`, `handle_event()`

## Env proměnné
- `STRAVA_CLIENT_ID`, `STRAVA_CLIENT_SECRET` — OAuth credentials
- `STRAVA_ACCESS_TOKEN`, `STRAVA_REFRESH_TOKEN` — tokeny (sync je auto-refreshuje)
- `STRAVA_WEBHOOK_VERIFY_TOKEN` — vlastní token pro Strava handshake

## Webhook registrace (jednorázově)
```bash
curl -X POST https://www.strava.com/api/v3/push_subscriptions \
  -F "client_id=$STRAVA_CLIENT_ID" -F "client_secret=$STRAVA_CLIENT_SECRET" \
  -F "callback_url=https://yourdomain.com/webhook" \
  -F "verify_token=$STRAVA_WEBHOOK_VERIFY_TOKEN"
```

## Konvence
- TDD: testy jsou mockované (requests, SQLite přes tmp_path)
- `handle_event` zpracovává jen `object_type=activity` + `aspect_type=create`
- `upsert_activity` ukládá kompletní JSON do sloupce `raw_json`
