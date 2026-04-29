# Admin Vitals Endpoint

The TYP0 server includes a protected admin endpoint that provides project health and status information.

## Endpoint

```
GET /api/admin/vitals?password=<ADMIN_PASSWORD>
```

## Authentication

The endpoint requires a query parameter `password` that matches the server's `ADMIN_PASSWORD` environment variable.

**Default password:** `admin_secret_123`

### Setting a Custom Password

When starting the server, set the `ADMIN_PASSWORD` environment variable:

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

## Response Format

The endpoint returns a JSON object with the following structure:

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
    "simon": {
      "count": 10,
      "top_score": 5000,
      "top_player": "Player1"
    },
    "bopit": {
      "count": 8,
      "top_score": 3500,
      "top_player": "Player2"
    },
    "keys_ninja": {
      "count": 5,
      "top_score": 2000,
      "top_player": "Player3"
    },
    "multiplayer": {
      "count": 0,
      "top_score": 0,
      "top_player": null
    }
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

### Using curl

```bash
# With default password
curl "http://localhost:15090/api/admin/vitals?password=admin_secret_123"

# With custom password
curl "http://localhost:15090/api/admin/vitals?password=your_secure_password"
```

### Using Python

```python
import requests

password = "admin_secret_123"
response = requests.get(f"http://localhost:15090/api/admin/vitals?password={password}")
vitals = response.json()

print(f"Server uptime: {vitals['server']['uptime_hours']} hours")
print(f"Active players: {vitals['multiplayer']['active_players']}")
print(f"Git commit: {vitals['git']['commit']}")
```

### Using the test script

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

⚠️ **Important:**
- Always set a strong `ADMIN_PASSWORD` in production
- Use HTTPS when accessing this endpoint over the network
- Keep the password secret and rotate it regularly
- Monitor access to the endpoint for suspicious activity
- The default password (`admin_secret_123`) should only be used for development

## Error Responses

### Unauthorized (401)
```bash
curl "http://localhost:15090/api/admin/vitals?password=wrong"
# Response: "Unauthorized"
```

### Missing Password

```bash
curl "http://localhost:15090/api/admin/vitals"
# Response: "Unauthorized"
```
