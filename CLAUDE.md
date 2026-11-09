# CLAUDE.md: chat-service

Part of the **Luna Engine** multi-repo system (AI VTuber). Sibling repos live in `../`, and the hub is `../luna-engine` (read its `CLAUDE.md` for the big picture). This service collects **Twitch** and **YouTube** live chat and broadcasts each message to the dashboard over a WebSocket, where it becomes prompt input. See `README.md` for the API, env vars and OAuth setup.

- **Stack:** Python 3.11, FastAPI, uvicorn, twitchio, google-api-python-client, google-auth-oauthlib
- **Port:** 8005. The UI reaches it through Nginx at `/api/chat/`
- **Entry point:** `src.main:app`. Unlike the other Python services, this one is split into modules

## Commands

```bash
# from ../luna-engine (normal workflow)
docker compose up -d --build chat-service
docker compose logs -f chat-service

# standalone / local (set GOOGLE_* paths to local files first)
docker compose up -d --build
pip install -r requirements.in && uvicorn src.main:app --port 8005 --reload
```

There are no tests. Verify with `curl localhost:8005/status`, connect a platform through `POST /connect/<platform>`, and watch `ws://localhost:8005/ws` (e.g. `websocat`).

## Code map

```
src/main.py                         app setup + GET /oauth2callback (Google OAuth redirect)
src/config.py                       env config, Platform + ConnectionStatus enums, state keys
src/routers/chat.py                 REST: /status, /auth-url, /connect|disconnect/{twitch,youtube}, /youtube/poll
src/core/lifespan.py                creates WS manager, status manager, orchestrator on app.state
src/core/websocket.py, websocket_manager.py   /ws endpoint + broadcast to all clients
src/core/dependencies.py            FastAPI deps that pull objects from app.state
src/services/chat_orchestrator.py   owns platform clients/tasks, connect/disconnect logic
src/services/status_manager.py      per-platform ConnectionStatus; broadcasts changes over WS
src/platforms/twitch/client.py      twitchio bot; pushes messages in real time
src/platforms/youtube/auth.py       OAuth flow, token pickle load/refresh/save
src/platforms/youtube/poller.py     finds active liveChatId, fetches messages on demand
src/utils/logging_config.py         logging setup
```

## How it works

- Shared objects live on `app.state` under the keys in `config.py` (`STATE_WS_MANAGER`, `STATE_CHAT_ORCHESTRATOR`) and are injected through `core/dependencies.py`.
- Broadcast message shape: `{platform, channel, author, text, timestamp}`. Status changes are broadcast as well.
- YouTube is polled **on demand**: the UI calls `GET /youtube/poll` after each of Luna's replies, and only while YouTube is `connected`. This keeps API quota use low, so don't switch it to continuous polling without a reason.
- `ConnectionStatus` has YouTube-specific states (`auth_required`, `error_quota`, `error_chat_ended`, `error_no_live_chat`). The UI relies on these exact string values.

## Gotchas

- The OAuth token is pickled to `$GOOGLE_CREDENTIALS_STORE_DIR/youtube_token.pickle` (`/app/credentials`). That path isn't on a volume, so you have to log in again after the container is recreated.
- compose mounts `./youtube_secret.json` read-only, and the file must exist for compose to start.
- `OAUTH_REDIRECT_URI` must match the redirect URI registered in Google Cloud (default `http://localhost:8005/oauth2callback`).

## Cross-repo contract

Consumer: `../luna-engine/src/lib/pages/services/chat/chatService.ts` (`chatService`, `platformStatus`). The engine loop in `EnginePage.svelte` triggers the YouTube polls.

## Working rules

- Default branch is `development`. Use feature branches and don't push unless asked.
- Never read or print `.env`, `youtube_secret.json` or `credentials/`, which hold OAuth secrets and tokens (enforced in `.claude/settings.json`).
