# Admin Vitals

The TYP0 server exposes a protected admin dashboard plus a JSON endpoint for project health and status information.

## URLs

| URL | Purpose | Auth |
|---|---|---|
| `GET /admin` | HTML dashboard with login form, auto-refreshes every 10 s | none (page itself) |
| `GET /api/admin/vitals` | JSON vitals payload | `Authorization: Bearer <ADMIN_PASSWORD>` |

## Authentication

The JSON endpoint requires the `Authorization: Bearer <ADMIN_PASSWORD>` header. The password is checked with a constant-time comparison.

The HTML page at `/admin` is unauthenticated — it just renders a login form, then calls the JSON endpoint with the entered password as a Bearer token. The password is held only in memory (no `localStorage`), so closing the tab signs you out.

**Default password:** `admin_secret_123` (development only — set `ADMIN_PASSWORD` for production).

### Setting a Custom Password

Set the `ADMIN_PASSWORD` environment variable when starting the server:

```bash
# Linux/Mac
export ADMIN_PASSWORD="your_secure_password"
python server/server.py

# Windows (PowerShell)
$env:ADMIN_PASSWORD = "your_secure_password"
python server/server.py

# Docker/CI
docker run -e ADMIN_PASSWORD="your_secure_password" ...
```

In CI/CD, store it as a GitHub Actions secret named `ADMIN_PASSWORD`; both `pybag-game.yml` (deploy + health checks) and `tests.yml` (CI vitals job) read it from there.

## Response Format

```json
{
  "timestamp": "2026-04-29T12:34:56.789Z",
  "server": {
    "uptime_seconds": 3600.5,
    "uptime_hours": 1.0,
    "host": "0.0.0.0",
    "port": 15090
  },
  "multiplayer": {
    "active_players": 2,
    "active_games": 1,
    "pending_challenges": 0
  },
  "scores": {
    "simon":      { "count": 10, "top_score": 5000, "top_player": "Player1" },
    "bopit":      { "count":  8, "top_score": 3500, "top_player": "Player2" },
    "keys_ninja": { "count":  5, "top_score": 2000, "top_player": "Player3" },
    "multiplayer":{ "count":  0, "top_score":    0, "top_player": null }
  },
  "build": {
    "timestamp": "2026-04-29T10:00:00Z",
    "static_dir": "/path/to/build/web"
  },
  "git": {
    "commit": "abc1234",
    "branch": "main"
  }
}
```

## Example Usage

### Browser

Open `http://localhost:15090/admin` and enter the password.

### curl

```bash
curl -H "Authorization: Bearer admin_secret_123" \
  http://localhost:15090/api/admin/vitals
```

### Python

```python
import requests

password = "admin_secret_123"
r = requests.get(
    "http://localhost:15090/api/admin/vitals",
    headers={"Authorization": f"Bearer {password}"},
)
vitals = r.json()
print(f"Server uptime: {vitals['server']['uptime_hours']} hours")
print(f"Active players: {vitals['multiplayer']['active_players']}")
print(f"Git commit: {vitals['git']['commit']}")
```

### Test script

```bash
python test_vitals.py admin_secret_123
```

## Vitals Provided

| Category | Details |
|----------|---------|
| **Server** | Uptime (seconds/hours), host, port |
| **Multiplayer** | Active players, active games, pending challenges |
| **Scores** | Per-game-type stats (count, top score, top player) |
| **Build** | Build timestamp, static directory path |
| **Git** | Current commit hash, branch name |

## Security Notes

- Always set a strong `ADMIN_PASSWORD` in production — leaving it as the default disables protection.
- Use HTTPS when accessing this endpoint over the network. The Bearer token is sent in plaintext over HTTP.
- The Bearer header is *not* logged by nginx by default (unlike a query-string password). The server itself does not log auth headers either.
- Password comparison uses `hmac.compare_digest` (constant-time) to avoid timing attacks.
- Rotate the password regularly and monitor access for suspicious activity.

## Error Responses

```bash
# Wrong password
$ curl -H "Authorization: Bearer wrong" http://localhost:15090/api/admin/vitals
Unauthorized   # HTTP 401

# Missing header
$ curl http://localhost:15090/api/admin/vitals
Unauthorized   # HTTP 401
```
