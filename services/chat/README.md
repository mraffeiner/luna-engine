# chat-service

Live chat input for [Luna Engine](../../README.md). It reads **Twitch** and **YouTube** live chat and forwards each message to the dashboard over a WebSocket, where it becomes part of Luna's prompt.

- **Twitch:** a twitchio IRC bot joins the configured channels and pushes messages in real time.
- **YouTube:** uses the YouTube Data API with Google OAuth. Messages are polled **on demand**: the dashboard calls `/youtube/poll` after each of Luna's replies, which keeps API quota use low.

- **Stack:** Python 3.11, FastAPI, twitchio, google-api-python-client
- **Port:** 8005
- **Proxied by Luna Engine at:** `/api/chat/`

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `GET` | `/status` | Connection status per platform, e.g. `{ "twitch": "connected", "youtube": "auth_required" }` |
| `GET` | `/auth-url` | Google OAuth URL to open in the browser, or a message explaining why none is needed |
| `GET` | `/oauth2callback` | OAuth redirect target. Stores the token and finishes YouTube auth |
| `POST` | `/connect/twitch` | Connects to Twitch |
| `POST` | `/disconnect/twitch` | Disconnects from Twitch |
| `POST` | `/connect/youtube` | Starts the YouTube poller, which finds the channel's active live chat |
| `POST` | `/disconnect/youtube` | Stops the YouTube poller |
| `GET` | `/youtube/poll` | Fetches new YouTube messages and broadcasts them on `/ws` |
| `WS` | `/ws` | Broadcasts chat messages and status updates |

Chat message format:

```json
{ "platform": "twitch", "channel": "mychannel", "author": "viewer", "text": "hi Luna", "timestamp": "..." }
```

Possible status values: `disconnected`, `connecting`, `connected`, `authenticated`, `auth_required`, `error`, `error_config`, `error_api`, `error_auth`, `error_quota`, `error_chat_ended` and `error_no_live_chat`.

Interactive docs: http://localhost:8005/docs

## Configuration

Copy `.env.example` to `.env` and fill it in:

| Variable | Default | Description |
|---|---|---|
| `TWITCH_OAUTH_TOKEN` | | Chat OAuth token for the bot account. The `oauth:` prefix is optional |
| `TWITCH_CLIENT_ID` | | Twitch application client ID |
| `TWITCH_NICK` | | Bot account username |
| `TWITCH_CHANNELS` | | Comma-separated list of channels to join |
| `YOUTUBE_CHANNEL_ID` | | Your channel ID. It must be set, but it's only used as a label: the live chat is found through the active broadcast of the Google account you log in with |
| `GOOGLE_CLIENT_SECRETS_FILE` | `/app/youtube_secret.json` | OAuth client secrets file |
| `GOOGLE_CREDENTIALS_STORE_DIR` | `/app/credentials` | Where the OAuth token (`youtube_token.pickle`) is saved |
| `OAUTH_REDIRECT_URI` | `http://localhost:8005/oauth2callback` | Must match the redirect URI registered in Google Cloud |
| `LOG_LEVEL` | `INFO` | Python log level |
| `HOST`, `PORT`, `WS_PING_INTERVAL`, `WS_PING_TIMEOUT` | `0.0.0.0`, `8005`, `20`, `20` | Only used by `python -m src.main`. The Docker image starts uvicorn with these values as flags |

### YouTube setup

1. In Google Cloud Console, enable the **YouTube Data API v3**.
2. Create an **OAuth client ID** of type *Web application* and add `http://localhost:8005/oauth2callback` as a redirect URI.
3. Download the client JSON and save it as `youtube_secret.json` in `services/chat/`. It is git-ignored, and compose mounts it read-only.
4. In the dashboard's Chat page, click **Connect YouTube**, open the auth URL and grant access. The token is saved and refreshed automatically after that.


## Running

**With the rest of the stack (recommended):** from the repo root, run `docker compose up -d --build chat-service`.

**Locally (without Docker):** set `GOOGLE_CLIENT_SECRETS_FILE` and `GOOGLE_CREDENTIALS_STORE_DIR` to local paths first.

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.in
uvicorn src.main:app --host 0.0.0.0 --port 8005 --reload
```

## Project layout

```
src/
├── main.py                 # app + OAuth callback
├── config.py               # env config, status enums
├── routers/chat.py         # REST endpoints
├── core/                   # lifespan, WebSocket endpoint and manager
├── services/               # chat orchestrator, status manager
└── platforms/
    ├── twitch/client.py    # twitchio bot
    └── youtube/            # OAuth + live chat poller
```

## Troubleshooting

### YouTube asks to log in again after an update
The OAuth token in `/app/credentials` isn't stored on a volume, so it's lost each time the container is recreated. To keep it, add a volume such as `./services/chat/credentials:/app/credentials` to the service in `docker-compose.yml` (the folder is git-ignored).

### YouTube status is `error_no_live_chat`
The service finds the chat through the logged-in account's active broadcast. Start the stream first, and log in with the account that owns it.

### YouTube status is `error_quota`
The YouTube Data API's daily quota is used up. It resets at midnight Pacific time.

### The OAuth flow fails with a redirect URI mismatch
`OAUTH_REDIRECT_URI` must exactly match a redirect URI registered for the OAuth client in Google Cloud.

## License

[MIT](../../LICENSE) © Matthias Raffeiner
